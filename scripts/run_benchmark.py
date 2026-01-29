#!/usr/bin/env python3
"""
论文生成与评分基准测试脚本

功能：
1. 评测 paper 目录中所有现有文件
2. 使用/不使用知识图谱生成新论文并评分
3. 汇总对比结果

使用方法:
    # 运行完整基准测试
    python scripts/run_benchmark.py

    # 只评测现有论文
    python scripts/run_benchmark.py --score-only

    # 只生成新论文（跳过评分）
    python scripts/run_benchmark.py --generate-only

    # 指定模型
    python scripts/run_benchmark.py --model qwen-max
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

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

    # 保存评分结果
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


def score_all_papers(paper_dir: Path, output_dir: Path) -> List[Dict[str, Any]]:
    """
    评测目录中所有论文

    Args:
        paper_dir: 论文目录
        output_dir: 输出目录

    Returns:
        评分结果列表
    """
    results = []

    # 获取所有 txt 文件
    txt_files = list(paper_dir.glob("*.txt"))

    if not txt_files:
        logger.warning(f"paper 目录中没有找到 txt 文件: {paper_dir}")
        return results

    logger.info(f"找到 {len(txt_files)} 个论文文件")
    print("\n" + "=" * 60)
    print("评测现有论文")
    print("=" * 60)

    for file_path in txt_files:
        result = score_paper(file_path, output_dir)
        if result:
            results.append(result)

    return results


def generate_paper_with_kg(
    model: str,
    output_dir: Path,
    use_knowledge_graph: bool = True
) -> Optional[Path]:
    """
    生成论文（使用或不使用知识图谱）

    Args:
        model: 模型名称
        output_dir: 输出目录
        use_knowledge_graph: 是否使用知识图谱

    Returns:
        生成的论文文件路径
    """
    from openai import OpenAI

    api_key = os.getenv("DASHSCOPE_API_KEY")
    base_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

    if not api_key:
        logger.error("未设置 DASHSCOPE_API_KEY")
        return None

    # 知识图谱上下文
    kg_context = ""
    if use_knowledge_graph:
        try:
            from tools.methodology_graph import MethodologyKnowledgeGraph
            kg = MethodologyKnowledgeGraph()

            # 查询相关方法论
            query_results = kg.query_by_variables(
                x_keywords=["environmental regulation", "环境规制", "环境监管"],
                y_keywords=["TFP", "productivity", "生产率", "全要素生产率"],
                top_k=10
            )

            if query_results.get("edges"):
                kg_context = "\n\n# METHODOLOGY KNOWLEDGE GRAPH CONTEXT\n\n"
                kg_context += "The following are established research designs from the literature:\n\n"

                for i, edge in enumerate(query_results["edges"][:10], 1):
                    kg_context += f"{i}. **{edge['x_name']}** → **{edge['y_name']}**\n"
                    kg_context += f"   - Method: {edge['method']}\n"
                    if edge.get('papers'):
                        kg_context += f"   - Papers: {', '.join(edge['papers'][:3])}\n"
                    kg_context += "\n"

                kg_context += "\nPlease incorporate these established methodological approaches in your paper design.\n"
                logger.info(f"知识图谱提供了 {len(query_results['edges'])} 条方法论参考")
            else:
                logger.warning("知识图谱没有返回相关结果")
                use_knowledge_graph = False
        except Exception as e:
            logger.warning(f"知识图谱查询失败: {e}")
            use_knowledge_graph = False

    # 系统提示
    system_prompt = """You are a senior economist with extensive publication experience in top economics journals (AER, QJE, JPE, Econometrica). Generate a complete, publication-ready academic paper.

## Core Requirements
- Rigorous causal identification (DID, IV, RDD, PSM, Fixed Effects)
- Clear theoretical framework with testable hypotheses
- Detailed empirical methodology
- Academic writing following top journal conventions"""

    # 用户提示
    user_prompt = f"""# RESEARCH TOPIC

**"The Impact of Environmental Regulation on Firm Total Factor Productivity (TFP)"**

{kg_context}

# REQUIREMENTS

Generate a complete academic paper (8,000-10,000 words) with:

1. **Introduction** (1,500 words)
   - Research background and motivation
   - Research gap and contribution
   - Methodology preview

2. **Theoretical Framework** (2,000 words)
   - Porter Hypothesis, Compliance Cost Theory, Induced Innovation Theory
   - Clear hypothesis derivation

3. **Research Design** (1,500 words)
   - Econometric models with LaTeX equations
   - Variable definitions and data sources
   - Identification strategy

4. **Empirical Results** (2,500 words)
   - Baseline results with regression tables
   - Robustness checks (5+ tests)
   - Endogeneity treatment (IV estimation)

5. **Mechanism & Heterogeneity** (1,500 words)
   - Mediation analysis
   - Subgroup analysis

6. **Conclusion** (800 words)
   - Key findings and policy implications

Include all necessary tables, equations, and at least 30 academic citations."""

    # 生成
    suffix = "with_kg" if use_knowledge_graph else "without_kg"
    logger.info(f"生成论文 ({suffix})...")

    client = OpenAI(api_key=api_key, base_url=base_url)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=16000,
            stream=True
        )

        content = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                content += chunk.choices[0].delta.content

        # 保存论文
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"generated_{model}_{suffix}_{timestamp}.txt"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"论文已生成: {output_file.name} ({len(content)} 字符)")
        return output_file

    except Exception as e:
        logger.error(f"论文生成失败: {e}")
        return None


def print_summary(results: List[Dict[str, Any]]):
    """打印评分汇总"""
    if not results:
        return

    print("\n" + "=" * 80)
    print("评分汇总")
    print("=" * 80)

    # 按总分排序
    sorted_results = sorted(results, key=lambda x: x["total_score"], reverse=True)

    # 表头
    print(f"\n{'文件名':<40} {'总分':>10} {'引用覆盖':>10} {'因果相关':>10} {'支持强度':>10} {'证据充分':>10}")
    print("-" * 100)

    for r in sorted_results:
        dims = r["dimension_scores"]
        print(f"{r['file_name']:<40} {r['total_score']:>10.2f} "
              f"{dims.get('citation_coverage', 0)*100:>10.2f} "
              f"{dims.get('causal_relevance', 0)*100:>10.2f} "
              f"{dims.get('support_strength', 0)*100:>10.2f} "
              f"{dims.get('evidence_sufficiency', 0)*100:>10.2f}")

    print("-" * 100)

    # 统计信息
    scores = [r["total_score"] for r in results]
    print(f"\n平均分: {sum(scores)/len(scores):.2f}")
    print(f"最高分: {max(scores):.2f} ({sorted_results[0]['file_name']})")
    print(f"最低分: {min(scores):.2f} ({sorted_results[-1]['file_name']})")


def main():
    parser = argparse.ArgumentParser(
        description="论文生成与评分基准测试",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--score-only", action="store_true", help="只评测现有论文")
    parser.add_argument("--generate-only", action="store_true", help="只生成新论文")
    parser.add_argument("--model", "-m", type=str, default="qwen-max", help="生成模型")
    parser.add_argument("--paper-dir", type=str, default="paper", help="论文目录")
    parser.add_argument("--output-dir", type=str, default="output/benchmark", help="输出目录")

    args = parser.parse_args()

    # 设置目录
    paper_dir = project_root / args.paper_dir
    output_dir = project_root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    all_results = []

    print("\n" + "=" * 80)
    print("论文生成与评分基准测试")
    print("=" * 80)
    print(f"论文目录: {paper_dir}")
    print(f"输出目录: {output_dir}")
    print(f"模型: {args.model}")
    print(f"日志文件: {LOG_FILE}")

    # 1. 评测现有论文
    if not args.generate_only:
        existing_results = score_all_papers(paper_dir, output_dir)
        all_results.extend(existing_results)

    # 2. 生成新论文（使用/不使用知识图谱）
    if not args.score_only:
        print("\n" + "=" * 60)
        print("生成新论文")
        print("=" * 60)

        # 不使用知识图谱
        print("\n--- 不使用知识图谱 ---")
        paper_without_kg = generate_paper_with_kg(args.model, paper_dir, use_knowledge_graph=False)
        if paper_without_kg:
            result = score_paper(paper_without_kg, output_dir)
            if result:
                result["generation_mode"] = "without_knowledge_graph"
                all_results.append(result)

        # 使用知识图谱
        print("\n--- 使用知识图谱 ---")
        paper_with_kg = generate_paper_with_kg(args.model, paper_dir, use_knowledge_graph=True)
        if paper_with_kg:
            result = score_paper(paper_with_kg, output_dir)
            if result:
                result["generation_mode"] = "with_knowledge_graph"
                all_results.append(result)

    # 3. 打印汇总
    print_summary(all_results)

    # 4. 保存完整结果
    summary_file = output_dir / f"benchmark_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "model": args.model,
            "results": all_results,
            "statistics": {
                "total_papers": len(all_results),
                "avg_score": sum(r["total_score"] for r in all_results) / len(all_results) if all_results else 0,
            }
        }, f, ensure_ascii=False, indent=2)

    print(f"\n汇总结果已保存: {summary_file}")
    print(f"日志文件: {LOG_FILE}")


if __name__ == "__main__":
    main()
