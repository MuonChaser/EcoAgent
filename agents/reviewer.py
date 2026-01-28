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

                logger.info(
                    f"AES 评分完成: {aes_result['normalized_score']:.2f}/100 "
                    f"(原始分: {aes_result['total_score']:.4f})"
                )

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
        生成简洁的 CSV 评分表（只包含8个核心指标）

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

        # 表头
        rows.append(["序号", "评分指标", "得分", "权重", "加权得分", "说明"])

        # 8个AES指标
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

        if aes_score:
            indicator_scores = aes_score.get("indicator_scores", {})
            weights = aes_score.get("weights", {})

            for i, (key, name, desc) in enumerate(aes_indicators, 1):
                score = indicator_scores.get(key, 0)
                weight = weights.get(key, 0)
                rows.append([
                    i,
                    name,
                    f"{score:.4f}",
                    f"{weight:.0%}",
                    f"{score * weight:.4f}",
                    desc
                ])

        else:
            # 如果没有 AES 评分，使用默认值
            for i, (key, name, desc) in enumerate(aes_indicators, 1):
                rows.append([i, name, "N/A", "N/A", "N/A", desc])

        # 写入 CSV
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        return str(csv_path)
