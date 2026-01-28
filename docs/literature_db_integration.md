# 文献搜集器本地数据库集成指南

## 问题背景

之前 `LiteratureCollectorAgent` 不调用本地文献数据库进行检索，每次都依赖 LLM 生成文献列表，导致：
- 无法复用已有的文献资源
- 生成的文献可能存在准确性问题
- 浪费 API 调用成本

## 解决方案

通过以下改进，现在 `LiteratureCollectorAgent` 能够**自动检索本地文献数据库**：

### 1. 创建 `ToolAgent` 基类

**文件**: `agents/tool_agent.py`

- 扩展 `BaseAgent`，添加工具调用能力
- 支持 LangChain 的 `bind_tools` 机制
- 实现 agent loop，自动执行工具调用

### 2. 升级 `LiteratureCollectorAgent`

**文件**: `agents/literature_collector.py`

**改动**:
- 继承 `ToolAgent` 而非 `BaseAgent`
- 集成 `LiteratureStorageTool` 作为可用工具
- 提供 3 个工具给 Agent:
  1. `search_literature_semantic`: 语义搜索本地数据库
  2. `search_literature_keyword`: 关键词搜索
  3. `get_literature_stats`: 获取数据库统计信息

### 3. 更新 Prompt

**文件**: `prompts/literature_collector.py`

**改动**:
- 在系统 prompt 中说明可以使用本地数据库工具
- 在任务 prompt 中添加明确的工作流程：
  1. **先检查本地数据库** (使用工具)
  2. 如果数据库文献不足，再补充

## 使用方法

### 基础使用

```python
from agents import LiteratureCollectorAgent

# 初始化 Agent (会自动连接本地数据库)
agent = LiteratureCollectorAgent(
    literature_storage_dir="data/literature"  # 数据库路径
)

# 运行任务
result = agent.run({
    "research_topic": "环境监管对企业全要素生产率的影响",
    "keyword_group_a": ["环境监管", "环境规制"],
    "keyword_group_b": ["全要素生产率", "TFP"],
    "min_papers": 10
})

# 查看工具调用情况
for call in result.get("tool_calls", []):
    print(f"调用工具: {call['tool']}, 参数: {call['args']}")
```

### 准备本地文献数据库

#### 方法1: 手动添加文献

```python
from tools.literature_storage import get_literature_storage

# 获取存储工具
lit_storage = get_literature_storage("data/literature")

# 添加文献
lit_storage.add_literature({
    "authors": "Porter, M. E.",
    "year": 1995,
    "title": "Toward a New Conception...",
    "journal": "Journal of Economic Perspectives",
    "variable_x_definition": "环境监管严格程度",
    "variable_y_definition": "企业竞争力",
    "core_conclusion": "严格的环境监管能够促进企业创新...",
    # ... 更多字段
})
```

#### 方法2: 从 CSV 导入

```python
# 从实证论文CSV导入
stats = lit_storage.import_from_csv(
    "data/实证论文提取结果.csv",
    research_project="我的研究项目"
)

print(f"导入 {stats['imported']} 篇文献")
```

#### 方法3: 保存之前的搜集结果

```python
# 运行一次 LiteratureCollectorAgent
result = agent.run({...})

# 将结果保存到数据库
lit_storage.import_from_literature_collector(
    result,
    research_project="环境监管研究"
)
```

### 查询本地数据库

```python
# 语义搜索
results = lit_storage.search_semantic(
    "数字化转型对企业创新的影响",
    n_results=10
)

# 关键词搜索
results = lit_storage.search_keyword("全要素生产率")

# 获取统计信息
stats = lit_storage.get_statistics()
print(f"总文献数: {stats['total_count']}")
print(f"按年份分布: {stats['by_year']}")
```

## 完整示例

运行示例脚本：

```bash
python examples/literature_collector_with_db_example.py
```

该示例会：
1. 准备一些示例文献数据
2. 运行 `LiteratureCollectorAgent`
3. 显示 Agent 如何自动调用工具检索本地数据库
4. 展示最终搜集的文献列表

## Agent 工作流程

当你运行 `LiteratureCollectorAgent` 时：

1. **初始化阶段**
   - Agent 连接本地文献数据库
   - 如果数据库可用，绑定 3 个检索工具

2. **执行阶段**
   - Agent 收到任务后，根据 prompt 指引
   - 首先调用 `get_literature_stats` 了解数据库状态
   - 然后调用 `search_literature_semantic` 搜索相关文献
   - 使用 `search_literature_keyword` 搜索特定关键词
   - 整理从数据库获取的文献

3. **补充阶段**
   - 如果本地文献不足（< min_papers）
   - Agent 会基于知识补充高质量文献
   - 确保最终文献数量满足要求

4. **输出阶段**
   - 返回结构化的文献列表
   - 包含工具调用记录（`tool_calls` 字段）

## 日志示例

运行时你会看到类似的日志：

```
09:00:00 | INFO     | 文献数据库已连接，共 15 篇文献
09:00:00 | INFO     | 文献搜集专家 已绑定 3 个工具: ['search_literature_semantic', 'search_literature_keyword', 'get_literature_stats']
09:00:01 | INFO     | 文献搜集专家 调用工具: get_literature_stats，参数: {}
09:00:01 | INFO     | 文献搜集专家 工具 get_literature_stats 执行成功
09:00:02 | INFO     | 文献搜集专家 调用工具: search_literature_semantic，参数: {'query': '环境监管对企业全要素生产率的影响', 'n_results': 10}
09:00:02 | INFO     | 文献搜集专家 工具 search_literature_semantic 执行成功
09:00:03 | INFO     | 文献搜集专家 完成，共执行 3 次迭代，调用了 3 个工具
```

## 技术细节

### 工具定义

每个工具都有清晰的描述，告诉 LLM 何时使用：

```python
Tool(
    name="search_literature_semantic",
    description="""在本地文献数据库中进行语义搜索。
    输入参数:
    - query: 搜索查询（中文或英文）
    - n_results: 返回结果数量（默认10）

    返回: 匹配的文献列表...

    使用场景: 当需要搜索特定主题的文献时，使用此工具先检查本地数据库。""",
    func=lambda query, n_results=10: self._search_literature_semantic(query, n_results)
)
```

### Agent Loop

`ToolAgent` 实现了标准的 agent loop：

1. 调用 LLM (带工具绑定)
2. 检查响应中的 `tool_calls`
3. 如果有工具调用，执行工具并将结果返回给 LLM
4. 继续循环，直到 LLM 返回最终答案
5. 最多迭代 10 次防止死循环

### 数据库技术栈

- **向量数据库**: ChromaDB (持久化)
- **嵌入模型**: `paraphrase-multilingual-MiniLM-L12-v2` (支持中英文)
- **搜索方式**: 语义搜索 + 关键词搜索 + 混合搜索

## 故障排查

### 问题1: Agent 不调用工具

**可能原因**:
- 本地数据库不可用（ChromaDB 或 sentence-transformers 未安装）
- 数据库目录不存在或权限问题

**解决方法**:
```bash
# 安装依赖
pip install chromadb sentence-transformers

# 检查日志
# 应该看到: "文献数据库已连接，共 X 篇文献"
# 如果看到警告，说明数据库初始化失败
```

### 问题2: 搜索结果为空

**可能原因**:
- 数据库中没有相关文献
- 查询与文献的语义相似度太低

**解决方法**:
- 先导入一些相关领域的文献
- 使用 `get_literature_stats` 查看数据库内容
- 尝试调整搜索关键词

### 问题3: 工具调用失败

**可能原因**:
- 嵌入模型加载失败
- 数据库文件损坏

**解决方法**:
- 检查日志中的错误信息
- 必要时删除 `data/literature/chroma_db` 重新初始化

## 后续优化建议

1. **增加更多工具**:
   - 按期刊筛选
   - 按年份范围筛选
   - 导出文献到 BibTeX

2. **改进搜索算法**:
   - 混合语义搜索和关键词搜索
   - 添加重排序(reranking)

3. **自动保存结果**:
   - Agent 运行后自动将新文献保存到数据库
   - 避免重复生成相同文献

4. **文献去重**:
   - 检测数据库中已有文献
   - 避免重复添加

## 相关文件

- `agents/tool_agent.py` - 支持工具的 Agent 基类
- `agents/literature_collector.py` - 文献搜集 Agent (已升级)
- `tools/literature_storage.py` - 文献存储和检索工具
- `prompts/literature_collector.py` - Prompt 模板 (已更新)
- `examples/literature_collector_with_db_example.py` - 使用示例

## 总结

通过本次改进，`LiteratureCollectorAgent` 现在能够：
- ✅ 自动检索本地文献数据库
- ✅ 优先使用已有文献，减少 LLM 调用
- ✅ 支持语义搜索和关键词搜索
- ✅ 提供详细的工具调用日志
- ✅ 灵活补充不足的文献

这大大提高了文献搜集的效率和准确性！
