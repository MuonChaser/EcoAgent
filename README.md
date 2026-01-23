# AI for Econometrics 多智能体研究系统

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-latest-green.svg)](https://github.com/langchain-ai/langchain)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

基于 LangChain 框架构建的多智能体系统，专门用于计量经济学研究的全流程自动化。该系统将传统计量经济学研究流程分解为6个专业智能体，协同完成从文献综述到论文撰写的完整研究过程。

## 🌟 核心特性

- **模块化设计**：8个专业智能体（0输入解析→6核心研究→7审稿评审），职责明确，易于扩展
- **完整工作流**：覆盖输入理解、文献搜集、变量设计、理论构建、模型设计、数据分析、报告撰写、成果评审
- **JSON格式化输出**：所有智能体强制输出结构化JSON数据，避免表格混乱，确保数据流规范
- **智能输入解析**：支持自然语言输入（如"我想研究X对Y的影响"），自动提取核心变量
- **审稿人评审**：定性分析（内生性等级）+ 定量打分（100分制）+ 修改建议
- **符合学术规范**：参考《经济研究》《管理世界》及 AER、QJE 等顶刊标准
- **灵活可配置**：支持全流程、部分流程或单步骤运行
- **工程规范**：清晰的项目结构，便于维护和扩展

## 📋 目录

- [系统架构](#系统架构)
- [智能体介绍](#智能体介绍)
- [快速开始](#快速开始)
- [使用指南](#使用指南)
- [配置说明](#配置说明)
- [项目结构](#项目结构)
- [扩展开发](#扩展开发)

## 🏗️ 系统架构

```
研究流程编排器 (ResearchOrchestrator)
    │
    ├─── 智能体0: 输入解析专家 (InputParserAgent) [新增]
    │       └─── 解析用户输入，提取核心变量X和Y
    │
    ├─── 智能体1: 文献搜集专家 (LiteratureCollectorAgent)
    │       └─── 搜集和分析经济学顶刊文献
    │
    ├─── 智能体2: 指标设置专家 (VariableDesignerAgent)
    │       └─── 设计变量体系和代理变量（支持X/Y输入）
    │
    ├─── 智能体3: 理论设置专家 (TheoryDesignerAgent)
    │       └─── 构建理论框架和研究假设
    │
    ├─── 智能体4: 计量模型专家 (ModelDesignerAgent)
    │       └─── 设计计量经济学模型
    │
    ├─── 智能体5: 数据分析专家 (DataAnalystAgent)
    │       └─── 执行数据分析和统计检验
    │
    ├─── 智能体6: 长文报告专家 (ReportWriterAgent)
    │       └─── 撰写完整学术论文
    │
    ### 0. 输入解析专家 ✨新增
- **职责**：解析用户的自然语言输入
- **输入**：自然语言描述（如"我想研究X对Y的影响"）
- **输出**：JSON格式的研究主题、variable_x、variable_y、关键词建议
- **关键能力**：语义理解、变量识别、学术规范化
- **JSON Schema**：
  ```json
  {
    "research_topic": "研究主题",
    "variable_x": {
      "name": "自变量名称",
      "nature": "政策/行为/特征",
      "chinese": "中文术语",
      "english": "英文术语",
      "related_concepts": ["相关概念"],
      "measurement_dimensions": ["测量维度"]
    },
    "variable_y": {...},
    "keywords": {
      "group_a": {"chinese": [], "english": []},
      "group_b": {"chinese": [], "english": []}
    }
  }
  ```

### 1. 文献搜集专家
- **职责**：搜集和分析顶刊文献
- **输出**：JSON格式的文献列表（每篇包含作者、年份、标题、期刊、变量定义、核心结论、理论机制、数据来源等）
- **关键能力**：精准检索、批判性分析、信息提取
- **JSON Schema**：
  ```json
  {
    "literature_list": [
      {
        "id": 1,
        "authors": "作者列表",
        "year": 2023,
        "title": "论文标题",
        "journal": "期刊名称",
        "variable_x_definition": "自变量定义",
        "variable_y_definition": "因变量定义",
        "core_conclusion": "核心结论",
        "theoretical_mechanism": "理论机制",
        "data_source": "数据来源",
        "heterogeneity_dimensions": ["异质性维度"],
        "identification_strategy": "识别策略",
        "limitations": ["研究局限"]
      }
    ]
  }
  ```

### 2. 指标设置专家
- **职责**：设计完整变量体系（接收来自输入解析的X/Y变量信息）
- **输出**：JSON格式的核心变量、中介/调节变量、控制变量的代理变量方案
- **关键能力**：变量设计、经济学内涵把握、数据可得性评估
- **JSON Schema**：
  ```json
  {
    "core_variables": {
      "independent": {...},
      "dependent": {...}
    },
    "mediating_moderating_variables": [...],
    "control_variables": [...],
    "variable_relationships": "关系说明",
    "justification": "设计依据"
  }
  ```

### 3. 理论设置专家
- **职责**：构建理论框架并提出假设
- **输出**：JSON格式的理论框架、研究假设、潜在机制
- **关键能力**：理论适配、逻辑推导、假设构建
- **JSON Schema**：
  ```json
  {
    "theoretical_framework": [
      {
        "theory_name": "理论名称",
        "core_arguments": "核心观点",
        "application": "在本研究中的应用",
        "references": ["参考文献"]
      }
    ],
    "research_hypotheses": [...],
    "potential_mechanisms": [...]
  }
  ```

### 4. 计量模型专家
- **职责**：设计计量经济学模型
- **输出**：JSON格式的基准模型、机制检验模型、稳健性检验方案
- **关键能力**：模型选择、因果识别、数学建模
- **JSON Schema**：
  ```json
  {
    "baseline_model": {
      "model_type": "模型类型",
      "equation": "LaTeX格式方程",
      "variables": {...},
      "estimation_method": "估计方法"
    },
    "mechanism_models": [...],
    "robustness_checks": [...]
  }
  ```

### 5. 数据分析专家
- **职责**：执行数据分析
- **输出**：JSON格式的预处理方案、描述性统计、回归结果、稳健性检验结果
- **关键能力**：数据处理、统计分析、结果解读
- **JSON Schema**：
  ```json
  {
    "preprocessing": {...},
    "descriptive_statistics": {...},
    "baseline_regression": {...},
    "mechanism_analysis": [...],
    "heterogeneity_analysis": [...],
    "robustness_checks": [...],
    "conclusions": "分析结论"
  }
  ```

### 6. 长文报告专家
- **职责**：撰写完整学术论文
- **输出**：符合顶刊规范的完整论文（Markdown格式）
- **关键能力**：学术写作、叙事能力、规范表达

### 7. 审稿人专家 ✨新增
- **职责**：对完整研究进行评审打分
- **输出**：JSON格式的定性评价（内生性等级A/B/C/D/E）、定量评分（100分制，10个维度）、修改建议
- **关键能力**：学术评审、问题诊断、建设性反馈
- **JSON Schema**：
  ```json
  {
    "overall_assessment": "总体评价",
    "qualitative_analysis": {
      "endogeneity_rating": "A/B/C/D/E",
      "main_concerns": [...],
      "strengths": [...]
    },
    "quantitative_analysis": {
      "total_score": 85,
      "dimension_scores": {
        "research_question": 9,
        "literature_review": 8,
        "theoretical_framework": 8,
        "research_design": 7,
        "data_quality": 8,
        "empirical_methods": 7,
        "results_robustness": 8,
        "interpretation": 9,
        "writing_quality": 9,
        "innovation": 7
      }
    },
    "revision_suggestions": [...]
  }
  ```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 阿里云百炼 API Key（推荐，国内访问稳定）或 OpenAI API Key

### 安装步骤

1. **克隆或下载项目**
```bash
cd multi-agent
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**

**推荐：使用阿里云通义千问（国内访问更稳定）**
```bash
# 复制模板文件
cp .env.template .env

# 编辑 .env 文件
nano .env
```

在 `.env` 文件中设置：
```env
# 阿里云百炼 API 配置（推荐）
DASHSCOPE_API_KEY=sk-13487e6596b54bdabf441e1a50f0f1e8
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 模型配置
# 可选模型: qwen-turbo, qwen-plus, qwen-max, qwen-max-longcontext
DEFAULT_MODEL=qwen-plus
```

**或使用OpenAI（需要国际网络）**
```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
DEFAULT_MODEL=gpt-4-turbo-preview
```

4. **测试配置**
```bash
# 测试阿里云通义千问连接
python test_qwen.py
```

### 基础使用

**方式1：使用自然语言输入** ✨新功能
```python
from main import ResearchOrchestrator

orchestrator = ResearchOrchestrator()

# 直接用自然语言描述研究意图
results = orchestrator.run_full_pipeline(
    user_input="我想研究绿色债券对企业业绩的影响",
    enable_steps=["input_parse", "literature", "variable", "theory", "model", "analysis", "report"],
    min_papers=10,
    word_count=8000,
)
```

**方式2：传统方式（指定研究主题和关键词）**
```python
from main import ResearchOrchestrator

# 创建编排器
orchestrator = ResearchOrchestrator(output_dir="output")

# 运行完整研究流程
results = orchestrator.run_full_pipeline(
    research_topic="绿色债券对企业业绩的影响研究",
    keyword_group_a=["绿色债券", "Green Bond"],
    keyword_group_b=["企业业绩", "Firm Performance"],
    min_papers=10,
    word_count=8000,
)

print(f"报告已生成: {results['report_path']}")
```

## 📖 使用指南

### 自然语言输入示例 ✨新功能

```python
from main import ResearchOrchestrator

orchestrator = ResearchOrchestrator()

# 使用自然语言描述研究意图
results = orchestrator.run_full_pipeline(
    user_input="我想研究碳交易政策对企业绿色创新的影响，特别是上市公司的表现",
    enable_steps=["input_parse", "literature", "variable", "theory", "model", "analysis", "report"],
    min_papers=12,
    word_count=10000,
)
```

### 完整流程+审稿示例 ✨新功能

```python
# 运行完整流程并进行审稿评审
results = orchestrator.run_full_pipeline(
    research_topic="数字化转型对企业创新的影响",
    keyword_group_a=["数字化转型", "Digital Transformation"],
    keyword_group_b=["企业创新", "Innovation"],
    min_papers=10,
    word_count=8000,
    enable_review=True,  # 启用审稿功能
)

# 查看审稿意见
print(results['review_report'])
```
输入解析 ✨新功能
parse_result = orchestrator.run_single_step(
    step="input_parse",
    input_data={
        "user_input": "我想研究AI技术对劳动力市场的影响",
    }
)

# 只运行审稿评审 ✨新功能
review_result = orchestrator.run_single_step(
    step="review",
    input_data={
        "research_topic": "...",
        "variable_system": "...",
        "theory_framework": "...",
        # ... 其他研究成果
    }
)

# 只运行
### 
```python
from main import ResearchOrchestrator

# 创建编排器
orchestrator = ResearchOrchestrator(output_dir="output")

# 运行完整研究流程
results = orchestrator.run_full_pipeline(
    research_topic="绿色债券对企业业绩的影响研究",
    keyword_group_a=["绿色债券", "Green Bond"],
    keyword_group_b=["企业业绩", "Firm Performance"],
    min_papers=10,
    word_count=8000,
)

print(f"报告已生成: {results['report_path']}")
```

## 📖 使用指南

### 完整流程示例

```python
from main import ResearchOrchestrator

orchestrator = ResearchOrchestrator()

results = orchestrator.run_full_pipeline(
    research_topic="数字化转型对企业创新的影响",
    keyword_group_a=["数字化转型", "Digital Transformation", "数字技术"],
    keyword_group_b=["企业创新", "Innovation", "技术创新"],
    min_papers=15,
    data_info="使用上市公司面板数据，2010-2022年",
    word_count=10000,
)
```

### 部分流程示例

```python
# 只运行前三个步骤
results = orchestrator.run_full_pipeline(
    research_topic="碳交易对企业绿色创新的影响",
    keyword_group_a=["碳交易", "碳市场"],
    keyword_group_b=["绿色创新", "环境创新"],
    enable_steps=["literature", "variable", "theory"],
)
```

### 单步骤运行

```python
# 只运行文献搜集
literature_result = orchestrator.run_single_step(
    step="literature",
    input_data={
        "research_topic": "AI在计量经济学中的应用",
        "keyword_group_a": ["人工智能", "机器学习"],
        "keyword_group_b": ["计量经济学", "因果推断"],
        "min_papers": 10,
    }
)
```

### 简化接口

```python
from main import SimplifiedOrchestrator

simple = SimplifiedOrchestrator()

# 快速研究（自动解析关键词）
report_path = simple.quick_research(
    topic="ESG投资对股票收益的影响",
    keywords_a="ESG投资,可持续投资,社会责任投资",
    keywords_b="股票收益,投资回报,市场表现"
)
```

## ⚙️ 配置说明

### 基础配置 (config/config.py)

**阿里云通义千问配置（推荐）**
```python
# API配置
DASHSCOPE_API_KEY = "sk-xxx"  # 你的阿里云API Key
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-plus"  # 可选: qwen-turbo, qwen-plus, qwen-max, qwen-max-longcontext
TEMPERATURE = 0.7
```

**OpenAI配置（可选）**
```python
# API配置
OPENAI_API_KEY = "your_api_key"
OPENAI_API_BASE = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4-turbo-preview"
TEMPERATURE = 0.7
```

### 阿里云通义千问模型说明

| 模型名称 | 特点 | 适用场景 |
|---------|------|---------|
| `qwen-turbo` | 速度最快，成本最低 | 简单任务、快速测试 |
| `qwen-plus` | **推荐**，性能均衡 | 大多数研究任务 |
| `qwen-max` | 能力最强 | 复杂分析、高质量写作 |
| `qwen-max-longcontext` | 支持长文本 | 长文献、长报告分析 |

### 智能体温度配置

```python
# 智能体配置
AGENT_CONFIG = {
    "input_parser": {
        "temperature": 0.3,  # 输入解析需要精确
    },
    "literature_collector": {
        "temperature": 0.3,  # 文献搜集需要精确
    },
    "variable_designer": {
        "temperature": 0.5,  # 变量设计需要平衡
    },
    "report_writer": {
        "temperature": 0.7,  # 写作需要创造性
    },
    "reviewer": {
        "temperature": 0.4,  # 审稿需要客观严谨
    },
    # ... 其他智能体配置
}
```

### 自定义智能体配置

```python
from agents import LiteratureCollectorAgent

# 自定义配置
custom_agent = LiteratureCollectorAgent(
    custom_config={
        "model": "qwen-max",  # 使用更强的模型
        "temperature": 0.2,
    }
)
```

## 📁 项目结构

```
multi-agent/
├── agents/                      # 智能体模块
│   ├── __init__.py
│   ├── base_agent.py           # 基础智能体类
│   ├── literature_collector.py # 智能体1
│   ├── variable_designer.py    # 智能体2
│   ├── theory_designer.py      # 智能体3
│   ├── model_designer.py       # 智能体4
│   ├── data_analyst.py         # 智能体5
│   └── report_writer.py        # 智能体6
├── config/                      # 配置模块
│   ├── __init__.py
│   └── config.py               # 配置文件
├── tools/                       # 工具模块
│   ├── __init__.py
│   ├── research_tools.py       # 研究工具
│   └── output_tools.py         # 输出工具
├── examples/                    # 示例代码
│   └── basic_usage.py          # 基础使用示例
├── data/                        # 数据目录
├── output/                      # 输出目录
├── logs/                        # 日志目录
├── orchestrator.py             # 主协调器
├── main.py                     # 主入口
├── requirements.txt            # 依赖列表
├── .env.template               # 环境变量模板
├── .gitignore                  # Git忽略文件
└── README.md                   # 项目文档
```
🆕 v1.1.0 新功能

### 1使用自然语言输入**：对于不确定如何表述研究问题的场景，使用`user_input`参数
2. **. 输入解析智能体
- **自然语言输入**：可以直接用"我想研究X对Y的影响"这样的自然语言描述
- **自动提取变量**：智能识别核心解释变量X和被解释变量Y
- **关键词建议**：自动生成文献搜索用的关键词组合
- **研究问题规范化**：将口语化表达转换为规范的学术问题

### 2. 审稿人智能体
- **定性分析**：内生性维度评估，输出等级制打分（好/一般/差）
- **定量分析**：多维度量化打分（满分100分）
  - 核心变量设定（25%）
  - 理论框架构建（20%）
  - 模型设计（25%）
  - 实证分析（20%）
  - 论文质量（10%）
- **修改建议**：提供具体、可操作的改进建议
- **迭代改进**：支持根据审稿意见优化研究

### 3. 增强的变量设计
- var启用审稿**：重要研究建议启用审稿功能（`enable_review=True`），获取改进建议
5. **iable_designer现在可以接收解析后的X和Y变量
- 更精准的变量体系设计

## 
## 🔧 扩展开发

### 添加新智能体

1. 在 `agents/` 目录下创建新文件：

```python
from .base_agent import BaseAgent

class MyCustomAgent(BaseAgent):
    def __init__(self, custom_config=None):
        super().__init__("my_custom_agent", custom_config)
    
    def get_system_prompt(self) -> str:
        return "你的系统提示词"
    
    def get_task_prompt(self, **kwargs) -> str:
        return "你的任务提示词"
```

2. 在 `config/config.py` 中添加配置：

```python
AGENT_CONFIG = {
    "my_custom_agent": {
        "name": "我的自定义智能体",
        "model": "gpt-4-turbo-preview",
        "temperature": 0.7,
    },
}
```

3. 在 `orchestrator.py` 中集成新智能体

### 添加新工具

在 `tools/` 目录下创建新工具类：

```python
class MyCustomTool:
    def process(self, data):
        # 你的处理逻辑
        return result
```

### 自定义工作流

```python
class CustomOrchestrator(ResearchOrchestrator):
    def run_custom_pipeline(self, **kwargs):
        # 自定义流程逻辑
        pass
```

## 📊 输出格式

系统支持多种输出格式：

- **Markdown**: 适合阅读和进一步编辑
- **JSON**: 适合程序化处理
- **LaTeX**: 适合学术发表

输出文件包含：
- 完整报告文件
- 阶段性结果文件
- JSON格式备份

## 🔍 最佳实践

1. **关键词选择**：选择具有代表性的中英文关键词组合
2. **温度参数**：分析类任务使用较低温度(0.3)，创作类任务使用较高温度(0.7)
3. **分步运行**：对于复杂研究，建议先运行部分流程，检查结果后再继续
4. **结果保存**：系统会自动保存各阶段结果，便于中断后继续

## 🐛 常见问题

**Q: 如何切换不同的通义千问模型？**
A: 编辑 `.env` 文件中的 `DEFAULT_MODEL` 参数：
```env
# 快速模型
DEFAULT_MODEL=qwen-turbo

# 平衡模型（推荐）
DEFAULT_MODEL=qwen-plus

# 最强模型
DEFAULT_MODEL=qwen-max

# 长文本模型
DEFAULT_MODEL=qwen-max-longcontext
```

**Q: 阿里云API调用失败怎么办？**
A: 检查以下几点：
1. `.env` 文件中的 `DASHSCOPE_API_KEY` 是否正确
2. 网络连接是否正常（国内网络可直接访问）
3. API额度是否充足（登录阿里云百炼平台查看）
4. 运行 `python test_qwen.py` 测试连接

**Q: 如何从OpenAI切换到阿里云？**
A: 修改 `.env` 文件：
```env
# 注释掉OpenAI配置
# OPENAI_API_KEY=xxx
# OPENAI_API_BASE=https://api.openai.com/v1

# 启用阿里云配置
DASHSCOPE_API_KEY=sk-xxx
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DEFAULT_MODEL=qwen-plus
```

**Q: 如何调整智能体的输出质量？**
A: 可以通过以下方式：
1. 调整 `temperature` 参数（0.1-1.0，越低越稳定）
2. 切换到更强的模型（如 `qwen-max`）
3. 修改智能体的提示词

**Q: 能否同时使用OpenAI和阿里云？**
A: 可以。系统会优先使用阿里云配置（如果 `DASHSCOPE_API_KEY` 存在），否则使用OpenAI配置。

**Q: 如何处理中文文献？**
A: 系统已针对中文顶刊（《经济研究》《管理世界》等）进行优化。使用阿里云通义千问处理中文效果更好。

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 📮 联系方式

如有问题或建议，请提交 Issue。

---

**注意**：本系统是研究辅助工具，生成的内容需要研究者进行审核和完善。学术研究应遵循严格的学术规范和诚信原则。
