"""
智能体5：数据分析专家
"""
from typing import Dict, Any
from .base_agent import BaseAgent
from .schemas import DATA_ANALYST_SCHEMA
from prompts.data_analyst import SYSTEM_PROMPT, get_task_prompt


class DataAnalystAgent(BaseAgent):
    """
    数据分析专家
    负责执行数据预处理、统计分析和模型估计
    """

    def __init__(self, custom_config: Dict[str, Any] = None):
        super().__init__("data_analyst", custom_config)

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT
    
    def get_output_schema(self) -> Dict[str, Any]:
        return DATA_ANALYST_SCHEMA
    
    def get_task_prompt(self, **kwargs) -> str:
        research_topic = kwargs.get("research_topic", "")
        variable_system = kwargs.get("variable_system", "")
        theory_framework = kwargs.get("theory_framework", "")
        model_design = kwargs.get("model_design", "")
        data_info = kwargs.get("data_info", "")

        return get_task_prompt(
            research_topic=research_topic,
            variable_system=variable_system,
            theory_framework=theory_framework,
            model_design=model_design,
            data_info=data_info
        )

    def process_output(self, raw_output: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        result = super().process_output(raw_output, input_data)
        
        parsed = result.get("parsed_data", {})
        result["data_analysis"] = parsed
        result["research_topic"] = input_data.get("research_topic")
        
        return result
