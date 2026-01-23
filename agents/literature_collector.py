"""
智能体1：文献搜集专家
"""
from typing import Dict, Any
from .base_agent import BaseAgent
from prompts.literature_collector import SYSTEM_PROMPT, get_task_prompt


class LiteratureCollectorAgent(BaseAgent):
    """
    文献搜集专家
    负责搜集和分析经济学文献
    """

    def __init__(self, custom_config: Dict[str, Any] = None):
        super().__init__("literature_collector", custom_config)

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT
    
    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "literature_list": {
                    "type": "array",
                    "description": "文献列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "number", "description": "序号"},
                            "authors": {"type": "string", "description": "作者"},
                            "year": {"type": "number", "description": "年份"},
                            "title": {"type": "string", "description": "论文标题"},
                            "journal": {"type": "string", "description": "期刊名称"},
                            "variable_x": {
                                "type": "object",
                                "properties": {
                                    "definition": {"type": "string", "description": "X的定义"},
                                    "measurement": {"type": "string", "description": "X的衡量方式"}
                                }
                            },
                            "variable_y": {
                                "type": "object",
                                "properties": {
                                    "definition": {"type": "string", "description": "Y的定义"},
                                    "measurement": {"type": "string", "description": "Y的衡量方式"}
                                }
                            },
                            "core_conclusion": {"type": "string", "description": "核心结论（量化）"},
                            "theoretical_mechanism": {"type": "array", "items": {"type": "string"}, "description": "理论机制列表"},
                            "data_source": {"type": "string", "description": "数据来源"},
                            "heterogeneity_dimensions": {"type": "array", "items": {"type": "string"}, "description": "异质性维度"},
                            "identification_strategy": {"type": "string", "description": "识别策略"},
                            "limitations": {"type": "array", "items": {"type": "string"}, "description": "研究不足"}
                        },
                        "required": ["id", "authors", "year", "title", "journal"]
                    }
                },
                "summary": {
                    "type": "object",
                    "properties": {
                        "total_papers": {"type": "number", "description": "总文献数"},
                        "main_findings": {"type": "array", "items": {"type": "string"}, "description": "主要发现"},
                        "research_gaps": {"type": "array", "items": {"type": "string"}, "description": "研究空白"}
                    }
                }
            },
            "required": ["literature_list"]
        }
    
    def get_task_prompt(self, **kwargs) -> str:
        research_topic = kwargs.get("research_topic", "")
        keyword_group_a = kwargs.get("keyword_group_a", [])
        keyword_group_b = kwargs.get("keyword_group_b", [])
        min_papers = kwargs.get("min_papers", 10)

        return get_task_prompt(
            research_topic=research_topic,
            keyword_group_a=keyword_group_a,
            keyword_group_b=keyword_group_b,
            min_papers=min_papers
        )
    
    def process_output(self, raw_output: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        result = super().process_output(raw_output, input_data)
        
        parsed = result.get("parsed_data", {})
        result["literature_list"] = parsed.get("literature_list", [])
        result["literature_summary"] = parsed  # 保留完整的解析数据
        result["research_topic"] = input_data.get("research_topic")
        
        return result
