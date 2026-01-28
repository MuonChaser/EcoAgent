"""
AES (Automatic Essay Scoring) 评分系统配置
"""

from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# AES 评分系统配置
AES_CONFIG = {
    # 停词库路径
    "stopwords_path": str(PROJECT_ROOT / "data" / "stopwords_zh.txt"),

    # 句向量模型（支持中文）
    # 可选：paraphrase-multilingual-MiniLM-L12-v2, distiluse-base-multilingual-cased
    "sentence_model": "paraphrase-multilingual-MiniLM-L12-v2",

    # NLI 模型
    # 可选：microsoft/deberta-v3-base, cross-encoder/nli-deberta-v3-base
    "nli_model": "cross-encoder/nli-deberta-v3-base",

    # 各指标权重（总和为1.0）
    "weights": {
        # 基于 NLP 的定量指标（5个）
        "citation_coverage": 0.15,      # 引用覆盖率
        "causal_relevance": 0.15,       # 因果相关性
        "support_strength": 0.20,       # 支持强度
        "contradiction_penalty": 0.15,  # 矛盾惩罚
        "evidence_sufficiency": 0.15,   # 证据充分性
        # 基于 LLM 的定性指标（3个，从 LLM 评审中提取）
        "endogeneity_quality": 0.07,    # 内生性处理质量（good=1.0, average=0.5, poor=0.0）
        "methodology_rigor": 0.07,      # 方法论严谨性（模型设计得分转换）
        "academic_standards": 0.06,     # 学术规范性（论文质量得分转换）
    },

    # 不同类型 claim 的证据需求数量
    "evidence_needs": {
        "background": 0,      # 背景陈述不需要证据
        "general": 1,         # 一般陈述需要1条证据
        "hypothesis": 3,      # 假设需要3条证据
        "conclusion": 3,      # 结论需要3条证据
        "mechanism": 2,       # 机制分析需要2条证据
    },

    # Claim 分类关键词
    "claim_keywords": {
        "hypothesis": ["假设", "假定", "H1", "H2", "H3", "命题", "预期"],
        "conclusion": ["结论", "表明", "证明", "发现", "显示", "结果显示"],
        "mechanism": ["机制", "路径", "中介", "调节", "影响渠道", "作用路径"],
        "background": ["背景", "现状", "政策", "制度", "历史", "发展"],
    },

    # Evidence 提取模式
    "evidence_patterns": {
        # 引用模式
        "citation": [
            r'[\(（]([^)）]*\d{4}[^)）]*)[\)）]',  # (作者, 2020)
            r'\\citep?\{[^}]+\}',                  # \citep{ref}
            r'[A-Z][a-z]+\s+et\s+al\.\s*\(\d{4}\)',  # Smith et al. (2020)
        ],
        # 数据关键词
        "data_keywords": ["数据", "样本", "观测", "企业", "平均", "标准差", "均值", "中位数"],
        # 结果关键词
        "result_keywords": ["系数", "显著", "p值", "t值", "R²", "回归", "估计", "效应"],
    },

    # 相似度阈值
    "thresholds": {
        "claim_evidence_similarity": 0.3,  # Claim-Evidence 绑定阈值
        "contradiction_threshold": 0.5,     # 矛盾检测阈值
        "support_threshold": 0.5,           # 支持强度阈值
        "neutral_support_score": 0.6,       # neutral 标签的支持分数（0-1，建议0.5-0.7）
    },

    # 文本处理参数
    "text_processing": {
        "min_claim_length": 10,   # 最短 claim 长度
        "max_claim_length": 500,  # 最长 claim 长度
        "min_evidence_length": 5,  # 最短 evidence 长度
    },

    # 性能优化参数
    "performance": {
        "nli_batch_size": 32,              # NLI 批量推理大小
        "max_support_pairs": 999999,       # 支持强度计算最大对数（设为999999表示不限制）
        "max_contradiction_pairs": 999999, # 矛盾检测最大对数（设为999999表示不限制）
        "max_evidences_per_claim": 999,    # 每个 claim 最多采样的 evidence 数（设为999表示不限制）
        "enable_nli": True,                # 是否启用 NLI 计算（如果为 False，使用默认值）
    },
}


def get_aes_config():
    """获取 AES 配置"""
    return AES_CONFIG.copy()