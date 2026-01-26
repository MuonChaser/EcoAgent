"""
增强版审稿人专家 - 支持工具调用
可以主动搜索权威文献、获取方法论标准进行专业评审
"""
from typing import Dict, Any, List, Optional
from loguru import logger

from .base_agent import BaseAgent
from .schemas import REVIEWER_SCHEMA
from prompts.reviewer import SYSTEM_PROMPT
from tools.reviewer_tools import ReviewerTools


class EnhancedReviewerAgent(BaseAgent):
    """
    增强版审稿人专家

    功能特点：
    1. 支持调用工具搜索权威文献进行对比评价
    2. 自动获取方法论评审标准
    3. 生成基于文献的专业评审意见
    4. 提供详细的修改建议和参考文献
    """

    def __init__(self, custom_config: Dict[str, Any] = None):
        super().__init__("reviewer", custom_config)
        # 初始化审稿人工具
        self.tools = ReviewerTools()
        logger.info("增强版审稿人Agent初始化完成，工具已加载")

    def get_system_prompt(self) -> str:
        """获取增强版系统提示词"""
        enhanced_prompt = SYSTEM_PROMPT + """

# 增强能力

你现在拥有以下增强能力：
1. **文献检索能力**：可以搜索和引用权威学术文献
2. **方法论验证能力**：掌握计量经济学方法论的标准和最佳实践
3. **内生性诊断能力**：能够系统性地识别和评估内生性问题
4. **评审标准知识**：了解顶级期刊的审稿标准和要求

在评审时，你应该：
- 参考相关领域的权威文献来评价研究的创新性
- 根据方法论标准评估识别策略的合理性
- 提供具体的文献支持来佐证你的评审意见
- 给出可操作的改进建议和参考文献
"""
        return enhanced_prompt

    def get_output_schema(self) -> Dict[str, Any]:
        return REVIEWER_SCHEMA

    def get_task_prompt(self, **kwargs) -> str:
        """构建包含工具调用结果的任务提示词"""
        research_topic = kwargs.get("research_topic", "")
        variable_system = kwargs.get("variable_system", "")
        theory_framework = kwargs.get("theory_framework", "")
        model_design = kwargs.get("model_design", "")
        data_analysis = kwargs.get("data_analysis", "")
        final_report = kwargs.get("final_report", "")

        # 提取关键词用于文献搜索
        keywords = self._extract_keywords(research_topic, variable_system)

        # 调用工具获取辅助信息
        tool_results = self._gather_tool_results(keywords, model_design)

        return self._build_task_prompt(
            research_topic=research_topic,
            variable_system=variable_system,
            theory_framework=theory_framework,
            model_design=model_design,
            data_analysis=data_analysis,
            final_report=final_report,
            tool_results=tool_results
        )

    def _extract_keywords(
        self,
        research_topic: str,
        variable_system: str
    ) -> List[str]:
        """从研究主题和变量体系中提取关键词"""
        keywords = []

        # 从研究主题提取
        if research_topic:
            # 简单的关键词提取
            words = research_topic.replace("的", " ").replace("对", " ").replace("与", " ")
            words = words.replace("研究", "").replace("影响", "").replace("分析", "")
            keywords.extend([w.strip() for w in words.split() if len(w.strip()) >= 2])

        # 从变量体系提取
        if variable_system and isinstance(variable_system, str):
            # 提取可能的变量名
            for marker in ["核心变量", "解释变量", "被解释变量"]:
                if marker in variable_system:
                    idx = variable_system.find(marker)
                    chunk = variable_system[idx:idx+100]
                    keywords.extend([w for w in chunk.split() if len(w) >= 2][:2])

        return list(set(keywords))[:5]  # 去重并限制数量

    def _gather_tool_results(
        self,
        keywords: List[str],
        model_design: str
    ) -> Dict[str, Any]:
        """调用工具收集评审所需信息"""
        results = {
            "related_literature": "",
            "methodology_standard": {},
            "review_checklist": {},
            "identification_evaluation": {}
        }

        try:
            # 1. 搜索相关文献
            if keywords:
                papers = self.tools.search_related_literature(keywords, max_results=5)
                results["related_literature"] = self.tools.format_literature_for_review(papers)
                logger.info(f"搜索到 {len(papers)} 篇相关文献")

            # 2. 检测使用的方法并获取标准
            detected_method = self._detect_methodology(model_design)
            if detected_method:
                results["methodology_standard"] = self.tools.get_methodology_standard(detected_method)
                results["review_checklist"] = self.tools.generate_review_checklist(detected_method)
                logger.info(f"检测到方法: {detected_method}")

            # 3. 评估识别策略
            if model_design:
                results["identification_evaluation"] = self.tools.evaluate_identification_strategy(
                    str(model_design)
                )

        except Exception as e:
            logger.warning(f"工具调用过程中出现错误: {e}")

        return results

    def _detect_methodology(self, model_design: str) -> Optional[str]:
        """从模型设计中检测使用的方法论"""
        if not model_design:
            return None

        model_str = str(model_design).upper()

        method_keywords = {
            "DID": ["DID", "双重差分", "DIFFERENCE-IN-DIFFERENCE", "DIFF-IN-DIFF"],
            "IV": ["IV", "工具变量", "INSTRUMENTAL", "2SLS", "两阶段"],
            "RDD": ["RDD", "断点回归", "DISCONTINUITY"],
            "FE": ["固定效应", "FIXED EFFECT", "FE模型", "面板固定"]
        }

        for method, keywords in method_keywords.items():
            for keyword in keywords:
                if keyword in model_str:
                    return method

        return "FE"  # 默认假设使用固定效应

    def _build_task_prompt(
        self,
        research_topic: str,
        variable_system: str,
        theory_framework: str,
        model_design: str,
        data_analysis: str,
        final_report: str,
        tool_results: Dict[str, Any]
    ) -> str:
        """构建完整的任务提示词"""

        # 格式化工具结果
        methodology_info = ""
        if tool_results.get("methodology_standard") and "error" not in tool_results["methodology_standard"]:
            std = tool_results["methodology_standard"]
            methodology_info = f"""
## 方法论评审标准参考

**方法名称**: {std.get('name', 'N/A')}

**核心假设要求**:
{chr(10).join(['- ' + a for a in std.get('key_assumptions', [])])}

**必要稳健性检验**:
{chr(10).join(['- ' + t for t in std.get('robustness_tests', [])])}

**权威参考文献**:
{chr(10).join(['- ' + r for r in std.get('key_references', [])])}
"""

        checklist_info = ""
        if tool_results.get("review_checklist"):
            checklist = tool_results["review_checklist"]
            checklist_items = []
            for category, items in checklist.items():
                if items:
                    checklist_items.append(f"**{category}**: {', '.join(items[:3])}")
            checklist_info = "\n## 评审检查要点\n" + "\n".join(checklist_items)

        literature_info = tool_results.get("related_literature", "")

        return f"""# 评审任务

请对以下完整研究成果进行专业评审。

## 研究主题
{research_topic}

## 指标体系说明
{variable_system if variable_system else "（未提供）"}

## 理论假设与路径
{theory_framework if theory_framework else "（未提供）"}

## 计量模型设计
{model_design if model_design else "（未提供）"}

## 实证分析结果
{data_analysis if data_analysis else "（未提供）"}

## 学术报告全文
{final_report if final_report else "（未提供）"}

---

# 评审参考信息（基于工具检索）

{methodology_info}

{checklist_info}

{literature_info if literature_info else ""}

---

# 评审核心要求

## （1）定性分析：内生性维度评估

请从以下维度评估研究的内生性问题处理：

### A. 内生性识别
- 是否充分识别了潜在的内生性来源？
- 遗漏变量偏误的讨论是否充分？
- 反向因果的可能性是否被考虑？

### B. 内生性处理策略
- 采用的识别策略是否合理？
- DID/IV/RDD等方法的使用是否恰当？
- 工具变量（如有）的有效性如何？

### C. 因果识别的可信度
- 因果关系的论证是否严谨？
- 识别假设是否合理且可信？

**输出要求**：
- 总体评级：**好 / 一般 / 差**
- 打分依据：结合上述方法论标准进行评价
- 改进建议：提供具体的改进方向和参考文献

## （2）定量分析：指标体系维度评估

请对以下维度进行量化打分（1-10分）：

### 维度1：核心变量设定（权重25%）
### 维度2：理论框架构建（权重20%）
### 维度3：模型设计（权重25%）
### 维度4：实证分析（权重20%）
### 维度5：论文质量（权重10%）

**总体得分**：满分100分

## （3）修改建议

请提供：
- **重大问题（Must Fix）**：必须修改的核心问题
- **次要问题（Should Fix）**：建议修改的问题
- **可选改进（Nice to Have）**：锦上添花的改进

请立即开始评审。"""

    def process_output(self, raw_output: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理输出，添加工具使用信息"""
        result = super().process_output(raw_output, input_data)

        parsed = result.get("parsed_data", {})
        result["review_report"] = parsed
        result["research_topic"] = input_data.get("research_topic")

        # 添加工具使用标记
        result["tools_used"] = {
            "literature_search": True,
            "methodology_standard": True,
            "review_checklist": True
        }

        return result

    def review_with_literature(
        self,
        input_data: Dict[str, Any],
        additional_keywords: List[str] = None
    ) -> Dict[str, Any]:
        """
        带额外文献搜索的评审方法

        Args:
            input_data: 输入数据
            additional_keywords: 额外的搜索关键词

        Returns:
            评审结果
        """
        if additional_keywords:
            # 搜索额外文献
            extra_papers = self.tools.search_related_literature(
                additional_keywords,
                max_results=3
            )
            extra_lit = self.tools.format_literature_for_review(extra_papers)
            input_data["additional_literature"] = extra_lit

        return self.run(input_data)
