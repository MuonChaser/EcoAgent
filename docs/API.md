# API 文档

## ResearchOrchestrator

主研究编排器类，负责协调所有智能体完成研究流程。

### 初始化

```python
ResearchOrchestrator(output_dir: str = "output")
```

**参数：**
- `output_dir` (str): 输出目录路径，默认为 "output"

### run_full_pipeline

运行完整的研究流程。

```python
run_full_pipeline(
    research_topic: str,
    keyword_group_a: List[str],
    keyword_group_b: List[str],
    min_papers: int = 10,
    data_info: Optional[str] = None,
    word_count: int = 8000,
    enable_steps: Optional[List[str]] = None,
) -> Dict[str, Any]
```

**参数：**
- `research_topic` (str): 研究主题
- `keyword_group_a` (List[str]): 关键词组A（核心解释变量相关）
- `keyword_group_b` (List[str]): 关键词组B（被解释变量相关）
- `min_papers` (int): 最少文献数量，默认10
- `data_info` (Optional[str]): 数据信息描述
- `word_count` (int): 最终报告字数，默认8000
- `enable_steps` (Optional[List[str]]): 启用的步骤列表，None表示全部启用
  - 可选值: `["literature", "variable", "theory", "model", "analysis", "report"]`

**返回：**
- `Dict[str, Any]`: 包含所有阶段结果的字典
  - `research_topic`: 研究主题
  - `literature_summary`: 文献综述
  - `variable_system`: 变量体系
  - `theory_framework`: 理论框架
  - `model_design`: 模型设计
  - `data_analysis`: 数据分析
  - `final_report`: 完整报告
  - `report_path`: 报告文件路径
  - `json_path`: JSON备份路径

**示例：**
```python
orchestrator = ResearchOrchestrator()

results = orchestrator.run_full_pipeline(
    research_topic="绿色债券对企业业绩的影响",
    keyword_group_a=["绿色债券", "Green Bond"],
    keyword_group_b=["企业业绩", "Firm Performance"],
    min_papers=10,
    word_count=8000,
)
```

### run_single_step

运行单个研究步骤。

```python
run_single_step(
    step: str,
    input_data: Dict[str, Any]
) -> Dict[str, Any]
```

**参数：**
- `step` (str): 步骤名称
  - `"literature"`: 文献搜集
  - `"variable"`: 变量设计
  - `"theory"`: 理论构建
  - `"model"`: 模型设计
  - `"analysis"`: 数据分析
  - `"report"`: 报告撰写
- `input_data` (Dict[str, Any]): 该步骤所需的输入数据

**返回：**
- `Dict[str, Any]`: 该步骤的执行结果

**示例：**
```python
result = orchestrator.run_single_step(
    step="literature",
    input_data={
        "research_topic": "AI在经济学中的应用",
        "keyword_group_a": ["AI", "机器学习"],
        "keyword_group_b": ["经济学", "计量分析"],
        "min_papers": 10,
    }
)
```

---

## SimplifiedOrchestrator

简化的编排器，提供更便捷的接口。

### quick_research

快速研究接口，自动解析关键词。

```python
quick_research(
    topic: str,
    keywords_a: str,
    keywords_b: str,
) -> str
```

**参数：**
- `topic` (str): 研究主题
- `keywords_a` (str): 关键词组A，用逗号、顿号或中文逗号分隔
- `keywords_b` (str): 关键词组B，用逗号、顿号或中文逗号分隔

**返回：**
- `str`: 生成的报告文件路径

**示例：**
```python
simple = SimplifiedOrchestrator()

report_path = simple.quick_research(
    topic="数字经济对产业升级的影响",
    keywords_a="数字经济,数字化转型,数字技术",
    keywords_b="产业升级,结构调整,转型升级"
)
```

---

## 智能体基类 (BaseAgent)

所有智能体的抽象基类。

### 初始化

```python
BaseAgent(
    agent_type: str,
    custom_config: Optional[Dict[str, Any]] = None
)
```

**参数：**
- `agent_type` (str): 智能体类型
- `custom_config` (Optional[Dict[str, Any]]): 自定义配置

### run

执行智能体任务。

```python
run(input_data: Dict[str, Any]) -> Dict[str, Any]
```

**参数：**
- `input_data` (Dict[str, Any]): 输入数据

**返回：**
- `Dict[str, Any]`: 执行结果

---

## LiteratureCollectorAgent

文献搜集专家智能体。

### 输入数据格式

```python
{
    "research_topic": str,           # 研究主题
    "keyword_group_a": List[str],    # 关键词组A
    "keyword_group_b": List[str],    # 关键词组B
    "min_papers": int,               # 最少文献数量
}
```

### 输出数据格式

```python
{
    "agent_type": "literature_collector",
    "agent_name": "文献搜集专家",
    "literature_summary": str,       # 文献综述（表格形式）
    "research_topic": str,
    ...
}
```

---

## VariableDesignerAgent

指标设置专家智能体。

### 输入数据格式

```python
{
    "research_topic": str,           # 研究主题
    "literature_summary": str,       # 文献综述（可选）
}
```

### 输出数据格式

```python
{
    "agent_type": "variable_designer",
    "agent_name": "指标设置专家",
    "variable_system": str,          # 变量体系设计
    "research_topic": str,
    ...
}
```

---

## TheoryDesignerAgent

理论设置专家智能体。

### 输入数据格式

```python
{
    "research_topic": str,           # 研究主题
    "variable_system": str,          # 变量体系（可选）
    "literature_summary": str,       # 文献综述（可选）
}
```

### 输出数据格式

```python
{
    "agent_type": "theory_designer",
    "agent_name": "理论设置专家",
    "theory_framework": str,         # 理论框架与假设
    "research_topic": str,
    ...
}
```

---

## ModelDesignerAgent

计量模型专家智能体。

### 输入数据格式

```python
{
    "research_topic": str,           # 研究主题
    "variable_system": str,          # 变量体系（可选）
    "theory_framework": str,         # 理论框架（可选）
}
```

### 输出数据格式

```python
{
    "agent_type": "model_designer",
    "agent_name": "计量模型专家",
    "model_design": str,             # 模型设计（LaTeX格式）
    "research_topic": str,
    ...
}
```

---

## DataAnalystAgent

数据分析专家智能体。

### 输入数据格式

```python
{
    "research_topic": str,           # 研究主题
    "variable_system": str,          # 变量体系（可选）
    "theory_framework": str,         # 理论框架（可选）
    "model_design": str,             # 模型设计（可选）
    "data_info": str,                # 数据信息（可选）
}
```

### 输出数据格式

```python
{
    "agent_type": "data_analyst",
    "agent_name": "数据分析专家",
    "data_analysis": str,            # 数据分析结果
    "research_topic": str,
    ...
}
```

---

## ReportWriterAgent

长文报告专家智能体。

### 输入数据格式

```python
{
    "research_topic": str,           # 研究主题
    "literature_summary": str,       # 文献综述（可选）
    "variable_system": str,          # 变量体系（可选）
    "theory_framework": str,         # 理论框架（可选）
    "model_design": str,             # 模型设计（可选）
    "data_analysis": str,            # 数据分析（可选）
    "word_count": int,               # 字数要求
}
```

### 输出数据格式

```python
{
    "agent_type": "report_writer",
    "agent_name": "长文报告专家",
    "final_report": str,             # 完整论文
    "research_topic": str,
    "word_count": int,
    ...
}
```

---

## 工具类

### LiteratureSearchTool

文献搜索工具。

```python
tool = LiteratureSearchTool()

# 搜索 arXiv
papers = tool.search_arxiv("green bond", max_results=10)

# 格式化文献信息
formatted = tool.format_literature_info(papers)
```

### DataProcessingTool

数据处理工具。

```python
tool = DataProcessingTool()

# 数据清洗
cleaned_data = tool.clean_data(data, method="drop")

# 缩尾处理
winsorized_data = tool.winsorize_data(data, limits=(0.01, 0.01))

# 标准化
standardized_data = tool.standardize_data(data)
```

### StatisticalAnalysisTool

统计分析工具。

```python
tool = StatisticalAnalysisTool()

# 描述性统计
stats = tool.descriptive_statistics(data)

# 相关性分析
corr = tool.correlation_analysis(data, method="pearson")

# 回归分析
results = tool.regression_analysis(y, X, model_type="ols")
```

### OutputFormatter

输出格式化工具。

```python
formatter = OutputFormatter()

# 转换为Markdown
markdown = formatter.format_to_markdown(content, title="研究报告")

# 保存文件
formatter.save_to_file(content, "output/report.md", format="md")

# 创建表格
table = formatter.create_table(data, headers=["列1", "列2"])
```

### ReportGenerator

报告生成器。

```python
generator = ReportGenerator(output_dir="output")

# 生成完整报告
report_path = generator.generate_full_report(
    research_topic="研究主题",
    results=results,
    format="markdown"
)

# 生成摘要
summary = generator.generate_summary(results)
```

---

## 配置选项

### 环境变量 (.env)

```
# OpenAI API配置
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1

# 模型配置
DEFAULT_MODEL=gpt-4-turbo-preview
TEMPERATURE=0.7

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/econometrics_agent.log

# 目录配置
DATA_DIR=data
OUTPUT_DIR=output
```

### 智能体配置 (config/config.py)

```python
AGENT_CONFIG = {
    "literature_collector": {
        "name": "文献搜集专家",
        "model": "gpt-4-turbo-preview",
        "temperature": 0.3,
    },
    # ... 其他智能体配置
}
```

---

## 错误处理

所有智能体和工具类都使用 `loguru` 进行日志记录。错误会被记录到日志文件中。

```python
from loguru import logger

try:
    results = orchestrator.run_full_pipeline(...)
except Exception as e:
    logger.error(f"执行失败: {str(e)}")
```

---

## 最佳实践

1. **始终检查输入数据**：确保必需的参数都已提供
2. **使用阶段性保存**：系统会自动保存各阶段结果
3. **自定义配置**：根据具体需求调整温度和模型参数
4. **错误恢复**：利用阶段性保存的结果，可以从中断处继续
