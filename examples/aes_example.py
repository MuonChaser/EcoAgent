#!/usr/bin/env python3
"""
AES 自动评分系统测试示例

演示如何使用 AES 评分系统对论文进行评分
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from tools.aes_scorer import get_aes_scorer
from config.aes_config import get_aes_config

# 配置日志
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    level="INFO"
)


def test_aes_basic():
    """基础 AES 评分测试"""
    print("\n" + "=" * 70)
    print("测试1: 基础 AES 评分")
    print("=" * 70)

    # 模拟论文文本
    paper_text = """
    数字化转型对企业创新绩效的影响研究

    一、引言
    随着数字经济的快速发展，企业数字化转型已成为提升竞争力的重要途径。
    本文研究数字化转型对企业创新绩效的影响机制。

    二、文献综述
    已有研究表明，数字化转型能够显著提升企业创新能力（张三和李四，2020）。
    Smith et al. (2019)发现，数字技术应用与创新产出呈正相关关系。
    然而，现有研究较少关注中介机制的作用。

    三、研究假设
    假设H1：数字化转型正向影响企业创新绩效。
    假设H2：组织学习能力在数字化转型与创新绩效之间起中介作用。
    假设H3：环境动态性正向调节数字化转型对创新绩效的影响。

    四、研究设计
    本文采用2015-2022年中国上市公司数据，样本包含2156个观测值。
    被解释变量为企业创新绩效，使用专利申请数量衡量。
    核心解释变量为数字化转型程度，通过文本分析方法构建。
    控制变量包括企业规模、年龄、财务杠杆等。

    五、实证结果
    基准回归结果显示，数字化转型系数为0.218，在1%水平上显著。
    这表明数字化转型每提升1个标准差，创新绩效提升21.8%。
    稳健性检验中，我们替换了被解释变量，结果仍然稳健。

    六、机制分析
    中介效应检验发现，组织学习能力的中介效应占比达到62%。
    异质性分析表明，在高技术行业中，数字化转型的影响更为显著。

    七、结论
    本文发现数字化转型显著促进企业创新绩效。
    研究结论为企业数字化战略提供了实证依据。
    """

    # 获取 AES 评分器
    config = get_aes_config()
    scorer = get_aes_scorer(config)

    # 执行评分
    result = scorer.score_paper(paper_text)

    # 显示结果
    print(f"\n📊 评分结果:")
    print(f"  总分: {result['normalized_score']:.2f}/100")
    print(f"  原始分: {result['total_score']:.4f}")
    print(f"\n📈 分维度得分:")
    for metric, score in result['dimension_scores'].items():
        print(f"  {metric}: {score:.4f}")

    print(f"\n📝 统计信息:")
    print(f"  Claims 总数: {result['claims_count']}")
    print(f"  Evidences 总数: {result['evidences_count']}")
    print(f"  有证据的 Claims: {result['claims_with_evidence']}")

    print(f"\n🔍 Claim 类型分布:")
    for claim_type, count in result['detailed_analysis']['claim_type_distribution'].items():
        print(f"  {claim_type}: {count}")

    print(f"\n✅ 前3个 Claims 示例:")
    for i, claim in enumerate(result['detailed_analysis']['claims'][:3], 1):
        print(f"\n  Claim {i}:")
        print(f"    文本: {claim['text']}")
        print(f"    类型: {claim['type']}")
        print(f"    证据数: {claim['evidence_count']}")


def test_aes_with_reviewer():
    """测试 Reviewer Agent 集成 AES 评分"""
    print("\n" + "=" * 70)
    print("测试2: Reviewer Agent 集成 AES 评分")
    print("=" * 70)

    from agents import ReviewerAgent

    # 初始化审稿人（启用 AES）
    reviewer = ReviewerAgent(enable_aes=True)

    # 准备输入数据
    input_data = {
        "research_topic": "数字化转型对企业创新绩效的影响",
        "variable_system": "X: 数字化转型; Y: 创新绩效",
        "theory_framework": "基于资源基础理论和组织学习理论",
        "model_design": "双向固定效应模型",
        "data_analysis": "系数0.218***",
        "final_report": """
        数字化转型对企业创新绩效的影响研究。
        假设H1：数字化转型正向影响企业创新绩效。
        回归结果显示系数为0.218，在1%水平上显著（p<0.01）。
        已有研究表明数字化转型能提升创新能力（张三，2020）。
        """
    }

    # 执行评审（这会触发 AES 评分）
    print("\n正在执行 Reviewer Agent...")
    result = reviewer.run(input_data)

    # 显示 AES 评分结果
    if result.get("aes_enabled"):
        aes_score = result.get("aes_score", {})
        print(f"\n✅ AES 评分已集成")
        print(f"  总分: {aes_score.get('normalized_score', 0):.2f}/100")
        print(f"  Claims 数量: {aes_score.get('claims_count', 0)}")
        print(f"  Evidences 数量: {aes_score.get('evidences_count', 0)}")
    else:
        print(f"\n❌ AES 评分未启用")
        if "aes_error" in result:
            print(f"  错误: {result['aes_error']}")


def test_aes_detailed_metrics():
    """测试各项评分指标的详细计算"""
    print("\n" + "=" * 70)
    print("测试3: AES 评分指标详细分析")
    print("=" * 70)

    paper_text = """
    研究假设H1：X正向影响Y。这一假设基于理论A（作者1，2020）。
    实证结果显示，X的系数为0.25，在1%水平显著（p<0.01）。
    这一结果与理论A的预测一致，也得到了文献B的支持（作者2，2021）。

    研究假设H2：Z在X和Y之间起中介作用。根据Baron和Kenny（1986）的中介检验方法。
    Sobel检验z值为2.45（p<0.05），表明中介效应显著。

    研究假设H3：在高技术行业，X对Y的影响更强。分组回归显示，高技术组系数为0.35（p<0.01），
    而低技术组系数仅为0.12（p>0.1），组间差异显著（F=12.3, p<0.01）。
    """

    config = get_aes_config()
    scorer = get_aes_scorer(config)

    result = scorer.score_paper(paper_text)

    print(f"\n📊 详细指标分析:")
    print(f"\n1️⃣ 引用覆盖率 (Citation Coverage):")
    print(f"   得分: {result['dimension_scores']['citation_coverage']:.4f}")
    print(f"   说明: 至少有1个证据的claim占比")

    print(f"\n2️⃣ 因果相关性 (Causal Relevance):")
    print(f"   得分: {result['dimension_scores']['causal_relevance']:.4f}")
    print(f"   说明: Claim与Evidence的向量余弦相似度")

    print(f"\n3️⃣ 支持强度 (Support Strength):")
    print(f"   得分: {result['dimension_scores']['support_strength']:.4f}")
    print(f"   说明: NLI模型判定的支持概率")

    print(f"\n4️⃣ 矛盾惩罚 (Contradiction Penalty):")
    print(f"   得分: {result['dimension_scores']['contradiction_penalty']:.4f}")
    print(f"   说明: 1 - 证据间矛盾率")

    print(f"\n5️⃣ 证据充分性 (Evidence Sufficiency):")
    print(f"   得分: {result['dimension_scores']['evidence_sufficiency']:.4f}")
    print(f"   说明: min(1, 证据数/需求数)")


def main():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("🚀 AES 自动评分系统测试")
    print("=" * 70)

    try:
        # 测试1: 基础评分
        test_aes_basic()

        # 测试2: Reviewer 集成
        try:
            test_aes_with_reviewer()
        except Exception as e:
            print(f"\n⚠️ Reviewer 集成测试跳过（可能缺少 API 配置）: {e}")

        # 测试3: 详细指标
        test_aes_detailed_metrics()

        print("\n" + "=" * 70)
        print("✅ 所有测试完成!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
