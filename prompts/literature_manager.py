"""
文献管理智能体提示词
Literature Manager Agent Prompts
"""

SYSTEM_PROMPT = """# 角色定义

你是一名专业的学术文献管理专家，精通经济学、金融学和管理学领域的学术文献。你的职责是帮助研究人员管理、组织和检索学术文献。

## 核心能力

1. **文献解析**: 能够从各种格式（文本、BibTeX、RIS等）中提取文献信息
2. **文献规范化**: 将文献信息标准化为统一格式
3. **关键词提取**: 从文献摘要和标题中提取关键研究主题
4. **文献分类**: 根据研究主题、方法论、数据类型等维度对文献进行分类
5. **文献推荐**: 基于研究主题推荐相关文献

## 工作原则

1. **准确性**: 确保文献信息的准确性，不要猜测或编造信息
2. **完整性**: 尽可能提取完整的文献元数据
3. **规范性**: 遵循学术规范，使用标准的引用格式
4. **实用性**: 提取对研究有价值的信息（理论机制、识别策略等）

## 支持的操作

- `add`: 添加新文献
- `search`: 搜索文献
- `parse`: 解析文献文本
- `recommend`: 推荐相关文献
- `summarize`: 总结文献集合
"""


def get_task_prompt(operation: str, **kwargs) -> str:
    """
    获取任务提示词

    Args:
        operation: 操作类型
        **kwargs: 操作相关参数

    Returns:
        任务提示词
    """
    if operation == "parse":
        return _get_parse_prompt(**kwargs)
    elif operation == "add":
        return _get_add_prompt(**kwargs)
    elif operation == "search":
        return _get_search_prompt(**kwargs)
    elif operation == "recommend":
        return _get_recommend_prompt(**kwargs)
    elif operation == "summarize":
        return _get_summarize_prompt(**kwargs)
    else:
        return _get_default_prompt(**kwargs)


def _get_parse_prompt(raw_text: str = "", **kwargs) -> str:
    """解析文献文本的提示词"""
    return f"""# 文献解析任务

请从以下文本中提取文献信息。如果某些字段无法确定，请使用null或空列表。

## 输入文本

{raw_text}

## 提取要求

请提取以下信息：
1. 基本信息：作者、年份、标题、期刊、DOI、URL
2. 内容信息：摘要、关键词
3. 研究信息（如适用）：
   - 解释变量(X)的定义和衡量方式
   - 被解释变量(Y)的定义和衡量方式
   - 核心结论（尽量量化）
   - 理论机制
   - 数据来源
   - 识别策略
   - 异质性维度
   - 研究局限

## 输出格式

请以JSON格式输出，包含以下字段：
```json
{{
  "authors": "作者（格式：姓名1, 姓名2, & 姓名3）",
  "year": 年份数字,
  "title": "论文标题",
  "journal": "期刊名称",
  "abstract": "摘要",
  "keywords": ["关键词1", "关键词2"],
  "doi": "DOI（如有）",
  "url": "URL（如有）",
  "variable_x_definition": "X变量定义",
  "variable_x_measurement": "X变量衡量方式",
  "variable_y_definition": "Y变量定义",
  "variable_y_measurement": "Y变量衡量方式",
  "core_conclusion": "核心结论",
  "theoretical_mechanism": ["机制1", "机制2"],
  "data_source": "数据来源",
  "identification_strategy": "识别策略",
  "heterogeneity_dimensions": ["维度1", "维度2"],
  "limitations": ["局限1", "局限2"],
  "tags": ["建议标签1", "建议标签2"]
}}
```
"""


def _get_add_prompt(literature_info: dict = None, **kwargs) -> str:
    """添加文献的提示词"""
    info_str = str(literature_info) if literature_info else "{}"
    return f"""# 文献添加任务

请验证并规范化以下文献信息，确保格式正确且信息完整。

## 输入信息

{info_str}

## 规范化要求

1. **作者格式**: 使用"姓名1, 姓名2, & 姓名3"格式
2. **年份**: 确保为4位数字
3. **标题**: 首字母大写，去除多余空格
4. **期刊**: 使用规范的期刊全称
5. **关键词**: 小写，去重

## 输出格式

请以JSON格式输出规范化后的文献信息，与输入格式相同。如发现任何问题，请在"notes"字段中说明。
"""


def _get_search_prompt(query: str = "", context: str = "", **kwargs) -> str:
    """搜索文献的提示词"""
    return f"""# 文献搜索任务

用户正在搜索相关文献。

## 搜索查询

{query}

## 现有文献库上下文

{context}

## 任务要求

1. 分析用户的搜索意图
2. 提取关键搜索词（中英文）
3. 建议搜索策略
4. 如果提供了文献库上下文，评估匹配程度

## 输出格式

```json
{{
  "search_intent": "用户搜索意图分析",
  "keywords_chinese": ["中文关键词1", "中文关键词2"],
  "keywords_english": ["English keyword 1", "English keyword 2"],
  "search_strategy": "建议的搜索策略",
  "recommended_filters": {{
    "year_range": [起始年份, 结束年份],
    "journals": ["推荐期刊1", "推荐期刊2"],
    "methods": ["推荐方法1"]
  }}
}}
```
"""


def _get_recommend_prompt(topic: str = "", existing_literature: list = None, **kwargs) -> str:
    """推荐文献的提示词"""
    existing_str = str(existing_literature) if existing_literature else "[]"
    return f"""# 文献推荐任务

基于当前研究主题，推荐相关的学术文献。

## 研究主题

{topic}

## 已有文献

{existing_str}

## 推荐要求

1. 推荐与主题高度相关的经典文献
2. 推荐近5年的重要新进展
3. 考虑方法论互补性
4. 避免与已有文献重复

## 输出格式

```json
{{
  "recommendations": [
    {{
      "authors": "作者",
      "year": 年份,
      "title": "论文标题",
      "journal": "期刊",
      "relevance_reason": "推荐理由",
      "relevance_score": 相关度评分(1-10)
    }}
  ],
  "research_gaps": ["研究空白1", "研究空白2"],
  "suggested_directions": ["建议方向1", "建议方向2"]
}}
```
"""


def _get_summarize_prompt(literature_list: list = None, focus: str = "", **kwargs) -> str:
    """总结文献的提示词"""
    lit_str = str(literature_list) if literature_list else "[]"
    return f"""# 文献总结任务

请对以下文献进行系统性总结。

## 文献列表

{lit_str}

## 关注焦点

{focus if focus else "综合总结"}

## 总结要求

1. **主要发现**: 归纳文献的核心结论
2. **方法论综述**: 总结使用的主要研究方法
3. **理论贡献**: 梳理主要的理论框架和机制
4. **数据特征**: 总结数据来源和样本特征
5. **研究趋势**: 识别研究发展趋势
6. **研究空白**: 指出现有研究的不足

## 输出格式

```json
{{
  "main_findings": [
    {{
      "finding": "发现内容",
      "supporting_papers": ["Paper1", "Paper2"]
    }}
  ],
  "methodological_summary": {{
    "common_methods": ["方法1", "方法2"],
    "identification_strategies": ["策略1", "策略2"],
    "data_sources": ["数据源1", "数据源2"]
  }},
  "theoretical_contributions": [
    {{
      "theory": "理论名称",
      "application": "应用方式"
    }}
  ],
  "research_trends": ["趋势1", "趋势2"],
  "research_gaps": ["空白1", "空白2"],
  "future_directions": ["方向1", "方向2"]
}}
```
"""


def _get_default_prompt(**kwargs) -> str:
    """默认提示词"""
    return """# 文献管理任务

请根据用户的需求处理文献相关事务。

## 输出格式

请以JSON格式输出处理结果。
"""
