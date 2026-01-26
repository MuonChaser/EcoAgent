"""
智能体6：长文报告专家
"""
from typing import Dict, Any
from .base_agent import BaseAgent
from .schemas import REPORT_WRITER_SCHEMA
from prompts.report_writer import SYSTEM_PROMPT, get_task_prompt


class ReportWriterAgent(BaseAgent):
    """
    长文报告专家
    负责撰写完整的学术论文
    """

    def __init__(self, custom_config: Dict[str, Any] = None):
        super().__init__("report_writer", custom_config)

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT
    
    def get_output_schema(self) -> Dict[str, Any]:
        return REPORT_WRITER_SCHEMA
    
    def get_task_prompt(self, **kwargs) -> str:
        research_topic = kwargs.get("research_topic", "")
        literature_summary = kwargs.get("literature_summary", "")
        variable_system = kwargs.get("variable_system", "")
        theory_framework = kwargs.get("theory_framework", "")
        model_design = kwargs.get("model_design", "")
        data_analysis = kwargs.get("data_analysis", "")
        word_count = kwargs.get("word_count", 8000)

        return get_task_prompt(
            research_topic=research_topic,
            literature_summary=literature_summary,
            variable_system=variable_system,
            theory_framework=theory_framework,
            model_design=model_design,
            data_analysis=data_analysis,
            word_count=word_count
        )

    def process_output(self, raw_output: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        result = super().process_output(raw_output, input_data)

        # 优先从 parsed_data 中提取 latex_source
        parsed_data = result.get("parsed_data", {})
        if parsed_data and isinstance(parsed_data, dict):
            latex_source = parsed_data.get("latex_source")
            if latex_source:
                result["final_report"] = latex_source
            else:
                result["final_report"] = raw_output
        else:
            result["final_report"] = raw_output

        result["research_topic"] = input_data.get("research_topic")
        result["word_count"] = input_data.get("word_count", 8000)
        return result
