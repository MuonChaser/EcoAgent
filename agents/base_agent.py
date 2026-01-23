"""
基础智能体类
"""

import json
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.callbacks import BaseCallbackHandler
from pydantic import BaseModel, ValidationError
from loguru import logger

from config.config import AGENT_CONFIG, API_KEY, API_BASE, ENABLE_TRACING, LANGCHAIN_PROJECT
from agents.schemas import get_schema_class


class ResearchCallbackHandler(BaseCallbackHandler):
    """
    自定义回调处理器 - 记录 Agent 执行过程
    提供 LLM 调用的可观测性
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs):
        """LLM 开始调用时触发"""
        logger.debug(f"[{self.agent_name}] LLM Start - Prompts: {len(prompts)} messages")

    def on_llm_end(self, response, **kwargs):
        """LLM 调用结束时触发"""
        # 提取 token 使用信息
        if hasattr(response, 'llm_output') and response.llm_output:
            token_usage = response.llm_output.get('token_usage', {})
            if token_usage:
                prompt_tokens = token_usage.get('prompt_tokens', 0)
                completion_tokens = token_usage.get('completion_tokens', 0)
                total_tokens = token_usage.get('total_tokens', 0)
                logger.info(
                    f"[{self.agent_name}] LLM End - "
                    f"Tokens: {total_tokens} (prompt: {prompt_tokens}, completion: {completion_tokens})"
                )
        else:
            logger.debug(f"[{self.agent_name}] LLM End")

    def on_llm_error(self, error: Exception, **kwargs):
        """LLM 调用出错时触发"""
        logger.error(f"[{self.agent_name}] LLM Error: {error}")

    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs):
        """Chain 开始时触发"""
        logger.debug(f"[{self.agent_name}] Chain Start")

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs):
        """Chain 结束时触发"""
        logger.debug(f"[{self.agent_name}] Chain End")


class BaseAgent(ABC):
    """
    基础智能体抽象类
    """
    
    def __init__(
        self,
        agent_type: str,
        custom_config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化智能体
        
        Args:
            agent_type: 智能体类型，对应配置中的key
            custom_config: 自定义配置，会覆盖默认配置
        """
        self.agent_type = agent_type
        
        # 获取配置
        config = AGENT_CONFIG.get(agent_type, {})
        if custom_config:
            config.update(custom_config)
        
        self.name = config.get("name", agent_type)
        self.model_name = config.get("model")
        self.temperature = config.get("temperature", 0.7)
        
        # 初始化LLM（支持阿里云通义千问）
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            openai_api_key=API_KEY,
            openai_api_base=API_BASE,
        )

        # 初始化 Pydantic Output Parser
        try:
            output_schema_class = get_schema_class(agent_type)
            self.output_parser = PydanticOutputParser(pydantic_object=output_schema_class)
            self.use_pydantic_parser = True
            logger.info(f"使用 PydanticOutputParser: {output_schema_class.__name__}")
        except Exception as e:
            logger.warning(f"PydanticOutputParser 初始化失败: {e}, 将使用传统 JSON 解析")
            self.output_parser = None
            self.use_pydantic_parser = False

        # 初始化 Callbacks
        self.callbacks = []

        # 添加自定义 callback handler
        self.callbacks.append(ResearchCallbackHandler(self.name))

        # 如果启用 LangSmith tracing，会自动添加 LangChainTracer
        if ENABLE_TRACING:
            logger.info(f"LangSmith tracing 已启用，项目: {LANGCHAIN_PROJECT}")

        logger.info(f"初始化智能体: {self.name} (模型: {self.model_name}, 温度: {self.temperature})")
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        获取系统提示词
        
        Returns:
            系统提示词字符串
        """
        pass
    
    @abstractmethod
    def get_task_prompt(self, **kwargs) -> str:
        """
        获取任务提示词
        
        Args:
            **kwargs: 任务相关参数
            
        Returns:
            任务提示词字符串
        """
        pass
    
    @abstractmethod
    def get_output_schema(self) -> Dict[str, Any]:
        """
        获取输出JSON Schema
        
        Returns:
            输出格式的JSON Schema定义
        """
        pass
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行智能体任务
        
        Args:
            input_data: 输入数据
            
        Returns:
            执行结果
        """
        try:
            logger.info(f"{self.name} 开始执行任务")
            
            # 构建提示词
            system_prompt = self.get_system_prompt()
            task_prompt = self.get_task_prompt(**input_data)

            # 添加JSON格式要求
            if self.use_pydantic_parser and self.output_parser:
                # 使用 Pydantic Output Parser 的格式指令
                format_instructions = self.output_parser.get_format_instructions()
                json_instruction = f"""

# 输出格式要求

{format_instructions}
"""
            else:
                # 使用传统的 JSON Schema 指令
                output_schema = self.get_output_schema()
                json_instruction = f"""

# 输出格式要求

请严格按照以下JSON格式输出，不要使用Markdown表格或其他格式。

输出JSON Schema:
{json.dumps(output_schema, ensure_ascii=False, indent=2)}

请直接输出符合上述schema的JSON对象。
"""

            full_task_prompt = task_prompt + json_instruction
            
            # 调用LLM（带 callbacks）
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=full_task_prompt)
            ]

            response = self.llm.invoke(
                messages,
                config={
                    "callbacks": self.callbacks,
                    "tags": [self.agent_type, self.name]
                }
            )
            
            # 处理输出
            result = self.process_output(response.content, input_data)
            
            logger.info(f"{self.name} 任务完成")
            return result
            
        except Exception as e:
            logger.error(f"{self.name} 执行失败: {str(e)}")
            raise
    
    def process_output(self, raw_output: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理LLM输出，提取JSON格式数据

        Args:
            raw_output: LLM原始输出
            input_data: 输入数据

        Returns:
            处理后的结果
        """
        parsed_data = None

        # 尝试使用 Pydantic Output Parser
        if self.use_pydantic_parser and self.output_parser:
            try:
                pydantic_output = self.output_parser.parse(raw_output)
                parsed_data = pydantic_output.dict()
                logger.debug(f"{self.name} Pydantic 解析成功")
            except ValidationError as e:
                logger.warning(f"{self.name} Pydantic 验证失败: {e}, 使用 fallback")
                parsed_data = None
            except Exception as e:
                logger.warning(f"{self.name} Pydantic 解析失败: {e}, 使用 fallback")
                parsed_data = None

        # Fallback: 使用传统 JSON 提取
        if parsed_data is None:
            parsed_data = self._extract_json(raw_output)

        return {
            "agent_type": self.agent_type,
            "agent_name": self.name,
            "raw_output": raw_output,
            "parsed_data": parsed_data,
            "input_data": input_data,
        }
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        从文本中提取JSON内容
        
        Args:
            text: 包含JSON的文本
            
        Returns:
            解析后的JSON对象，如果解析失败返回原始文本
        """
        try:
            # 尝试提取代码块中的内容
            json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                return json.loads(json_str)
            
            # 尝试直接解析整个文本
            # 查找第一个 { 和最后一个 } 之间的内容
            first_brace = text.find('{')
            last_brace = text.rfind('}')
            if first_brace != -1 and last_brace != -1:
                json_str = text[first_brace:last_brace+1]
                return json.loads(json_str)
            
            logger.warning(f"{self.name} 无法提取JSON格式，返回原始输出")
            return {"raw_text": text}
            
        except json.JSONDecodeError as e:
            logger.warning(f"{self.name} JSON解析失败: {str(e)}，返回原始输出")
            return {"raw_text": text}
        except Exception as e:
            logger.error(f"{self.name} 提取JSON时出错: {str(e)}")
            return {"raw_text": text}
    
    def validate_input(self, input_data: Dict[str, Any], required_keys: List[str]) -> bool:
        """
        验证输入数据
        
        Args:
            input_data: 输入数据
            required_keys: 必需的键列表
            
        Returns:
            是否验证通过
        """
        for key in required_keys:
            if key not in input_data:
                raise ValueError(f"{self.name} 缺少必需参数: {key}")
        return True
