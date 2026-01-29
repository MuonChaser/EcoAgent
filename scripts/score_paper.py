#!/usr/bin/env python3
"""
论文评分脚本

只运行 AES 评分部分，输入一个 txt 文件路径，输出评分结果。

使用方法:
    python scripts/score_paper.py <txt文件路径>

    # 示例
    python scripts/score_paper.py paper.txt
    python scripts/score_paper.py /path/to/paper.txt

    # 输出为 JSON 格式
    python scripts/score_paper.py paper.txt --json

    # 保存结果到文件
    python scripts/score_paper.py paper.txt --output result.json
"""

import sys
import json
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from tools.aes_scorer import get_aes_scorer
from config.aes_config import get_aes_config


def setup_logger(verbose: bool = False):
    """配置日志"""
    logger.remove()
    level = "DEBUG" if verbose else "INFO"
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level=level
    )


def score_paper(file_path: str) -> dict:
    """
    对论文进行评分

    Args:
        file_path: txt 文件路径

    Returns:
        评分结果字典
    """
    # 读取文件
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    with open(path, "r", encoding="utf-8") as f:
        paper_text = f.read()

    if not paper_text.strip():
        raise ValueError("文件内容为空")

    logger.info(f"已读取文件: {file_path} ({len(paper_text)} 字符)")

    # 获取 AES 评分器
    config = get_aes_config()
    scorer = get_aes_scorer(config)

    # 执行评分
    result = scorer.score_paper(paper_text)

    return result


def print_result(result: dict, json_output: bool = False):
    """打印评分结果"""
    if json_output:
        # JSON 格式输出
        output = {
            "total_score": result["normalized_score"],
            "raw_score": result["total_score"],
            "dimension_scores": result["dimension_scores"],
            "weights": result["weights"],
            "statistics": {
                "claims_count": result["claims_count"],
                "evidences_count": result["evidences_count"],
                "claims_with_evidence": result["claims_with_evidence"],
            },
            "claim_type_distribution": result["detailed_analysis"]["claim_type_distribution"],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        # 友好格式输出
        print("\n" + "=" * 60)
        print("评分结果")
        print("=" * 60)

        print(f"\n总分: {result['normalized_score']:.2f}/100")
        print(f"原始分: {result['total_score']:.4f}")

        print("\n分维度得分:")
        print("-" * 40)
        for metric, score in result["dimension_scores"].items():
            weight = result["weights"].get(metric, 0.0)
            weighted = score * weight
            print(f"  {metric:25s}: {score:.4f} (权重: {weight:.0%}, 加权: {weighted:.4f})")

        print("\n统计信息:")
        print("-" * 40)
        print(f"  Claims 总数: {result['claims_count']}")
        print(f"  Evidences 总数: {result['evidences_count']}")
        print(f"  有证据的 Claims: {result['claims_with_evidence']}")

        print("\nClaim 类型分布:")
        print("-" * 40)
        for claim_type, count in result["detailed_analysis"]["claim_type_distribution"].items():
            print(f"  {claim_type}: {count}")

        print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="论文评分脚本 - 使用 AES 系统对论文进行自动评分",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python scripts/score_paper.py paper.txt
    python scripts/score_paper.py paper.txt --json
    python scripts/score_paper.py paper.txt --output result.json
        """
    )

    parser.add_argument("file", type=str, help="论文 txt 文件路径")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出结果")
    parser.add_argument("--output", "-o", type=str, help="保存结果到指定文件")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细日志")

    args = parser.parse_args()

    # 配置日志
    setup_logger(args.verbose)

    try:
        # 评分
        result = score_paper(args.file)

        # 输出结果
        if args.output:
            # 保存到文件
            output = {
                "file": args.file,
                "total_score": result["normalized_score"],
                "raw_score": result["total_score"],
                "dimension_scores": result["dimension_scores"],
                "weights": result["weights"],
                "statistics": {
                    "claims_count": result["claims_count"],
                    "evidences_count": result["evidences_count"],
                    "claims_with_evidence": result["claims_with_evidence"],
                },
                "claim_type_distribution": result["detailed_analysis"]["claim_type_distribution"],
            }
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            print(f"结果已保存到: {args.output}")
        else:
            # 打印结果
            print_result(result, json_output=args.json)

    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"评分失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
