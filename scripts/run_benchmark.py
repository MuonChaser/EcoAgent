#!/usr/bin/env python3
"""
论文批量评分脚本

功能：
1. 评测 paper 目录中所有论文文件
2. 以文件名命名评分结果
3. 汇总对比各论文得分

使用方法:
    # 评测 paper 目录中所有论文
    python scripts/run_benchmark.py

    # 指定论文目录
    python scripts/run_benchmark.py --paper-dir /path/to/papers

    # 指定输出目录
    python scripts/run_benchmark.py --output-dir output/scores

生成论文请使用:
    python run_full_pipeline.py --topic "研究主题"
    python run_full_pipeline.py --topic "研究主题" --no-kg  # 不使用知识图谱
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from config.logging_config import setup_logger

# 配置日志
LOG_FILE = setup_logger("run_benchmark")


def score_paper(file_path: Path, output_dir: Path) -> Optional[Dict[str, Any]]:
    """
    评分单个论文文件

    Args:
        file_path: 论文文件路径
        output_dir: 评分结果输出目录

    Returns:
        评分结果字典
    """
    from tools.aes_scorer import AESScorer
    from config.aes_config import get_aes_config

    # 检查文件是否为空
    if file_path.stat().st_size == 0:
        logger.warning(f"跳过空文件: {file_path.name}")
        return None

    logger.info(f"评分: {file_path.name}")

    # 读取文件
    with open(file_path, "r", encoding="utf-8") as f:
        paper_text = f.read()

    if not paper_text.strip():
        logger.warning(f"文件内容为空: {file_path.name}")
        return None

    # 创建新的评分器实例（避免单例缓存）
    config = get_aes_config()
    scorer = AESScorer(config)

    # 评分
    result = scorer.score_paper(paper_text)

    # 保存评分结果（以原文件名命名）
    score_file = output_dir / f"{file_path.stem}_score.json"
    output = {
        "file": str(file_path),
        "file_name": file_path.name,
        "scored_at": datetime.now().isoformat(),
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

    with open(score_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    logger.info(f"评分完成: {result['normalized_score']:.2f}/100 -> {score_file.name}")

    return output


def print_summary(results: List[Dict[str, Any]]):
    """打印评分汇总"""
    if not results:
        print("\n没有可评分的论文")
        return

    print("\n" + "=" * 100)
    print("评分汇总")
    print("=" * 100)

    # 按总分排序
    sorted_results = sorted(results, key=lambda x: x["total_score"], reverse=True)

    # 表头
    print(f"\n{'排名':<4} {'文件名':<40} {'总分':>8} {'引用覆盖':>8} {'因果相关':>8} {'支持强度':>8} {'证据充分':>8}")
    print("-" * 100)

    for i, r in enumerate(sorted_results, 1):
        dims = r["dimension_scores"]
        print(f"{i:<4} {r['file_name']:<40} {r['total_score']:>8.2f} "
              f"{dims.get('citation_coverage', 0)*100:>8.2f} "
              f"{dims.get('causal_relevance', 0)*100:>8.2f} "
              f"{dims.get('support_strength', 0)*100:>8.2f} "
              f"{dims.get('evidence_sufficiency', 0)*100:>8.2f}")

    print("-" * 100)

    # 统计信息
    scores = [r["total_score"] for r in results]
    print(f"\n统计信息:")
    print(f"  论文数量: {len(results)}")
    print(f"  平均分: {sum(scores)/len(scores):.2f}")
    print(f"  最高分: {max(scores):.2f} ({sorted_results[0]['file_name']})")
    print(f"  最低分: {min(scores):.2f} ({sorted_results[-1]['file_name']})")


def main():
    parser = argparse.ArgumentParser(
        description="论文批量评分",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python scripts/run_benchmark.py
    python scripts/run_benchmark.py --paper-dir paper
    python scripts/run_benchmark.py --output-dir output/scores

生成论文请使用:
    python run_full_pipeline.py --topic "研究主题"
        """
    )

    parser.add_argument("--paper-dir", type=str, default="paper", help="论文目录 (默认: paper)")
    parser.add_argument("--output-dir", type=str, default="output/benchmark", help="输出目录 (默认: output/benchmark)")

    args = parser.parse_args()

    # 设置目录
    paper_dir = project_root / args.paper_dir
    output_dir = project_root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("论文批量评分")
    print("=" * 60)
    print(f"论文目录: {paper_dir}")
    print(f"输出目录: {output_dir}")
    print(f"日志文件: {LOG_FILE}")

    # 获取所有 txt 文件
    txt_files = list(paper_dir.glob("*.txt"))

    if not txt_files:
        logger.warning(f"paper 目录中没有找到 txt 文件: {paper_dir}")
        return

    logger.info(f"找到 {len(txt_files)} 个论文文件")

    # 评测所有论文
    results = []
    for file_path in txt_files:
        result = score_paper(file_path, output_dir)
        if result:
            results.append(result)

    # 打印汇总
    print_summary(results)

    # 保存汇总结果
    if results:
        summary_file = output_dir / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "paper_dir": str(paper_dir),
                "total_papers": len(results),
                "avg_score": sum(r["total_score"] for r in results) / len(results),
                "results": results,
            }, f, ensure_ascii=False, indent=2)
        print(f"\n汇总文件: {summary_file}")


if __name__ == "__main__":
    main()
