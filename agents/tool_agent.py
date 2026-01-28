"""
支持工具调用的智能体基类
Extends BaseAgent with tool-calling capabilities
"""

from typing import Dict, Any, List, Optional, Callable
from langchain_core.tools import Tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from loguru import logger

from .base_agent import BaseAgent


class ToolAgent(BaseAgent):
    """
    支持工具调用的智能体基类

    子类可以通过实现 get_tools() 方法来提供可用工具
    """

    def __init__(
        self,
        agent_type: str,
        custom_config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(agent_type, custom_config)

        # 获取并绑定工具
        self.tools = self.get_tools()
        if self.tools:
            self.llm_with_tools = self.llm.bind_tools(self.tools)
            logger.info(f"{self.name} 已绑定 {len(self.tools)} 个工具: {[t.name for t in self.tools]}")
        else:
            self.llm_with_tools = self.llm
            logger.info(f"{self.name} 未配置工具")

    def get_tools(self) -> List[Tool]:
        """
        获取可用工具列表

        子类应该重写此方法来提供工具

        Returns:
            工具列表
        """
        return []

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行智能体任务（支持工具调用）

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

            # 如果没有工具，使用父类的标准流程
            if not self.tools:
                return super().run(input_data)

            # 有工具时，使用 agent loop
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=task_prompt)
            ]

            # Agent loop：最多迭代 10 次
            max_iterations = 10
            iteration = 0
            tool_results = []

            while iteration < max_iterations:
                iteration += 1
                logger.debug(f"{self.name} 执行第 {iteration} 次迭代")

                # 调用 LLM
                response = self.llm_with_tools.invoke(
                    messages,
                    config={
                        "callbacks": self.callbacks,
                        "tags": [self.agent_type, self.name]
                    }
                )

                messages.append(response)

                # 检查是否需要调用工具
                if not response.tool_calls:
                    # 没有工具调用，任务完成
                    logger.info(f"{self.name} 完成，共执行 {iteration} 次迭代，调用了 {len(tool_results)} 个工具")

                    # 处理最终输出
                    result = self.process_output(response.content, input_data)
                    result["tool_calls"] = tool_results
                    return result

                # 执行工具调用
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool_id = tool_call["id"]

                    logger.info(f"{self.name} 调用工具: {tool_name}，参数: {tool_args}")

                    # 查找工具
                    tool = next((t for t in self.tools if t.name == tool_name), None)
                    if not tool:
                        error_msg = f"未找到工具: {tool_name}"
                        logger.error(error_msg)
                        messages.append(ToolMessage(
                            content=error_msg,
                            tool_call_id=tool_id
                        ))
                        continue

                    # 执行工具
                    try:
                        tool_result = tool.invoke(tool_args)
                        tool_result_str = str(tool_result)

                        # 记录工具调用
                        tool_results.append({
                            "tool": tool_name,
                            "args": tool_args,
                            "result": tool_result
                        })

                        logger.info(f"{self.name} 工具 {tool_name} 执行成功")
                        logger.debug(f"工具结果: {tool_result_str[:200]}...")

                        messages.append(ToolMessage(
                            content=tool_result_str,
                            tool_call_id=tool_id
                        ))

                    except Exception as e:
                        error_msg = f"工具执行失败: {str(e)}"
                        logger.error(f"{self.name} {error_msg}")
                        messages.append(ToolMessage(
                            content=error_msg,
                            tool_call_id=tool_id
                        ))

            # 达到最大迭代次数
            logger.warning(f"{self.name} 达到最大迭代次数 {max_iterations}")

            # 返回最后一次响应
            final_response = messages[-1]
            result = self.process_output(
                final_response.content if hasattr(final_response, 'content') else str(final_response),
                input_data
            )
            result["tool_calls"] = tool_results
            result["max_iterations_reached"] = True

            return result

        except Exception as e:
            logger.error(f"{self.name} 执行失败: {str(e)}")
            raise
