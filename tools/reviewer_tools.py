"""
审稿人专用工具模块
提供文献搜索、方法论验证、评审标准查询等功能
"""
import json
from typing import List, Dict, Any, Optional
from loguru import logger


class ReviewerTools:
    """
    审稿人专用工具集
    用于支持审稿人获取权威文献、评审标准等信息
    """

    # 顶级期刊列表
    TOP_JOURNALS = {
        "economics_cn": ["经济研究", "管理世界", "中国社会科学", "金融研究", "中国工业经济"],
        "economics_en": ["American Economic Review", "Quarterly Journal of Economics",
                        "Journal of Political Economy", "Econometrica", "Review of Economic Studies"],
        "finance": ["Journal of Finance", "Journal of Financial Economics",
                   "Review of Financial Studies", "Journal of Monetary Economics"],
        "management": ["Management Science", "Strategic Management Journal",
                      "Academy of Management Journal", "Organization Science"]
    }

    # 计量经济学方法论标准
    METHODOLOGY_STANDARDS = {
        "DID": {
            "name": "双重差分法 (Difference-in-Differences)",
            "key_assumptions": [
                "平行趋势假设 (Parallel Trends)",
                "无预期效应 (No Anticipation)",
                "SUTVA假设 (Stable Unit Treatment Value)"
            ],
            "robustness_tests": [
                "平行趋势检验",
                "安慰剂检验 (Placebo Test)",
                "事件研究法 (Event Study)",
                "PSM-DID匹配",
                "更换处理组/控制组"
            ],
            "key_references": [
                "Angrist & Pischke (2009). Mostly Harmless Econometrics",
                "Bertrand et al. (2004). How Much Should We Trust Differences-in-Differences Estimates?",
                "Callaway & Sant'Anna (2021). Difference-in-Differences with Multiple Time Periods"
            ]
        },
        "IV": {
            "name": "工具变量法 (Instrumental Variables)",
            "key_assumptions": [
                "相关性假设 (Relevance)",
                "外生性假设 (Exogeneity/Exclusion Restriction)"
            ],
            "robustness_tests": [
                "一阶段F统计量 (>10)",
                "过度识别检验 (Sargan/Hansen Test)",
                "弱工具变量检验",
                "工具变量有效性论证"
            ],
            "key_references": [
                "Stock & Yogo (2005). Testing for Weak Instruments",
                "Angrist & Krueger (2001). Instrumental Variables and the Search for Identification"
            ]
        },
        "RDD": {
            "name": "断点回归设计 (Regression Discontinuity Design)",
            "key_assumptions": [
                "连续性假设 (Continuity)",
                "无操纵假设 (No Manipulation)"
            ],
            "robustness_tests": [
                "McCrary密度检验",
                "带宽敏感性分析",
                "多项式阶数选择",
                "协变量平衡检验"
            ],
            "key_references": [
                "Lee & Lemieux (2010). Regression Discontinuity Designs in Economics",
                "Cattaneo et al. (2020). A Practical Introduction to Regression Discontinuity Designs"
            ]
        },
        "FE": {
            "name": "固定效应模型 (Fixed Effects)",
            "key_assumptions": [
                "严格外生性 (Strict Exogeneity)",
                "无遗漏时变变量"
            ],
            "robustness_tests": [
                "Hausman检验",
                "聚类标准误",
                "双向固定效应",
                "高维固定效应"
            ],
            "key_references": [
                "Wooldridge (2010). Econometric Analysis of Cross Section and Panel Data",
                "Abadie et al. (2023). When Should You Adjust Standard Errors for Clustering?"
            ]
        }
    }

    # 内生性问题类型
    ENDOGENEITY_TYPES = {
        "omitted_variable": {
            "name": "遗漏变量偏误",
            "description": "存在与X和Y同时相关的变量未被纳入模型",
            "solutions": ["添加控制变量", "使用固定效应", "工具变量法", "代理变量法"]
        },
        "reverse_causality": {
            "name": "反向因果",
            "description": "Y可能反过来影响X",
            "solutions": ["滞后自变量", "DID方法", "工具变量法", "格兰杰因果检验"]
        },
        "measurement_error": {
            "name": "测量误差",
            "description": "变量测量存在系统性或随机误差",
            "solutions": ["工具变量法", "多指标验证", "测量误差模型"]
        },
        "sample_selection": {
            "name": "样本选择偏误",
            "description": "样本选择过程与研究变量相关",
            "solutions": ["Heckman两阶段法", "PSM匹配", "扩大样本范围"]
        }
    }

    def __init__(self):
        """初始化审稿人工具"""
        self.literature_search = None
        try:
            from tools.research_tools import LiteratureSearchTool
            self.literature_search = LiteratureSearchTool()
            logger.info("审稿人工具初始化成功，文献搜索功能已启用")
        except Exception as e:
            logger.warning(f"文献搜索工具初始化失败: {e}")

    def search_related_literature(
        self,
        keywords: List[str],
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        搜索相关权威文献

        Args:
            keywords: 搜索关键词列表
            max_results: 最大结果数

        Returns:
            文献列表
        """
        papers = []

        if self.literature_search:
            for keyword in keywords[:3]:  # 限制搜索次数
                try:
                    results = self.literature_search.search_arxiv(
                        keyword,
                        max_results=max_results
                    )
                    papers.extend(results)
                except Exception as e:
                    logger.warning(f"搜索关键词 '{keyword}' 失败: {e}")

        # 去重
        seen_titles = set()
        unique_papers = []
        for paper in papers:
            if paper.get('title') not in seen_titles:
                seen_titles.add(paper.get('title'))
                unique_papers.append(paper)

        return unique_papers[:max_results * 2]

    def get_methodology_standard(self, method: str) -> Dict[str, Any]:
        """
        获取指定方法论的评审标准

        Args:
            method: 方法名称 (DID, IV, RDD, FE)

        Returns:
            方法论标准信息
        """
        method_upper = method.upper()
        if method_upper in self.METHODOLOGY_STANDARDS:
            return self.METHODOLOGY_STANDARDS[method_upper]

        # 模糊匹配
        for key, value in self.METHODOLOGY_STANDARDS.items():
            if key in method_upper or method_upper in key:
                return value
            if method.lower() in value["name"].lower():
                return value

        return {"error": f"未找到方法 '{method}' 的评审标准"}

    def get_endogeneity_analysis(self, issue_type: str = None) -> Dict[str, Any]:
        """
        获取内生性问题分析指南

        Args:
            issue_type: 内生性问题类型（可选）

        Returns:
            内生性问题分析指南
        """
        if issue_type:
            for key, value in self.ENDOGENEITY_TYPES.items():
                if issue_type.lower() in key or issue_type.lower() in value["name"]:
                    return value
            return {"error": f"未找到内生性类型: {issue_type}"}

        return self.ENDOGENEITY_TYPES

    def get_top_journals(self, field: str = "economics_cn") -> List[str]:
        """
        获取指定领域的顶级期刊列表

        Args:
            field: 领域名称

        Returns:
            期刊列表
        """
        return self.TOP_JOURNALS.get(field, self.TOP_JOURNALS["economics_cn"])

    def evaluate_identification_strategy(
        self,
        strategy_description: str
    ) -> Dict[str, Any]:
        """
        评估识别策略的合理性

        Args:
            strategy_description: 识别策略描述

        Returns:
            评估结果和建议
        """
        evaluation = {
            "detected_methods": [],
            "suggestions": [],
            "required_tests": [],
            "references": []
        }

        strategy_lower = strategy_description.lower()

        # 检测使用的方法
        for method_key, method_info in self.METHODOLOGY_STANDARDS.items():
            if (method_key.lower() in strategy_lower or
                method_info["name"].lower() in strategy_lower):
                evaluation["detected_methods"].append(method_key)
                evaluation["required_tests"].extend(method_info["robustness_tests"])
                evaluation["references"].extend(method_info["key_references"])

        # 生成建议
        if not evaluation["detected_methods"]:
            evaluation["suggestions"].append("未检测到明确的识别策略，建议补充因果识别方法")
        else:
            evaluation["suggestions"].append(
                f"检测到使用了 {', '.join(evaluation['detected_methods'])} 方法"
            )
            evaluation["suggestions"].append("请确保进行了必要的稳健性检验")

        return evaluation

    def generate_review_checklist(
        self,
        model_type: str = "DID"
    ) -> Dict[str, List[str]]:
        """
        生成审稿检查清单

        Args:
            model_type: 模型类型

        Returns:
            审稿检查清单
        """
        checklist = {
            "核心假设检验": [],
            "稳健性检验": [],
            "数据要求": [
                "数据来源是否清晰",
                "样本选择是否合理",
                "变量定义是否规范",
                "数据处理是否透明"
            ],
            "结果报告": [
                "系数估计是否显著",
                "经济意义是否合理",
                "标准误是否正确聚类",
                "R方是否合理"
            ],
            "学术规范": [
                "文献引用是否充分",
                "理论框架是否完整",
                "研究贡献是否明确",
                "局限性是否讨论"
            ]
        }

        method_info = self.get_methodology_standard(model_type)
        if "error" not in method_info:
            checklist["核心假设检验"] = method_info.get("key_assumptions", [])
            checklist["稳健性检验"] = method_info.get("robustness_tests", [])

        return checklist

    def format_literature_for_review(
        self,
        papers: List[Dict[str, Any]]
    ) -> str:
        """
        将搜索到的文献格式化为评审参考文本

        Args:
            papers: 文献列表

        Returns:
            格式化的文献参考文本
        """
        if not papers:
            return "未找到相关参考文献"

        formatted = ["## 相关权威文献参考\n"]
        for i, paper in enumerate(papers, 1):
            formatted.append(f"### {i}. {paper.get('title', 'Unknown')}")
            formatted.append(f"- 作者: {', '.join(paper.get('authors', ['Unknown']))}")
            formatted.append(f"- 发表时间: {paper.get('published', 'Unknown')}")
            if paper.get('abstract'):
                abstract = paper['abstract'][:300] + "..." if len(paper['abstract']) > 300 else paper['abstract']
                formatted.append(f"- 摘要: {abstract}")
            formatted.append("")

        return "\n".join(formatted)


# 便捷函数
def get_reviewer_tools() -> ReviewerTools:
    """获取审稿人工具实例"""
    return ReviewerTools()
