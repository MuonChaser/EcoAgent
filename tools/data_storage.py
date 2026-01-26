"""
数据存储与检索工具 - 支持RAG检索和数据路径管理
Data Storage Tool with RAG support for dataset discovery and management
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

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("pandas未安装，数据读取功能将受限。请运行: pip install pandas")


# ==================== 数据模型 ====================

class StoredDataItem(BaseModel):
    """存储的数据项摘要"""
    id: str = Field(description="唯一标识符")
    name: str = Field(description="数据集名称")
    description: str = Field(description="数据集描述/摘要")
    file_path: str = Field(description="数据文件路径")
    file_type: str = Field(default="csv", description="文件类型: csv, xlsx, json, parquet等")

    # 数据元信息
    row_count: Optional[int] = Field(default=None, description="行数")
    column_count: Optional[int] = Field(default=None, description="列数")
    columns: List[str] = Field(default_factory=list, description="列名列表")
    column_types: Dict[str, str] = Field(default_factory=dict, description="列类型映射")

    # 数据摘要统计
    sample_values: Dict[str, List[Any]] = Field(default_factory=dict, description="各列的样本值")
    numeric_summary: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="数值列的统计摘要")
    missing_values: Dict[str, int] = Field(default_factory=dict, description="各列的缺失值数量")

    # 语义信息
    keywords: List[str] = Field(default_factory=list, description="关键词标签")
    domain: Optional[str] = Field(default=None, description="数据领域: 经济、金融、社会等")
    time_range: Optional[str] = Field(default=None, description="时间范围")
    geographic_scope: Optional[str] = Field(default=None, description="地理范围")

    # 研究相关
    suggested_uses: List[str] = Field(default_factory=list, description="建议的使用场景")
    related_variables: Dict[str, str] = Field(default_factory=dict, description="相关变量说明")
    data_quality_notes: Optional[str] = Field(default=None, description="数据质量备注")

    # 元数据
    source: str = Field(default="manual", description="来源: manual, import, scan")
    added_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="添加时间")
    updated_at: Optional[str] = Field(default=None, description="更新时间")
    tags: List[str] = Field(default_factory=list, description="自定义标签")
    notes: Optional[str] = Field(default=None, description="备注")


class DataSearchResult(BaseModel):
    """数据搜索结果"""
    items: List[StoredDataItem] = Field(description="匹配的数据列表")
    total_count: int = Field(description="总匹配数")
    query: str = Field(description="查询内容")
    search_type: str = Field(description="搜索类型: semantic, keyword, hybrid")


# ==================== 数据存储工具 ====================

class DataStorageTool:
    """
    数据存储与检索工具

    功能:
    1. 存储数据摘要到向量数据库(RAG)和JSON备份
    2. 语义搜索(基于embedding相似度)找到合适的数据集
    3. 关键词搜索
    4. 混合搜索
    5. 手动添加数据集信息
    6. 自动扫描目录导入数据集

    使用场景:
    - Agent需要找到合适的数据进行分析时，可以通过语义搜索快速定位
    - 支持自然语言查询，如"需要企业创新相关的面板数据"
    """

    def __init__(
        self,
        storage_dir: str = "data/datasets",
        collection_name: str = "research_datasets",
        embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    ):
        """
        初始化数据存储工具

        Args:
            storage_dir: 存储目录
            collection_name: ChromaDB集合名称
            embedding_model: 嵌入模型名称(支持中英文)
        """
        self.storage_dir = Path(storage_dir)
        self.backup_dir = self.storage_dir / "metadata"
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
                logger.info(f"[DataStorage] 嵌入模型加载成功: {embedding_model}")
            except Exception as e:
                logger.warning(f"[DataStorage] 嵌入模型加载失败: {e}")

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
                    metadata={"description": "Research datasets collection for RAG"}
                )
                logger.info(f"[DataStorage] ChromaDB初始化成功，集合: {collection_name}")
            except Exception as e:
                logger.error(f"[DataStorage] ChromaDB初始化失败: {e}")

        # 加载现有索引
        self.index_file = self.storage_dir / "data_index.json"
        self.index = self._load_index()

        logger.info(f"[DataStorage] 数据存储工具初始化完成，已有 {len(self.index.get('items', {}))} 个数据集")

    def _load_index(self) -> Dict[str, Any]:
        """加载数据索引"""
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"items": {}, "stats": {"total": 0, "by_type": {}, "by_domain": {}}}

    def _save_index(self):
        """保存数据索引"""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)

    def _generate_id(self, item: Union[StoredDataItem, Dict]) -> str:
        """生成数据唯一ID"""
        if isinstance(item, dict):
            name = item.get('name', '')
            file_path = item.get('file_path', '')
        else:
            name = item.name
            file_path = item.file_path

        content = f"{name}_{file_path}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _create_document_text(self, item: StoredDataItem) -> str:
        """创建用于嵌入的文档文本"""
        parts = [
            f"数据集名称: {item.name}",
            f"描述: {item.description}",
        ]

        if item.columns:
            parts.append(f"包含字段: {', '.join(item.columns[:20])}")  # 限制字段数量
        if item.keywords:
            parts.append(f"关键词: {', '.join(item.keywords)}")
        if item.domain:
            parts.append(f"领域: {item.domain}")
        if item.time_range:
            parts.append(f"时间范围: {item.time_range}")
        if item.geographic_scope:
            parts.append(f"地理范围: {item.geographic_scope}")
        if item.suggested_uses:
            parts.append(f"适用场景: {', '.join(item.suggested_uses)}")
        if item.related_variables:
            vars_desc = "; ".join([f"{k}: {v}" for k, v in item.related_variables.items()])
            parts.append(f"相关变量: {vars_desc}")
        if item.row_count:
            parts.append(f"数据量: {item.row_count}行")

        return "\n".join(parts)

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """获取文本嵌入向量"""
        if self.embedding_model:
            return self.embedding_model.encode(text).tolist()
        return None

    def _extract_data_summary(self, file_path: str) -> Dict[str, Any]:
        """
        从数据文件中提取摘要信息

        Args:
            file_path: 数据文件路径

        Returns:
            数据摘要信息
        """
        summary = {}
        path = Path(file_path)

        if not path.exists():
            logger.warning(f"[DataStorage] 文件不存在: {file_path}")
            return summary

        if not PANDAS_AVAILABLE:
            logger.warning("[DataStorage] pandas未安装，无法提取数据摘要")
            return summary

        try:
            # 根据文件类型读取
            suffix = path.suffix.lower()
            if suffix == '.csv':
                df = pd.read_csv(file_path, encoding='utf-8-sig', nrows=1000)  # 先读取1000行
                df_full = pd.read_csv(file_path, encoding='utf-8-sig')
            elif suffix in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path, nrows=1000)
                df_full = pd.read_excel(file_path)
            elif suffix == '.json':
                df_full = pd.read_json(file_path)
                df = df_full.head(1000)
            elif suffix == '.parquet':
                df_full = pd.read_parquet(file_path)
                df = df_full.head(1000)
            else:
                logger.warning(f"[DataStorage] 不支持的文件类型: {suffix}")
                return summary

            # 基本信息
            summary['row_count'] = len(df_full)
            summary['column_count'] = len(df_full.columns)
            summary['columns'] = list(df_full.columns)
            summary['column_types'] = {col: str(dtype) for col, dtype in df_full.dtypes.items()}

            # 缺失值统计
            summary['missing_values'] = {col: int(df_full[col].isna().sum()) for col in df_full.columns}

            # 样本值（每列取前5个非空值）
            summary['sample_values'] = {}
            for col in df_full.columns:
                non_null = df_full[col].dropna().head(5).tolist()
                summary['sample_values'][col] = [str(v)[:100] for v in non_null]  # 限制长度

            # 数值列统计
            summary['numeric_summary'] = {}
            numeric_cols = df_full.select_dtypes(include=['number']).columns
            for col in numeric_cols:
                try:
                    summary['numeric_summary'][col] = {
                        'mean': float(df_full[col].mean()),
                        'std': float(df_full[col].std()),
                        'min': float(df_full[col].min()),
                        'max': float(df_full[col].max()),
                        'median': float(df_full[col].median())
                    }
                except Exception:
                    pass

            logger.info(f"[DataStorage] 成功提取数据摘要: {path.name} ({summary['row_count']}行 x {summary['column_count']}列)")

        except Exception as e:
            logger.error(f"[DataStorage] 提取数据摘要失败: {e}")

        return summary

    # ==================== 核心功能 ====================

    def add_data(
        self,
        item: Union[StoredDataItem, Dict[str, Any]],
        auto_extract_summary: bool = True,
        source: str = "manual"
    ) -> str:
        """
        添加数据集信息

        Args:
            item: 数据项(Pydantic模型或字典)
            auto_extract_summary: 是否自动提取数据摘要
            source: 来源标识

        Returns:
            数据ID
        """
        logger.info(f"[DataStorage] 开始添加数据集...")

        # 确保是字典
        if isinstance(item, StoredDataItem):
            item_dict = item.model_dump()
        else:
            item_dict = item.copy()

        # 生成ID
        item_id = self._generate_id(item_dict)
        item_dict['id'] = item_id
        item_dict['source'] = source

        if 'added_at' not in item_dict:
            item_dict['added_at'] = datetime.now().isoformat()

        # 自动提取数据摘要
        if auto_extract_summary and item_dict.get('file_path'):
            file_path = item_dict['file_path']
            if Path(file_path).exists():
                summary = self._extract_data_summary(file_path)
                # 合并摘要（不覆盖已有值）
                for key, value in summary.items():
                    if key not in item_dict or not item_dict[key]:
                        item_dict[key] = value

        # 推断文件类型
        if item_dict.get('file_path') and not item_dict.get('file_type'):
            suffix = Path(item_dict['file_path']).suffix.lower()
            item_dict['file_type'] = suffix.lstrip('.')

        # 验证并创建Pydantic模型
        validated_item = StoredDataItem(**item_dict)

        # 1. 保存到JSON备份
        backup_file = self.backup_dir / f"{item_id}.json"
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(validated_item.model_dump(), f, ensure_ascii=False, indent=2)

        # 2. 更新索引
        self.index["items"][item_id] = {
            "name": validated_item.name,
            "description": validated_item.description[:200] if validated_item.description else "",
            "file_path": validated_item.file_path,
            "file_type": validated_item.file_type,
            "row_count": validated_item.row_count,
            "column_count": validated_item.column_count,
            "domain": validated_item.domain,
            "added_at": validated_item.added_at,
            "source": validated_item.source,
            "tags": validated_item.tags
        }
        self.index["stats"]["total"] = len(self.index["items"])

        # 统计文件类型
        file_type = validated_item.file_type or "unknown"
        self.index["stats"]["by_type"][file_type] = self.index["stats"]["by_type"].get(file_type, 0) + 1

        # 统计领域
        if validated_item.domain:
            self.index["stats"]["by_domain"][validated_item.domain] = \
                self.index["stats"]["by_domain"].get(validated_item.domain, 0) + 1

        self._save_index()

        # 3. 添加到向量数据库
        if self.collection is not None:
            doc_text = self._create_document_text(validated_item)
            embedding = self._get_embedding(doc_text)

            try:
                metadata_to_store = {
                    "name": validated_item.name,
                    "file_path": validated_item.file_path,
                    "file_type": validated_item.file_type or "",
                    "domain": validated_item.domain or "",
                    "source": validated_item.source,
                    "tags": ",".join(validated_item.tags),
                    "row_count": validated_item.row_count or 0
                }
                if embedding:
                    self.collection.add(
                        ids=[item_id],
                        documents=[doc_text],
                        embeddings=[embedding],
                        metadatas=[metadata_to_store]
                    )
                else:
                    self.collection.add(
                        ids=[item_id],
                        documents=[doc_text],
                        metadatas=[metadata_to_store]
                    )
                logger.info(f"[DataStorage] 数据集已添加到向量数据库: {validated_item.name}")
            except Exception as e:
                logger.error(f"[DataStorage] 添加到向量数据库失败: {e}")

        logger.info(f"[DataStorage] 数据集添加成功: [{item_id}] {validated_item.name}")
        return item_id

    def add_data_batch(
        self,
        items: List[Union[StoredDataItem, Dict[str, Any]]],
        auto_extract_summary: bool = True,
        source: str = "batch_import"
    ) -> List[str]:
        """
        批量添加数据集

        Args:
            items: 数据列表
            auto_extract_summary: 是否自动提取摘要
            source: 来源标识

        Returns:
            数据ID列表
        """
        ids = []
        for item in items:
            try:
                item_id = self.add_data(item, auto_extract_summary, source)
                ids.append(item_id)
            except Exception as e:
                logger.error(f"[DataStorage] 批量添加失败: {e}")

        logger.info(f"[DataStorage] 批量添加完成: {len(ids)}/{len(items)} 个数据集")
        return ids

    def search_semantic(
        self,
        query: str,
        n_results: int = 10,
        filter_domain: Optional[str] = None,
        filter_type: Optional[str] = None
    ) -> DataSearchResult:
        """
        语义搜索(基于向量相似度)

        使用自然语言描述你需要的数据，例如:
        - "需要企业创新相关的面板数据"
        - "包含GDP和人口的省级数据"
        - "上市公司财务数据"

        Args:
            query: 查询文本
            n_results: 返回结果数
            filter_domain: 领域过滤
            filter_type: 文件类型过滤

        Returns:
            搜索结果
        """
        logger.info(f"[DataStorage] 语义搜索: {query}")

        if self.collection is None:
            logger.warning("[DataStorage] 向量数据库不可用，无法进行语义搜索")
            return DataSearchResult(items=[], total_count=0, query=query, search_type="semantic")

        # 构建过滤条件
        where_filter = {}
        if filter_domain:
            where_filter["domain"] = filter_domain
        if filter_type:
            where_filter["file_type"] = filter_type

        try:
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

            # 加载完整数据信息
            items = []
            if results['ids'] and results['ids'][0]:
                for item_id in results['ids'][0]:
                    item = self.get_data(item_id)
                    if item:
                        items.append(item)

            logger.info(f"[DataStorage] 语义搜索找到 {len(items)} 个匹配数据集")
            return DataSearchResult(
                items=items,
                total_count=len(items),
                query=query,
                search_type="semantic"
            )

        except Exception as e:
            logger.error(f"[DataStorage] 语义搜索失败: {e}")
            return DataSearchResult(items=[], total_count=0, query=query, search_type="semantic")

    def search_keyword(
        self,
        keyword: str,
        fields: List[str] = None,
        n_results: int = 10
    ) -> DataSearchResult:
        """
        关键词搜索(精确匹配)

        Args:
            keyword: 关键词
            fields: 搜索字段
            n_results: 返回结果数

        Returns:
            搜索结果
        """
        logger.info(f"[DataStorage] 关键词搜索: {keyword}")

        if fields is None:
            fields = ["name", "description", "columns", "keywords", "domain", "tags"]

        keyword_lower = keyword.lower()
        matched_items = []

        for item_id in self.index["items"]:
            item = self.get_data(item_id)
            if item is None:
                continue

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

        logger.info(f"[DataStorage] 关键词搜索找到 {len(matched_items)} 个匹配数据集")
        return DataSearchResult(
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
    ) -> DataSearchResult:
        """
        混合搜索(语义+关键词)

        Args:
            query: 查询内容
            n_results: 返回结果数
            semantic_weight: 语义搜索权重

        Returns:
            搜索结果
        """
        logger.info(f"[DataStorage] 混合搜索: {query}")

        semantic_results = self.search_semantic(query, n_results * 2)
        keyword_results = self.search_keyword(query, n_results=n_results * 2)

        # 合并结果(去重)
        seen_ids = set()
        merged_items = []

        for item in semantic_results.items:
            if item.id not in seen_ids:
                seen_ids.add(item.id)
                merged_items.append(item)

        for item in keyword_results.items:
            if item.id not in seen_ids:
                seen_ids.add(item.id)
                merged_items.append(item)

        logger.info(f"[DataStorage] 混合搜索找到 {len(merged_items)} 个匹配数据集")
        return DataSearchResult(
            items=merged_items[:n_results],
            total_count=len(merged_items),
            query=query,
            search_type="hybrid"
        )

    def get_data(self, item_id: str) -> Optional[StoredDataItem]:
        """
        获取数据集详情

        Args:
            item_id: 数据ID

        Returns:
            数据详情
        """
        backup_file = self.backup_dir / f"{item_id}.json"
        if backup_file.exists():
            with open(backup_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return StoredDataItem(**data)
        return None

    def delete_data(self, item_id: str) -> bool:
        """
        删除数据集记录

        Args:
            item_id: 数据ID

        Returns:
            是否成功
        """
        logger.info(f"[DataStorage] 删除数据集: {item_id}")

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
                logger.error(f"[DataStorage] 从向量数据库删除失败: {e}")

        logger.info(f"[DataStorage] 数据集已删除: {item_id}")
        return True

    def update_data(
        self,
        item_id: str,
        updates: Dict[str, Any]
    ) -> Optional[StoredDataItem]:
        """
        更新数据集信息

        Args:
            item_id: 数据ID
            updates: 更新内容

        Returns:
            更新后的数据
        """
        item = self.get_data(item_id)
        if item is None:
            return None

        item_dict = item.model_dump()
        item_dict.update(updates)
        item_dict['updated_at'] = datetime.now().isoformat()

        # 删除旧记录
        self.delete_data(item_id)

        # 添加新记录
        new_item = StoredDataItem(**item_dict)
        self.add_data(new_item, auto_extract_summary=False, source="update")

        return new_item

    def list_all(
        self,
        sort_by: str = "added_at",
        descending: bool = True,
        limit: int = 100
    ) -> List[StoredDataItem]:
        """
        列出所有数据集

        Args:
            sort_by: 排序字段
            descending: 是否降序
            limit: 返回数量限制

        Returns:
            数据列表
        """
        items = []
        for item_id in self.index["items"]:
            item = self.get_data(item_id)
            if item:
                items.append(item)

        items.sort(
            key=lambda x: getattr(x, sort_by, "") or "",
            reverse=descending
        )

        return items[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_count": self.index["stats"]["total"],
            "by_type": self.index["stats"]["by_type"],
            "by_domain": self.index["stats"]["by_domain"],
            "storage_path": str(self.storage_dir),
            "chroma_available": self.collection is not None,
            "embedding_model": self.embedding_model_name if self.embedding_model else "default"
        }

    # ==================== 扫描导入 ====================

    def scan_directory(
        self,
        directory: str,
        patterns: List[str] = None,
        recursive: bool = True,
        auto_extract: bool = True
    ) -> Dict[str, Any]:
        """
        扫描目录并导入数据集

        Args:
            directory: 目录路径
            patterns: 文件模式列表，如 ["*.csv", "*.xlsx"]
            recursive: 是否递归扫描
            auto_extract: 是否自动提取摘要

        Returns:
            扫描结果统计
        """
        logger.info(f"[DataStorage] 开始扫描目录: {directory}")

        if patterns is None:
            patterns = ["*.csv", "*.xlsx", "*.xls", "*.json", "*.parquet"]

        dir_path = Path(directory)
        if not dir_path.exists():
            logger.error(f"[DataStorage] 目录不存在: {directory}")
            return {"success": False, "error": "目录不存在"}

        stats = {
            "total_files": 0,
            "imported": 0,
            "skipped": 0,
            "errors": 0,
            "imported_ids": []
        }

        # 收集所有匹配文件
        files = []
        for pattern in patterns:
            if recursive:
                files.extend(dir_path.rglob(pattern))
            else:
                files.extend(dir_path.glob(pattern))

        stats["total_files"] = len(files)
        logger.info(f"[DataStorage] 找到 {len(files)} 个数据文件")

        for file_path in files:
            try:
                # 检查是否已存在
                existing_id = self._generate_id({"name": file_path.stem, "file_path": str(file_path)})
                if existing_id in self.index["items"]:
                    logger.debug(f"[DataStorage] 跳过已存在: {file_path.name}")
                    stats["skipped"] += 1
                    continue

                # 创建数据项
                item_data = {
                    "name": file_path.stem,
                    "description": f"从 {file_path.parent.name} 目录导入的数据文件",
                    "file_path": str(file_path.absolute()),
                    "file_type": file_path.suffix.lstrip('.'),
                    "tags": ["自动导入", file_path.parent.name]
                }

                item_id = self.add_data(item_data, auto_extract_summary=auto_extract, source="scan")
                stats["imported_ids"].append(item_id)
                stats["imported"] += 1

            except Exception as e:
                logger.error(f"[DataStorage] 导入失败 {file_path}: {e}")
                stats["errors"] += 1

        stats["success"] = True
        logger.info(
            f"[DataStorage] 扫描完成: 总计 {stats['total_files']} 个文件, "
            f"导入 {stats['imported']}, 跳过 {stats['skipped']}, 错误 {stats['errors']}"
        )

        return stats


# ==================== 便捷函数 ====================

def get_data_storage(
    storage_dir: str = "data/datasets"
) -> DataStorageTool:
    """
    获取数据存储工具实例

    Args:
        storage_dir: 存储目录

    Returns:
        数据存储工具实例
    """
    return DataStorageTool(storage_dir=storage_dir)
