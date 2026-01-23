"""
智能体2：指标设置专家
"""
from typing import Dict, Any
from .base_agent import BaseAgent
from .schemas import VARIABLE_DESIGNER_SCHEMA
from prompts.variable_designer import SYSTEM_PROMPT, get_task_prompt


class VariableDesignerAgent(BaseAgent):
    """
    指标设置专家
    负责设置研究变量和代理变量
    """

    def __init__(self, custom_config: Dict[str, Any] = None):
        super().__init__("variable_designer", custom_config)

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT    
    def get_output_schema(self) -> Dict[str, Any]:
        return VARIABLE_DESIGNER_SCHEMA

    def get_task_prompt(self, **kwargs) -> str:
        research_topic = kwargs.get("research_topic", "")
        literature_summary = kwargs.get("literature_summary", "")
        variable_x = kwargs.get("variable_x", "")
        variable_y = kwargs.get("variable_y", "")
        parsed_input = kwargs.get("parsed_input", "")

        return get_task_prompt(
            research_topic=research_topic,
            literature_summary=literature_summary,
            variable_x=variable_x,
            variable_y=variable_y,
            parsed_input=parsed_input
        )
    
    def process_output(self, raw_output: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        result = super().process_output(raw_output, input_data)
        
        parsed = result.get("parsed_data", {})
        result["variable_system"] = parsed
        result["research_topic"] = input_data.get("research_topic")
        
        return result
