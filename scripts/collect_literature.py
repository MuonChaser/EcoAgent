#!/usr/bin/env python
"""
使用大模型搜集文献并添加到知识图谱

该脚本调用大模型来生成相关实证论文信息，并将其添加到方法论知识图谱中。

使用方法:
    # 基本用法
    python scripts/collect_literature.py --topic "数字经济对企业创新的影响"

    # 指定生成论文数量
    python scripts/collect_literature.py --topic "环境规制与绿色创新" --count 10

    # 指定领域
    python scripts/collect_literature.py --topic "金融发展" --domain "宏观经济学"

    # 直接添加单篇论文
    python scripts/collect_literature.py --add --title "论文标题" --x "自变量" --y "因变量" --method "DID"
"""

# 必须在所有其他导入之前加载环境变量
from dotenv import load_dotenv
load_dotenv()

import os
import sys
import json
import argparse
from typing import List, Dict, Any, Optional
from datetime import datetime

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from config.config import API_KEY, API_BASE, DEFAULT_MODEL, DATA_DIR
from tools.methodology_graph import MethodologyKnowledgeGraph


# 论文生成的系统提示
SYSTEM_PROMPT = """你是一位经济学研究专家，专注于实证研究方法论。

你的任务是根据给定的研究主题，生成一批相关的实证论文信息。每篇论文信息需要包含：
1. 论文标题（中文或英文）
2. 核心研究问题
3. X（自变量）：影响因素或解释变量
4. Y（因变量）：被影响的结果变量
5. 计量方法：使用的实证分析方法

请确保：
- 生成的论文主题与给定研究方向相关
- 变量设置合理，符合经济学研究规范
- 计量方法适合研究问题
- 可以包含真实存在的论文，也可以基于研究领域特点生成合理的研究设计

输出格式要求：
请以JSON数组格式输出，每个元素包含以下字段：
{
    "title": "论文标题",
    "research_question": "核心研究问题",
    "x": "自变量（可以用逗号分隔多个）",
    "y": "因变量（可以用逗号分隔多个）",
    "method": "计量方法（可以用逗号分隔多个）"
}

请只输出JSON数组，不要包含其他文本。"""

USER_PROMPT_TEMPLATE = """请为以下研究主题生成 {count} 篇相关实证论文的信息：

研究主题：{topic}
{domain_info}

要求：
1. 论文应覆盖该研究领域的不同角度和方法
2. 自变量和因变量的选择应具有学术代表性
3. 计量方法应包括常见的实证方法（如OLS、固定效应、DID、IV、PSM-DID、RDD等）
4. 优先生成在顶级经济学期刊发表过的经典研究设计

请以JSON数组格式输出。"""


class LiteratureCollector:
    """文献搜集器"""

    def __init__(
        self,
        model: str = None,
        temperature: float = 0.7,
        storage_dir: str = None
    ):
        """
        初始化文献搜集器

        Args:
            model: 使用的模型名称
            temperature: 生成温度
            storage_dir: 知识图谱存储目录
        """
        self.model = model or DEFAULT_MODEL
        self.temperature = temperature
        self.storage_dir = storage_dir or str(DATA_DIR / "methodology_graph")

        # 初始化LLM
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            openai_api_key=API_KEY,
            openai_api_base=API_BASE,
        )

        # 初始化知识图谱
        self.kg = MethodologyKnowledgeGraph(storage_dir=self.storage_dir)

        logger.info(f"文献搜集器初始化完成，模型: {self.model}")

    def collect_papers(
        self,
        topic: str,
        count: int = 5,
        domain: str = None
    ) -> List[Dict[str, Any]]:
        """
        使用大模型搜集相关论文信息

        Args:
            topic: 研究主题
            count: 生成论文数量
            domain: 研究领域（可选）

        Returns:
            论文信息列表
        """
        logger.info(f"开始搜集文献，主题: {topic}, 数量: {count}")

        # 构建提示
        domain_info = f"研究领域：{domain}" if domain else ""
        user_prompt = USER_PROMPT_TEMPLATE.format(
            topic=topic,
            count=count,
            domain_info=domain_info
        )

        # 调用LLM
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ]

        try:
            response = self.llm.invoke(messages)
            content = response.content.strip()

            # 尝试解析JSON
            # 处理可能的markdown代码块
            if content.startswith("```"):
                # 移除markdown代码块标记
                lines = content.split("\n")
                content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

            papers = json.loads(content)

            if not isinstance(papers, list):
                papers = [papers]

            logger.info(f"成功生成 {len(papers)} 篇论文信息")
            return papers

        except json.JSONDecodeError as e:
            logger.error(f"解析LLM输出失败: {e}")
            logger.error(f"原始输出: {content[:500]}...")
            return []
        except Exception as e:
            logger.error(f"调用LLM失败: {e}")
            return []

    def add_paper_to_graph(
        self,
        title: str,
        x: str,
        y: str,
        method: str,
        research_question: str = ""
    ) -> bool:
        """
        将单篇论文添加到知识图谱

        Args:
            title: 论文标题
            x: 自变量
            y: 因变量
            method: 计量方法
            research_question: 研究问题

        Returns:
            是否添加成功
        """
        try:
            # 解析变量
            x_vars = self.kg._parse_variables(x)
            y_vars = self.kg._parse_variables(y)
            methods = self.kg._parse_methods(method)

            if not x_vars or not y_vars or not methods:
                logger.warning(f"跳过无效论文: {title}")
                return False

            # 添加节点和边
            for x_var in x_vars:
                x_node = self.kg._add_or_update_node(x_var, "X", title)

                for y_var in y_vars:
                    y_node = self.kg._add_or_update_node(y_var, "Y", title)

                    for m in methods:
                        self.kg._add_edge(x_node.id, y_node.id, m, title, research_question)

            return True

        except Exception as e:
            logger.error(f"添加论文失败 [{title}]: {e}")
            return False

    def add_papers_to_graph(self, papers: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        批量添加论文到知识图谱

        Args:
            papers: 论文信息列表

        Returns:
            统计信息
        """
        stats = {"total": len(papers), "added": 0, "skipped": 0}

        for paper in papers:
            success = self.add_paper_to_graph(
                title=paper.get("title", ""),
                x=paper.get("x", ""),
                y=paper.get("y", ""),
                method=paper.get("method", ""),
                research_question=paper.get("research_question", "")
            )

            if success:
                stats["added"] += 1
            else:
                stats["skipped"] += 1

        # 重新计算嵌入
        if stats["added"] > 0 and self.kg.embedding_model:
            logger.info("正在更新节点嵌入...")
            self.kg._compute_embeddings()

        # 保存图谱
        self.kg._save_graph()

        logger.info(f"批量添加完成: 总计 {stats['total']}, 成功 {stats['added']}, 跳过 {stats['skipped']}")
        return stats

    def collect_and_add(
        self,
        topic: str,
        count: int = 5,
        domain: str = None
    ) -> Dict[str, Any]:
        """
        搜集文献并添加到知识图谱

        Args:
            topic: 研究主题
            count: 生成论文数量
            domain: 研究领域

        Returns:
            执行结果
        """
        # 搜集论文
        papers = self.collect_papers(topic, count, domain)

        if not papers:
            return {
                "success": False,
                "message": "未能生成论文信息",
                "papers": []
            }

        # 添加到图谱
        stats = self.add_papers_to_graph(papers)

        # 获取更新后的统计
        graph_stats = self.kg.get_statistics()

        return {
            "success": True,
            "message": f"成功添加 {stats['added']} 篇论文到知识图谱",
            "papers": papers,
            "add_stats": stats,
            "graph_stats": graph_stats
        }


def main():
    parser = argparse.ArgumentParser(
        description="使用大模型搜集文献并添加到知识图谱",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 搜集数字经济相关论文
    python scripts/collect_literature.py --topic "数字经济对企业创新的影响"

    # 搜集10篇环境规制相关论文
    python scripts/collect_literature.py --topic "环境规制与绿色创新" --count 10

    # 手动添加单篇论文
    python scripts/collect_literature.py --add --title "数字化转型与企业绩效" \\
        --x "数字化水平,数字技术采纳" --y "企业绩效,全要素生产率" --method "DID,固定效应"
        """
    )

    # 搜集模式参数
    parser.add_argument("--topic", type=str, help="研究主题")
    parser.add_argument("--count", type=int, default=5, help="生成论文数量（默认5）")
    parser.add_argument("--domain", type=str, help="研究领域（可选）")

    # 手动添加模式参数
    parser.add_argument("--add", action="store_true", help="手动添加单篇论文模式")
    parser.add_argument("--title", type=str, help="论文标题")
    parser.add_argument("--x", type=str, help="自变量（多个用逗号分隔）")
    parser.add_argument("--y", type=str, help="因变量（多个用逗号分隔）")
    parser.add_argument("--method", type=str, help="计量方法（多个用逗号分隔）")
    parser.add_argument("--question", type=str, default="", help="研究问题（可选）")

    # 通用参数
    parser.add_argument("--storage", type=str, default="data/methodology_graph", help="图谱存储目录")
    parser.add_argument("--model", type=str, help="使用的模型名称")
    parser.add_argument("--temperature", type=float, default=0.7, help="生成温度")
    parser.add_argument("--dry-run", action="store_true", help="只生成不添加到图谱")
    parser.add_argument("--stats", action="store_true", help="显示图谱统计信息")

    args = parser.parse_args()

    # 初始化搜集器
    storage_dir = os.path.join(project_root, args.storage)
    collector = LiteratureCollector(
        model=args.model,
        temperature=args.temperature,
        storage_dir=storage_dir
    )

    # 显示统计信息
    if args.stats:
        stats = collector.kg.get_statistics()
        print("\n=== 知识图谱统计 ===")
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
        return

    # 手动添加模式
    if args.add:
        if not all([args.title, args.x, args.y, args.method]):
            print("错误: 手动添加模式需要提供 --title, --x, --y, --method")
            sys.exit(1)

        success = collector.add_paper_to_graph(
            title=args.title,
            x=args.x,
            y=args.y,
            method=args.method,
            research_question=args.question
        )

        if success:
            collector.kg._save_graph()
            print(f"成功添加论文: {args.title}")
            stats = collector.kg.get_statistics()
            print(f"图谱当前状态: {stats['total_nodes']} 节点, {stats['total_edges']} 边")
        else:
            print("添加失败，请检查输入参数")
            sys.exit(1)
        return

    # 搜集模式
    if not args.topic:
        parser.print_help()
        print("\n错误: 搜集模式需要提供 --topic 参数")
        sys.exit(1)

    print(f"\n开始搜集文献...")
    print(f"  主题: {args.topic}")
    print(f"  数量: {args.count}")
    if args.domain:
        print(f"  领域: {args.domain}")
    print()

    if args.dry_run:
        # 只生成不添加
        papers = collector.collect_papers(args.topic, args.count, args.domain)
        if papers:
            print("=== 生成的论文信息 ===")
            for i, paper in enumerate(papers, 1):
                print(f"\n{i}. {paper.get('title', 'N/A')}")
                print(f"   研究问题: {paper.get('research_question', 'N/A')}")
                print(f"   X: {paper.get('x', 'N/A')}")
                print(f"   Y: {paper.get('y', 'N/A')}")
                print(f"   方法: {paper.get('method', 'N/A')}")
            print(f"\n共生成 {len(papers)} 篇论文信息（dry-run模式，未添加到图谱）")
    else:
        # 搜集并添加
        result = collector.collect_and_add(args.topic, args.count, args.domain)

        if result["success"]:
            print("=== 生成的论文信息 ===")
            for i, paper in enumerate(result["papers"], 1):
                print(f"\n{i}. {paper.get('title', 'N/A')}")
                print(f"   X: {paper.get('x', 'N/A')}")
                print(f"   Y: {paper.get('y', 'N/A')}")
                print(f"   方法: {paper.get('method', 'N/A')}")

            print(f"\n=== 添加结果 ===")
            print(f"总计: {result['add_stats']['total']}")
            print(f"成功添加: {result['add_stats']['added']}")
            print(f"跳过: {result['add_stats']['skipped']}")

            print(f"\n=== 图谱状态 ===")
            gs = result["graph_stats"]
            print(f"总节点数: {gs['total_nodes']}")
            print(f"总边数: {gs['total_edges']}")
        else:
            print(f"搜集失败: {result['message']}")
            sys.exit(1)


if __name__ == "__main__":
    main()
