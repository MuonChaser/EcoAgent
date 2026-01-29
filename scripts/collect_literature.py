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
import requests
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from config.config import API_KEY, API_BASE, DEFAULT_MODEL, DATA_DIR
from config.logging_config import setup_logger
from tools.methodology_graph import MethodologyKnowledgeGraph

# 配置日志
LOG_FILE = setup_logger("collect_literature")


# 搜索关键词扩展的系统提示
QUERY_EXPANSION_PROMPT = """你是一位学术文献搜索专家，擅长将研究主题转换为有效的学术搜索关键词。

你的任务是根据用户提供的研究主题，生成多个搜索查询词，以便在学术数据库（如Arxiv、Crossref）中搜索相关论文。

请生成以下内容：
1. 英文翻译：将研究主题准确翻译成学术英文
2. 核心关键词：提取3-5个核心英文关键词
3. 搜索变体：生成3-5个不同角度的英文搜索短语
4. 相关领域词：2-3个相关学科/方法的英文术语

输出格式要求（JSON）：
{
    "english_translation": "研究主题的英文翻译",
    "core_keywords": ["keyword1", "keyword2", "keyword3"],
    "search_variants": [
        "search phrase 1",
        "search phrase 2",
        "search phrase 3"
    ],
    "related_terms": ["term1", "term2"]
}

请只输出JSON，不要包含其他文本。"""

# 论文提取的系统提示
SYSTEM_PROMPT = """你是一位经济学研究专家，专注于实证研究方法论。

你的任务是根据提供的真实论文信息（标题和摘要），提取其核心研究设计。每篇论文信息需要包含：
1. 论文标题
2. 核心研究问题
3. X（自变量）：影响因素或解释变量
4. Y（因变量）：被影响的结果变量
5. 计量方法：使用的实证分析方法

请确保：
- 基于提供的论文标题和摘要进行提取
- 如果摘要中未明确提及某些信息，请基于标题和经济学常识进行合理推断，并在研究问题中注明"（推断）"
- 变量提取要简洁规范
- 计量方法应识别出具体的实证方法（如OLS、DID、IV、Fixed Effects等）

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

USER_PROMPT_TEMPLATE = """请为以下搜集到的真实论文提取研究设计信息：

{papers_info}

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

    def _expand_query(self, topic: str, domain: str = None) -> Dict[str, Any]:
        """
        使用大模型扩展搜索关键词

        Args:
            topic: 原始研究主题
            domain: 研究领域（可选）

        Returns:
            扩展后的查询信息
        """
        logger.info(f"正在扩展搜索关键词: {topic}")

        domain_hint = f"\n研究领域: {domain}" if domain else ""
        user_prompt = f"研究主题: {topic}{domain_hint}"

        messages = [
            SystemMessage(content=QUERY_EXPANSION_PROMPT),
            HumanMessage(content=user_prompt)
        ]

        try:
            response = self.llm.invoke(messages)
            content = response.content.strip()

            # 处理markdown代码块
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

            result = json.loads(content)
            logger.info(f"关键词扩展成功: {result.get('english_translation', 'N/A')}")
            logger.info(f"  核心关键词: {result.get('core_keywords', [])}")
            logger.info(f"  搜索变体: {result.get('search_variants', [])}")

            return result

        except json.JSONDecodeError as e:
            logger.warning(f"解析关键词扩展结果失败: {e}")
            # 降级：直接使用原始主题
            return {
                "english_translation": topic,
                "core_keywords": [topic],
                "search_variants": [topic],
                "related_terms": []
            }
        except Exception as e:
            logger.warning(f"关键词扩展失败: {e}")
            return {
                "english_translation": topic,
                "core_keywords": [topic],
                "search_variants": [topic],
                "related_terms": []
            }

    def _search_arxiv(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """搜索Arxiv"""
        try:
            import arxiv
            logger.info(f"正在从Arxiv搜索: {query}")
            client = arxiv.Client()
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            results = []
            for r in client.results(search):
                results.append({
                    "title": r.title,
                    "abstract": r.summary.replace("\n", " "),
                    "source": "arxiv"
                })
            logger.info(f"Arxiv返回 {len(results)} 条结果")
            return results
        except ImportError:
            logger.warning("未安装arxiv库，跳过Arxiv搜索")
            return []
        except Exception as e:
            logger.error(f"Arxiv搜索失败: {e}")
            return []

    def _search_crossref(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """搜索Crossref"""
        try:
            logger.info(f"正在从Crossref搜索: {query}")
            url = "https://api.crossref.org/works"
            params = {
                "query": query,
                "rows": max_results,
                "select": "title,abstract,DOI,author,published-print"
            }
            response = requests.get(url, params=params, timeout=30)
            
            results = []
            if response.status_code == 200:
                data = response.json()
                items = data.get('message', {}).get('items', [])
                for item in items:
                    title_list = item.get('title', [])
                    if not title_list:
                        continue
                    title = title_list[0]
                    abstract = item.get('abstract', '')
                    # 清理abstract中的XML标签（如果有）
                    if abstract and '<' in abstract:
                        # 简单去除标签，实际可以用BS4
                        abstract = abstract.replace('<jats:p>', '').replace('</jats:p>', '').replace('<jats:title>', '').replace('</jats:title>', '')
                    
                    results.append({
                        "title": title,
                        "abstract": abstract if abstract else "Abstract not available.",
                        "source": "crossref"
                    })
            logger.info(f"Crossref返回 {len(results)} 条结果")
            return results
        except Exception as e:
            logger.error(f"Crossref搜索失败: {e}")
            return []

    def collect_papers(
        self,
        topic: str,
        count: int = 5,
        domain: str = None,
        expand_query: bool = True
    ) -> List[Dict[str, Any]]:
        """
        搜集真实论文并提取信息

        Args:
            topic: 研究主题
            count: 生成论文数量
            domain: 研究领域（可选）
            expand_query: 是否使用大模型扩展搜索关键词（默认True）

        Returns:
            论文信息列表
        """
        logger.info(f"开始搜集文献，主题: {topic}, 目标数量: {count}")

        # 1. 扩展搜索关键词
        search_queries = [topic]  # 默认使用原始主题

        if expand_query:
            expanded = self._expand_query(topic, domain)

            # 构建多个搜索查询
            search_queries = []

            # 添加英文翻译作为主查询
            if expanded.get("english_translation"):
                search_queries.append(expanded["english_translation"])

            # 添加搜索变体
            search_queries.extend(expanded.get("search_variants", []))

            # 添加核心关键词组合
            keywords = expanded.get("core_keywords", [])
            if len(keywords) >= 2:
                search_queries.append(" ".join(keywords[:3]))

            # 去重
            search_queries = list(dict.fromkeys(search_queries))
            logger.info(f"将使用 {len(search_queries)} 个搜索查询")

        # 2. 联网搜索
        # 为了保证有足够的结果，多搜索一些
        search_count_per_query = max(count, 5)
        raw_papers = []
        seen_titles = set()

        for query in search_queries:
            if len(raw_papers) >= count * 3:
                break  # 已经有足够的候选论文

            # 搜索Arxiv
            arxiv_results = self._search_arxiv(query, max_results=search_count_per_query)
            for p in arxiv_results:
                if p['title'] not in seen_titles:
                    seen_titles.add(p['title'])
                    raw_papers.append(p)

            # 搜索Crossref
            crossref_results = self._search_crossref(query, max_results=search_count_per_query)
            for p in crossref_results:
                if p['title'] not in seen_titles:
                    seen_titles.add(p['title'])
                    raw_papers.append(p)

            # 避免请求过快
            time.sleep(0.5)

        logger.info(f"共搜索到 {len(raw_papers)} 篇不重复论文")

        # 截取所需数量
        target_papers = raw_papers[:count]
        
        if not target_papers:
            logger.warning("未能搜索到任何相关论文")
            return []

        logger.info(f"共获取 {len(target_papers)} 篇真实论文，开始提取信息...")

        # 2. 构建提示文本
        papers_info_text = ""
        for i, p in enumerate(target_papers, 1):
            papers_info_text += f"\n[{i}] 标题: {p['title']}\n    摘要: {p['abstract'][:500]}...\n"

        user_prompt = USER_PROMPT_TEMPLATE.format(papers_info=papers_info_text)

        # 3. 调用LLM提取信息
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ]

        try:
            response = self.llm.invoke(messages)
            content = response.content.strip()

            # 尝试解析JSON
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

            extracted_papers = json.loads(content)

            if not isinstance(extracted_papers, list):
                extracted_papers = [extracted_papers]

            # 确保提取的标题与搜索的标题对应（LLM可能会修改标题）
            # 这里简单信任LLM的提取，或者可以做后处理匹配
            
            logger.info(f"成功提取 {len(extracted_papers)} 篇论文信息")
            return extracted_papers

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
        domain: str = None,
        batch_size: int = 10,
        expand_query: bool = True
    ) -> Dict[str, Any]:
        """
        搜集文献并添加到知识图谱 (分批处理)

        Args:
            topic: 研究主题
            count: 生成论文数量
            domain: 研究领域
            batch_size: 每批生成的数量
            expand_query: 是否使用大模型扩展搜索关键词

        Returns:
            执行结果
        """
        all_papers = []
        total_added = 0
        total_skipped = 0

        remaining = count
        batch_num = 1

        logger.info(f"开始分批搜集文献，总数: {count}, 批次大小: {batch_size}")

        while remaining > 0:
            current_batch_size = min(remaining, batch_size)
            logger.info(f"正在处理第 {batch_num} 批，数量: {current_batch_size}")

            # 搜集论文（只在第一批扩展关键词，后续批次复用）
            papers = self.collect_papers(
                topic, current_batch_size, domain,
                expand_query=(expand_query and batch_num == 1)
            )
            
            if papers:
                all_papers.extend(papers)
                
                # 添加到图谱
                stats = self.add_papers_to_graph(papers)
                total_added += stats['added']
                total_skipped += stats['skipped']
            else:
                logger.warning(f"第 {batch_num} 批未能生成论文信息")
            
            remaining -= current_batch_size
            batch_num += 1

        # 获取更新后的统计
        graph_stats = self.kg.get_statistics()

        return {
            "success": True,
            "message": f"成功添加 {total_added} 篇论文到知识图谱 (总目标 {count})",
            "papers": all_papers,
            "add_stats": {
                "total": len(all_papers),
                "added": total_added,
                "skipped": total_skipped
            },
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
    python scripts/collect_literature.py --add --title "数字化转型与企业绩效" \
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
    parser.add_argument("--no-expand", action="store_true", help="禁用搜索关键词扩展（不使用大模型扩写）")

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

    expand_query = not args.no_expand

    print(f"\n开始搜集文献...")
    print(f"  主题: {args.topic}")
    print(f"  数量: {args.count}")
    if args.domain:
        print(f"  领域: {args.domain}")
    print(f"  关键词扩展: {'启用' if expand_query else '禁用'}")
    print()

    if args.dry_run:
        # 只生成不添加
        papers = collector.collect_papers(args.topic, args.count, args.domain, expand_query=expand_query)
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
        result = collector.collect_and_add(args.topic, args.count, args.domain, expand_query=expand_query)

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