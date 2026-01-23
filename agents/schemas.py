"""
智能体输出 Schema 定义 - Pydantic 模型版本
使用 Pydantic 进行结构化输出解析，替代原有的 JSON Schema
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Literal
from enum import Enum


# ==================== InputParser Agent Schema ====================

class VariableInfo(BaseModel):
    """变量信息"""
    name: str = Field(description="变量名称")
    nature: str = Field(description="变量性质")
    chinese: str = Field(description="中文规范表述")
    english: str = Field(description="英文规范表述")
    related_concepts: List[str] = Field(default_factory=list, description="相关概念列表")
    measurement_dimensions: List[str] = Field(default_factory=list, description="可能的测量维度")


class RelationshipInfo(BaseModel):
    """变量关系信息"""
    type: str = Field(description="关系类型")
    direction: str = Field(description="预期方向")
    level: str = Field(description="研究层次")


class ResearchContext(BaseModel):
    """研究背景信息"""
    time_range: Optional[str] = Field(default=None, description="时间范围")
    space_range: Optional[str] = Field(default=None, description="空间范围")
    sample_characteristics: Optional[str] = Field(default=None, description="样本特征")
    policy_background: Optional[str] = Field(default=None, description="政策背景")


class Keywords(BaseModel):
    """关键词分组"""
    group_a_chinese: List[str] = Field(default_factory=list, description="关键词组A中文")
    group_a_english: List[str] = Field(default_factory=list, description="关键词组A英文")
    group_b_chinese: List[str] = Field(default_factory=list, description="关键词组B中文")
    group_b_english: List[str] = Field(default_factory=list, description="关键词组B英文")


class InputParserOutput(BaseModel):
    """InputParser Agent 输出模型"""
    research_topic: str = Field(description="标准的学术表述的研究主题")
    research_subtitle: Optional[str] = Field(default=None, description="副标题建议，如'——基于XX的证据'")
    variable_x: VariableInfo = Field(description="解释变量X")
    variable_y: VariableInfo = Field(description="被解释变量Y")
    relationship: Optional[RelationshipInfo] = Field(default=None, description="变量关系")
    research_context: Optional[ResearchContext] = Field(default=None, description="研究背景")
    keywords: Keywords = Field(description="关键词分组")


# ==================== LiteratureCollector Agent Schema ====================

class VariableDef(BaseModel):
    """变量定义"""
    definition: str = Field(description="变量的定义")
    measurement: str = Field(description="变量的衡量方式")


class LiteratureItem(BaseModel):
    """单篇文献信息"""
    id: int = Field(description="序号")
    authors: str = Field(description="作者")
    year: int = Field(description="年份")
    title: str = Field(description="论文标题")
    journal: str = Field(description="期刊名称")
    variable_x: Optional[VariableDef] = Field(default=None, description="X的定义和衡量")
    variable_y: Optional[VariableDef] = Field(default=None, description="Y的定义和衡量")
    core_conclusion: Optional[str] = Field(default=None, description="核心结论（量化）")
    theoretical_mechanism: List[str] = Field(default_factory=list, description="理论机制列表")
    data_source: Optional[str] = Field(default=None, description="数据来源")
    heterogeneity_dimensions: List[str] = Field(default_factory=list, description="异质性维度")
    identification_strategy: Optional[str] = Field(default=None, description="识别策略")
    limitations: List[str] = Field(default_factory=list, description="研究不足")


class LiteratureSummary(BaseModel):
    """文献综述摘要"""
    total_papers: int = Field(description="总文献数")
    main_findings: List[str] = Field(default_factory=list, description="主要发现")
    research_gaps: List[str] = Field(default_factory=list, description="研究空白")


class LiteratureCollectorOutput(BaseModel):
    """LiteratureCollector Agent 输出模型"""
    literature_list: List[LiteratureItem] = Field(description="文献列表")
    summary: Optional[LiteratureSummary] = Field(default=None, description="文献综述摘要")


# ==================== VariableDesigner Agent Schema ====================

class ProxyVariable(BaseModel):
    """代理变量"""
    id: str = Field(description="变量ID")
    name: str = Field(description="变量名称")
    definition: str = Field(description="变量定义")
    economic_rationale: str = Field(description="经济学理论依据")
    measurement: str = Field(description="测量方式")
    data_source: str = Field(description="数据来源")
    literature_support: List[str] = Field(default_factory=list, description="文献支撑")
    processing_method: str = Field(description="数据处理方法")


class CoreVariables(BaseModel):
    """核心变量"""
    explanatory_variable_x: List[ProxyVariable] = Field(description="解释变量X的代理变量列表")
    dependent_variable_y: List[ProxyVariable] = Field(description="被解释变量Y的代理变量列表")


class MediatingModeratingVariable(BaseModel):
    """中介/调节变量"""
    type: Literal["mediating", "moderating"] = Field(description="变量类型")
    id: str = Field(description="变量ID")
    name: str = Field(description="变量名称")
    definition: str = Field(description="变量定义")
    role: str = Field(description="在模型中的作用")
    proxy_variables: List[Dict[str, Any]] = Field(default_factory=list, description="代理变量列表")


class ControlVariable(BaseModel):
    """控制变量"""
    name: str = Field(description="变量名称")
    definition: str = Field(description="变量定义")
    data_source: str = Field(description="数据来源")
    processing_method: str = Field(description="数据处理方法")


class VariableRelationships(BaseModel):
    """变量关系"""
    x_to_z: Optional[str] = Field(default=None, description="X到Z的路径")
    z_to_y: Optional[str] = Field(default=None, description="Z到Y的路径")
    z_moderates_x_y: Optional[str] = Field(default=None, description="Z调节X到Y的效应")


class VariableDesignerOutput(BaseModel):
    """VariableDesigner Agent 输出模型"""
    core_variables: CoreVariables = Field(description="核心变量")
    mediating_moderating_variables: List[MediatingModeratingVariable] = Field(
        default_factory=list, description="中介/调节变量列表"
    )
    control_variables: List[ControlVariable] = Field(description="控制变量列表")
    variable_relationships: Optional[VariableRelationships] = Field(default=None, description="变量关系")
    justification: str = Field(description="变量设置合理性总结")


# ==================== TheoryDesigner Agent Schema ====================

class TheoryFramework(BaseModel):
    """理论框架"""
    theory_name: str = Field(description="理论名称")
    core_content: str = Field(description="核心内容")
    application_logic: str = Field(description="应用逻辑")
    literature_support: List[str] = Field(default_factory=list, description="文献支撑")


class TheoreticalJustification(BaseModel):
    """理论论证"""
    for_variable_x: str = Field(description="对解释变量X的理论依据")
    for_variable_y: str = Field(description="对被解释变量Y的理论依据")
    for_mediating_moderating: Optional[str] = Field(default=None, description="对中介/调节变量的理论依据")


class ResearchHypothesis(BaseModel):
    """研究假设"""
    hypothesis_id: str = Field(description="假设编号")
    hypothesis_name: str = Field(description="假设名称")
    hypothesis_content: str = Field(description="假设内容")
    theoretical_basis: str = Field(description="理论基础")
    derivation_logic: str = Field(description="推导逻辑")
    literature_support: List[str] = Field(default_factory=list, description="文献支撑")


class PotentialMechanisms(BaseModel):
    """潜在机制"""
    policy_shock: bool = Field(description="是否存在政策冲击")
    endogeneity_issues: List[str] = Field(default_factory=list, description="内生性问题")
    data_type: Literal["panel", "cross-section", "time-series"] = Field(description="数据类型")


class TheoryDesignerOutput(BaseModel):
    """TheoryDesigner Agent 输出模型"""
    theoretical_framework: List[TheoryFramework] = Field(description="理论框架列表")
    theoretical_justification: Optional[TheoreticalJustification] = Field(
        default=None, description="理论论证"
    )
    research_hypotheses: List[ResearchHypothesis] = Field(description="研究假设列表")
    potential_mechanisms: Optional[PotentialMechanisms] = Field(default=None, description="潜在机制")
    references: List[str] = Field(default_factory=list, description="参考文献")


# ==================== ModelDesigner Agent Schema ====================

class BaselineModel(BaseModel):
    """基准模型"""
    model_type: str = Field(description="模型类型（如OLS、FE、DID等）")
    rationale: str = Field(description="选择该模型的理由")
    equation: str = Field(description="模型方程（LaTeX格式）")
    variables: Dict[str, Any] = Field(default_factory=dict, description="变量说明")
    expected_signs: Dict[str, Any] = Field(default_factory=dict, description="预期符号")


class MechanismModel(BaseModel):
    """机制检验模型"""
    step: int = Field(description="步骤编号")
    description: str = Field(description="步骤描述")
    equation: str = Field(description="模型方程（LaTeX格式）")


class HeterogeneityModel(BaseModel):
    """异质性检验模型"""
    dimension: str = Field(description="异质性维度")
    groups: List[str] = Field(description="分组列表")
    equation: str = Field(description="模型方程（LaTeX格式）")


class RobustnessCheck(BaseModel):
    """稳健性检验"""
    check_type: str = Field(description="检验类型")
    description: str = Field(description="检验描述")
    equation: str = Field(description="模型方程（LaTeX格式）")


class HypothesisTest(BaseModel):
    """假设检验"""
    hypothesis_id: str = Field(description="假设编号")
    test_method: str = Field(description="检验方法")


class ModelDesignerOutput(BaseModel):
    """ModelDesigner Agent 输出模型"""
    baseline_model: BaselineModel = Field(description="基准模型")
    mechanism_models: List[MechanismModel] = Field(default_factory=list, description="机制检验模型列表")
    heterogeneity_models: List[HeterogeneityModel] = Field(default_factory=list, description="异质性检验模型列表")
    robustness_checks: List[RobustnessCheck] = Field(default_factory=list, description="稳健性检验列表")
    hypothesis_tests: List[HypothesisTest] = Field(default_factory=list, description="假设检验列表")


# ==================== DataAnalyst Agent Schema ====================

class DataPreprocessing(BaseModel):
    """数据预处理"""
    data_sources: List[str] = Field(default_factory=list, description="数据来源")
    sample_size: Dict[str, Any] = Field(default_factory=dict, description="样本量信息")
    cleaning_steps: List[str] = Field(default_factory=list, description="清洗步骤")
    processing_details: str = Field(description="处理细节")


class DescriptiveStatistics(BaseModel):
    """描述性统计"""
    variables: List[Dict[str, Any]] = Field(default_factory=list, description="变量统计信息")
    summary: str = Field(description="统计摘要")


class BaselineRegression(BaseModel):
    """基准回归"""
    results: List[Dict[str, Any]] = Field(default_factory=list, description="回归结果")
    interpretation: str = Field(description="结果解释")
    hypothesis_support: List[str] = Field(default_factory=list, description="支持的假设")


class MechanismAnalysis(BaseModel):
    """机制分析"""
    steps: List[Dict[str, Any]] = Field(default_factory=list, description="分步回归结果")
    mediation_effects: Dict[str, Any] = Field(default_factory=dict, description="中介效应")


class HeterogeneityAnalysis(BaseModel):
    """异质性分析"""
    dimension: str = Field(description="异质性维度")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="分组回归结果")
    interpretation: str = Field(description="结果解释")


class RobustnessCheckResult(BaseModel):
    """稳健性检验结果"""
    check_type: str = Field(description="检验类型")
    results: Dict[str, Any] = Field(default_factory=dict, description="检验结果")
    conclusion: str = Field(description="结论")


class AnalysisConclusions(BaseModel):
    """分析结论"""
    supported_hypotheses: List[str] = Field(default_factory=list, description="支持的假设")
    effect_size: str = Field(description="效应大小")
    robustness: str = Field(description="稳健性评价")


class DataAnalystOutput(BaseModel):
    """DataAnalyst Agent 输出模型"""
    data_preprocessing: Optional[DataPreprocessing] = Field(default=None, description="数据预处理")
    descriptive_statistics: Optional[DescriptiveStatistics] = Field(default=None, description="描述性统计")
    baseline_regression: BaselineRegression = Field(description="基准回归")
    mechanism_analysis: Optional[MechanismAnalysis] = Field(default=None, description="机制分析")
    heterogeneity_analysis: List[HeterogeneityAnalysis] = Field(
        default_factory=list, description="异质性分析列表"
    )
    robustness_checks: List[RobustnessCheckResult] = Field(default_factory=list, description="稳健性检验列表")
    conclusions: Optional[AnalysisConclusions] = Field(default=None, description="分析结论")


# ==================== ReportWriter Agent Schema ====================

class Introduction(BaseModel):
    """引言"""
    background: str = Field(description="研究背景")
    research_question: str = Field(description="研究问题")
    significance: str = Field(description="研究意义")
    contribution: List[str] = Field(default_factory=list, description="边际贡献")
    structure: str = Field(description="文章结构")


class LiteratureReview(BaseModel):
    """文献综述"""
    overview: str = Field(description="文献综述")
    key_studies: List[Dict[str, Any]] = Field(default_factory=list, description="关键研究")
    research_gaps: List[str] = Field(default_factory=list, description="研究空白")


class TheoreticalFrameworkSection(BaseModel):
    """理论框架章节"""
    theories: List[Dict[str, Any]] = Field(default_factory=list, description="理论列表")
    hypotheses: List[Dict[str, Any]] = Field(default_factory=list, description="假设列表")


class Methodology(BaseModel):
    """研究方法"""
    data_description: str = Field(description="数据描述")
    variable_description: str = Field(description="变量描述")
    model_specification: str = Field(description="模型设定")
    identification_strategy: str = Field(description="识别策略")


class EmpiricalResults(BaseModel):
    """实证结果"""
    descriptive_stats: str = Field(description="描述性统计")
    baseline_results: str = Field(description="基准回归结果")
    mechanism_analysis: str = Field(description="机制分析")
    heterogeneity_analysis: str = Field(description="异质性分析")
    robustness_checks: str = Field(description="稳健性检验")


class Conclusion(BaseModel):
    """结论"""
    summary: str = Field(description="研究总结")
    policy_implications: List[str] = Field(default_factory=list, description="政策启示")
    limitations: List[str] = Field(default_factory=list, description="研究局限")
    future_research: List[str] = Field(default_factory=list, description="未来研究方向")


class ReportWriterOutput(BaseModel):
    """ReportWriter Agent 输出模型"""
    latex_source: Optional[str] = Field(default=None, description="完整的LaTeX源代码（从\\documentclass到\\end{document}），当输出LaTeX格式时使用此字段")
    title: str = Field(default="", description="论文标题")
    subtitle: Optional[str] = Field(default=None, description="副标题")
    abstract: str = Field(default="", description="摘要")
    keywords: List[str] = Field(default_factory=list, description="关键词")
    introduction: Optional[Introduction] = Field(default=None, description="引言")
    literature_review: Optional[LiteratureReview] = Field(default=None, description="文献综述")
    theoretical_framework: Optional[TheoreticalFrameworkSection] = Field(default=None, description="理论框架")
    methodology: Optional[Methodology] = Field(default=None, description="研究方法")
    empirical_results: Optional[EmpiricalResults] = Field(default=None, description="实证结果")
    conclusion: Optional[Conclusion] = Field(default=None, description="结论")
    references: List[str] = Field(default_factory=list, description="参考文献")
    word_count: Optional[int] = Field(default=None, description="字数统计")


# ==================== Reviewer Agent Schema ====================

class RecommendationType(str, Enum):
    """审稿建议类型"""
    ACCEPT = "accept"
    MINOR_REVISION = "minor_revision"
    MAJOR_REVISION = "major_revision"
    REJECT = "reject"


class EndogeneityRating(str, Enum):
    """内生性评级"""
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"


class OverallAssessment(BaseModel):
    """总体评价"""
    strengths: List[str] = Field(default_factory=list, description="优势")
    weaknesses: List[str] = Field(default_factory=list, description="不足")
    overall_level: str = Field(description="总体水平")
    recommendation: RecommendationType = Field(description="审稿建议")


class QualitativeAnalysis(BaseModel):
    """定性分析"""
    endogeneity_rating: EndogeneityRating = Field(description="内生性评级")
    endogeneity_identification: List[str] = Field(default_factory=list, description="内生性识别")
    endogeneity_treatment: List[str] = Field(default_factory=list, description="内生性处理")
    causal_credibility: List[str] = Field(default_factory=list, description="因果可信度")
    improvement_suggestions: List[str] = Field(default_factory=list, description="改进建议")


class DimensionScore(BaseModel):
    """维度评分"""
    dimension: str = Field(description="评分维度")
    weight: float = Field(description="权重")
    subscores: List[Dict[str, Any]] = Field(default_factory=list, description="细分项评分")
    total_score: float = Field(description="维度总分")


class QuantitativeAnalysis(BaseModel):
    """定量分析"""
    dimension_scores: List[DimensionScore] = Field(default_factory=list, description="维度评分列表")
    overall_score: float = Field(description="总体得分")
    grade: str = Field(description="等级评定")


class RevisionSuggestions(BaseModel):
    """修改建议"""
    critical_issues: List[Dict[str, Any]] = Field(default_factory=list, description="关键问题")
    minor_issues: List[Dict[str, Any]] = Field(default_factory=list, description="次要问题")
    optional_improvements: List[Dict[str, Any]] = Field(default_factory=list, description="可选改进")


class ReviewerOutput(BaseModel):
    """Reviewer Agent 输出模型"""
    overall_assessment: OverallAssessment = Field(description="总体评价")
    qualitative_analysis: QualitativeAnalysis = Field(description="定性分析")
    quantitative_analysis: QuantitativeAnalysis = Field(description="定量分析")
    revision_suggestions: Optional[RevisionSuggestions] = Field(default=None, description="修改建议")
    summary: str = Field(description="评审总结")


# ==================== LaTeX Formatter Agent Schema（新增）====================

class LaTeXFormatterOutput(BaseModel):
    """LaTeX Formatter Agent 输出模型"""
    latex_content: str = Field(description="完整的 LaTeX 源码")
    sections_count: Optional[int] = Field(default=None, description="章节数量")
    equations_count: Optional[int] = Field(default=None, description="公式数量")
    tables_count: Optional[int] = Field(default=None, description="表格数量")
    compilation_ready: bool = Field(default=True, description="是否可直接编译")


# ==================== LiteratureManager Agent Schema（新增）====================

class LiteratureManagerOutput(BaseModel):
    """LiteratureManager Agent 输出模型"""
    status: str = Field(default="success", description="操作状态")
    operation: str = Field(default="", description="执行的操作类型")
    data: Dict[str, Any] = Field(default_factory=dict, description="操作结果数据")
    message: str = Field(default="", description="操作消息")


# ==================== Schema 字典映射（向后兼容）====================

SCHEMA_MAP = {
    "input_parser": InputParserOutput,
    "literature_collector": LiteratureCollectorOutput,
    "variable_designer": VariableDesignerOutput,
    "theory_designer": TheoryDesignerOutput,
    "model_designer": ModelDesignerOutput,
    "data_analyst": DataAnalystOutput,
    "report_writer": ReportWriterOutput,
    "reviewer": ReviewerOutput,
    "latex_formatter": LaTeXFormatterOutput,
    "literature_manager": LiteratureManagerOutput,
}


def get_schema_class(agent_type: str) -> type[BaseModel]:
    """
    根据 agent 类型获取对应的 Pydantic 模型类

    Args:
        agent_type: Agent 类型标识

    Returns:
        对应的 Pydantic 模型类

    Raises:
        ValueError: 如果 agent_type 不存在
    """
    if agent_type not in SCHEMA_MAP:
        raise ValueError(f"Unknown agent type: {agent_type}")
    return SCHEMA_MAP[agent_type]


# ==================== 旧版 JSON Schema（向后兼容）====================
# 保留旧的 JSON Schema 定义，作为 fallback

VARIABLE_DESIGNER_SCHEMA = {
    "type": "object",
    "properties": {
        "core_variables": {
            "type": "object",
            "properties": {
                "explanatory_variable_x": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "definition": {"type": "string"},
                            "economic_rationale": {"type": "string"},
                            "measurement": {"type": "string"},
                            "data_source": {"type": "string"},
                            "literature_support": {"type": "array", "items": {"type": "string"}},
                            "processing_method": {"type": "string"}
                        }
                    }
                },
                "dependent_variable_y": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "definition": {"type": "string"},
                            "economic_rationale": {"type": "string"},
                            "measurement": {"type": "string"},
                            "data_source": {"type": "string"},
                            "literature_support": {"type": "array", "items": {"type": "string"}},
                            "processing_method": {"type": "string"}
                        }
                    }
                }
            }
        },
        "mediating_moderating_variables": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["mediating", "moderating"]},
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "definition": {"type": "string"},
                    "role": {"type": "string"},
                    "proxy_variables": {"type": "array", "items": {"type": "object"}}
                }
            }
        },
        "control_variables": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "definition": {"type": "string"},
                    "data_source": {"type": "string"},
                    "processing_method": {"type": "string"}
                }
            }
        },
        "variable_relationships": {
            "type": "object",
            "properties": {
                "x_to_z": {"type": "string"},
                "z_to_y": {"type": "string"},
                "z_moderates_x_y": {"type": "string"}
            }
        },
        "justification": {
            "type": "string",
            "description": "变量设置合理性总结"
        }
    },
    "required": ["core_variables", "control_variables"]
}

THEORY_DESIGNER_SCHEMA = {
    "type": "object",
    "properties": {
        "theoretical_framework": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "theory_name": {"type": "string"},
                    "core_content": {"type": "string"},
                    "application_logic": {"type": "string"},
                    "literature_support": {"type": "array", "items": {"type": "string"}}
                }
            }
        },
        "theoretical_justification": {
            "type": "object",
            "properties": {
                "for_variable_x": {"type": "string"},
                "for_variable_y": {"type": "string"},
                "for_mediating_moderating": {"type": "string"}
            }
        },
        "research_hypotheses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "hypothesis_id": {"type": "string"},
                    "hypothesis_name": {"type": "string"},
                    "hypothesis_content": {"type": "string"},
                    "theoretical_basis": {"type": "string"},
                    "derivation_logic": {"type": "string"},
                    "literature_support": {"type": "array", "items": {"type": "string"}}
                }
            }
        },
        "potential_mechanisms": {
            "type": "object",
            "properties": {
                "policy_shock": {"type": "boolean"},
                "endogeneity_issues": {"type": "array", "items": {"type": "string"}},
                "data_type": {"type": "string", "enum": ["panel", "cross-section", "time-series"]}
            }
        },
        "references": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["theoretical_framework", "research_hypotheses"]
}

MODEL_DESIGNER_SCHEMA = {
    "type": "object",
    "properties": {
        "baseline_model": {
            "type": "object",
            "properties": {
                "model_type": {"type": "string"},
                "rationale": {"type": "string"},
                "equation": {"type": "string"},
                "variables": {"type": "object"},
                "expected_signs": {"type": "object"}
            }
        },
        "mechanism_models": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "step": {"type": "number"},
                    "description": {"type": "string"},
                    "equation": {"type": "string"}
                }
            }
        },
        "heterogeneity_models": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "dimension": {"type": "string"},
                    "groups": {"type": "array", "items": {"type": "string"}},
                    "equation": {"type": "string"}
                }
            }
        },
        "robustness_checks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "check_type": {"type": "string"},
                    "description": {"type": "string"},
                    "equation": {"type": "string"}
                }
            }
        },
        "hypothesis_tests": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "hypothesis_id": {"type": "string"},
                    "test_method": {"type": "string"}
                }
            }
        }
    },
    "required": ["baseline_model"]
}

DATA_ANALYST_SCHEMA = {
    "type": "object",
    "properties": {
        "data_preprocessing": {
            "type": "object",
            "properties": {
                "data_sources": {"type": "array", "items": {"type": "string"}},
                "sample_size": {"type": "object"},
                "cleaning_steps": {"type": "array", "items": {"type": "string"}},
                "processing_details": {"type": "string"}
            }
        },
        "descriptive_statistics": {
            "type": "object",
            "properties": {
                "variables": {"type": "array", "items": {"type": "object"}},
                "summary": {"type": "string"}
            }
        },
        "baseline_regression": {
            "type": "object",
            "properties": {
                "results": {"type": "array", "items": {"type": "object"}},
                "interpretation": {"type": "string"},
                "hypothesis_support": {"type": "array", "items": {"type": "string"}}
            }
        },
        "mechanism_analysis": {
            "type": "object",
            "properties": {
                "steps": {"type": "array", "items": {"type": "object"}},
                "mediation_effects": {"type": "object"}
            }
        },
        "heterogeneity_analysis": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "dimension": {"type": "string"},
                    "results": {"type": "array", "items": {"type": "object"}},
                    "interpretation": {"type": "string"}
                }
            }
        },
        "robustness_checks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "check_type": {"type": "string"},
                    "results": {"type": "object"},
                    "conclusion": {"type": "string"}
                }
            }
        },
        "conclusions": {
            "type": "object",
            "properties": {
                "supported_hypotheses": {"type": "array", "items": {"type": "string"}},
                "effect_size": {"type": "string"},
                "robustness": {"type": "string"}
            }
        }
    },
    "required": ["baseline_regression"]
}

REPORT_WRITER_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "论文标题"},
        "subtitle": {"type": "string", "description": "副标题"},
        "abstract": {"type": "string", "description": "摘要"},
        "keywords": {"type": "array", "items": {"type": "string"}, "description": "关键词"},
        "introduction": {
            "type": "object",
            "properties": {
                "background": {"type": "string"},
                "research_question": {"type": "string"},
                "significance": {"type": "string"},
                "contribution": {"type": "array", "items": {"type": "string"}},
                "structure": {"type": "string"}
            }
        },
        "literature_review": {
            "type": "object",
            "properties": {
                "overview": {"type": "string"},
                "key_studies": {"type": "array", "items": {"type": "object"}},
                "research_gaps": {"type": "array", "items": {"type": "string"}}
            }
        },
        "theoretical_framework": {
            "type": "object",
            "properties": {
                "theories": {"type": "array", "items": {"type": "object"}},
                "hypotheses": {"type": "array", "items": {"type": "object"}}
            }
        },
        "methodology": {
            "type": "object",
            "properties": {
                "data_description": {"type": "string"},
                "variable_description": {"type": "string"},
                "model_specification": {"type": "string"},
                "identification_strategy": {"type": "string"}
            }
        },
        "empirical_results": {
            "type": "object",
            "properties": {
                "descriptive_stats": {"type": "string"},
                "baseline_results": {"type": "string"},
                "mechanism_analysis": {"type": "string"},
                "heterogeneity_analysis": {"type": "string"},
                "robustness_checks": {"type": "string"}
            }
        },
        "conclusion": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "policy_implications": {"type": "array", "items": {"type": "string"}},
                "limitations": {"type": "array", "items": {"type": "string"}},
                "future_research": {"type": "array", "items": {"type": "string"}}
            }
        },
        "references": {"type": "array", "items": {"type": "string"}},
        "word_count": {"type": "number"}
    },
    "required": ["title", "abstract", "keywords", "introduction", "empirical_results", "conclusion"]
}

REVIEWER_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_assessment": {
            "type": "object",
            "properties": {
                "strengths": {"type": "array", "items": {"type": "string"}},
                "weaknesses": {"type": "array", "items": {"type": "string"}},
                "overall_level": {"type": "string"},
                "recommendation": {"type": "string", "enum": ["accept", "minor_revision", "major_revision", "reject"]}
            }
        },
        "qualitative_analysis": {
            "type": "object",
            "properties": {
                "endogeneity_rating": {"type": "string", "enum": ["good", "average", "poor"]},
                "endogeneity_identification": {"type": "array", "items": {"type": "string"}},
                "endogeneity_treatment": {"type": "array", "items": {"type": "string"}},
                "causal_credibility": {"type": "array", "items": {"type": "string"}},
                "improvement_suggestions": {"type": "array", "items": {"type": "string"}}
            }
        },
        "quantitative_analysis": {
            "type": "object",
            "properties": {
                "dimension_scores": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "dimension": {"type": "string"},
                            "weight": {"type": "number"},
                            "subscores": {"type": "array", "items": {"type": "object"}},
                            "total_score": {"type": "number"}
                        }
                    }
                },
                "overall_score": {"type": "number"},
                "grade": {"type": "string"}
            }
        },
        "revision_suggestions": {
            "type": "object",
            "properties": {
                "critical_issues": {"type": "array", "items": {"type": "object"}},
                "minor_issues": {"type": "array", "items": {"type": "object"}},
                "optional_improvements": {"type": "array", "items": {"type": "object"}}
            }
        },
        "summary": {"type": "string"}
    },
    "required": ["overall_assessment", "qualitative_analysis", "quantitative_analysis"]
}
