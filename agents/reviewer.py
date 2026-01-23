"""
智能体7：审稿人专家
"""
from typing import Dict, Any
from .base_agent import BaseAgent
from .schemas import REVIEWER_SCHEMA
from prompts.reviewer import SYSTEM_PROMPT, get_task_prompt


class ReviewerAgent(BaseAgent):
    """
    审稿人专家
    负责对完整研究进行定性和定量评审打分
    """

    def __init__(self, custom_config: Dict[str, Any] = None):
        super().__init__("reviewer", custom_config)

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT    
    def get_output_schema(self) -> Dict[str, Any]:
        return REVIEWER_SCHEMA

    def get_task_prompt(self, **kwargs) -> str:
        research_topic = kwargs.get("research_topic", "")
        variable_system = kwargs.get("variable_system", "")
        theory_framework = kwargs.get("theory_framework", "")
        model_design = kwargs.get("model_design", "")
        data_analysis = kwargs.get("data_analysis", "")
        final_report = kwargs.get("final_report", "")

        return get_task_prompt(
            research_topic=research_topic,
            variable_system=variable_system,
            theory_framework=theory_framework,
            model_design=model_design,
            data_analysis=data_analysis,
            final_report=final_report
        )

    def process_output(self, raw_output: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        result = super().process_output(raw_output, input_data)
        
        parsed = result.get("parsed_data", {})
        result["review_report"] = parsed
        result["research_topic"] = input_data.get("research_topic")
        
        return result
