"""
智能体7：审稿人专家
"""
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from loguru import logger
from .base_agent import BaseAgent
from .schemas import REVIEWER_SCHEMA
from prompts.reviewer import SYSTEM_PROMPT, get_task_prompt

# 导入 AES 评分系统
try:
    from tools.aes_scorer import get_aes_scorer
    from config.aes_config import get_aes_config
    AES_AVAILABLE = True
except ImportError:
    AES_AVAILABLE = False
    logger.warning("AES 评分系统不可用")


class ReviewerAgent(BaseAgent):
    """
    审稿人专家
    负责对完整研究进行定性和定量评审打分

    集成两种评分机制：
    1. LLM 定性评审（基于大模型）
    2. AES 定量评分（基于传统 NLP，不依赖大模型）
    """

    def __init__(
        self,
        custom_config: Dict[str, Any] = None,
        enable_aes: bool = True,
        aes_config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化审稿人 Agent

        Args:
            custom_config: Agent 自定义配置
            enable_aes: 是否启用 AES 评分系统
            aes_config: AES 评分系统配置
        """
        super().__init__("reviewer", custom_config)

        # AES 评分系统
        self.enable_aes = enable_aes and AES_AVAILABLE
        self.aes_scorer = None

        if self.enable_aes:
            try:
                aes_cfg = aes_config or get_aes_config()
                self.aes_scorer = get_aes_scorer(aes_cfg)
                logger.info("AES 评分系统已启用")
            except Exception as e:
                logger.warning(f"AES 评分系统初始化失败: {e}")
                self.enable_aes = False

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

        # 添加 AES 评分（如果启用）
        if self.enable_aes and self.aes_scorer:
            try:
                logger.info("开始 AES 自动评分")

                # 提取论文全文
                final_report = input_data.get("final_report", "")

                # 如果 final_report 是 JSON 格式，提取 latex_source
                if isinstance(final_report, str) and "latex_source" in final_report:
                    try:
                        import json
                        report_data = json.loads(final_report)
                        paper_text = report_data.get("latex_source", final_report)
                    except:
                        paper_text = final_report
                else:
                    paper_text = final_report

                # 构建论文元数据
                metadata = {
                    "research_topic": input_data.get("research_topic", ""),
                    "variable_system": input_data.get("variable_system", ""),
                    "theory_framework": input_data.get("theory_framework", ""),
                    "model_design": input_data.get("model_design", ""),
                    "data_analysis": input_data.get("data_analysis", ""),
                }

                # 执行 AES 评分（传入 LLM 评审结果以提取定性指标）
                aes_result = self.aes_scorer.score_paper(
                    paper_text,
                    metadata,
                    llm_review=parsed  # 传入 LLM 评审的 parsed_data
                )

                # 添加到结果中
                result["aes_score"] = aes_result
                result["aes_enabled"] = True

                # 输出详细评分到日志
                logger.info("=" * 60)
                logger.info("AES 评分完成")
                logger.info("=" * 60)
                logger.info(f"总分: {aes_result['normalized_score']:.2f}/100 (原始分: {aes_result['total_score']:.4f})")
                logger.info(f"Claims数: {aes_result.get('claims_count', 0)}, Evidences数: {aes_result.get('evidences_count', 0)}")
                logger.info("-" * 60)
                logger.info("各维度评分:")
                dimension_scores = aes_result.get("dimension_scores", aes_result.get("indicator_scores", {}))
                weights = aes_result.get("weights", {})
                for metric, score in dimension_scores.items():
                    weight = weights.get(metric, 0)
                    logger.info(f"  - {metric}: {score:.4f} (权重: {weight:.0%})")
                logger.info("=" * 60)

            except Exception as e:
                logger.error(f"AES 评分失败: {e}")
                result["aes_enabled"] = False
                result["aes_error"] = str(e)
        else:
            result["aes_enabled"] = False

        # 生成 CSV 评分表
        try:
            csv_path = self._generate_score_csv(parsed, result.get("aes_score"), input_data)
            if csv_path:
                result["score_csv_path"] = csv_path
                logger.info(f"评分表已生成: {csv_path}")
        except Exception as e:
            logger.warning(f"生成评分表失败: {e}")

        return result

    def _generate_score_csv(
        self,
        llm_review: Dict[str, Any],
        aes_score: Optional[Dict[str, Any]],
        input_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        生成综合评分 CSV 表（包含 LLM 评审和 AES 评分）

        Args:
            llm_review: LLM 评审结果
            aes_score: AES 评分结果
            input_data: 输入数据

        Returns:
            CSV 文件路径
        """
        # 创建输出目录
        output_dir = Path("output/research/scores")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = output_dir / f"review_scores_{timestamp}.csv"

        rows = []

        # === 基本信息 ===
        rows.append(["评分类别", "评分项", "满分", "得分", "权重", "加权得分", "评分理由/说明"])
        rows.append(["基本信息", "研究主题", "", "", "", "", input_data.get("research_topic", "")])
        rows.append(["基本信息", "评审时间", "", "", "", "", timestamp])
        rows.append([])

        # === LLM 定性评审 ===
        rows.append(["LLM定性评审", "总体评价", "", "", "", "", ""])

        # 提取 LLM 评审的关键信息
        overall = llm_review.get("overall_assessment", {})
        if overall:
            rows.append(["总体评价", "推荐意见", "", "", "", "", overall.get("recommendation", "")])
            rows.append(["总体评价", "总体水平", "", "", "", "", overall.get("overall_level", "")])

            strengths = overall.get("major_strengths", [])
            if strengths:
                for i, s in enumerate(strengths[:3], 1):
                    rows.append(["总体评价", f"优势{i}", "", "", "", "", s])

            weaknesses = overall.get("major_weaknesses", [])
            if weaknesses:
                for i, w in enumerate(weaknesses[:3], 1):
                    rows.append(["总体评价", f"不足{i}", "", "", "", "", w])

        rows.append([])

        # 内生性评估
        quant = llm_review.get("quantitative_analysis", {})
        endogeneity = quant.get("endogeneity_assessment", {})
        rows.append(["内生性评估", "总体评级", "", endogeneity.get("overall_rating", ""), "", "", "good/average/poor"])
        rows.append([])

        # === LLM 维度评分 ===
        rows.append(["LLM定量评分", "维度评分详情", "", "", "", "", ""])

        dimension_config = [
            ("variable_design", "核心变量设定", 25, [
                ("x_proxy_quality", "X的代理变量设计"),
                ("y_proxy_quality", "Y的代理变量设计"),
            ]),
            ("theoretical_framework", "理论框架构建", 20, [
                ("theory_selection", "理论选择与适配"),
                ("hypothesis_development", "假设提出与推导"),
            ]),
            ("model_design", "模型设计", 25, [
                ("baseline_model", "基准模型设计"),
                ("identification_strategy", "识别策略"),
            ]),
            ("empirical_analysis", "实证分析", 20, [
                ("data_handling", "数据处理"),
                ("result_interpretation", "结果呈现与解读"),
            ]),
            ("paper_quality", "论文质量", 10, [
                ("academic_rigor", "学术规范"),
                ("innovation", "创新性与贡献"),
            ]),
        ]

        total_llm_score = 0
        for dim_key, dim_name, dim_weight, sub_items in dimension_config:
            dim_data = quant.get(dim_key, {})
            dim_score = dim_data.get("score", 0) if isinstance(dim_data, dict) else 0
            weighted_score = dim_score * dim_weight / 100
            total_llm_score += weighted_score

            rows.append(["维度评分", dim_name, "100", dim_score, f"{dim_weight}%", f"{weighted_score:.1f}", ""])

            # 子项评分
            for sub_key, sub_name in sub_items:
                sub_data = dim_data.get(sub_key, {}) if isinstance(dim_data, dict) else {}
                sub_score = sub_data.get("score", "") if isinstance(sub_data, dict) else ""
                sub_reason = sub_data.get("reason", "") if isinstance(sub_data, dict) else ""
                rows.append([f"  {dim_name}", sub_name, "10", sub_score, "", "", sub_reason])

        rows.append([])
        rows.append(["LLM评分汇总", "加权总分", "100", f"{total_llm_score:.2f}", "100%", f"{total_llm_score:.2f}", ""])

        # 评级
        if total_llm_score >= 85:
            grade = "优秀"
        elif total_llm_score >= 75:
            grade = "良好"
        elif total_llm_score >= 60:
            grade = "中等"
        else:
            grade = "不合格"
        rows.append(["LLM评分汇总", "等级评定", "", grade, "", "", "优秀(85+)/良好(75-84)/中等(60-74)/不合格(<60)"])

        rows.append([])

        # === AES 自动评分 ===
        if aes_score:
            rows.append(["AES自动评分", "评分详情", "", "", "", "", ""])

            # 获取评分数据（兼容两种键名）
            indicator_scores = aes_score.get("dimension_scores", aes_score.get("indicator_scores", {}))
            weights = aes_score.get("weights", {})

            aes_indicators = [
                ("citation_coverage", "引用覆盖率", "论文中引用是否充分覆盖claims"),
                ("causal_relevance", "因果相关性", "evidence与claim的语义相关程度"),
                ("support_strength", "支持强度", "evidence对claim的NLI支持程度"),
                ("contradiction_penalty", "矛盾惩罚", "证据间矛盾程度（越高越好）"),
                ("evidence_sufficiency", "证据充分性", "每个claim是否有足够的证据支持"),
                ("endogeneity_quality", "内生性处理质量", "从LLM评审提取"),
                ("methodology_rigor", "方法论严谨性", "从LLM评审提取"),
                ("academic_standards", "学术规范性", "从LLM评审提取"),
            ]

            for key, name, desc in aes_indicators:
                score = indicator_scores.get(key, 0)
                weight = weights.get(key, 0)
                weighted = score * weight
                rows.append(["AES评分", name, "1.0", f"{score:.4f}", f"{weight:.0%}", f"{weighted:.4f}", desc])

            rows.append([])
            aes_total = aes_score.get("normalized_score", 0)
            rows.append(["AES评分汇总", "总分", "100", f"{aes_total:.2f}", "", "", ""])
            rows.append(["AES评分汇总", "Claims数", "", aes_score.get("claims_count", 0), "", "", ""])
            rows.append(["AES评分汇总", "Evidences数", "", aes_score.get("evidences_count", 0), "", "", ""])
        else:
            rows.append(["AES自动评分", "状态", "", "未启用或评分失败", "", "", ""])

        rows.append([])

        # === 综合评分 ===
        rows.append(["综合评分", "", "", "", "", "", ""])
        rows.append(["综合评分", "LLM评分", "100", f"{total_llm_score:.2f}", "100%", f"{total_llm_score:.2f}", "仅LLM评分"])

        if aes_score:
            aes_total = aes_score.get("normalized_score", 0)
            # 综合评分 = 70% LLM + 30% AES
            combined = total_llm_score * 0.7 + aes_total * 0.3
            rows.append(["综合评分", "AES评分", "100", f"{aes_total:.2f}", "", "", ""])
            rows.append(["综合评分", "综合总分", "100", f"{combined:.2f}", "", "", "LLM(70%) + AES(30%)"])

        # 写入 CSV
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        # 输出日志
        logger.info("=" * 60)
        logger.info(f"评分表已生成: {csv_path}")
        logger.info(f"LLM评分: {total_llm_score:.2f}/100 ({grade})")
        if aes_score:
            logger.info(f"AES评分: {aes_score.get('normalized_score', 0):.2f}/100")
        logger.info("=" * 60)

        return str(csv_path)
