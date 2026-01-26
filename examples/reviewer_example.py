"""
审稿人Agent调用示例

本示例展示：
1. 直接调用审稿人Agent进行评审
2. 调用增强版审稿人Agent（支持工具调用获取权威文献）
3. 完整流程：先生成文章，再进行评审
4. 结果存储和导出

使用方法：
    python examples/reviewer_example.py
"""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

# 确保可以导入项目模块
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents import (
    ReviewerAgent,
    EnhancedReviewerAgent,
    ReportWriterAgent,
    LiteratureCollectorAgent,
    VariableDesignerAgent,
    TheoryDesignerAgent,
    ModelDesignerAgent,
    DataAnalystAgent,
)
from tools.reviewer_tools import ReviewerTools


class ResearchResultStorage:
    """
    研究结果存储类
    负责保存和管理研究成果和评审意见
    """

    def __init__(self, output_dir: str = "output/reviews"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"结果存储目录: {self.output_dir}")

    def save_review_result(
        self,
        research_topic: str,
        review_result: Dict[str, Any],
        report_content: Optional[str] = None,
        format: str = "all"
    ) -> Dict[str, str]:
        """
        保存评审结果

        Args:
            research_topic: 研究主题
            review_result: 评审结果
            report_content: 原始报告内容（可选）
            format: 保存格式 ("json", "markdown", "all")

        Returns:
            保存的文件路径字典
        """
        # 生成时间戳和文件名前缀
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = "".join(c if c.isalnum() or c in "_ " else "_" for c in research_topic)[:50]
        prefix = f"{timestamp}_{safe_topic}"

        saved_files = {}

        # 保存JSON格式
        if format in ["json", "all"]:
            json_path = self.output_dir / f"{prefix}_review.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump({
                    "research_topic": research_topic,
                    "timestamp": timestamp,
                    "review_result": review_result,
                    "report_content": report_content[:2000] if report_content else None
                }, f, ensure_ascii=False, indent=2)
            saved_files["json"] = str(json_path)
            logger.info(f"JSON结果已保存: {json_path}")

        # 保存Markdown格式
        if format in ["markdown", "all"]:
            md_path = self.output_dir / f"{prefix}_review.md"
            md_content = self._format_review_to_markdown(research_topic, review_result)
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            saved_files["markdown"] = str(md_path)
            logger.info(f"Markdown结果已保存: {md_path}")

        return saved_files

    def _format_review_to_markdown(
        self,
        research_topic: str,
        review_result: Dict[str, Any]
    ) -> str:
        """将评审结果格式化为Markdown"""
        parsed = review_result.get("parsed_data", review_result.get("review_report", {}))

        md_lines = [
            f"# 学术评审报告",
            f"",
            f"**研究主题**: {research_topic}",
            f"**评审时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            "---",
            ""
        ]

        # 总体评价
        if "overall_assessment" in parsed:
            oa = parsed["overall_assessment"]
            md_lines.extend([
                "## 一、总体评价",
                "",
                f"**总体水平**: {oa.get('overall_level', 'N/A')}",
                f"**审稿建议**: {oa.get('recommendation', 'N/A')}",
                "",
                "### 优势",
            ])
            for s in oa.get("strengths", []):
                md_lines.append(f"- {s}")
            md_lines.extend(["", "### 不足"])
            for w in oa.get("weaknesses", []):
                md_lines.append(f"- {w}")
            md_lines.append("")

        # 定性分析
        if "qualitative_analysis" in parsed:
            qa = parsed["qualitative_analysis"]
            md_lines.extend([
                "## 二、定性分析：内生性评估",
                "",
                f"**内生性评级**: {qa.get('endogeneity_rating', 'N/A')}",
                "",
                "### 改进建议"
            ])
            for s in qa.get("improvement_suggestions", []):
                md_lines.append(f"- {s}")
            md_lines.append("")

        # 定量分析
        if "quantitative_analysis" in parsed:
            qna = parsed["quantitative_analysis"]
            md_lines.extend([
                "## 三、定量分析：评分",
                "",
                f"**总体得分**: {qna.get('overall_score', 'N/A')}/100",
                f"**等级评定**: {qna.get('grade', 'N/A')}",
                ""
            ])

            # 各维度得分
            if "dimension_scores" in qna:
                md_lines.append("### 各维度得分")
                md_lines.append("")
                md_lines.append("| 维度 | 权重 | 得分 |")
                md_lines.append("|------|------|------|")
                for dim in qna["dimension_scores"]:
                    md_lines.append(
                        f"| {dim.get('dimension', 'N/A')} | "
                        f"{dim.get('weight', 0)*100:.0f}% | "
                        f"{dim.get('total_score', 0):.1f} |"
                    )
                md_lines.append("")

        # 修改建议
        if "revision_suggestions" in parsed:
            rs = parsed["revision_suggestions"]
            md_lines.extend([
                "## 四、修改建议",
                "",
                "### 重大问题 (Must Fix)"
            ])
            for issue in rs.get("critical_issues", []):
                if isinstance(issue, dict):
                    md_lines.append(f"- {issue.get('issue', issue)}")
                else:
                    md_lines.append(f"- {issue}")
            md_lines.extend(["", "### 次要问题 (Should Fix)"])
            for issue in rs.get("minor_issues", []):
                if isinstance(issue, dict):
                    md_lines.append(f"- {issue.get('issue', issue)}")
                else:
                    md_lines.append(f"- {issue}")
            md_lines.append("")

        # 评审总结
        if "summary" in parsed:
            md_lines.extend([
                "## 五、评审总结",
                "",
                parsed["summary"],
                ""
            ])

        # 工具使用信息
        if review_result.get("tools_used"):
            md_lines.extend([
                "---",
                "",
                "*本评审报告由增强版审稿人Agent生成，使用了文献搜索和方法论验证工具。*",
                ""
            ])

        return "\n".join(md_lines)


# ==================== 示例1：直接调用审稿人Agent ====================

def example_basic_reviewer():
    """
    示例1：直接调用基础审稿人Agent

    适用场景：已有完整的研究报告，需要快速获取评审意见
    """
    print("\n" + "=" * 70)
    print("示例1：直接调用审稿人Agent")
    print("=" * 70)

    # 初始化审稿人Agent
    reviewer = ReviewerAgent()

    # 准备评审输入（模拟已完成的研究）
    review_input = {
        "research_topic": "数字化转型对企业创新绩效的影响研究",
        "variable_system": """
        核心变量：
        - X（解释变量）：数字化转型程度，采用企业年报中数字化相关词频测度
        - Y（被解释变量）：企业创新绩效，采用专利申请数量衡量
        控制变量：企业规模、企业年龄、资产负债率、研发投入等
        """,
        "theory_framework": """
        理论基础：
        1. 资源基础观（RBV）：数字化能力作为核心资源
        2. 动态能力理论：数字化转型提升企业适应性
        3. 创新扩散理论：数字技术促进知识流动
        主要假设：数字化转型对企业创新绩效有正向促进作用
        """,
        "model_design": """
        基准模型：双向固定效应模型
        Innovation_{it} = β₀ + β₁Digital_{it} + γControls_{it} + μ_i + λ_t + ε_{it}

        稳健性检验：
        1. 更换因变量（发明专利、实用新型专利）
        2. PSM-DID方法
        3. 工具变量法（使用地区互联网普及率作为IV）
        """,
        "data_analysis": """
        样本：2010-2022年A股上市公司，共15,680个观测值
        主要发现：
        - 数字化转型系数为0.125，在1%水平显著
        - 经济意义：数字化转型程度提高1个标准差，创新产出增加12.5%
        - 机制检验：研发效率和知识吸收能力是重要中介
        """,
        "final_report": """
        [论文摘要]
        本文基于2010-2022年A股上市公司数据，研究数字化转型对企业创新绩效的影响。
        研究发现：（1）数字化转型显著促进企业创新；（2）这一效应在高科技企业中更为明显；
        （3）研发效率和知识吸收能力是重要的中介机制。
        本文的贡献在于...
        """
    }

    # 执行评审
    print("\n正在执行评审...")
    result = reviewer.run(review_input)

    # 显示评审结果
    print("\n【评审完成】")
    print("-" * 50)

    parsed = result.get("parsed_data", {})
    if "overall_assessment" in parsed:
        oa = parsed["overall_assessment"]
        print(f"总体评价: {oa.get('overall_level', 'N/A')}")
        print(f"审稿建议: {oa.get('recommendation', 'N/A')}")

    if "quantitative_analysis" in parsed:
        qa = parsed["quantitative_analysis"]
        print(f"总体得分: {qa.get('overall_score', 'N/A')}/100")
        print(f"等级评定: {qa.get('grade', 'N/A')}")

    # 保存结果
    storage = ResearchResultStorage()
    saved = storage.save_review_result(
        research_topic=review_input["research_topic"],
        review_result=result
    )
    print(f"\n结果已保存: {saved}")

    return result


# ==================== 示例2：使用增强版审稿人Agent ====================

def example_enhanced_reviewer():
    """
    示例2：使用增强版审稿人Agent（带工具调用）

    特点：
    - 自动搜索相关权威文献
    - 获取方法论评审标准
    - 提供更专业的评审意见
    """
    print("\n" + "=" * 70)
    print("示例2：增强版审稿人Agent（带文献搜索）")
    print("=" * 70)

    # 初始化增强版审稿人Agent
    enhanced_reviewer = EnhancedReviewerAgent()

    # 准备评审输入
    review_input = {
        "research_topic": "碳交易政策对企业绿色创新的影响研究——基于中国碳排放权交易试点的证据",
        "variable_system": """
        核心变量设计：
        - 解释变量X：碳交易政策实施（DID处理变量，试点地区×试点后）
        - 被解释变量Y：企业绿色创新，使用绿色专利申请数量衡量

        控制变量：
        - 企业规模（总资产对数）
        - 资产负债率
        - 企业年龄
        - 研发投入强度
        - 盈利能力（ROA）
        - 所有权性质
        - 地区GDP增长率
        """,
        "theory_framework": """
        理论框架：
        1. 波特假说：适度的环境规制可以激发企业创新
        2. 合规成本理论：环境规制增加企业成本，可能抑制创新
        3. 信号传递理论：绿色创新向市场传递积极信号

        研究假设：
        H1：碳交易政策对企业绿色创新有正向促进作用
        H2：这一效应在高碳行业更为显著
        H3：融资约束在碳交易政策与绿色创新之间起调节作用
        """,
        "model_design": """
        识别策略：双重差分法（DID）

        基准模型：
        GreenPatent_{it} = α + β·Treat_i×Post_t + γX_{it} + μ_i + λ_t + ε_{it}

        其中：
        - Treat_i：企业是否位于碳交易试点地区
        - Post_t：碳交易政策实施后
        - β：政策效应的DID估计量

        稳健性检验：
        1. 平行趋势检验
        2. 安慰剂检验（随机处理组）
        3. PSM-DID
        4. 排除同期政策干扰
        5. 更换因变量测度
        """,
        "data_analysis": """
        数据来源：CSMAR数据库、国家知识产权局
        样本期间：2008-2020年
        样本量：12,456个公司-年度观测值

        主要结果：
        1. 基准回归：DID系数β=0.089***，表明碳交易政策显著促进绿色创新
        2. 平行趋势检验：政策前各期系数不显著，满足平行趋势假设
        3. 异质性分析：高碳行业效应更强（β=0.156***）
        4. 机制检验：研发投入和环保补贴是重要渠道
        """,
        "final_report": """
        摘要：
        本文利用中国碳排放权交易试点政策作为准自然实验，采用双重差分法考察碳交易政策对企业绿色创新的影响。
        研究发现：（1）碳交易政策显著促进了试点地区企业的绿色创新，使绿色专利申请增加约9%；
        （2）这一效应在高碳行业、国有企业和融资约束较低的企业中更为显著；
        （3）机制分析表明，研发投入增加和政府环保补贴是重要传导渠道。
        本研究为完善中国碳市场建设提供了经验证据。

        关键词：碳交易政策；绿色创新；双重差分；波特假说
        """
    }

    # 执行增强版评审
    print("\n正在执行增强版评审（包含文献搜索）...")
    result = enhanced_reviewer.run(review_input)

    # 显示评审结果
    print("\n【评审完成】")
    print("-" * 50)

    parsed = result.get("parsed_data", {})
    if "overall_assessment" in parsed:
        oa = parsed["overall_assessment"]
        print(f"总体评价: {oa.get('overall_level', 'N/A')}")
        print(f"审稿建议: {oa.get('recommendation', 'N/A')}")
        print("\n优势:")
        for s in oa.get("strengths", [])[:3]:
            print(f"  - {s}")
        print("\n不足:")
        for w in oa.get("weaknesses", [])[:3]:
            print(f"  - {w}")

    if "quantitative_analysis" in parsed:
        qa = parsed["quantitative_analysis"]
        print(f"\n总体得分: {qa.get('overall_score', 'N/A')}/100")
        print(f"等级评定: {qa.get('grade', 'N/A')}")

    # 显示工具使用情况
    if result.get("tools_used"):
        print("\n【工具使用情况】")
        for tool, used in result["tools_used"].items():
            status = "✓ 已使用" if used else "✗ 未使用"
            print(f"  - {tool}: {status}")

    # 保存结果
    storage = ResearchResultStorage()
    saved = storage.save_review_result(
        research_topic=review_input["research_topic"],
        review_result=result
    )
    print(f"\n结果已保存: {saved}")

    return result


# ==================== 示例3：完整流程 - 生成文章再评审 ====================

def example_generate_and_review():
    """
    示例3：完整流程 - 先生成文章，再进行评审

    流程：
    1. 文献搜集
    2. 变量设计
    3. 理论构建
    4. 模型设计
    5. 数据分析
    6. 报告撰写
    7. 增强版评审
    8. 存储所有结果
    """
    print("\n" + "=" * 70)
    print("示例3：完整流程 - 生成文章 → 评审 → 存储")
    print("=" * 70)

    # 研究主题和关键词
    research_topic = "人工智能技术对劳动力市场的影响研究"
    keyword_group_a = ["人工智能", "AI", "机器学习", "自动化"]
    keyword_group_b = ["劳动力市场", "就业", "工资", "劳动需求"]

    # 存储器
    storage = ResearchResultStorage(output_dir="output/full_research")

    # 用于收集所有结果
    all_results = {
        "research_topic": research_topic,
        "timestamp": datetime.now().isoformat(),
        "stages": {}
    }

    try:
        # ========== 阶段1：文献搜集 ==========
        print("\n[1/7] 文献搜集...")
        literature_agent = LiteratureCollectorAgent()
        lit_result = literature_agent.run({
            "research_topic": research_topic,
            "keyword_group_a": keyword_group_a,
            "keyword_group_b": keyword_group_b,
            "min_papers": 8
        })
        all_results["stages"]["literature"] = lit_result.get("parsed_data", {})
        literature_summary = json.dumps(lit_result.get("parsed_data", {}), ensure_ascii=False)[:2000]
        print("  ✓ 文献搜集完成")

        # ========== 阶段2：变量设计 ==========
        print("\n[2/7] 变量设计...")
        variable_agent = VariableDesignerAgent()
        var_result = variable_agent.run({
            "research_topic": research_topic,
            "literature_summary": literature_summary,
            "variable_x_info": "人工智能技术采用程度",
            "variable_y_info": "劳动力市场表现（就业、工资等）"
        })
        all_results["stages"]["variable"] = var_result.get("parsed_data", {})
        variable_system = json.dumps(var_result.get("parsed_data", {}), ensure_ascii=False)[:2000]
        print("  ✓ 变量设计完成")

        # ========== 阶段3：理论构建 ==========
        print("\n[3/7] 理论构建...")
        theory_agent = TheoryDesignerAgent()
        theory_result = theory_agent.run({
            "research_topic": research_topic,
            "variable_system": variable_system,
            "literature_summary": literature_summary
        })
        all_results["stages"]["theory"] = theory_result.get("parsed_data", {})
        theory_framework = json.dumps(theory_result.get("parsed_data", {}), ensure_ascii=False)[:2000]
        print("  ✓ 理论构建完成")

        # ========== 阶段4：模型设计 ==========
        print("\n[4/7] 模型设计...")
        model_agent = ModelDesignerAgent()
        model_result = model_agent.run({
            "research_topic": research_topic,
            "variable_system": variable_system,
            "theory_framework": theory_framework
        })
        all_results["stages"]["model"] = model_result.get("parsed_data", {})
        model_design = json.dumps(model_result.get("parsed_data", {}), ensure_ascii=False)[:2000]
        print("  ✓ 模型设计完成")

        # ========== 阶段5：数据分析 ==========
        print("\n[5/7] 数据分析...")
        data_agent = DataAnalystAgent()
        data_result = data_agent.run({
            "research_topic": research_topic,
            "variable_system": variable_system,
            "theory_framework": theory_framework,
            "model_design": model_design,
            "data_info": "使用中国企业-劳动者匹配数据，2010-2022年"
        })
        all_results["stages"]["analysis"] = data_result.get("parsed_data", {})
        data_analysis = json.dumps(data_result.get("parsed_data", {}), ensure_ascii=False)[:2000]
        print("  ✓ 数据分析完成")

        # ========== 阶段6：报告撰写 ==========
        print("\n[6/7] 报告撰写...")
        report_agent = ReportWriterAgent()
        report_result = report_agent.run({
            "research_topic": research_topic,
            "literature_review": literature_summary,
            "variable_system": variable_system,
            "theory_framework": theory_framework,
            "model_design": model_design,
            "data_analysis": data_analysis,
            "word_count": 6000
        })
        all_results["stages"]["report"] = report_result.get("parsed_data", {})
        final_report = report_result.get("raw_output", "")[:5000]
        print("  ✓ 报告撰写完成")

        # ========== 阶段7：增强版评审 ==========
        print("\n[7/7] 学术评审（增强版）...")
        enhanced_reviewer = EnhancedReviewerAgent()
        review_result = enhanced_reviewer.run({
            "research_topic": research_topic,
            "variable_system": variable_system,
            "theory_framework": theory_framework,
            "model_design": model_design,
            "data_analysis": data_analysis,
            "final_report": final_report
        })
        all_results["stages"]["review"] = review_result.get("parsed_data", {})
        print("  ✓ 学术评审完成")

        # ========== 保存所有结果 ==========
        print("\n" + "-" * 50)
        print("保存研究成果...")

        # 保存完整结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_result_path = storage.output_dir / f"{timestamp}_full_research.json"
        with open(full_result_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"  ✓ 完整结果: {full_result_path}")

        # 保存评审报告
        saved_review = storage.save_review_result(
            research_topic=research_topic,
            review_result=review_result,
            report_content=final_report
        )
        print(f"  ✓ 评审报告: {saved_review}")

        # ========== 显示最终结果 ==========
        print("\n" + "=" * 70)
        print("【研究流程完成】")
        print("=" * 70)

        parsed_review = review_result.get("parsed_data", {})
        if "overall_assessment" in parsed_review:
            oa = parsed_review["overall_assessment"]
            print(f"\n研究主题: {research_topic}")
            print(f"总体评价: {oa.get('overall_level', 'N/A')}")
            print(f"审稿建议: {oa.get('recommendation', 'N/A')}")

        if "quantitative_analysis" in parsed_review:
            qa = parsed_review["quantitative_analysis"]
            print(f"总体得分: {qa.get('overall_score', 'N/A')}/100")

        print(f"\n所有结果已保存至: {storage.output_dir}")

        return all_results

    except Exception as e:
        logger.error(f"研究流程执行出错: {e}")
        raise


# ==================== 示例4：仅使用审稿人工具 ====================

def example_reviewer_tools_only():
    """
    示例4：仅使用审稿人工具（不调用LLM）

    适用场景：
    - 快速获取方法论标准
    - 生成评审检查清单
    - 搜索相关文献
    """
    print("\n" + "=" * 70)
    print("示例4：审稿人工具独立使用")
    print("=" * 70)

    tools = ReviewerTools()

    # 1. 获取DID方法的评审标准
    print("\n[1] DID方法评审标准:")
    did_standard = tools.get_methodology_standard("DID")
    print(f"  方法名称: {did_standard.get('name')}")
    print("  核心假设:")
    for assumption in did_standard.get("key_assumptions", []):
        print(f"    - {assumption}")
    print("  必要检验:")
    for test in did_standard.get("robustness_tests", [])[:3]:
        print(f"    - {test}")

    # 2. 生成评审检查清单
    print("\n[2] DID方法评审检查清单:")
    checklist = tools.generate_review_checklist("DID")
    for category, items in checklist.items():
        if items:
            print(f"  {category}:")
            for item in items[:2]:
                print(f"    - {item}")

    # 3. 内生性问题分析
    print("\n[3] 内生性问题类型:")
    endogeneity = tools.get_endogeneity_analysis()
    for key, info in list(endogeneity.items())[:2]:
        print(f"  {info['name']}:")
        print(f"    描述: {info['description']}")
        print(f"    解决方案: {', '.join(info['solutions'][:2])}")

    # 4. 评估识别策略
    print("\n[4] 识别策略评估:")
    strategy = "本文采用双重差分法（DID），利用碳交易试点政策作为准自然实验"
    evaluation = tools.evaluate_identification_strategy(strategy)
    print(f"  检测到方法: {evaluation.get('detected_methods')}")
    print(f"  建议: {evaluation.get('suggestions')}")

    # 5. 获取顶级期刊列表
    print("\n[5] 经济学顶级期刊（中文）:")
    journals = tools.get_top_journals("economics_cn")
    for j in journals:
        print(f"  - {j}")

    return {
        "did_standard": did_standard,
        "checklist": checklist,
        "endogeneity": endogeneity,
        "evaluation": evaluation
    }


# ==================== 主函数 ====================

def main():
    """主函数 - 运行所有示例"""
    print("=" * 70)
    print("AI for Econometrics - 审稿人Agent调用示例")
    print("=" * 70)

    print("\n请选择要运行的示例：")
    print("1. 直接调用审稿人Agent（基础版）")
    print("2. 使用增强版审稿人Agent（带文献搜索）")
    print("3. 完整流程：生成文章 → 评审 → 存储")
    print("4. 仅使用审稿人工具（不调用LLM）")
    print("5. 运行所有示例")

    choice = input("\n请输入选项 (1-5): ").strip()

    try:
        if choice == "1":
            example_basic_reviewer()
        elif choice == "2":
            example_enhanced_reviewer()
        elif choice == "3":
            example_generate_and_review()
        elif choice == "4":
            example_reviewer_tools_only()
        elif choice == "5":
            print("\n运行所有示例...\n")
            example_reviewer_tools_only()  # 先运行不需要API的示例
            print("\n" + "=" * 70)
            print("工具示例完成，以下示例需要API调用")
            print("=" * 70)
            proceed = input("是否继续运行需要API的示例？(y/n): ").strip().lower()
            if proceed == "y":
                example_basic_reviewer()
                example_enhanced_reviewer()
                example_generate_and_review()
        else:
            print("无效选项，运行示例4（仅工具）...")
            example_reviewer_tools_only()

    except KeyboardInterrupt:
        print("\n\n用户中断执行")
    except Exception as e:
        logger.error(f"运行示例时出错: {e}")
        print(f"\n错误: {e}")
        print("\n提示：请确保已配置 .env 文件中的 API Key")


if __name__ == "__main__":
    main()
