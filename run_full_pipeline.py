#!/usr/bin/env python3
"""
完整研究流程运行脚本

运行完整的多智能体研究流程：
1. 输入解析（可选）
2. 文献搜集
3. 变量设计
4. 理论设计
5. 模型设计
6. 数据分析（支持本地数据库）
7. 报告撰写（LaTeX输出）
8. 审稿人评审与评分

使用方法:
    python run_full_pipeline.py                           # 使用默认主题运行
    python run_full_pipeline.py --topic "研究主题"        # 指定研究主题
    python run_full_pipeline.py --input "自然语言描述"    # 使用自然语言输入
    python run_full_pipeline.py --data-file path/to/data.csv  # 指定数据文件
    python run_full_pipeline.py --no-review               # 不进行审稿评分
"""

# ⚠️ 必须在所有其他导入之前加载环境变量！
# 否则 sentence_transformers 等库会在 HF_ENDPOINT 生效前就访问 HuggingFace
from dotenv import load_dotenv
load_dotenv()

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from loguru import logger

# 配置日志
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    level="INFO"
)
logger.add(
    "logs/pipeline_{time:YYYYMMDD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    level="DEBUG",
    rotation="1 day"
)


def run_full_pipeline(
    research_topic: str = None,
    user_input: str = None,
    keyword_group_a: list = None,
    keyword_group_b: list = None,
    data_file: str = None,
    min_papers: int = 10,
    word_count: int = 10000,
    enable_review: bool = True,
    output_dir: str = "output/research",
):
    """
    运行完整研究流程

    Args:
        research_topic: 研究主题
        user_input: 自然语言输入（如"我想研究X对Y的影响"）
        keyword_group_a: 关键词组A
        keyword_group_b: 关键词组B
        data_file: 指定的数据文件路径
        min_papers: 最少文献数量
        word_count: 论文字数
        enable_review: 是否启用审稿评分
        output_dir: 输出目录

    Returns:
        包含所有结果的字典
    """
    from orchestrator import ResearchOrchestrator

    logger.info("=" * 70)
    logger.info("开始完整研究流程")
    logger.info("=" * 70)

    # 显示配置信息
    logger.info(f"研究主题: {research_topic or '(从自然语言输入解析)'}")
    if user_input:
        logger.info(f"自然语言输入: {user_input[:50]}...")
    if data_file:
        logger.info(f"指定数据文件: {data_file}")
    logger.info(f"目标字数: {word_count}")
    logger.info(f"审稿评分: {'启用' if enable_review else '禁用'}")
    logger.info("=" * 70)

    # 初始化编排器
    orchestrator = ResearchOrchestrator(output_dir=output_dir)

    # 确定启用的步骤
    enable_steps = ["literature", "variable", "theory", "model", "analysis", "report"]
    if user_input and not research_topic:
        enable_steps.insert(0, "input_parse")

    # 运行完整流程
    results = orchestrator.run_full_pipeline(
        research_topic=research_topic,
        user_input=user_input,
        keyword_group_a=keyword_group_a,
        keyword_group_b=keyword_group_b,
        data_file=data_file,
        min_papers=min_papers,
        word_count=word_count,
        enable_steps=enable_steps,
        enable_review=enable_review,
    )

    # 显示结果摘要
    logger.info("\n" + "=" * 70)
    logger.info("研究流程完成！")
    logger.info("=" * 70)

    # 输出文件信息
    logger.info("\n生成的文件:")
    if results.get("latex_path"):
        logger.info(f"  LaTeX论文: {results['latex_path']}")
    if results.get("report_path"):
        logger.info(f"  Markdown报告: {results['report_path']}")
    if results.get("json_path"):
        logger.info(f"  JSON数据: {results['json_path']}")

    # 评分信息
    if enable_review and "review_scores" in results:
        scores = results["review_scores"]
        logger.info("\n审稿评分:")
        logger.info(f"  总评分: {scores.get('overall_score', 'N/A')}")
        logger.info(f"  评审意见: {scores.get('decision', 'N/A')}")

        dimension_scores = scores.get("dimension_scores", {})
        if dimension_scores:
            logger.info("  各维度评分:")
            for dim, score in dimension_scores.items():
                logger.info(f"    - {dim}: {score}")

    # 保存评分结果到单独文件
    if enable_review and "review_scores" in results:
        save_review_results(results, output_dir)

    logger.info("=" * 70)

    return results


def save_review_results(results: dict, output_dir: str):
    """保存评分结果到单独文件"""
    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        review_file = output_path / f"review_scores_{timestamp}.json"

        review_data = {
            "timestamp": timestamp,
            "research_topic": results.get("research_topic", ""),
            "scores": results.get("review_scores", {}),
            "review_report": results.get("review_report", ""),
            "latex_path": results.get("latex_path", ""),
        }

        with open(review_file, "w", encoding="utf-8") as f:
            json.dump(review_data, f, ensure_ascii=False, indent=2)

        logger.info(f"\n评分结果已保存: {review_file}")

    except Exception as e:
        logger.warning(f"保存评分结果失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="运行完整研究流程",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_full_pipeline.py --topic "数字化转型对企业创新的影响"
  python run_full_pipeline.py --input "我想研究碳交易政策对企业绿色创新的影响"
  python run_full_pipeline.py --topic "..." --data-file data/raw/panel_data.csv
        """
    )

    parser.add_argument(
        "--topic", "-t",
        type=str,
        help="研究主题"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        help="自然语言输入（如'我想研究X对Y的影响'）"
    )
    parser.add_argument(
        "--keywords-a", "-ka",
        type=str,
        help="关键词组A（逗号分隔）"
    )
    parser.add_argument(
        "--keywords-b", "-kb",
        type=str,
        help="关键词组B（逗号分隔）"
    )
    parser.add_argument(
        "--data-file", "-d",
        type=str,
        help="指定数据文件路径"
    )
    parser.add_argument(
        "--min-papers", "-p",
        type=int,
        default=10,
        help="最少文献数量 (默认: 10)"
    )
    parser.add_argument(
        "--word-count", "-w",
        type=int,
        default=10000,
        help="论文字数 (默认: 10000)"
    )
    parser.add_argument(
        "--no-review",
        action="store_true",
        help="不进行审稿评分"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="output/research",
        help="输出目录 (默认: output/research)"
    )

    args = parser.parse_args()

    # 解析关键词
    keyword_group_a = None
    keyword_group_b = None
    if args.keywords_a:
        keyword_group_a = [k.strip() for k in args.keywords_a.split(",") if k.strip()]
    if args.keywords_b:
        keyword_group_b = [k.strip() for k in args.keywords_b.split(",") if k.strip()]

    # 检查是否有输入
    if not args.topic and not args.input:
        # 使用默认主题
        args.topic = "环境监管对企业全要素生产率的影响"
        logger.info(f"未指定主题，使用默认主题: {args.topic}")

    # 运行流程
    try:
        results = run_full_pipeline(
            research_topic=args.topic,
            user_input=args.input,
            keyword_group_a=keyword_group_a,
            keyword_group_b=keyword_group_b,
            data_file=args.data_file,
            min_papers=args.min_papers,
            word_count=args.word_count,
            enable_review=not args.no_review,
            output_dir=args.output_dir,
        )

        # 返回成功状态
        return 0

    except KeyboardInterrupt:
        logger.info("\n用户中断")
        return 1
    except Exception as e:
        logger.error(f"运行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
