#!/usr/bin/env python
"""
构建方法论知识图谱

从实证论文CSV文件构建变量-方法关联知识图谱。

使用方法:
    python scripts/build_methodology_graph.py
    python scripts/build_methodology_graph.py --csv data/raw/实证论文提取结果.csv
    python scripts/build_methodology_graph.py --search "数字经济"
"""

# ⚠️ 必须在所有其他导入之前加载环境变量！
from dotenv import load_dotenv
load_dotenv()

import os
import sys
import argparse

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from tools.methodology_graph import MethodologyKnowledgeGraph, _format_subgraph_result


def main():
    parser = argparse.ArgumentParser(description="构建方法论知识图谱")
    parser.add_argument(
        "--csv",
        type=str,
        default="data/raw/实证论文提取结果.csv",
        help="CSV文件路径"
    )
    parser.add_argument(
        "--storage",
        type=str,
        default="data/methodology_graph",
        help="图谱存储目录"
    )
    parser.add_argument(
        "--search",
        type=str,
        help="搜索变量（构建后测试）"
    )
    parser.add_argument(
        "--recommend",
        type=str,
        help="推荐方法，格式: 'X变量,Y变量'"
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="强制重新构建（忽略已有图谱）"
    )

    args = parser.parse_args()

    # 初始化知识图谱
    print(f"初始化知识图谱，存储目录: {args.storage}")
    kg = MethodologyKnowledgeGraph(storage_dir=args.storage)

    # 检查是否需要构建
    if args.rebuild or kg.get_statistics()["total_nodes"] == 0:
        csv_path = os.path.join(project_root, args.csv)
        if not os.path.exists(csv_path):
            print(f"错误: CSV文件不存在: {csv_path}")
            sys.exit(1)

        print(f"\n正在从CSV构建图谱: {csv_path}")
        stats = kg.build_from_csv(csv_path)

        print("\n=== 构建完成 ===")
        print(f"处理论文数: {stats['papers']}")
        print(f"创建节点数: {stats['nodes']}")
        print(f"创建边数: {stats['edges']}")
        print(f"跳过记录数: {stats['skipped']}")
    else:
        print("已加载现有图谱")

    # 显示统计信息
    print("\n=== 图谱统计 ===")
    stats = kg.get_statistics()
    print(f"总节点数: {stats['total_nodes']}")
    print(f"总边数: {stats['total_edges']}")
    print(f"唯一方法数: {stats['unique_methods']}")
    print(f"\n节点角色分布:")
    print(f"  - 仅作为X: {stats['node_roles']['x_only']}")
    print(f"  - 仅作为Y: {stats['node_roles']['y_only']}")
    print(f"  - 同时作为X和Y: {stats['node_roles']['both_x_and_y']}")
    print(f"\n热门计量方法 (Top 10):")
    for method, count in stats['top_methods']:
        print(f"  - {method}: {count}次")

    # 搜索测试
    if args.search:
        print(f"\n=== 搜索测试: {args.search} ===")
        result = kg.retrieve_subgraph(query_x=args.search, query_y=args.search)
        print(_format_subgraph_result(result))

    # 方法推荐测试
    if args.recommend:
        parts = args.recommend.split(",")
        if len(parts) >= 2:
            x_query = parts[0].strip()
            y_query = parts[1].strip()
            print(f"\n=== 方法推荐: X={x_query}, Y={y_query} ===")
            recommendations = kg.recommend_methods(x_query, y_query)
            for rec in recommendations:
                print(f"\n方法: {rec['method']}")
                print(f"使用频次: {rec['frequency']}")
                print("相关论文:")
                for paper in rec['example_papers']:
                    print(f"  - {paper}")


if __name__ == "__main__":
    main()
