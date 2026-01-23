"""
简单测试 LaTeX 输出功能
"""

from agents.report_writer import ReportWriterAgent
from loguru import logger

def test_latex_generation():
    """测试 LaTeX 生成"""
    logger.info("="*70)
    logger.info("简单测试 LaTeX 论文生成")
    logger.info("="*70)

    # 创建 agent
    agent = ReportWriterAgent()

    # 准备输入数据
    input_data = {
        "research_topic": "数字化转型对企业创新的影响",
        "literature_summary": "现有研究表明数字化转型显著提升企业创新能力...",
        "variable_system": "X: 数字化投入强度; Y: 创新绩效",
        "theory_framework": "基于TOE框架和内生增长理论...",
        "model_design": "双向固定效应模型",
        "data_analysis": "基准回归系数为0.218***",
        "word_count": 3000
    }

    # 运行 agent
    result = agent.run(input_data)

    # 检查结果
    logger.info(f"\n生成结果类型: {type(result)}")
    if isinstance(result, dict):
        logger.info(f"结果包含的字段: {list(result.keys())}")

        # 检查 latex_source
        if "latex_source" in result:
            latex_content = result["latex_source"]
            logger.info(f"✅ 发现 latex_source 字段")
            logger.info(f"LaTeX 内容长度: {len(latex_content) if latex_content else 0} 字符")

            if latex_content and "\\documentclass" in latex_content:
                logger.info(f"✅ LaTeX 内容包含 \\documentclass")
                logger.info(f"\nLaTeX 前 200 字符:")
                logger.info(latex_content[:200])

                # 保存到文件
                with open("output/test_latex_simple.tex", "w", encoding="utf-8") as f:
                    f.write(latex_content)
                logger.info(f"\n✅ LaTeX 已保存到 output/test_latex_simple.tex")
            else:
                logger.warning(f"❌ latex_source 不包含有效的 LaTeX 内容")
        else:
            logger.warning(f"❌ 结果中没有 latex_source 字段")

        # 显示 final_report 字段（如果存在）
        if "final_report" in result:
            final_report = result["final_report"]
            logger.info(f"\nfinal_report 长度: {len(str(final_report))} 字符")
            logger.info(f"final_report 前 200 字符: {str(final_report)[:200]}")
    else:
        logger.warning(f"结果不是字典类型: {result}")

    return result

if __name__ == "__main__":
    test_latex_generation()
