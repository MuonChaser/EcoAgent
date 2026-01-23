"""
智能体0：输入解析专家
"""
from typing import Dict, Any
from .base_agent import BaseAgent
from prompts.input_parser import SYSTEM_PROMPT, get_task_prompt


class InputParserAgent(BaseAgent):
    """
    输入解析专家
    负责解析用户的初始研究意图，提取核心变量X和Y
    """

    def __init__(self, custom_config: Dict[str, Any] = None):
        super().__init__("input_parser", custom_config)

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT
    
    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "research_topic": {
                    "type": "string",
                    "description": "标准的学术表述的研究主题"
                },
                "research_subtitle": {
                    "type": "string",
                    "description": "副标题建议，如'——基于XX的证据'"
                },
                "variable_x": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "变量名称"},
                        "nature": {"type": "string", "description": "变量性质"},
                        "chinese": {"type": "string", "description": "中文规范表述"},
                        "english": {"type": "string", "description": "英文规范表述"},
                        "related_concepts": {"type": "array", "items": {"type": "string"}, "description": "相关概念列表"},
                        "measurement_dimensions": {"type": "array", "items": {"type": "string"}, "description": "可能的测量维度"}
                    }
                },
                "variable_y": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "变量名称"},
                        "nature": {"type": "string", "description": "变量性质"},
                        "chinese": {"type": "string", "description": "中文规范表述"},
                        "english": {"type": "string", "description": "英文规范表述"},
                        "related_concepts": {"type": "array", "items": {"type": "string"}, "description": "相关概念列表"},
                        "measurement_dimensions": {"type": "array", "items": {"type": "string"}, "description": "可能的测量维度"}
                    }
                },
                "relationship": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "description": "关系类型"},
                        "direction": {"type": "string", "description": "预期方向"},
                        "level": {"type": "string", "description": "研究层次"}
                    }
                },
                "research_context": {
                    "type": "object",
                    "properties": {
                        "time_range": {"type": "string", "description": "时间范围"},
                        "space_range": {"type": "string", "description": "空间范围"},
                        "sample_characteristics": {"type": "string", "description": "样本特征"},
                        "policy_background": {"type": "string", "description": "政策背景"}
                    }
                },
                "keywords": {
                    "type": "object",
                    "properties": {
                        "group_a_chinese": {"type": "array", "items": {"type": "string"}, "description": "关键词组A中文"},
                        "group_a_english": {"type": "array", "items": {"type": "string"}, "description": "关键词组A英文"},
                        "group_b_chinese": {"type": "array", "items": {"type": "string"}, "description": "关键词组B中文"},
                        "group_b_english": {"type": "array", "items": {"type": "string"}, "description": "关键词组B英文"}
                    }
                }
            },
            "required": ["research_topic", "variable_x", "variable_y", "keywords"]
        }
    
    def get_task_prompt(self, **kwargs) -> str:
        user_input = kwargs.get("user_input", "")
        return get_task_prompt(user_input)
    
    def process_output(self, raw_output: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        result = super().process_output(raw_output, input_data)
        
        # 从解析后的数据中提取关键信息
        parsed = result.get("parsed_data", {})
        
        result["research_topic"] = parsed.get("research_topic", input_data.get("user_input"))
        result["variable_x"] = parsed.get("variable_x", {})
        result["variable_y"] = parsed.get("variable_y", {})
        result["keywords"] = parsed.get("keywords", {})
        result["user_input"] = input_data.get("user_input")
        
        return result
