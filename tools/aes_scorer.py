"""
自动论文评分系统 (Automatic Essay Scoring - AES)
基于传统 NLP 方法，不依赖大模型的打分系统
"""

import re
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from loguru import logger

try:
    import torch
    CUDA_AVAILABLE = torch.cuda.is_available()
except ImportError:
    CUDA_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers 未安装，将使用简化的相似度计算")

try:
    from transformers import pipeline
    NLI_AVAILABLE = True
except ImportError:
    NLI_AVAILABLE = False
    logger.warning("transformers 未安装，NLI 功能将不可用")


@dataclass
class Claim:
    """陈述（Claim）"""
    id: int
    text: str
    claim_type: str = "general"  # general, hypothesis, conclusion, background
    evidences: List['Evidence'] = field(default_factory=list)
    scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class Evidence:
    """证据（Evidence）"""
    id: int
    text: str
    source: str  # citation, data, result, theory
    claim_id: int = -1


class AESScorer:
    """
    自动论文评分系统

    评分流程：
    1. 文本预处理和分句
    2. Claim 识别和分类
    3. Evidence 提取和绑定
    4. 8个维度评分
    5. 加权汇总得到总分
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化评分系统

        Args:
            config: 配置参数
                - stopwords_path: 停词库路径
                - sentence_model: 句向量模型名称
                - nli_model: NLI 模型名称
                - weights: 各指标权重
                - thresholds: 各类型 claim 的证据需求数量
        """
        self.config = config or {}

        # 加载停词库
        self.stopwords = self._load_stopwords()

        # 加载模型
        self._load_models()

        # 配置参数 - 8个评分指标及其权重（总和为1.0）
        self.weights = self.config.get("weights", {
            "citation_coverage": 0.15,      # 1. 引用覆盖率
            "causal_relevance": 0.15,       # 2. 因果相关性
            "support_strength": 0.20,       # 3. 支持强度
            "contradiction_penalty": 0.15,  # 4. 矛盾惩罚（越高越好）
            "evidence_sufficiency": 0.15,   # 5. 证据充分性
            "endogeneity_quality": 0.07,    # 6. 内生性处理质量（从LLM评审提取）
            "methodology_rigor": 0.07,      # 7. 方法论严谨性（从LLM评审提取）
            "academic_standards": 0.06,     # 8. 学术规范性（从LLM评审提取）
        })

        # 不同类型 claim 的证据需求数量
        self.evidence_needs = self.config.get("evidence_needs", {
            "background": 0,      # 背景陈述不需要证据
            "general": 1,         # 一般陈述需要1条证据
            "hypothesis": 3,      # 假设需要3条证据
            "conclusion": 3,      # 结论需要3条证据
            "mechanism": 2,       # 机制分析需要2条证据
        })

        logger.info("AES 评分系统初始化完成")

    def _load_stopwords(self) -> set:
        """加载停词库"""
        stopwords_path = self.config.get("stopwords_path")
        if stopwords_path:
            try:
                with open(stopwords_path, 'r', encoding='utf-8') as f:
                    return set(line.strip() for line in f if line.strip())
            except Exception as e:
                logger.warning(f"加载停词库失败: {e}，使用默认停词")

        # 默认中文停词（简化版）
    
        return {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这'
        }

    def _load_models(self):
        """加载 NLP 模型"""
        # 加载句向量模型
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            model_name = self.config.get("sentence_model", "paraphrase-multilingual-MiniLM-L12-v2")
            try:
                device = "cuda" if CUDA_AVAILABLE else "cpu"
                self.sentence_model = SentenceTransformer(model_name, device=device)
                logger.info(f"句向量模型加载成功: {model_name} (device={device})")
            except Exception as e:
                logger.warning(f"句向量模型加载失败: {e}")
                self.sentence_model = None
        else:
            self.sentence_model = None

        # 加载 NLI 模型
        if NLI_AVAILABLE:
            nli_model = self.config.get("nli_model", "microsoft/deberta-v3-base")
            try:
                # pipeline device argument: -1 for CPU, >=0 for GPU device ordinal
                device_id = 0 if CUDA_AVAILABLE else -1
                self.nli_pipeline = pipeline("text-classification", model=nli_model, device=device_id)
                logger.info(f"NLI 模型加载成功: {nli_model} (device={'cuda:0' if CUDA_AVAILABLE else 'cpu'})")
            except Exception as e:
                logger.warning(f"NLI 模型加载失败: {e}")
                self.nli_pipeline = None
        else:
            self.nli_pipeline = None

    def score_paper(
        self,
        paper_text: str,
        metadata: Optional[Dict] = None,
        llm_review: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        对论文进行评分

        Args:
            paper_text: 论文全文
            metadata: 论文元数据（可选）
            llm_review: LLM 评审结果（可选），用于提取定性指标

        Returns:
            评分结果字典
        """
        logger.info("=" * 50)
        logger.info("开始 AES 评分流程")
        logger.info("=" * 50)

        # 1. 分割 claims
        logger.info("步骤 1/5: 提取 claims（陈述）")
        claims = self._extract_claims(paper_text)
        logger.info(f"  提取到 {len(claims)} 个 claims")

        # 2. 提取 evidences
        logger.info("步骤 2/5: 提取 evidences（证据）")
        evidences = self._extract_evidences(paper_text)
        logger.info(f"  提取到 {len(evidences)} 个 evidences")

        # 3. 绑定 claim 和 evidence
        logger.info("步骤 3/5: 绑定 claims 和 evidences")
        self._bind_claims_evidences(claims, evidences)

        # 4. 计算各项指标
        logger.info("步骤 4/5: 计算评分指标")
        scores = {}

        # 指标1: 引用覆盖率
        logger.info("  计算指标 1/8: 引用覆盖率")
        scores["citation_coverage"] = self._calc_citation_coverage(claims)

        # 指标2: 因果相关性
        logger.info("  计算指标 2/8: 因果相关性")
        scores["causal_relevance"] = self._calc_causal_relevance(claims)

        # 指标3: 支持强度
        logger.info("  计算指标 3/8: 支持强度")
        scores["support_strength"] = self._calc_support_strength(claims)

        # 指标4: 矛盾惩罚
        logger.info("  计算指标 4/8: 矛盾惩罚")
        scores["contradiction_penalty"] = self._calc_contradiction_penalty(claims)

        # 指标5: 证据充分性
        logger.info("  计算指标 5/8: 证据充分性")
        scores["evidence_sufficiency"] = self._calc_evidence_sufficiency(claims)

        # 指标6-8: 从 LLM 评审中提取定性指标
        logger.info("  计算指标 6-8: 定性指标（从LLM评审提取）")
        if llm_review:
            llm_scores = self._extract_llm_qualitative_scores(llm_review)
            scores["endogeneity_quality"] = llm_scores.get("endogeneity_quality", 0.0)
            scores["methodology_rigor"] = llm_scores.get("methodology_rigor", 0.0)
            scores["academic_standards"] = llm_scores.get("academic_standards", 0.0)
        else:
            logger.warning("  未提供 LLM 评审结果，定性指标将使用默认值 0.0")
            scores["endogeneity_quality"] = 0.0
            scores["methodology_rigor"] = 0.0
            scores["academic_standards"] = 0.0

        # 5. 加权汇总
        logger.info("步骤 5/5: 加权汇总总分")
        total_score = self._calculate_total_score(scores)

        result = {
            "total_score": total_score,
            "normalized_score": total_score * 100,  # 归一化到 0-100
            "dimension_scores": scores,
            "indicator_scores": scores,  # 兼容别名
            "weights": self.weights,  # 包含权重信息
            "claims_count": len(claims),
            "evidences_count": len(evidences),
            "claims_with_evidence": sum(1 for c in claims if c.evidences),
            "detailed_analysis": {
                "claims": [self._claim_to_dict(c) for c in claims[:10]],  # 仅返回前10个
                "claim_type_distribution": self._get_claim_type_distribution(claims),
            }
        }

        # 输出详细评分日志
        logger.info("=" * 50)
        logger.info("AES 评分结果汇总")
        logger.info("=" * 50)
        for metric, score in scores.items():
            weight = self.weights.get(metric, 0.0)
            weighted = score * weight
            logger.info(f"  {metric}: {score:.4f} (权重: {weight:.0%}, 加权: {weighted:.4f})")
        logger.info("-" * 50)
        logger.info(f"  总分: {total_score:.4f} ({result['normalized_score']:.2f}/100)")
        logger.info(f"  Claims数: {len(claims)}, Evidences数: {len(evidences)}")
        logger.info("=" * 50)
        return result

    def _extract_claims(self, text: str) -> List[Claim]:
        """
        提取 claims（陈述）

        策略：
        1. 按句子分割
        2. 过滤太短或太长的句子
        3. 分类 claim 类型
        """
        # 按标点符号分句
        sentences = re.split(r'[。！？；\n]+', text)

        claims = []
        for i, sent in enumerate(sentences):
            sent = sent.strip()

            # 过滤条件
            if len(sent) < 10 or len(sent) > 500:
                continue

            # 创建 claim
            claim = Claim(
                id=i,
                text=sent,
                claim_type=self._classify_claim_type(sent)
            )
            claims.append(claim)

        return claims

    def _classify_claim_type(self, text: str) -> str:
        """
        分类 claim 类型

        简单规则：
        - 包含"假设"、"假定" -> hypothesis
        - 包含"结论"、"表明"、"证明" -> conclusion
        - 包含"机制"、"路径"、"中介" -> mechanism
        - 包含"背景"、"现状" -> background
        - 其他 -> general
        """
        if any(kw in text for kw in ["假设", "假定", "H1", "H2", "H3", "命题"]):
            return "hypothesis"
        elif any(kw in text for kw in ["结论", "表明", "证明", "发现", "显示"]):
            return "conclusion"
        elif any(kw in text for kw in ["机制", "路径", "中介", "调节", "影响渠道"]):
            return "mechanism"
        elif any(kw in text for kw in ["背景", "现状", "政策", "制度"]):
            return "background"
        else:
            return "general"

    def _extract_evidences(self, text: str) -> List[Evidence]:
        """
        提取 evidences（证据）

        证据类型：
        1. 引用文献：包含作者、年份
        2. 数据：包含数字、统计值
        3. 实证结果：包含回归系数、显著性
        4. 理论：包含理论名称
        """
        evidences = []
        evi_id = 0

        # 提取引用文献
        citation_pattern = r'[\(（]([^)）]*\d{4}[^)）]*)[\)）]|\\citep?\{[^}]+\}'
        for match in re.finditer(citation_pattern, text):
            evidences.append(Evidence(
                id=evi_id,
                text=match.group(0),
                source="citation"
            ))
            evi_id += 1

        # 提取数据证据（包含数字和统计关键词的句子）
        sentences = re.split(r'[。！？；\n]+', text)
        for sent in sentences:
            if re.search(r'\d+\.?\d*[%％]?', sent) and any(kw in sent for kw in
                ["数据", "样本", "观测", "企业", "平均", "标准差", "均值"]):
                evidences.append(Evidence(
                    id=evi_id,
                    text=sent.strip(),
                    source="data"
                ))
                evi_id += 1

        # 提取回归结果
        for sent in sentences:
            if any(kw in sent for kw in ["系数", "显著", "p值", "t值", "R²", "回归"]):
                evidences.append(Evidence(
                    id=evi_id,
                    text=sent.strip(),
                    source="result"
                ))
                evi_id += 1

        # 去重
        unique_evidences = []
        seen_texts = set()
        for evi in evidences:
            if evi.text not in seen_texts:
                unique_evidences.append(evi)
                seen_texts.add(evi.text)

        return unique_evidences

    def _bind_claims_evidences(self, claims: List[Claim], evidences: List[Evidence]):
        """
        绑定 claim 和 evidence

        策略：基于文本相似度或位置邻近性
        """
        logger.info(f"开始绑定 claims 和 evidences...")

        if not self.sentence_model:
            logger.info("使用简单文本匹配策略（sentence_model 不可用）")
            # 简单策略：基于文本包含关系
            for i, claim in enumerate(claims):
                if i % 100 == 0:
                    logger.info(f"  处理进度: {i}/{len(claims)} claims")
                for evi in evidences:
                    # 如果 evidence 在 claim 附近（简化为文本包含）
                    if evi.text in claim.text or any(word in evi.text for word in claim.text.split()[:10]):
                        claim.evidences.append(evi)
                        evi.claim_id = claim.id
        else:
            logger.info(f"使用句向量模型计算相似度 (claims: {len(claims)}, evidences: {len(evidences)})")
            # 使用句向量计算相似度
            claim_texts = [c.text for c in claims]
            evi_texts = [e.text for e in evidences]

            logger.info("  正在编码 claims...")
            claim_embeddings = self.sentence_model.encode(claim_texts, show_progress_bar=True)

            logger.info("  正在编码 evidences...")
            evi_embeddings = self.sentence_model.encode(evi_texts, show_progress_bar=True)

            # 计算相似度矩阵
            logger.info("  计算相似度矩阵...")
            similarity_matrix = np.dot(claim_embeddings, evi_embeddings.T)

            # 绑定最相关的证据（阈值 > 0.3）
            threshold = 0.3
            logger.info(f"  绑定证据到 claims (阈值: {threshold})...")
            matched_count = 0
            for i, claim in enumerate(claims):
                if i % 100 == 0:
                    logger.info(f"    绑定进度: {i}/{len(claims)} claims")
                for j, evi in enumerate(evidences):
                    if similarity_matrix[i, j] > threshold:
                        claim.evidences.append(evi)
                        matched_count += 1
                        if evi.claim_id == -1:
                            evi.claim_id = claim.id

            logger.info(f"绑定完成: {matched_count} 个 claim-evidence 对")

    def _calc_citation_coverage(self, claims: List[Claim]) -> float:
        """
        指标1: 引用覆盖率（更严格版本）

        两种计算模式：
        1. 加权覆盖率：考虑每个 claim 的 evidence 数量
        2. 阈值覆盖率：claim 需要达到最低 evidence 数量才算覆盖
        """
        if not claims:
            return 0.0

        # 获取配置
        coverage_config = self.config.get("citation_coverage", {})
        min_evi = coverage_config.get("min_evidences_per_claim", 2)
        use_weighted = coverage_config.get("use_weighted_coverage", True)

        if use_weighted:
            # 加权覆盖率：每个 claim 的得分 = min(1.0, evidence_count / min_evi)
            scores = []
            for c in claims:
                evi_count = len(c.evidences)
                score = min(1.0, evi_count / min_evi) if min_evi > 0 else (1.0 if evi_count > 0 else 0.0)
                scores.append(score)
            coverage = np.mean(scores) if scores else 0.0
        else:
            # 阈值覆盖率：只有达到 min_evi 才算覆盖
            claims_with_enough_evi = sum(1 for c in claims if len(c.evidences) >= min_evi)
            coverage = claims_with_enough_evi / len(claims)

        logger.debug(f"引用覆盖率: {coverage:.4f} (min_evi={min_evi}, weighted={use_weighted})")
        return float(coverage)

    def _calc_causal_relevance(self, claims: List[Claim]) -> float:
        """
        指标2: 因果相关性
        Claim 和 evi 的向量余弦相似度
        如果一个 claim 有多条 evi，取最大值或 top2 均值
        """
        if not self.sentence_model:
            logger.warning("句向量模型不可用，因果相关性使用默认值 0.5")
            return 0.5

        relevance_scores = []

        for claim in claims:
            if not claim.evidences:
                continue

            # 计算 claim 和所有 evidence 的相似度
            claim_emb = self.sentence_model.encode([claim.text])[0]
            evi_texts = [e.text for e in claim.evidences]
            evi_embs = self.sentence_model.encode(evi_texts)

            # 余弦相似度
            similarities = np.dot(evi_embs, claim_emb) / (
                np.linalg.norm(evi_embs, axis=1) * np.linalg.norm(claim_emb)
            )

            # 取 top2 均值或最大值
            if len(similarities) >= 2:
                top2 = np.sort(similarities)[-2:]
                claim_relevance = np.mean(top2)
            else:
                claim_relevance = np.max(similarities)

            relevance_scores.append(claim_relevance)

        if not relevance_scores:
            return 0.0

        avg_relevance = np.mean(relevance_scores)
        logger.debug(f"因果相关性: {avg_relevance:.4f}")
        return float(avg_relevance)

    def _calc_support_strength(self, claims: List[Claim]) -> float:
        """
        指标3: 支持强度
        用 NLI 测试 evi 支持/反驳/无关 claim 的概率

        优化策略：
        1. 批量处理 NLI 推理
        2. 限制最大计算数量（采样）
        3. 添加进度日志
        """
        if not self.nli_pipeline:
            logger.warning("NLI 模型不可用，支持强度使用默认值 0.6")
            return 0.6

        # 收集所有需要计算的 (evidence, claim) 对
        text_pairs = []
        max_pairs = self.config.get("performance", {}).get("max_support_pairs", 500)
        batch_size = self.config.get("performance", {}).get("nli_batch_size", 32)

        for claim in claims:
            if not claim.evidences:
                continue

            claim_text = claim.text

            for evi in claim.evidences:
                text_pairs.append(f"{evi.text} [SEP] {claim_text}")

                # 如果超过限制，停止收集
                if len(text_pairs) >= max_pairs:
                    break

            if len(text_pairs) >= max_pairs:
                logger.info(f"  支持强度计算已达到最大限制 {max_pairs} 对，将采样计算")
                break

        if not text_pairs:
            logger.warning("  没有可计算的 evidence-claim 对")
            return 0.0

        logger.info(f"  将计算 {len(text_pairs)} 个 evidence-claim 对的支持强度...")

        # 批量处理（如果 pipeline 支持）
        support_scores = []

        try:
            for i in range(0, len(text_pairs), batch_size):
                batch = text_pairs[i:i + batch_size]

                # 显示进度
                if i % (batch_size * 5) == 0 and i > 0:
                    logger.info(f"    进度: {i}/{len(text_pairs)}")

                try:
                    # 批量推理
                    results = self.nli_pipeline(batch)

                    # 处理批量结果
                    # 评分逻辑：entailment=1.0, neutral=0.6, contradiction=0.0
                    # 学术论文中的证据往往是间接支持关系，不是严格的文本蕴含
                    # neutral 表示"不矛盾"，在学术语境下也是一种支持
                    neutral_score = self.config.get("thresholds", {}).get("neutral_support_score", 0.6)

                    if isinstance(results, list) and len(results) > 0:
                        # 如果返回的是列表的列表（每个输入返回多个结果）
                        if isinstance(results[0], list):
                            for result_list in results:
                                support_prob = 0.0
                                for item in result_list:
                                    label = item.get('label', '').lower()
                                    score = item.get('score', 0.0)
                                    if 'entail' in label:
                                        support_prob = score
                                        break
                                    elif 'neutral' in label:
                                        support_prob = neutral_score * score
                                        break
                                support_scores.append(support_prob)
                        # 如果返回的是单层列表（每个输入一个结果）
                        else:
                            for item in results:
                                label = item.get('label', '').lower()
                                score = item.get('score', 0.0)
                                if 'entail' in label:
                                    support_scores.append(score)
                                elif 'neutral' in label:
                                    support_scores.append(neutral_score * score)
                                elif 'contradict' in label:
                                    support_scores.append(0.0)
                                else:
                                    support_scores.append(0.3)

                except Exception as e:
                    logger.warning(f"  批量 NLI 计算失败: {e}，跳过该批次")
                    continue

        except Exception as e:
            logger.error(f"  支持强度计算失败: {e}")
            return 0.6  # 使用默认值

        if not support_scores:
            logger.warning("  未能计算任何支持强度分数")
            return 0.0

        avg_support = np.mean(support_scores)
        logger.info(f"  支持强度计算完成: 平均分 {avg_support:.4f}")
        return float(avg_support)

    def _calc_contradiction_penalty(self, claims: List[Claim]) -> float:
        """
        指标4: 矛盾惩罚
        多证据下，证据两两做 NLI，检测矛盾
        返回值越高越好（1 - 矛盾率）

        优化策略：
        1. 批量处理 NLI 推理
        2. 限制最大计算数量（采样）
        3. 对 evidences 过多的 claim 进行采样
        """
        if not self.nli_pipeline:
            logger.warning("NLI 模型不可用，矛盾惩罚使用默认值 0.8")
            return 0.8

        # 收集所有需要比较的 evidence 对
        text_pairs = []
        max_pairs = self.config.get("performance", {}).get("max_contradiction_pairs", 300)
        batch_size = self.config.get("performance", {}).get("nli_batch_size", 32)
        max_evi_per_claim = self.config.get("performance", {}).get("max_evidences_per_claim", 5)

        for claim in claims:
            evidences = claim.evidences
            if len(evidences) < 2:
                continue

            # 如果 evidence 太多，采样比较
            if len(evidences) > max_evi_per_claim:
                # 随机采样
                import random
                sampled_evidences = random.sample(evidences, max_evi_per_claim)
            else:
                sampled_evidences = evidences

            # 两两比较
            for i in range(len(sampled_evidences)):
                for j in range(i + 1, len(sampled_evidences)):
                    text_pairs.append(f"{sampled_evidences[i].text} [SEP] {sampled_evidences[j].text}")

                    # 达到上限就停止
                    if len(text_pairs) >= max_pairs:
                        break

                if len(text_pairs) >= max_pairs:
                    break

            if len(text_pairs) >= max_pairs:
                logger.info(f"  矛盾检测已达到最大限制 {max_pairs} 对，将采样计算")
                break

        if not text_pairs:
            logger.info("  没有足够的 evidence 对进行矛盾检测")
            return 1.0

        logger.info(f"  将检测 {len(text_pairs)} 个 evidence 对的矛盾性...")

        # 批量处理
        contradiction_count = 0
        total_pairs = 0

        try:
            for i in range(0, len(text_pairs), batch_size):
                batch = text_pairs[i:i + batch_size]

                # 显示进度
                if i % (batch_size * 5) == 0 and i > 0:
                    logger.info(f"    进度: {i}/{len(text_pairs)}")

                try:
                    # 批量推理
                    results = self.nli_pipeline(batch)

                    # 处理批量结果
                    if isinstance(results, list) and len(results) > 0:
                        # 如果返回的是列表的列表
                        if isinstance(results[0], list):
                            for result_list in results:
                                for item in result_list:
                                    if 'contradiction' in item.get('label', '').lower():
                                        if item.get('score', 0.0) > 0.5:
                                            contradiction_count += 1
                                        break
                                total_pairs += 1
                        # 如果返回的是单层列表
                        else:
                            for item in results:
                                if 'contradiction' in item.get('label', '').lower():
                                    if item.get('score', 0.0) > 0.5:
                                        contradiction_count += 1
                                total_pairs += 1

                except Exception as e:
                    logger.warning(f"  批量矛盾检测失败: {e}，跳过该批次")
                    continue

        except Exception as e:
            logger.error(f"  矛盾惩罚计算失败: {e}")
            return 0.8  # 使用默认值

        if total_pairs == 0:
            logger.warning("  未能计算任何矛盾对")
            return 1.0

        # 矛盾惩罚：1 - 矛盾率
        penalty = 1.0 - (contradiction_count / total_pairs)
        logger.info(f"  矛盾检测完成: {contradiction_count}/{total_pairs} 对存在矛盾, 得分 {penalty:.4f}")
        return penalty

    def _calc_evidence_sufficiency(self, claims: List[Claim]) -> float:
        """
        指标5: 证据充分性
        SU = min(1, independent_evidence_count / need)
        不同类型 claim 的 need 不同
        """
        sufficiency_scores = []

        for claim in claims:
            claim_type = claim.claim_type
            need = self.evidence_needs.get(claim_type, 1)

            if need == 0:
                # 背景类陈述不需要证据
                sufficiency_scores.append(1.0)
                continue

            # 计算独立证据数量
            independent_count = len(set(e.text for e in claim.evidences))

            # 充分性得分
            su = min(1.0, independent_count / need)
            sufficiency_scores.append(su)

        if not sufficiency_scores:
            return 0.0

        avg_sufficiency = np.mean(sufficiency_scores)
        logger.debug(f"证据充分性: {avg_sufficiency:.4f}")
        return float(avg_sufficiency)

    def _extract_llm_qualitative_scores(self, llm_review: Dict[str, Any]) -> Dict[str, float]:
        """
        从 LLM 评审结果中提取定性指标（转换为 0-1 的量化值）

        支持两种数据结构：
        1. Pydantic 模型结构: qualitative_analysis.endogeneity_rating, quantitative_analysis.dimension_scores
        2. 简化结构: quantitative_analysis.endogeneity_assessment, quantitative_analysis.model_design

        Args:
            llm_review: LLM 评审结果字典

        Returns:
            包含 3 个定性指标的字典
        """
        scores = {
            "endogeneity_quality": 0.0,      # 指标6: 内生性处理质量
            "methodology_rigor": 0.0,        # 指标7: 方法论严谨性
            "academic_standards": 0.0,       # 指标8: 学术规范性
        }

        try:
            qualitative = llm_review.get("qualitative_analysis", {})
            quantitative = llm_review.get("quantitative_analysis", {})

            # ========== 指标6: 内生性处理质量 ==========
            # 尝试多种路径获取 endogeneity_rating
            endogeneity_rating = None

            # 路径1: qualitative_analysis.endogeneity_rating
            if qualitative:
                endogeneity_rating = qualitative.get("endogeneity_rating", "")

            # 路径2: quantitative_analysis.endogeneity_assessment.overall_rating
            if not endogeneity_rating and quantitative:
                endo_assess = quantitative.get("endogeneity_assessment", {})
                if isinstance(endo_assess, dict):
                    endogeneity_rating = endo_assess.get("overall_rating", "")
                    # 也可能直接是分数
                    if not endogeneity_rating and "score" in endo_assess:
                        endo_score = endo_assess.get("score", 0)
                        if endo_score >= 70:
                            endogeneity_rating = "good"
                        elif endo_score >= 40:
                            endogeneity_rating = "average"
                        else:
                            endogeneity_rating = "poor"

            if isinstance(endogeneity_rating, str):
                endogeneity_rating = endogeneity_rating.lower()
                if endogeneity_rating == "good":
                    scores["endogeneity_quality"] = 1.0
                elif endogeneity_rating == "average":
                    scores["endogeneity_quality"] = 0.5
                elif endogeneity_rating == "poor":
                    scores["endogeneity_quality"] = 0.0

            # ========== 指标7: 方法论严谨性 ==========
            model_score = None

            # 路径1: quantitative_analysis.dimension_scores 列表
            dimension_scores = quantitative.get("dimension_scores", [])
            if isinstance(dimension_scores, list):
                for dim in dimension_scores:
                    if isinstance(dim, dict) and "模型设计" in dim.get("dimension", ""):
                        model_score = dim.get("total_score", 0)
                        break

            # 路径2: quantitative_analysis.model_design.score
            if model_score is None:
                model_design = quantitative.get("model_design", {})
                if isinstance(model_design, dict):
                    model_score = model_design.get("score", 0)

            if model_score is not None:
                # 转换为0-1分数（假设满分100）
                if model_score > 10:  # 满分100的情况
                    model_score = model_score / 10
                if model_score >= 8:
                    scores["methodology_rigor"] = 1.0
                elif model_score >= 5:
                    scores["methodology_rigor"] = 0.5
                else:
                    scores["methodology_rigor"] = model_score / 10  # 更细粒度

            # ========== 指标8: 学术规范性 ==========
            quality_score = None

            # 路径1: quantitative_analysis.dimension_scores 列表
            if isinstance(dimension_scores, list):
                for dim in dimension_scores:
                    if isinstance(dim, dict) and "论文质量" in dim.get("dimension", ""):
                        quality_score = dim.get("total_score", 0)
                        break

            # 路径2: quantitative_analysis.paper_quality.score
            if quality_score is None:
                paper_quality = quantitative.get("paper_quality", {})
                if isinstance(paper_quality, dict):
                    quality_score = paper_quality.get("score", 0)

            if quality_score is not None:
                # 转换为0-1分数
                if quality_score > 10:
                    quality_score = quality_score / 10
                if quality_score >= 8:
                    scores["academic_standards"] = 1.0
                elif quality_score >= 5:
                    scores["academic_standards"] = 0.5
                else:
                    scores["academic_standards"] = quality_score / 10

            logger.info(f"  LLM定性指标提取: 内生性={scores['endogeneity_quality']:.2f}, "
                       f"方法论={scores['methodology_rigor']:.2f}, 学术规范={scores['academic_standards']:.2f}")

        except Exception as e:
            logger.warning(f"提取 LLM 定性指标失败: {e}")

        return scores

    def _calculate_total_score(self, scores: Dict[str, float]) -> float:
        """
        加权汇总总分
        """
        total = 0.0
        for metric, score in scores.items():
            weight = self.weights.get(metric, 0.0)
            total += weight * score

        return total

    def _get_claim_type_distribution(self, claims: List[Claim]) -> Dict[str, int]:
        """获取 claim 类型分布"""
        distribution = defaultdict(int)
        for claim in claims:
            distribution[claim.claim_type] += 1
        return dict(distribution)

    def _claim_to_dict(self, claim: Claim) -> Dict[str, Any]:
        """将 Claim 转换为字典"""
        return {
            "id": claim.id,
            "text": claim.text[:100] + "..." if len(claim.text) > 100 else claim.text,
            "type": claim.claim_type,
            "evidence_count": len(claim.evidences),
        }


def get_aes_scorer(config: Optional[Dict[str, Any]] = None) -> AESScorer:
    """
    获取 AES 评分器实例（单例模式）

    Args:
        config: 配置参数

    Returns:
        AESScorer 实例
    """
    if not hasattr(get_aes_scorer, "_instance"):
        get_aes_scorer._instance = AESScorer(config)
    return get_aes_scorer._instance