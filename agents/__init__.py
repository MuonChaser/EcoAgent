"""
智能体模块

包含以下智能体:
- BaseAgent: 基础智能体抽象类
- InputParserAgent: 输入解析专家
- LiteratureCollectorAgent: 文献搜集专家
- VariableDesignerAgent: 变量设计专家
- TheoryDesignerAgent: 理论设计专家
- ModelDesignerAgent: 模型设计专家
- DataAnalystAgent: 数据分析专家（支持读取本地数据）
- ReportWriterAgent: 报告撰写专家
- ReviewerAgent: 审稿人专家
- EnhancedReviewerAgent: 增强版审稿人

DataAnalystAgent 已集成数据工具功能:
- search_data(): 搜索数据集
- preview_dataset(): 预览数据
- get_data_statistics(): 获取统计信息
- query_data(): 查询数据
- run_with_data(): 使用指定数据文件运行分析
"""
from .base_agent import BaseAgent
from .input_parser import InputParserAgent
from .literature_collector import LiteratureCollectorAgent
from .variable_designer import VariableDesignerAgent
from .theory_designer import TheoryDesignerAgent
from .model_designer import ModelDesignerAgent
from .data_analyst import DataAnalystAgent
from .report_writer import ReportWriterAgent
from .reviewer import ReviewerAgent
from .enhanced_reviewer import EnhancedReviewerAgent

__all__ = [
    "BaseAgent",
    "InputParserAgent",
    "LiteratureCollectorAgent",
    "VariableDesignerAgent",
    "TheoryDesignerAgent",
    "ModelDesignerAgent",
    "DataAnalystAgent",
    "ReportWriterAgent",
    "ReviewerAgent",
    "EnhancedReviewerAgent",
]
