# AES 自动论文评分系统使用指南

## 1. 系统概述

AES (Automatic Essay Scoring) 是一个基于传统 NLP 方法的自动论文评分系统，不依赖大模型，通过 8 个量化指标对学术论文进行客观评估。

### 核心特点

- **不依赖大模型**：使用传统 NLP 技术（句向量、NLI 模型）
- **多维度评分**：8 个评分维度全面评估论文质量
- **可解释性强**：每个指标都有明确的计算逻辑
- **可配置性高**：支持自定义权重、阈值等参数

## 2. 评分维度

### 已实现的 5 个指标

#### 2.1 引用覆盖率 (Citation Coverage)

**定义**：至少有 1 个证据的 claim 数量 / claim 总数量

**计算方法**：
```python
coverage = claims_with_evidence / total_claims
```

**含义**：文献调研的广度，能否为每个陈述提供证据支持

**权重**：15%

---

#### 2.2 因果相关性 (Causal Relevance)

**定义**：Claim 和 Evidence 的向量余弦相似度

**计算方法**：
- 使用句向量模型（如 paraphrase-multilingual-MiniLM-L12-v2）
- 计算 claim 与所有 evidence 的相似度
- 如果有多条 evidence，取 top2 均值

**含义**：识别策略的选取是否恰当

**权重**：15%

---

#### 2.3 支持强度 (Support Strength)

**定义**：使用 NLI 模型测试证据对陈述的支持程度

**计算方法**：
```python
使用 NLI 模型（如 deberta-v3-base）计算：
- P(evidence ⊨ claim)  # 支持概率
- P(evidence ⊥ claim)  # 反驳概率
- P(evidence ∥ claim)  # 无关概率
```

**含义**：因果推断的置信度，论证是否令人信服

**权重**：20%

---

#### 2.4 矛盾惩罚 (Contradiction Penalty)

**定义**：多证据场景下，证据之间的矛盾程度

**计算方法**：
```python
对每个 claim 的证据两两进行 NLI 检测
penalty = 1.0 - (contradiction_count / total_pairs)
```

**含义**：文章内在一致性，结论是否稳健

**权重**：15%

---

#### 2.5 证据充分性 (Evidence Sufficiency)

**定义**：证据数量是否满足 claim 类型的需求

**计算方法**：
```python
SU = min(1, independent_evidence_count / need)
```

不同类型 claim 的 need：
- background: 0（背景陈述不需要证据）
- general: 1（一般陈述需要 1 条）
- hypothesis: 3（假设需要 3 条）
- conclusion: 3（结论需要 3 条）
- mechanism: 2（机制分析需要 2 条）

**含义**：论证的完备性，是否从多个角度充分论证

**权重**：15%

---

### 基于 LLM 的 3 个定性指标

**说明**：这 3 个指标从 LLM 定性评审结果中提取，转换为离散值（0/0.5/1）进行量化。

#### 2.6 内生性处理质量 (Endogeneity Quality)

**定义**：LLM 对论文内生性问题识别与处理的定性评级

**计算方法**：
```python
从 LLM 评审的 qualitative_analysis.endogeneity_rating 提取：
- "good" (好) → 1.0
- "average" (一般) → 0.5
- "poor" (差) → 0.0
```

**含义**：
- 内生性识别的充分性
- 内生性处理策略的有效性
- 因果推断的可信度

**权重**：7%

---

#### 2.7 方法论严谨性 (Methodology Rigor)

**定义**：LLM 对论文模型设计维度的定量评分（转换为离散值）

**计算方法**：
```python
从 LLM 评审的 dimension_scores[维度3：模型设计] 提取：
- 8-10 分 → 1.0 (方法严谨)
- 5-7 分 → 0.5 (方法基本合理)
- <5 分 → 0.0 (方法存在问题)
```

**含义**：
- 模型选择的合理性
- 识别策略的有效性
- 变量设定的完整性

**权重**：7%

---

#### 2.8 学术规范性 (Academic Standards)

**定义**：LLM 对论文质量维度的定量评分（转换为离散值）

**计算方法**：
```python
从 LLM 评审的 dimension_scores[维度5：论文质量] 提取：
- 8-10 分 → 1.0 (规范性优秀)
- 5-7 分 → 0.5 (规范性良好)
- <5 分 → 0.0 (规范性不足)
```

**含义**：
- 写作规范性
- 文献引用规范性
- 图表质量与学术表达

**权重**：6%

---

## 3. 使用方法

### 3.1 基础使用

```python
from tools.aes_scorer import get_aes_scorer
from config.aes_config import get_aes_config

# 初始化评分器
config = get_aes_config()
scorer = get_aes_scorer(config)

# 评分
paper_text = "论文全文..."
result = scorer.score_paper(paper_text)

# 查看结果
print(f"总分: {result['normalized_score']:.2f}/100")
print(f"分维度得分: {result['dimension_scores']}")
```

### 3.2 与 Reviewer Agent 集成

```python
from agents import ReviewerAgent

# 启用 AES 评分
reviewer = ReviewerAgent(enable_aes=True)

# 执行审稿
input_data = {
    "research_topic": "...",
    "final_report": "论文全文...",
    # ... 其他字段
}

result = reviewer.run(input_data)

# AES 评分结果
aes_score = result.get("aes_score", {})
print(f"AES 总分: {aes_score['normalized_score']:.2f}/100")
```

### 3.3 完整流程示例

```bash
# 运行完整研究流程（包含 AES 评分）
python run_full_pipeline.py --topic "研究主题"

# 单独测试 AES 评分
python examples/aes_example.py

# 测试 Reviewer + AES 集成
python examples/reviewer_aes_example.py
```

---

## 4. 配置说明

### 4.1 配置文件位置

- **AES 配置**：`config/aes_config.py`
- **停词库**：`data/stopwords_zh.txt`

### 4.2 关键配置项

```python
AES_CONFIG = {
    # 句向量模型
    "sentence_model": "paraphrase-multilingual-MiniLM-L12-v2",

    # NLI 模型
    "nli_model": "cross-encoder/nli-deberta-v3-base",

    # 各指标权重（总和为 1.0）
    "weights": {
        # 基于 NLP 的定量指标（5个）
        "citation_coverage": 0.15,
        "causal_relevance": 0.15,
        "support_strength": 0.20,
        "contradiction_penalty": 0.15,
        "evidence_sufficiency": 0.15,
        # 基于 LLM 的定性指标（3个）
        "endogeneity_quality": 0.07,
        "methodology_rigor": 0.07,
        "academic_standards": 0.06,
    },

    # Claim 类型证据需求
    "evidence_needs": {
        "background": 0,
        "general": 1,
        "hypothesis": 3,
        "conclusion": 3,
        "mechanism": 2,
    },

    # 相似度阈值
    "thresholds": {
        "claim_evidence_similarity": 0.3,
        "contradiction_threshold": 0.5,
        "support_threshold": 0.5,
    },
}
```

### 4.3 自定义配置

```python
from config.aes_config import get_aes_config

# 获取默认配置
config = get_aes_config()

# 修改权重
config["weights"]["citation_coverage"] = 0.20
config["weights"]["support_strength"] = 0.25

# 修改证据需求
config["evidence_needs"]["hypothesis"] = 5

# 使用自定义配置
from tools.aes_scorer import AESScorer
scorer = AESScorer(config)
```

---

## 5. 技术架构

### 5.1 核心组件

```
AESScorer
├── Claim 提取与分类
│   ├── 句子分割
│   ├── 过滤（长度、停词）
│   └── 类型分类（hypothesis/conclusion/mechanism/background/general）
├── Evidence 提取
│   ├── 引用文献（正则匹配）
│   ├── 数据证据（数字+关键词）
│   └── 回归结果（系数、显著性）
├── Claim-Evidence 绑定
│   ├── 句向量相似度计算
│   └── 阈值过滤（> 0.3）
└── 8 维度评分
    ├── NLP 定量指标（5个）
    │   ├── 引用覆盖率
    │   ├── 因果相关性
    │   ├── 支持强度
    │   ├── 矛盾惩罚
    │   └── 证据充分性
    └── LLM 定性指标（3个）
        ├── 内生性处理质量
        ├── 方法论严谨性
        └── 学术规范性
```

### 5.2 依赖模型

| 模型 | 用途 | 大小 | 是否必须 |
|------|------|------|----------|
| paraphrase-multilingual-MiniLM-L12-v2 | 句向量 | ~420MB | 否（有简化方案） |
| cross-encoder/nli-deberta-v3-base | NLI 推理 | ~1.5GB | 否（有简化方案） |

**注意**：即使没有安装模型，AES 系统仍可运行，会使用简化的规则匹配方法。

---

## 6. 输出格式

### 6.1 评分结果结构

```python
{
    "total_score": 0.7234,           # 原始总分（0-1）
    "normalized_score": 72.34,       # 归一化分数（0-100）
    "dimension_scores": {
        # NLP 定量指标
        "citation_coverage": 0.85,
        "causal_relevance": 0.72,
        "support_strength": 0.68,
        "contradiction_penalty": 0.91,
        "evidence_sufficiency": 0.65,
        # LLM 定性指标（从 LLM 评审提取）
        "endogeneity_quality": 1.0,      # good=1.0, average=0.5, poor=0.0
        "methodology_rigor": 0.5,        # 模型设计 5-7分 → 0.5
        "academic_standards": 1.0,       # 论文质量 8-10分 → 1.0
    },
    "claims_count": 45,              # Claim 总数
    "evidences_count": 38,           # Evidence 总数
    "claims_with_evidence": 32,      # 有证据的 Claim 数
    "detailed_analysis": {
        "claims": [...],             # 前 10 个 Claim 详情
        "claim_type_distribution": {
            "hypothesis": 3,
            "conclusion": 5,
            "mechanism": 2,
            "background": 8,
            "general": 27,
        }
    }
}
```

### 6.2 集成到 Reviewer 输出

```python
{
    "research_topic": "...",
    "review_report": {...},          # LLM 定性评审
    "aes_score": {...},              # AES 定量评分
    "aes_enabled": true,
}
```

---

## 7. 常见问题

### Q1: 为什么 AES 评分和 LLM 评分差异很大？

**A**: AES 评分基于客观的文本特征（引用数量、相似度等），而 LLM 评分侧重主观的学术判断（创新性、理论深度等）。两者互补，建议综合参考。

### Q2: 如何提高 AES 评分？

**A**:
1. **引用覆盖率**：为每个重要陈述提供文献支持
2. **支持强度**：使用明确的因果语言，确保证据与结论的逻辑链条清晰
3. **矛盾惩罚**：避免前后矛盾的陈述，确保结论一致
4. **证据充分性**：对假设和结论提供 3 条以上独立证据

### Q3: 模型下载失败怎么办？

**A**: AES 系统会自动降级到简化模式。也可以手动下载模型：
```bash
# 安装 sentence-transformers
pip install sentence-transformers

# 预下载模型
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"
```

### Q4: 如何调整评分权重？

**A**: 修改 `config/aes_config.py` 中的 `weights` 字典，确保总和为 1.0。

---

## 8. 扩展开发

### 8.1 添加新的评分指标

```python
# 在 tools/aes_scorer.py 中添加新方法
def _calc_your_new_metric(self, claims: List[Claim]) -> float:
    """
    新指标计算逻辑
    """
    # ... 实现逻辑
    return score

# 在 score_paper() 方法中调用
scores["your_new_metric"] = self._calc_your_new_metric(claims)
```

### 8.2 自定义 Claim 分类规则

```python
# 修改 _classify_claim_type() 方法
def _classify_claim_type(self, text: str) -> str:
    if "你的关键词" in text:
        return "your_custom_type"
    # ... 其他规则
```

---

## 9. 参考文献

- Baron, R. M., & Kenny, D. A. (1986). The moderator–mediator variable distinction in social psychological research.
- Imai, K., Keele, L., & Tingley, D. (2010). A general approach to causal mediation analysis.
- NLI 模型: [Hugging Face - Text Classification](https://huggingface.co/tasks/text-classification)
- Sentence Transformers: [SBERT](https://www.sbert.net/)

---

## 10. 更新日志

### v1.1.0 (2026-01-26)

- ✅ 集成 LLM 定性指标作为指标 6-8
- ✅ 实现 8 个完整评分维度
- ✅ 支持混合评分（NLP 定量 + LLM 定性）

### v1.0.0 (2026-01-26)

- ✅ 实现 5 个核心评分指标（基于 NLP）
- ✅ 集成到 ReviewerAgent
- ✅ 支持中文论文评分
- ✅ 创建配置系统和停词库

---

## 联系与反馈

如有问题或建议，请提交 Issue 或联系开发团队。
