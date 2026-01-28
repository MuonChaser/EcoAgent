"""
方法论知识图谱工具 - 变量与计量方法关联图谱
Methodology Knowledge Graph Tool - Variable-Method Association Graph

功能：
1. 从实证论文CSV构建知识图谱（X/Y作为节点，方法作为边）
2. 基于语义相似度检索相关节点
3. 返回K跳邻域子图
4. 支持研究空白识别
"""

import os
import re
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from loguru import logger

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logger.warning("sentence-transformers未安装，语义搜索将不可用")

try:
    from langchain.tools import Tool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


# ==================== 数据模型 ====================

@dataclass
class VariableNode:
    """变量节点"""
    id: str  # 唯一ID
    name: str  # 变量名称（原始文本）
    normalized_name: str  # 标准化名称
    roles: Set[str] = field(default_factory=set)  # 角色集合: {"X", "Y"}
    papers: List[str] = field(default_factory=list)  # 出现的论文列表
    embedding: Optional[List[float]] = None  # 语义向量

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "normalized_name": self.normalized_name,
            "roles": list(self.roles),
            "papers": self.papers,
        }


@dataclass
class MethodEdge:
    """方法边（连接X和Y）"""
    id: str
    source_id: str  # X节点ID
    target_id: str  # Y节点ID
    method: str  # 计量方法
    paper_title: str  # 论文标题
    research_question: str  # 研究问题

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SubgraphResult:
    """子图检索结果"""
    query_nodes: List[Dict]  # 查询匹配的节点
    neighbor_nodes: List[Dict]  # 邻居节点
    edges: List[Dict]  # 相关的边
    methods: List[str]  # 涉及的方法列表
    papers: List[str]  # 相关论文


# ==================== 知识图谱核心类 ====================

class MethodologyKnowledgeGraph:
    """
    方法论知识图谱

    图结构：
    - 节点：变量（X或Y，一个变量可以同时扮演两种角色）
    - 边：计量方法（从X指向Y，附带论文信息）

    核心功能：
    1. 从CSV构建图谱
    2. 语义相似度节点检索
    3. K跳邻域子图返回
    4. 方法推荐
    """

    def __init__(
        self,
        storage_dir: str = "data/methodology_graph",
        embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    ):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 图结构
        self.nodes: Dict[str, VariableNode] = {}  # node_id -> VariableNode
        self.edges: List[MethodEdge] = []
        self.adjacency: Dict[str, Set[str]] = defaultdict(set)  # node_id -> neighbor_ids
        self.reverse_adjacency: Dict[str, Set[str]] = defaultdict(set)  # node_id -> nodes pointing to it

        # 索引
        self.name_to_id: Dict[str, str] = {}  # normalized_name -> node_id
        self.method_index: Dict[str, List[int]] = defaultdict(list)  # method -> edge indices

        # 嵌入模型
        self.embedding_model = None
        self.embedding_model_name = embedding_model
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer(embedding_model)
                logger.info(f"嵌入模型加载成功: {embedding_model}")
            except Exception as e:
                logger.warning(f"嵌入模型加载失败: {e}")

        # 尝试加载已有图谱
        self._load_graph()

    def _normalize_variable_name(self, name: str) -> str:
        """标准化变量名称"""
        if not name or not isinstance(name, str):
            return ""
        # 去除空白、括号内容，转小写
        name = name.strip()
        name = re.sub(r'[（(].*?[）)]', '', name)  # 移除括号及其内容
        name = re.sub(r'\s+', '', name)  # 移除空白
        return name.lower()

    def _generate_node_id(self, name: str) -> str:
        """生成节点ID"""
        normalized = self._normalize_variable_name(name)
        return hashlib.md5(normalized.encode()).hexdigest()[:12]

    def _generate_edge_id(self, source_id: str, target_id: str, method: str, paper: str) -> str:
        """生成边ID"""
        content = f"{source_id}_{target_id}_{method}_{paper}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _parse_variables(self, text: str) -> List[str]:
        """解析变量文本，可能包含多个变量（用逗号、顿号等分隔）"""
        if not text or not isinstance(text, str) or text.strip() in ['', 'N/A', '不适用', '未提及']:
            return []

        # 分隔符
        separators = r'[,，、;；\n]'
        parts = re.split(separators, text)

        variables = []
        for part in parts:
            part = part.strip()
            if part and len(part) > 1:  # 过滤太短的
                variables.append(part)

        return variables

    def _parse_methods(self, text: str) -> List[str]:
        """解析方法文本"""
        if not text or not isinstance(text, str):
            return []

        separators = r'[,，、;；\n]'
        parts = re.split(separators, text)

        methods = []
        for part in parts:
            part = part.strip()
            if part and len(part) > 1:
                methods.append(part)

        return methods if methods else [text.strip()]

    def build_from_csv(self, csv_path: str, encoding: str = 'utf-8') -> Dict[str, int]:
        """
        从CSV文件构建知识图谱

        Args:
            csv_path: CSV文件路径
            encoding: 文件编码

        Returns:
            统计信息
        """
        import csv

        stats = {"papers": 0, "nodes": 0, "edges": 0, "skipped": 0}

        # 读取CSV
        try:
            with open(csv_path, 'r', encoding=encoding) as f:
                # 尝试检测BOM
                first_line = f.readline()
                f.seek(0)
                if first_line.startswith('\ufeff'):
                    encoding = 'utf-8-sig'

            with open(csv_path, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)

                for row in reader:
                    paper_title = row.get('文章名称', row.get('title', '')).strip()
                    research_question = row.get('核心研究问题', row.get('research_question', '')).strip()
                    x_text = row.get('X (自变量)', row.get('X', '')).strip()
                    y_text = row.get('Y (因变量)', row.get('Y', '')).strip()
                    method_text = row.get('计量模型 (方法)', row.get('method', '')).strip()

                    # 解析变量
                    x_vars = self._parse_variables(x_text)
                    y_vars = self._parse_variables(y_text)
                    methods = self._parse_methods(method_text)

                    if not x_vars or not y_vars or not methods:
                        stats["skipped"] += 1
                        continue

                    stats["papers"] += 1

                    # 添加节点和边
                    for x_var in x_vars:
                        x_node = self._add_or_update_node(x_var, "X", paper_title)

                        for y_var in y_vars:
                            y_node = self._add_or_update_node(y_var, "Y", paper_title)

                            for method in methods:
                                self._add_edge(x_node.id, y_node.id, method, paper_title, research_question)
                                stats["edges"] += 1

        except Exception as e:
            logger.error(f"读取CSV失败: {e}")
            raise

        stats["nodes"] = len(self.nodes)

        # 计算嵌入
        if self.embedding_model:
            self._compute_embeddings()

        # 保存图谱
        self._save_graph()

        logger.info(f"知识图谱构建完成: {stats}")
        return stats

    def _add_or_update_node(self, name: str, role: str, paper: str) -> VariableNode:
        """添加或更新节点"""
        normalized = self._normalize_variable_name(name)

        # 检查是否已存在
        if normalized in self.name_to_id:
            node_id = self.name_to_id[normalized]
            node = self.nodes[node_id]
            node.roles.add(role)
            if paper not in node.papers:
                node.papers.append(paper)
            return node

        # 创建新节点
        node_id = self._generate_node_id(name)
        node = VariableNode(
            id=node_id,
            name=name,
            normalized_name=normalized,
            roles={role},
            papers=[paper]
        )

        self.nodes[node_id] = node
        self.name_to_id[normalized] = node_id

        return node

    def _add_edge(self, source_id: str, target_id: str, method: str, paper: str, research_question: str):
        """添加边"""
        edge_id = self._generate_edge_id(source_id, target_id, method, paper)

        # 检查是否已存在
        for edge in self.edges:
            if edge.id == edge_id:
                return

        edge = MethodEdge(
            id=edge_id,
            source_id=source_id,
            target_id=target_id,
            method=method,
            paper_title=paper,
            research_question=research_question
        )

        edge_idx = len(self.edges)
        self.edges.append(edge)

        # 更新邻接表
        self.adjacency[source_id].add(target_id)
        self.reverse_adjacency[target_id].add(source_id)

        # 更新方法索引
        self.method_index[method].append(edge_idx)

    def _compute_embeddings(self):
        """计算所有节点的嵌入向量"""
        if not self.embedding_model:
            return

        logger.info("正在计算节点嵌入向量...")

        names = [node.name for node in self.nodes.values()]
        embeddings = self.embedding_model.encode(names, show_progress_bar=True)

        for node, emb in zip(self.nodes.values(), embeddings):
            node.embedding = emb.tolist()

        logger.info(f"完成 {len(self.nodes)} 个节点的嵌入计算")

    def _save_graph(self):
        """保存图谱到文件"""
        graph_data = {
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "edges": [edge.to_dict() for edge in self.edges],
            "name_to_id": self.name_to_id,
            "stats": {
                "node_count": len(self.nodes),
                "edge_count": len(self.edges),
                "method_count": len(self.method_index),
                "updated_at": datetime.now().isoformat()
            }
        }

        # 保存主数据
        with open(self.storage_dir / "graph.json", 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)

        # 保存嵌入向量（单独文件，可能较大）
        if any(node.embedding for node in self.nodes.values()):
            embeddings = {nid: node.embedding for nid, node in self.nodes.items() if node.embedding}
            with open(self.storage_dir / "embeddings.json", 'w', encoding='utf-8') as f:
                json.dump(embeddings, f)

        logger.info(f"图谱已保存到 {self.storage_dir}")

    def _load_graph(self):
        """从文件加载图谱"""
        graph_file = self.storage_dir / "graph.json"
        if not graph_file.exists():
            logger.info("未找到已有图谱，将创建新图谱")
            return

        try:
            with open(graph_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 恢复节点
            for nid, node_data in data.get("nodes", {}).items():
                self.nodes[nid] = VariableNode(
                    id=node_data["id"],
                    name=node_data["name"],
                    normalized_name=node_data["normalized_name"],
                    roles=set(node_data["roles"]),
                    papers=node_data["papers"]
                )

            # 恢复边
            for edge_data in data.get("edges", []):
                edge = MethodEdge(**edge_data)
                self.edges.append(edge)
                self.adjacency[edge.source_id].add(edge.target_id)
                self.reverse_adjacency[edge.target_id].add(edge.source_id)
                self.method_index[edge.method].append(len(self.edges) - 1)

            # 恢复索引
            self.name_to_id = data.get("name_to_id", {})

            # 加载嵌入
            emb_file = self.storage_dir / "embeddings.json"
            if emb_file.exists():
                with open(emb_file, 'r', encoding='utf-8') as f:
                    embeddings = json.load(f)
                for nid, emb in embeddings.items():
                    if nid in self.nodes:
                        self.nodes[nid].embedding = emb

            logger.info(f"已加载图谱: {len(self.nodes)} 节点, {len(self.edges)} 边")

        except Exception as e:
            logger.error(f"加载图谱失败: {e}")

    def search_similar_nodes(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.3
    ) -> List[Tuple[VariableNode, float]]:
        """
        语义相似度搜索节点

        Args:
            query: 查询文本
            top_k: 返回数量
            threshold: 相似度阈值

        Returns:
            [(node, similarity_score), ...]
        """
        if not self.embedding_model:
            # 降级为关键词匹配
            return self._keyword_search(query, top_k)

        # 计算查询向量
        query_emb = self.embedding_model.encode([query])[0]

        # 计算相似度
        results = []
        for node in self.nodes.values():
            if node.embedding:
                node_emb = np.array(node.embedding)
                similarity = np.dot(query_emb, node_emb) / (
                    np.linalg.norm(query_emb) * np.linalg.norm(node_emb)
                )
                if similarity >= threshold:
                    results.append((node, float(similarity)))

        # 排序并返回
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def _keyword_search(self, query: str, top_k: int) -> List[Tuple[VariableNode, float]]:
        """关键词搜索（降级方案）"""
        query_lower = query.lower()
        results = []

        for node in self.nodes.values():
            if query_lower in node.name.lower() or query_lower in node.normalized_name:
                results.append((node, 1.0))
            elif any(q in node.name.lower() for q in query_lower.split()):
                results.append((node, 0.5))

        return results[:top_k]

    def get_neighbors(self, node_id: str, k_hops: int = 1) -> Set[str]:
        """
        获取K跳邻居节点

        Args:
            node_id: 起始节点ID
            k_hops: 跳数

        Returns:
            邻居节点ID集合
        """
        visited = {node_id}
        current_level = {node_id}

        for _ in range(k_hops):
            next_level = set()
            for nid in current_level:
                # 正向邻居（该节点作为X指向的Y）
                next_level.update(self.adjacency.get(nid, set()))
                # 反向邻居（指向该节点的X）
                next_level.update(self.reverse_adjacency.get(nid, set()))

            next_level -= visited
            visited.update(next_level)
            current_level = next_level

        visited.discard(node_id)  # 移除起始节点
        return visited

    def get_edges_between(self, node_ids: Set[str]) -> List[MethodEdge]:
        """获取节点集合之间的所有边"""
        result = []
        for edge in self.edges:
            if edge.source_id in node_ids and edge.target_id in node_ids:
                result.append(edge)
        return result

    def retrieve_subgraph(
        self,
        query_x: Optional[str] = None,
        query_y: Optional[str] = None,
        top_k: int = 5,
        k_hops: int = 1,
        similarity_threshold: float = 0.3
    ) -> SubgraphResult:
        """
        检索相关子图

        这是供Agent调用的核心方法。

        Args:
            query_x: 查询的X变量描述
            query_y: 查询的Y变量描述
            top_k: 每个查询返回的相似节点数
            k_hops: 邻域扩展跳数
            similarity_threshold: 相似度阈值

        Returns:
            SubgraphResult 包含相关节点、边和方法信息
        """
        query_node_ids = set()
        query_nodes = []

        # 搜索X相关节点
        if query_x:
            x_results = self.search_similar_nodes(query_x, top_k, similarity_threshold)
            for node, score in x_results:
                query_node_ids.add(node.id)
                node_dict = node.to_dict()
                node_dict["similarity"] = score
                node_dict["query_type"] = "X"
                query_nodes.append(node_dict)

        # 搜索Y相关节点
        if query_y:
            y_results = self.search_similar_nodes(query_y, top_k, similarity_threshold)
            for node, score in y_results:
                if node.id not in query_node_ids:
                    query_node_ids.add(node.id)
                    node_dict = node.to_dict()
                    node_dict["similarity"] = score
                    node_dict["query_type"] = "Y"
                    query_nodes.append(node_dict)

        # 获取邻居节点
        all_neighbors = set()
        for nid in query_node_ids:
            all_neighbors.update(self.get_neighbors(nid, k_hops))

        # 移除已经是查询节点的
        all_neighbors -= query_node_ids

        neighbor_nodes = [
            self.nodes[nid].to_dict() for nid in all_neighbors if nid in self.nodes
        ]

        # 获取相关边
        all_node_ids = query_node_ids | all_neighbors
        related_edges = self.get_edges_between(all_node_ids)
        edges = [edge.to_dict() for edge in related_edges]

        # 收集方法和论文
        methods = list(set(edge.method for edge in related_edges))
        papers = list(set(edge.paper_title for edge in related_edges))

        return SubgraphResult(
            query_nodes=query_nodes,
            neighbor_nodes=neighbor_nodes,
            edges=edges,
            methods=methods,
            papers=papers
        )

    def recommend_methods(self, x_query: str, y_query: str, top_k: int = 5) -> List[Dict]:
        """
        根据X和Y推荐计量方法

        Args:
            x_query: X变量描述
            y_query: Y变量描述
            top_k: 返回数量

        Returns:
            推荐的方法列表，包含频次和相关论文
        """
        subgraph = self.retrieve_subgraph(x_query, y_query, top_k=top_k)

        # 统计方法频次
        method_count = defaultdict(int)
        method_papers = defaultdict(list)

        for edge in subgraph.edges:
            method_count[edge["method"]] += 1
            method_papers[edge["method"]].append(edge["paper_title"])

        # 排序
        recommendations = []
        for method, count in sorted(method_count.items(), key=lambda x: -x[1])[:top_k]:
            recommendations.append({
                "method": method,
                "frequency": count,
                "example_papers": method_papers[method][:3]
            })

        return recommendations

    def get_statistics(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        # 计算度分布
        out_degrees = [len(self.adjacency.get(nid, set())) for nid in self.nodes]
        in_degrees = [len(self.reverse_adjacency.get(nid, set())) for nid in self.nodes]

        # 统计变量角色
        x_only = sum(1 for n in self.nodes.values() if n.roles == {"X"})
        y_only = sum(1 for n in self.nodes.values() if n.roles == {"Y"})
        both = sum(1 for n in self.nodes.values() if "X" in n.roles and "Y" in n.roles)

        # 方法统计
        method_freq = {m: len(edges) for m, edges in self.method_index.items()}
        top_methods = sorted(method_freq.items(), key=lambda x: -x[1])[:10]

        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "unique_methods": len(self.method_index),
            "node_roles": {
                "x_only": x_only,
                "y_only": y_only,
                "both_x_and_y": both
            },
            "degree_stats": {
                "avg_out_degree": sum(out_degrees) / len(out_degrees) if out_degrees else 0,
                "max_out_degree": max(out_degrees) if out_degrees else 0,
                "avg_in_degree": sum(in_degrees) / len(in_degrees) if in_degrees else 0,
                "max_in_degree": max(in_degrees) if in_degrees else 0,
            },
            "top_methods": top_methods
        }


# ==================== LangChain工具封装 ====================

def _format_subgraph_result(result: SubgraphResult) -> str:
    """格式化子图结果为可读文本"""
    lines = []

    lines.append("=== 查询匹配节点 ===")
    for node in result.query_nodes:
        roles = "/".join(node.get("roles", []))
        sim = node.get("similarity", 0)
        lines.append(f"- {node['name']} [{roles}] (相似度: {sim:.2f})")

    lines.append("\n=== 邻居节点 ===")
    for node in result.neighbor_nodes[:10]:  # 限制显示数量
        roles = "/".join(node.get("roles", []))
        lines.append(f"- {node['name']} [{roles}]")
    if len(result.neighbor_nodes) > 10:
        lines.append(f"  ... 还有 {len(result.neighbor_nodes) - 10} 个节点")

    lines.append("\n=== 相关计量方法 ===")
    for method in result.methods[:10]:
        lines.append(f"- {method}")

    lines.append("\n=== 相关论文 ===")
    for paper in result.papers[:5]:
        lines.append(f"- {paper}")
    if len(result.papers) > 5:
        lines.append(f"  ... 还有 {len(result.papers) - 5} 篇论文")

    return "\n".join(lines)


# 全局实例
_kg_instance: Optional[MethodologyKnowledgeGraph] = None


def get_methodology_graph(storage_dir: str = "data/methodology_graph") -> MethodologyKnowledgeGraph:
    """获取知识图谱单例"""
    global _kg_instance
    if _kg_instance is None:
        _kg_instance = MethodologyKnowledgeGraph(storage_dir=storage_dir)
    return _kg_instance


def create_langchain_tools(kg: Optional[MethodologyKnowledgeGraph] = None) -> List:
    """
    创建LangChain工具列表

    Returns:
        LangChain Tool对象列表
    """
    if not LANGCHAIN_AVAILABLE:
        logger.warning("LangChain未安装，无法创建工具")
        return []

    if kg is None:
        kg = get_methodology_graph()

    def search_methodology_graph(query: str) -> str:
        """
        在方法论知识图谱中搜索相关变量和方法。
        输入可以是变量描述（如"数字经济"、"企业创新"）。
        返回相似的变量节点及其关联的计量方法。
        """
        try:
            # 解析输入，支持 "X: xxx, Y: yyy" 格式
            query_x = None
            query_y = None

            if "X:" in query or "Y:" in query:
                parts = query.split(",")
                for part in parts:
                    part = part.strip()
                    if part.startswith("X:"):
                        query_x = part[2:].strip()
                    elif part.startswith("Y:"):
                        query_y = part[2:].strip()
            else:
                # 单一查询，同时作为X和Y搜索
                query_x = query
                query_y = query

            result = kg.retrieve_subgraph(query_x=query_x, query_y=query_y)
            return _format_subgraph_result(result)
        except Exception as e:
            return f"搜索失败: {str(e)}"

    def recommend_methods(query: str) -> str:
        """
        根据研究变量推荐合适的计量方法。
        输入格式: "X: 自变量描述, Y: 因变量描述"
        返回推荐的计量方法及相关论文。
        """
        try:
            parts = query.split(",")
            x_query = ""
            y_query = ""

            for part in parts:
                part = part.strip()
                if part.startswith("X:"):
                    x_query = part[2:].strip()
                elif part.startswith("Y:"):
                    y_query = part[2:].strip()

            if not x_query and not y_query:
                return "请提供正确格式: X: 自变量描述, Y: 因变量描述"

            recommendations = kg.recommend_methods(x_query, y_query)

            if not recommendations:
                return "未找到相关方法推荐，请尝试其他变量描述"

            lines = ["=== 推荐的计量方法 ==="]
            for rec in recommendations:
                lines.append(f"\n方法: {rec['method']}")
                lines.append(f"使用频次: {rec['frequency']}")
                lines.append("相关论文:")
                for paper in rec['example_papers']:
                    lines.append(f"  - {paper}")

            return "\n".join(lines)
        except Exception as e:
            return f"推荐失败: {str(e)}"

    def get_graph_stats(query: str = "") -> str:
        """获取方法论知识图谱的统计信息"""
        try:
            stats = kg.get_statistics()

            lines = [
                "=== 方法论知识图谱统计 ===",
                f"总节点数: {stats['total_nodes']}",
                f"总边数: {stats['total_edges']}",
                f"唯一方法数: {stats['unique_methods']}",
                "",
                "节点角色分布:",
                f"  - 仅作为X: {stats['node_roles']['x_only']}",
                f"  - 仅作为Y: {stats['node_roles']['y_only']}",
                f"  - 同时作为X和Y: {stats['node_roles']['both_x_and_y']}",
                "",
                "热门计量方法 (Top 10):"
            ]

            for method, count in stats['top_methods']:
                lines.append(f"  - {method}: {count}次")

            return "\n".join(lines)
        except Exception as e:
            return f"获取统计信息失败: {str(e)}"

    tools = [
        Tool(
            name="search_methodology_graph",
            func=search_methodology_graph,
            description="在方法论知识图谱中搜索相关变量和计量方法。输入变量描述（如'数字经济'、'企业创新'），或使用格式'X: 自变量, Y: 因变量'进行精确搜索。返回相似变量、邻居节点和相关的计量方法。"
        ),
        Tool(
            name="recommend_econometric_methods",
            func=recommend_methods,
            description="根据研究的X（自变量）和Y（因变量）推荐合适的计量方法。输入格式: 'X: 自变量描述, Y: 因变量描述'。返回在相似研究中使用过的方法及相关论文。"
        ),
        Tool(
            name="get_methodology_graph_stats",
            func=get_graph_stats,
            description="获取方法论知识图谱的统计信息，包括节点数、边数、热门方法等。"
        ),
    ]

    return tools


# ==================== 命令行入口 ====================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="方法论知识图谱工具")
    parser.add_argument("--build", type=str, help="从CSV构建图谱")
    parser.add_argument("--search", type=str, help="搜索变量")
    parser.add_argument("--stats", action="store_true", help="显示统计信息")
    parser.add_argument("--storage", type=str, default="data/methodology_graph", help="存储目录")

    args = parser.parse_args()

    kg = MethodologyKnowledgeGraph(storage_dir=args.storage)

    if args.build:
        stats = kg.build_from_csv(args.build)
        print(f"构建完成: {stats}")

    if args.search:
        result = kg.retrieve_subgraph(query_x=args.search, query_y=args.search)
        print(_format_subgraph_result(result))

    if args.stats:
        stats = kg.get_statistics()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
