"""
检查 LaTeX 生成结果的详细信息
"""

from agents.report_writer import ReportWriterAgent
from loguru import logger
import json

def test_check_result():
    """检查生成结果的结构"""
    logger.info("="*70)
    logger.info("检查 LaTeX 生成结果结构")
    logger.info("="*70)

    agent = ReportWriterAgent()

    input_data = {
        "research_topic": "数字化转型对企业创新的影响",
        "literature_summary": "现有研究表明...",
        "variable_system": "X: 数字化投入; Y: 创新绩效",
        "theory_framework": "基于TOE框架...",
        "model_design": "双向固定效应模型",
        "data_analysis": "系数0.218***",
        "word_count": 2000
    }

    result = agent.run(input_data)

    # 检查 parsed_data
    if "parsed_data" in result:
        parsed_data = result["parsed_data"]
        logger.info(f"\nparsed_data 类型: {type(parsed_data)}")

        if hasattr(parsed_data, "latex_source"):
            latex_src = parsed_data.latex_source
            logger.info(f"✅ parsed_data 有 latex_source 属性")
            logger.info(f"latex_source 长度: {len(latex_src) if latex_src else 0}")

            if latex_src and "\\documentclass" in latex_src:
                logger.info(f"✅ latex_source 包含有效的 LaTeX 代码!")
                logger.info(f"\n前 300 字符:\n{latex_src[:300]}")

                # 保存到文件
                with open("output/test_latex.tex", "w", encoding="utf-8") as f:
                    f.write(latex_src)
                logger.info(f"\n✅ 已保存到 output/test_latex.tex")
                return True
            else:
                logger.warning("❌ latex_source 为空或不包含 \\documentclass")
        else:
            logger.warning("❌ parsed_data 没有 latex_source 属性")

            # 打印所有属性
            if hasattr(parsed_data, "__dict__"):
                logger.info(f"parsed_data 的属性: {list(parsed_data.__dict__.keys())}")
    else:
        logger.warning("❌ 结果中没有 parsed_data")

    # 检查 final_report
    if "final_report" in result:
        final_report = result["final_report"]
        logger.info(f"\nfinal_report 类型: {type(final_report)}")

        # 如果是字符串，尝试解析 JSON
        if isinstance(final_report, str):
            try:
                # 移除可能的 markdown 代码块标记
                clean_json = final_report.strip()
                if clean_json.startswith("```json"):
                    clean_json = clean_json[7:]
                if clean_json.endswith("```"):
                    clean_json = clean_json[:-3]

                data = json.loads(clean_json.strip())
                if "latex_source" in data:
                    latex_src = data["latex_source"]
                    logger.info(f"✅ 从 final_report JSON 中找到 latex_source")
                    logger.info(f"长度: {len(latex_src)}")

                    if "\\documentclass" in latex_src:
                        logger.info(f"✅ 包含有效的 LaTeX!")
                        with open("output/test_latex_from_final_report.tex", "w", encoding="utf-8") as f:
                            f.write(latex_src)
                        logger.info(f"✅ 已保存到 output/test_latex_from_final_report.tex")
                        return True
            except Exception as e:
                logger.error(f"解析 final_report JSON 失败: {e}")

    return False

if __name__ == "__main__":
    success = test_check_result()
    if success:
        logger.info("\n" + "="*70)
        logger.info("✅ LaTeX 生成成功!")
        logger.info("="*70)
    else:
        logger.error("\n" + "="*70)
        logger.error("❌ LaTeX 生成失败")
        logger.error("="*70)
