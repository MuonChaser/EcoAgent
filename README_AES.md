# AES 自动论文评分系统

## 系统概述

AES (Automatic Essay Scoring) 是一个混合评分系统，结合了**传统 NLP 定量指标**和 **LLM 定性评审**，对学术论文进行全面、客观的自动评估。

### 核心特点

✅ **8 个评分维度**：5 个 NLP 定量指标 + 3 个 LLM 定性指标
✅ **混合评分机制**：传统 NLP + 大模型定性分析
✅ **高可解释性**：每个指标都有明确的计算逻辑和学术含义
✅ **无缝集成**：与 ReviewerAgent 深度集成，一次调用完成双重评审

---

## 评分体系

### 第一部分：NLP 定量指标（5个，权重 80%）

基于传统 NLP 技术（句向量、NLI 模型），对论文文本进行客观量化评估。

| 指标 | 权重 | 计算方法 | 学术含义 |
|------|------|----------|----------|
| 引用覆盖率 | 15% | 有证据的 claim / 总 claim | 文献调研广度 |
| 因果相关性 | 15% | Claim-Evidence 余弦相似度 | 识别策略恰当性 |
| 支持强度 | 20% | NLI 模型判定的支持概率 | 因果推断置信度 |
| 矛盾惩罚 | 15% | 1 - 证据间矛盾率 | 文章内在一致性 |
| 证据充分性 | 15% | 证据数 / 需求数 | 论证完备性 |

### 第二部分：LLM 定性指标（3个，权重 20%）

从 LLM 定性评审结果中提取，转换为离散值（0/0.5/1）。

| 指标 | 权重 | 来源 | 转换规则 |
|------|------|------|----------|
| 内生性处理质量 | 7% | LLM 内生性评级 | good=1.0, average=0.5, poor=0.0 |
| 方法论严谨性 | 7% | LLM 模型设计得分 | 8-10分→1.0, 5-7分→0.5, <5分→0.0 |
| 学术规范性 | 6% | LLM 论文质量得分 | 8-10分→1.0, 5-7分→0.5, <5分→0.0 |

**总分公式**：

```
AES总分 = Σ(指标得分 × 权重)
归一化分数 = AES总分 × 100  (0-100分)
```

---

## 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│  1. 用户调用 ReviewerAgent                                   │
│     reviewer = ReviewerAgent(enable_aes=True)               │
│     result = reviewer.run(input_data)                       │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│  2. LLM 定性评审（自动执行）                                 │
│     - 内生性分析（good/average/poor）                        │
│     - 5 维度量化评分（各 10 分）                             │
│     - 修改建议与总体评价                                      │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│  3. AES 自动评分（自动执行）                                 │
│                                                             │
│  3.1 NLP 定量分析                                           │
│      - 提取 Claims（分类为 5 种类型）                        │
│      - 提取 Evidences（引用、数据、回归结果）                │
│      - 绑定 Claim-Evidence（基于句向量相似度）              │
│      - 计算 5 个 NLP 指标                                    │
│                                                             │
│  3.2 LLM 定性指标提取                                        │
│      - 从 LLM 评审结果提取 3 个定性指标                      │
│      - 转换为 0/0.5/1 的离散值                               │
│                                                             │
│  3.3 加权汇总                                               │
│      - 总分 = Σ(8个指标 × 权重)                             │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│  4. 返回综合评审结果                                         │
│     {                                                       │
│       "review_report": {...},      # LLM 定性评审           │
│       "aes_score": {               # AES 定量评分           │
│         "normalized_score": 72.3,  # 归一化总分             │
│         "dimension_scores": {...}, # 8 维度得分             │
│       }                                                     │
│     }                                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 1. 基础使用

```python
from agents import ReviewerAgent

# 初始化审稿人（默认启用 AES）
reviewer = ReviewerAgent(enable_aes=True)

# 准备输入数据
input_data = {
    "research_topic": "数字化转型对企业创新的影响",
    "final_report": "论文全文...",
    # ... 其他字段
}

# 执行审稿（LLM + AES）
result = reviewer.run(input_data)

# 查看结果
print(f"LLM 定性评分: {result['review_report']['quantitative_analysis']['overall_score']}")
print(f"AES 定量评分: {result['aes_score']['normalized_score']:.2f}/100")
```

### 2. 完整流程

```bash
# 运行完整研究流程（包含 AES 评分）
python run_full_pipeline.py --topic "你的研究主题"

# 生成的文件包含：
# - LaTeX 论文
# - LLM 定性评审报告
# - AES 定量评分结果
```

### 3. 测试示例

```bash
# 测试 AES 基础功能
python examples/aes_example.py

# 测试 Reviewer + AES 集成
python examples/reviewer_aes_example.py
```

---

## 文件结构

```
multi-agent/
├── tools/
│   └── aes_scorer.py          # AES 评分核心模块
├── config/
│   └── aes_config.py          # AES 配置文件
├── data/
│   └── stopwords_zh.txt       # 中文停词库
├── agents/
│   └── reviewer.py            # 审稿人 Agent（集成 AES）
├── examples/
│   ├── aes_example.py         # AES 测试示例
│   └── reviewer_aes_example.py # 完整审稿示例
├── docs/
│   └── AES_SCORING_GUIDE.md   # 详细使用指南
└── README_AES.md              # 本文件
```

---

## 配置说明

### 修改评分权重

编辑 `config/aes_config.py`：

```python
"weights": {
    # NLP 定量指标
    "citation_coverage": 0.15,
    "causal_relevance": 0.15,
    "support_strength": 0.20,
    "contradiction_penalty": 0.15,
    "evidence_sufficiency": 0.15,
    # LLM 定性指标
    "endogeneity_quality": 0.07,
    "methodology_rigor": 0.07,
    "academic_standards": 0.06,
}
```

### 修改 Claim 类型证据需求

```python
"evidence_needs": {
    "background": 0,      # 背景陈述不需要证据
    "general": 1,         # 一般陈述需要 1 条
    "hypothesis": 3,      # 假设需要 3 条（可调整）
    "conclusion": 3,      # 结论需要 3 条
    "mechanism": 2,       # 机制分析需要 2 条
}
```

---

## 输出示例

```json
{
  "total_score": 0.7234,
  "normalized_score": 72.34,
  "dimension_scores": {
    "citation_coverage": 0.85,
    "causal_relevance": 0.72,
    "support_strength": 0.68,
    "contradiction_penalty": 0.91,
    "evidence_sufficiency": 0.65,
    "endogeneity_quality": 1.0,
    "methodology_rigor": 0.5,
    "academic_standards": 1.0
  },
  "claims_count": 45,
  "evidences_count": 38,
  "claims_with_evidence": 32,
  "claim_type_distribution": {
    "hypothesis": 3,
    "conclusion": 5,
    "mechanism": 2,
    "background": 8,
    "general": 27
  }
}
```

---

## 技术依赖

### 可选依赖（增强功能）

- `sentence-transformers`：句向量计算（用于因果相关性）
- `transformers`：NLI 模型（用于支持强度和矛盾惩罚）

**注意**：即使不安装这些库，AES 系统仍可运行，会使用简化的规则匹配方法。

### 安装依赖

```bash
# 安装可选依赖
pip install sentence-transformers transformers

# 或使用轻量版（不安装模型）
# AES 会自动降级到简化模式
```

---

## 常见问题

### Q1: LLM 定性指标从哪里来？

**A**: 从 ReviewerAgent 的定性评审结果中自动提取：
- `qualitative_analysis.endogeneity_rating` → 内生性处理质量
- `quantitative_analysis.dimension_scores[模型设计]` → 方法论严谨性
- `quantitative_analysis.dimension_scores[论文质量]` → 学术规范性

### Q2: 为什么 LLM 指标是离散值（0/0.5/1）？

**A**: 定性评级本质上是分类而非连续值。将其量化为 3 档（优秀/良好/不足）：
- 保留定性判断的语义信息
- 避免过度精细化带来的虚假精度
- 更符合学术评审的实际操作

### Q3: 如何调整 NLP 和 LLM 指标的权重比例？

**A**: 当前配置：NLP 定量 80% + LLM 定性 20%

如果想提高 LLM 权重，可以调整 `config/aes_config.py`：

```python
# 示例：NLP 70% + LLM 30%
"weights": {
    "citation_coverage": 0.14,        # 15% → 14%
    "causal_relevance": 0.14,         # 15% → 14%
    "support_strength": 0.17,         # 20% → 17%
    "contradiction_penalty": 0.13,    # 15% → 13%
    "evidence_sufficiency": 0.12,     # 15% → 12%
    "endogeneity_quality": 0.10,      # 7% → 10%
    "methodology_rigor": 0.10,        # 7% → 10%
    "academic_standards": 0.10,       # 6% → 10%
}
```

### Q4: 能否只使用 AES 而不用 LLM？

**A**: 可以，但会损失 3 个定性指标（指标 6-8 将为 0）。

```python
# 单独使用 AES
from tools.aes_scorer import get_aes_scorer

scorer = get_aes_scorer()
result = scorer.score_paper(paper_text)  # 不传入 llm_review
```

---

## 进阶使用

### 自定义综合评分公式

```python
# 在完整流程中自定义综合分
llm_score = result['review_report']['quantitative_analysis']['overall_score']
aes_score = result['aes_score']['normalized_score']

# 方案1：简单加权平均
combined = 0.6 * llm_score + 0.4 * aes_score

# 方案2：考虑置信度加权
llm_confidence = 0.8  # LLM 的置信度
combined = (llm_confidence * llm_score + (1 - llm_confidence) * aes_score)

# 方案3：取上下界
combined_min = min(llm_score, aes_score)
combined_max = max(llm_score, aes_score)
```

---

## 更新计划

- [ ] 支持英文论文评分
- [ ] 添加更多 Claim 类型（如反事实陈述）
- [ ] 支持多模态证据（图表、公式）
- [ ] 提供评分报告可视化

---

## 参考文献

1. Baron, R. M., & Kenny, D. A. (1986). The moderator–mediator variable distinction.
2. Imai, K., et al. (2010). A general approach to causal mediation analysis.
3. Sentence Transformers: https://www.sbert.net/
4. NLI Models: https://huggingface.co/tasks/text-classification

---

## 许可与贡献

欢迎提交 Issue 和 Pull Request！

详细文档请参考：[docs/AES_SCORING_GUIDE.md](docs/AES_SCORING_GUIDE.md)
