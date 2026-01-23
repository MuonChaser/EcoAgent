"""
智能体4：计量模型专家
"""
from typing import Dict, Any
from .base_agent import BaseAgent
from .schemas import MODEL_DESIGNER_SCHEMA
from prompts.model_designer import SYSTEM_PROMPT, get_task_prompt


class ModelDesignerAgent(BaseAgent):
    """
    计量模型专家
    负责选择和构建计量经济学模型
    """

    def __init__(self, custom_config: Dict[str, Any] = None):
        super().__init__("model_designer", custom_config)

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT
    
    def get_output_schema(self) -> Dict[str, Any]:
        return MODEL_DESIGNER_SCHEMA
    
    def get_task_prompt(self, **kwargs) -> str:
        research_topic = kwargs.get("research_topic", "")
        variable_system = kwargs.get("variable_system", "")
        theory_framework = kwargs.get("theory_framework", "")

        return get_task_prompt(
            research_topic=research_topic,
            variable_system=variable_system,
            theory_framework=theory_framework
        )
    def process_output(self, raw_output: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        result = super().process_output(raw_output, input_data)
        
        parsed = result.get("parsed_data", {})
        result["model_design"] = parsed
        result["research_topic"] = input_data.get("research_topic")
        
        return result
