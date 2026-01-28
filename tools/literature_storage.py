"""
文献存储与检索工具 - 支持RAG检索和原始格式备份
Literature Storage Tool with RAG support and original format backup
"""

import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from pydantic import BaseModel, Field
from loguru import logger

# 尝试导入向量数据库依赖
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("ChromaDB未安装，RAG功能将不可用。请运行: pip install chromadb")

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logger.warning("sentence-transformers未安装，将使用ChromaDB默认嵌入。请运行: pip install sentence-transformers")


# ==================== 数据模型 ====================

class StoredLiteratureItem(BaseModel):
    """存储的文献项"""
    id: str = Field(description="唯一标识符")
    authors: str = Field(description="作者")
    year: int = Field(description="年份")
    title: str = Field(description="论文标题")
    journal: Optional[str] = Field(default=None, description="期刊名称")
    abstract: Optional[str] = Field(default=None, description="摘要")
    keywords: List[str] = Field(default_factory=list, description="关键词")
    doi: Optional[str] = Field(default=None, description="DOI")
    url: Optional[str] = Field(default=None, description="链接")
    pdf_url: Optional[str] = Field(default=None, description="PDF链接")

    # 经济学特定字段
    variable_x_definition: Optional[str] = Field(default=None, description="X变量定义")
    variable_x_measurement: Optional[str] = Field(default=None, description="X变量衡量")
    variable_y_definition: Optional[str] = Field(default=None, description="Y变量定义")
    variable_y_measurement: Optional[str] = Field(default=None, description="Y变量衡量")
    core_conclusion: Optional[str] = Field(default=None, description="核心结论")
    theoretical_mechanism: List[str] = Field(default_factory=list, description="理论机制")
    data_source: Optional[str] = Field(default=None, description="数据来源")
    identification_strategy: Optional[str] = Field(default=None, description="识别策略")
    heterogeneity_dimensions: List[str] = Field(default_factory=list, description="异质性维度")
    limitations: List[str] = Field(default_factory=list, description="研究不足")

    # 元数据
    source: str = Field(default="manual", description="来源: manual, search, import")
    added_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="添加时间")
    tags: List[str] = Field(default_factory=list, description="自定义标签")
    notes: Optional[str] = Field(default=None, description="备注")
    research_project: Optional[str] = Field(default=None, description="关联研究项目")


class LiteratureSearchResult(BaseModel):
    """文献搜索结果"""
    items: List[StoredLiteratureItem] = Field(description="匹配的文献列表")
    total_count: int = Field(description="总匹配数")
    query: str = Field(description="查询内容")
    search_type: str = Field(description="搜索类型: semantic, keyword, hybrid")


# ==================== 文献存储工具 ====================

class LiteratureStorageTool:
    """
    文献存储与检索工具

    功能:
    1. 存储文献到向量数据库(RAG)和JSON备份
    2. 语义搜索(基于embedding相似度)
    3. 关键词搜索
    4. 混合搜索
    5. 手动添加文献
    6. 批量导入导出
    """

    def __init__(
        self,
        storage_dir: str = "data/literature",
        collection_name: str = "research_literature",
        embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    ):
        """
        初始化文献存储工具

        Args:
            storage_dir: 存储目录
            collection_name: ChromaDB集合名称
            embedding_model: 嵌入模型名称(支持中英文)
        """
        self.storage_dir = Path(storage_dir)
        self.backup_dir = self.storage_dir / "backup"
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model

        # 创建目录
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # 初始化嵌入模型
        self.embedding_model = None
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer(embedding_model)
                logger.info(f"嵌入模型加载成功: {embedding_model}")
            except Exception as e:
                logger.warning(f"嵌入模型加载失败: {e}")

        # 初始化ChromaDB
        self.chroma_client = None
        self.collection = None
        if CHROMA_AVAILABLE:
            try:
                self.chroma_client = chromadb.PersistentClient(
                    path=str(self.storage_dir / "chroma_db")
                )
                self.collection = self.chroma_client.get_or_create_collection(
                    name=collection_name,
                    metadata={"description": "Research literature collection for RAG"}
                )
                logger.info(f"ChromaDB初始化成功，集合: {collection_name}")
            except Exception as e:
                logger.error(f"ChromaDB初始化失败: {e}")

        # 加载现有备份索引
        self.index_file = self.storage_dir / "literature_index.json"
        self.index = self._load_index()

    def _load_index(self) -> Dict[str, Any]:
        """加载文献索引"""
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"items": {}, "stats": {"total": 0, "by_year": {}, "by_journal": {}}}

    def _save_index(self):
        """保存文献索引"""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)

    def _generate_id(self, item: Union[StoredLiteratureItem, Dict]) -> str:
        """生成文献唯一ID"""
        if isinstance(item, dict):
            title = item.get('title', '')
            authors = item.get('authors', '')
            year = item.get('year', '')
        else:
            title = item.title
            authors = item.authors
            year = item.year

        content = f"{title}_{authors}_{year}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _create_document_text(self, item: StoredLiteratureItem) -> str:
        """创建用于嵌入的文档文本"""
        parts = [
            f"标题: {item.title}",
            f"作者: {item.authors}",
            f"年份: {item.year}",
        ]

        if item.journal:
            parts.append(f"期刊: {item.journal}")
        if item.abstract:
            parts.append(f"摘要: {item.abstract}")
        if item.keywords:
            parts.append(f"关键词: {', '.join(item.keywords)}")
        if item.core_conclusion:
            parts.append(f"核心结论: {item.core_conclusion}")
        if item.theoretical_mechanism:
            parts.append(f"理论机制: {', '.join(item.theoretical_mechanism)}")
        if item.variable_x_definition:
            parts.append(f"解释变量定义: {item.variable_x_definition}")
        if item.variable_y_definition:
            parts.append(f"被解释变量定义: {item.variable_y_definition}")
        if item.identification_strategy:
            parts.append(f"识别策略: {item.identification_strategy}")

        return "\n".join(parts)

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """获取文本嵌入向量"""
        if self.embedding_model:
            return self.embedding_model.encode(text).tolist()
        return None

    def _extract_author_from_filename(self, filename: str) -> Optional[str]:
        """
        从文件名中提取作者名

        支持格式:
        - 标题_作者.pdf (如: 环境规制强度和生产技术进步_张成.pdf)
        - 标题_作者名.docx
        - 复杂标题(带括号)_作者.pdf (如: 中国的绿色工业革命(1980—2008)_陈诗一.pdf)

        Returns:
            提取的作者名，若无法提取则返回None
        """
        import re

        if not filename:
            return None

        # 去除扩展名
        name = Path(filename).stem

        # 按下划线分割，最后一部分通常是作者名
        parts = name.split('_')
        if len(parts) < 2:
            return None

        author_candidate = parts[-1].strip()

        # 验证是否像中文作者名（2-4个汉字，可能带"等"字）
        # 或英文作者名
        chinese_pattern = re.compile(r'^[\u4e00-\u9fa5]{2,4}(等)?$')
        english_pattern = re.compile(r'^[A-Za-z\s\.\-]+$')

        if chinese_pattern.match(author_candidate) or english_pattern.match(author_candidate):
            return author_candidate

        # 如果最后一部分不像作者名，尝试倒数第二部分
        if len(parts) >= 3:
            author_candidate = parts[-2].strip()
            if chinese_pattern.match(author_candidate) or english_pattern.match(author_candidate):
                return author_candidate

        return None

    def _extract_year_from_text(self, text: str) -> Optional[int]:
        """
        从文本中提取年份

        支持格式:
        - (2020)
        - (1980-2008) -> 取较新的年份
        - 2020年
        - 直接的4位数字年份

        Returns:
            提取的年份，若无法提取则返回None
        """
        import re

        if not text:
            return None

        # 优先匹配括号中的年份
        bracket_pattern = re.compile(r'[（\(](\d{4})[-—～]?(\d{4})?[）\)]')
        match = bracket_pattern.search(text)
        if match:
            year1 = int(match.group(1))
            year2 = int(match.group(2)) if match.group(2) else year1
            return max(year1, year2)  # 返回较新的年份

        # 匹配"XXXX年"格式
        year_pattern = re.compile(r'(\d{4})年')
        match = year_pattern.search(text)
        if match:
            return int(match.group(1))

        # 匹配独立的4位年份数字（2000-2030范围）
        standalone_pattern = re.compile(r'\b(20[0-3]\d)\b')
        matches = standalone_pattern.findall(text)
        if matches:
            return int(matches[-1])  # 返回最后一个匹配

        return None

    # ==================== 核心功能 ====================

    def add_literature(
        self,
        item: Union[StoredLiteratureItem, Dict[str, Any]],
        source: str = "manual"
    ) -> str:
        """
        添加单篇文献

        Args:
            item: 文献项(Pydantic模型或字典)
            source: 来源标识

        Returns:
            文献ID
        """
        # Step 1: Ensure we are working with a dictionary
        if isinstance(item, StoredLiteratureItem):
            item_dict = item.model_dump()
        else:
            item_dict = item.copy()

        # Step 2: Generate and assign ID
        item_id = self._generate_id(item_dict)
        item_dict['id'] = item_id

        # Step 3: Add other metadata
        item_dict['source'] = source
        if 'added_at' not in item_dict:
            item_dict['added_at'] = datetime.now().isoformat()

        # Step 4: Validate and create the Pydantic model
        validated_item = StoredLiteratureItem(**item_dict)

        # 1. 保存到JSON备份
        backup_file = self.backup_dir / f"{item_id}.json"
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(validated_item.model_dump(), f, ensure_ascii=False, indent=2)

        # 2. 更新索引
        self.index["items"][item_id] = {
            "title": validated_item.title,
            "authors": validated_item.authors,
            "year": validated_item.year,
            "journal": validated_item.journal,
            "added_at": validated_item.added_at,
            "source": validated_item.source,
            "tags": validated_item.tags
        }
        self.index["stats"]["total"] = len(self.index["items"])

        # 统计年份
        year_str = str(validated_item.year)
        self.index["stats"]["by_year"][year_str] = self.index["stats"]["by_year"].get(year_str, 0) + 1

        # 统计期刊
        if validated_item.journal:
            self.index["stats"]["by_journal"][validated_item.journal] = \
                self.index["stats"]["by_journal"].get(validated_item.journal, 0) + 1

        self._save_index()

        # 3. 添加到向量数据库
        if self.collection is not None:
            doc_text = self._create_document_text(validated_item)
            embedding = self._get_embedding(doc_text)

            try:
                metadata_to_store = {
                    "title": validated_item.title,
                    "authors": validated_item.authors,
                    "year": validated_item.year,
                    "journal": validated_item.journal or "",
                    "source": validated_item.source,
                    "tags": ",".join(validated_item.tags)
                }
                if embedding:
                    self.collection.add(
                        ids=[item_id],
                        documents=[doc_text],
                        embeddings=[embedding],
                        metadatas=[metadata_to_store]
                    )
                else:
                    # 使用ChromaDB默认嵌入
                    self.collection.add(
                        ids=[item_id],
                        documents=[doc_text],
                        metadatas=[metadata_to_store]
                    )
                logger.info(f"文献已添加到向量数据库: {validated_item.title[:50]}...")
            except Exception as e:
                logger.error(f"添加到向量数据库失败: {e}")

        logger.info(f"文献添加成功: [{item_id}] {validated_item.title}")
        return item_id

    def add_literature_batch(
        self,
        items: List[Union[StoredLiteratureItem, Dict[str, Any]]],
        source: str = "batch_import"
    ) -> List[str]:
        """
        批量添加文献

        Args:
            items: 文献列表
            source: 来源标识

        Returns:
            文献ID列表
        """
        ids = []
        for item in items:
            try:
                item_id = self.add_literature(item, source)
                ids.append(item_id)
            except Exception as e:
                logger.error(f"批量添加失败: {e}")

        logger.info(f"批量添加完成: {len(ids)}/{len(items)} 篇文献")
        return ids

    def search_semantic(
        self,
        query: str,
        n_results: int = 10,
        filter_year: Optional[int] = None,
        filter_journal: Optional[str] = None
    ) -> LiteratureSearchResult:
        """
        语义搜索(基于向量相似度)

        Args:
            query: 查询文本
            n_results: 返回结果数
            filter_year: 年份过滤
            filter_journal: 期刊过滤

        Returns:
            搜索结果
        """
        if self.collection is None:
            logger.warning("向量数据库不可用，无法进行语义搜索")
            return LiteratureSearchResult(items=[], total_count=0, query=query, search_type="semantic")

        # 构建过滤条件
        where_filter = {}
        if filter_year:
            where_filter["year"] = filter_year
        if filter_journal:
            where_filter["journal"] = filter_journal

        try:
            # 获取查询嵌入
            query_embedding = self._get_embedding(query)

            if query_embedding:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    where=where_filter if where_filter else None
                )
            else:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where_filter if where_filter else None
                )

            # 加载完整文献信息
            items = []
            if results['ids'] and results['ids'][0]:
                for item_id in results['ids'][0]:
                    item = self.get_literature(item_id)
                    if item:
                        items.append(item)

            return LiteratureSearchResult(
                items=items,
                total_count=len(items),
                query=query,
                search_type="semantic"
            )

        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            return LiteratureSearchResult(items=[], total_count=0, query=query, search_type="semantic")

    def search_keyword(
        self,
        keyword: str,
        fields: List[str] = None,
        n_results: int = 10
    ) -> LiteratureSearchResult:
        """
        关键词搜索(精确匹配)

        Args:
            keyword: 关键词
            fields: 搜索字段(默认搜索标题、作者、关键词)
            n_results: 返回结果数

        Returns:
            搜索结果
        """
        if fields is None:
            fields = ["title", "authors", "keywords", "abstract", "core_conclusion"]

        keyword_lower = keyword.lower()
        matched_items = []

        for item_id in self.index["items"]:
            item = self.get_literature(item_id)
            if item is None:
                continue

            # 检查各字段
            for field in fields:
                value = getattr(item, field, None)
                if value:
                    if isinstance(value, list):
                        if any(keyword_lower in str(v).lower() for v in value):
                            matched_items.append(item)
                            break
                    elif keyword_lower in str(value).lower():
                        matched_items.append(item)
                        break

        return LiteratureSearchResult(
            items=matched_items[:n_results],
            total_count=len(matched_items),
            query=keyword,
            search_type="keyword"
        )

    def search_hybrid(
        self,
        query: str,
        n_results: int = 10,
        semantic_weight: float = 0.7
    ) -> LiteratureSearchResult:
        """
        混合搜索(语义+关键词)

        Args:
            query: 查询内容
            n_results: 返回结果数
            semantic_weight: 语义搜索权重

        Returns:
            搜索结果
        """
        # 执行两种搜索
        semantic_results = self.search_semantic(query, n_results * 2)
        keyword_results = self.search_keyword(query, n_results=n_results * 2)

        # 合并结果(去重)
        seen_ids = set()
        merged_items = []

        # 优先添加语义搜索结果
        for item in semantic_results.items:
            if item.id not in seen_ids:
                seen_ids.add(item.id)
                merged_items.append(item)

        # 添加关键词搜索结果
        for item in keyword_results.items:
            if item.id not in seen_ids:
                seen_ids.add(item.id)
                merged_items.append(item)

        return LiteratureSearchResult(
            items=merged_items[:n_results],
            total_count=len(merged_items),
            query=query,
            search_type="hybrid"
        )

    def get_literature(self, item_id: str) -> Optional[StoredLiteratureItem]:
        """
        获取单篇文献详情

        Args:
            item_id: 文献ID

        Returns:
            文献详情
        """
        backup_file = self.backup_dir / f"{item_id}.json"
        if backup_file.exists():
            with open(backup_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return StoredLiteratureItem(**data)
        return None

    def delete_literature(self, item_id: str) -> bool:
        """
        删除文献

        Args:
            item_id: 文献ID

        Returns:
            是否成功
        """
        # 从索引删除
        if item_id in self.index["items"]:
            del self.index["items"][item_id]
            self.index["stats"]["total"] = len(self.index["items"])
            self._save_index()

        # 从备份删除
        backup_file = self.backup_dir / f"{item_id}.json"
        if backup_file.exists():
            backup_file.unlink()

        # 从向量数据库删除
        if self.collection is not None:
            try:
                self.collection.delete(ids=[item_id])
            except Exception as e:
                logger.error(f"从向量数据库删除失败: {e}")

        logger.info(f"文献已删除: {item_id}")
        return True

    def update_literature(
        self,
        item_id: str,
        updates: Dict[str, Any]
    ) -> Optional[StoredLiteratureItem]:
        """
        更新文献信息

        Args:
            item_id: 文献ID
            updates: 更新内容

        Returns:
            更新后的文献
        """
        item = self.get_literature(item_id)
        if item is None:
            return None

        # 更新字段
        item_dict = item.model_dump()
        item_dict.update(updates)

        # 删除旧记录
        self.delete_literature(item_id)

        # 添加新记录
        new_item = StoredLiteratureItem(**item_dict)
        self.add_literature(new_item, source="update")

        return new_item

    def list_all(
        self,
        sort_by: str = "added_at",
        descending: bool = True,
        limit: int = 100
    ) -> List[StoredLiteratureItem]:
        """
        列出所有文献

        Args:
            sort_by: 排序字段
            descending: 是否降序
            limit: 返回数量限制

        Returns:
            文献列表
        """
        items = []
        for item_id in self.index["items"]:
            item = self.get_literature(item_id)
            if item:
                items.append(item)

        # 排序
        items.sort(
            key=lambda x: getattr(x, sort_by, ""),
            reverse=descending
        )

        return items[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_count": self.index["stats"]["total"],
            "by_year": self.index["stats"]["by_year"],
            "by_journal": self.index["stats"]["by_journal"],
            "storage_path": str(self.storage_dir),
            "chroma_available": self.collection is not None,
            "embedding_model": self.embedding_model_name if self.embedding_model else "default"
        }

    # ==================== 导入导出 ====================

    def export_to_json(self, output_file: str) -> str:
        """
        导出所有文献到JSON文件

        Args:
            output_file: 输出文件路径

        Returns:
            输出文件路径
        """
        items = self.list_all(limit=10000)
        data = {
            "export_time": datetime.now().isoformat(),
            "total_count": len(items),
            "items": [item.model_dump() for item in items]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"已导出 {len(items)} 篇文献到: {output_file}")
        return output_file

    def import_from_json(self, input_file: str) -> int:
        """
        从JSON文件导入文献

        Args:
            input_file: 输入文件路径

        Returns:
            导入数量
        """
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        items = data.get("items", [])
        if not items:
            # 兼容旧格式
            items = data if isinstance(data, list) else [data]

        ids = self.add_literature_batch(items, source="json_import")
        return len(ids)

    def import_from_literature_collector(
        self,
        literature_output: Dict[str, Any],
        research_project: Optional[str] = None
    ) -> List[str]:
        """
        从LiteratureCollector输出导入

        Args:
            literature_output: LiteratureCollector的输出
            research_project: 关联的研究项目名称

        Returns:
            导入的文献ID列表
        """
        literature_list = literature_output.get("literature_list", [])
        ids = []

        for lit in literature_list:
            # 转换格式
            item_data = {
                "authors": lit.get("authors", ""),
                "year": lit.get("year", 2020),
                "title": lit.get("title", ""),
                "journal": lit.get("journal", ""),
                "core_conclusion": lit.get("core_conclusion", ""),
                "theoretical_mechanism": lit.get("theoretical_mechanism", []),
                "data_source": lit.get("data_source", ""),
                "identification_strategy": lit.get("identification_strategy", ""),
                "heterogeneity_dimensions": lit.get("heterogeneity_dimensions", []),
                "limitations": lit.get("limitations", []),
                "source": "literature_collector",
                "research_project": research_project
            }

            # 处理变量定义
            if "variable_x" in lit and isinstance(lit["variable_x"], dict):
                item_data["variable_x_definition"] = lit["variable_x"].get("definition", "")
                item_data["variable_x_measurement"] = lit["variable_x"].get("measurement", "")

            if "variable_y" in lit and isinstance(lit["variable_y"], dict):
                item_data["variable_y_definition"] = lit["variable_y"].get("definition", "")
                item_data["variable_y_measurement"] = lit["variable_y"].get("measurement", "")

            try:
                item_id = self.add_literature(item_data, source="literature_collector")
                ids.append(item_id)
            except Exception as e:
                logger.error(f"导入文献失败: {lit.get('title', 'Unknown')}, 错误: {e}")

        logger.info(f"从LiteratureCollector导入 {len(ids)} 篇文献")
        return ids

    def import_from_csv(
        self,
        csv_path: str,
        column_mapping: Dict[str, str] = None,
        research_project: Optional[str] = None,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        从CSV文件导入实证论文数据

        Args:
            csv_path: CSV文件路径
            column_mapping: 列名映射（CSV列名 -> 内部字段名）
            research_project: 关联的研究项目名称
            batch_size: 批量导入大小（用于显示进度）

        Returns:
            导入结果统计
        """
        try:
            import pandas as pd
        except ImportError:
            logger.error("需要安装pandas: pip install pandas")
            return {"success": False, "error": "pandas未安装"}

        # 默认列名映射（针对"实证论文提取结果.csv"格式）
        default_mapping = {
            "文章名称": "title",
            "核心研究问题": "abstract",
            "X (自变量)": "variable_x_definition",
            "Y (因变量)": "variable_y_definition",
            "计量模型 (方法)": "identification_strategy",
            "所属期刊": "journal",
            "文件路径": "notes",
        }

        if column_mapping:
            default_mapping.update(column_mapping)

        # 读取CSV
        try:
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            logger.info(f"读取CSV文件: {len(df)} 行, 列: {list(df.columns)}")
        except Exception as e:
            logger.error(f"读取CSV失败: {e}")
            return {"success": False, "error": str(e)}

        # 导入统计
        stats = {
            "total": len(df),
            "imported": 0,
            "skipped": 0,
            "errors": 0,
            "imported_ids": []
        }

        # 逐行导入
        for idx, row in df.iterrows():
            try:
                # 尝试从文件路径/文件名提取作者和年份
                file_path = row.get("文件路径", "") if "文件路径" in df.columns else ""
                title = row.get("文章名称", "") if "文章名称" in df.columns else ""

                # 提取作者：优先从文件名，其次设为未知
                extracted_author = None
                if file_path:
                    filename = Path(str(file_path)).name
                    extracted_author = self._extract_author_from_filename(filename)

                # 提取年份：优先从文件名，其次从标题
                extracted_year = None
                if file_path:
                    extracted_year = self._extract_year_from_text(str(file_path))
                if not extracted_year and title:
                    extracted_year = self._extract_year_from_text(str(title))

                # 构建文献数据
                item_data = {
                    "authors": extracted_author or "未知",
                    "year": extracted_year or 2020,
                    "source": "csv_import",
                    "research_project": research_project,
                    "tags": ["实证论文", "CSV导入"]
                }

                # 映射列
                for csv_col, field_name in default_mapping.items():
                    if csv_col in df.columns:
                        value = row.get(csv_col, "")
                        if pd.notna(value) and str(value).strip():
                            item_data[field_name] = str(value).strip()

                # 检查必要字段
                if not item_data.get("title"):
                    stats["skipped"] += 1
                    continue

                # 从期刊信息推断（如果期刊格式包含年份）
                journal = item_data.get("journal", "")
                if journal:
                    item_data["journal"] = journal

                # 添加到数据库
                item_id = self.add_literature(item_data, source="csv_import")
                stats["imported_ids"].append(item_id)
                stats["imported"] += 1

                # 显示进度
                if (idx + 1) % batch_size == 0:
                    logger.info(f"导入进度: {idx + 1}/{len(df)}")

            except Exception as e:
                stats["errors"] += 1
                logger.warning(f"导入第 {idx + 1} 行失败: {e}")

        stats["success"] = True
        logger.info(
            f"CSV导入完成: 总计 {stats['total']} 行, "
            f"成功 {stats['imported']}, 跳过 {stats['skipped']}, 错误 {stats['errors']}"
        )

        return stats

    def import_from_pdf_directory(
        self,
        pdf_dir: str,
        research_project: Optional[str] = None,
        extract_text: bool = False
    ) -> Dict[str, Any]:
        """
        从PDF目录批量导入文献

        从PDF文件名自动提取:
        - 作者名（文件名最后一个下划线后的部分）
        - 年份（从括号或文件名中提取）
        - 标题（文件名去除作者部分）

        Args:
            pdf_dir: 包含PDF文件的目录路径
            research_project: 关联的研究项目名称
            extract_text: 是否尝试提取PDF文本内容作为摘要（需要PyPDF2）

        Returns:
            导入结果统计
        """
        pdf_path = Path(pdf_dir)
        if not pdf_path.exists():
            logger.error(f"目录不存在: {pdf_dir}")
            return {"success": False, "error": "目录不存在"}

        # 查找所有PDF文件
        pdf_files = list(pdf_path.glob("*.pdf")) + list(pdf_path.glob("*.PDF"))
        logger.info(f"找到 {len(pdf_files)} 个PDF文件")

        if not pdf_files:
            return {"success": True, "total": 0, "imported": 0, "skipped": 0, "errors": 0}

        # 尝试导入PDF解析库
        pdf_reader = None
        if extract_text:
            try:
                import PyPDF2
                pdf_reader = PyPDF2
                logger.info("PyPDF2已加载，将提取PDF文本")
            except ImportError:
                logger.warning("PyPDF2未安装，跳过文本提取。安装: pip install PyPDF2")

        stats = {
            "total": len(pdf_files),
            "imported": 0,
            "skipped": 0,
            "errors": 0,
            "imported_ids": []
        }

        for pdf_file in pdf_files:
            try:
                filename = pdf_file.name
                stem = pdf_file.stem  # 不含扩展名的文件名

                # 提取作者
                author = self._extract_author_from_filename(filename)
                if not author:
                    author = "未知"
                    logger.debug(f"无法从文件名提取作者: {filename}")

                # 提取年份
                year = self._extract_year_from_text(stem)
                if not year:
                    year = 2020
                    logger.debug(f"无法从文件名提取年份: {filename}")

                # 提取标题（去除作者部分）
                title_parts = stem.split('_')
                if len(title_parts) > 1 and author != "未知":
                    # 移除最后一个部分（作者名）
                    title = '_'.join(title_parts[:-1])
                else:
                    title = stem
                # 清理标题中的括号年份
                import re
                title = re.sub(r'[（\(]\d{4}[-—～]?\d{0,4}[）\)]', '', title).strip()

                # 提取PDF文本作为摘要（可选）
                abstract = None
                if pdf_reader:
                    try:
                        with open(pdf_file, 'rb') as f:
                            reader = pdf_reader.PdfReader(f)
                            if len(reader.pages) > 0:
                                # 只读取第一页
                                first_page = reader.pages[0].extract_text()
                                if first_page:
                                    # 截取前500字符作为摘要预览
                                    abstract = first_page[:500].strip()
                    except Exception as e:
                        logger.debug(f"提取PDF文本失败 {filename}: {e}")

                # 构建文献数据
                item_data = {
                    "authors": author,
                    "year": year,
                    "title": title,
                    "abstract": abstract,
                    "source": "pdf_import",
                    "research_project": research_project,
                    "tags": ["PDF导入"],
                    "notes": str(pdf_file.absolute())  # 保存原始文件路径
                }

                # 添加到数据库
                item_id = self.add_literature(item_data, source="pdf_import")
                stats["imported_ids"].append(item_id)
                stats["imported"] += 1
                logger.info(f"导入成功: {title} - {author} ({year})")

            except Exception as e:
                stats["errors"] += 1
                logger.warning(f"导入PDF失败 {pdf_file.name}: {e}")

        stats["success"] = True
        logger.info(
            f"PDF导入完成: 总计 {stats['total']} 个, "
            f"成功 {stats['imported']}, 错误 {stats['errors']}"
        )

        return stats


# ==================== 便捷函数 ====================

def get_literature_storage(
    storage_dir: str = "data/literature"
) -> LiteratureStorageTool:
    """
    获取文献存储工具实例

    Args:
        storage_dir: 存储目录

    Returns:
        文献存储工具实例
    """
    return LiteratureStorageTool(storage_dir=storage_dir)
