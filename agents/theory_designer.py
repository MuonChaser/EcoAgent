"""
智能体3：理论设置专家
"""
from typing import Dict, Any
from .base_agent import BaseAgent
from .schemas import THEORY_DESIGNER_SCHEMA
from prompts.theory_designer import SYSTEM_PROMPT, get_task_prompt


class TheoryDesignerAgent(BaseAgent):
    """
    理论设置专家
    负责梳理理论并提出研究假设
    """

    def __init__(self, custom_config: Dict[str, Any] = None):
        super().__init__("theory_designer", custom_config)

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT    
    def get_output_schema(self) -> Dict[str, Any]:
        return THEORY_DESIGNER_SCHEMA

    def get_task_prompt(self, **kwargs) -> str:
        research_topic = kwargs.get("research_topic", "")
        variable_system = kwargs.get("variable_system", "")
        literature_summary = kwargs.get("literature_summary", "")

        return get_task_prompt(
            research_topic=research_topic,
            variable_system=variable_system,
            literature_summary=literature_summary
        )
    def process_output(self, raw_output: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        result = super().process_output(raw_output, input_data)
        
        parsed = result.get("parsed_data", {})
        result["theory_framework"] = parsed
        result["research_topic"] = input_data.get("research_topic")
        
        return result
