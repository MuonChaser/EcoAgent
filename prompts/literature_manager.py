"""
Literature Manager Agent Prompts
"""

SYSTEM_PROMPT = """# Role Definition

You are a professional academic literature management expert, well-versed in the fields of economics, finance, and management. Your responsibility is to help researchers manage, organize, and retrieve academic literature.

## Core Capabilities

1. **Literature Parsing**: Ability to extract literature information from various formats (text, BibTeX, RIS, etc.)
2. **Literature Standardization**: Standardize literature information into a unified format
3. **Keyword Extraction**: Extract key research themes from literature abstracts and titles
4. **Literature Classification**: Classify literature by research topic, methodology, data type, and other dimensions
5. **Literature Recommendation**: Recommend related literature based on research topics

## Working Principles

1. **Accuracy**: Ensure the accuracy of literature information; do not guess or fabricate information
2. **Completeness**: Extract complete literature metadata as much as possible
3. **Standardization**: Follow academic norms and use standard citation formats
4. **Utility**: Extract information valuable for research (theoretical mechanisms, identification strategies, etc.)

## Supported Operations

- `add`: Add new literature
- `search`: Search literature
- `parse`: Parse literature text
- `recommend`: Recommend related literature
- `summarize`: Summarize literature collection
"""


def get_task_prompt(operation: str, **kwargs) -> str:
    """
    Get task prompt

    Args:
        operation: Operation type
        **kwargs: Operation-related parameters

    Returns:
        Task prompt
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
    """Prompt for parsing literature text"""
    return f"""# Literature Parsing Task

Please extract literature information from the following text. If certain fields cannot be determined, use null or empty lists.

## Input Text

{raw_text}

## Extraction Requirements

Please extract the following information:
1. Basic Information: authors, year, title, journal, DOI, URL
2. Content Information: abstract, keywords
3. Research Information (if applicable):
   - Explanatory variable (X) definition and measurement
   - Dependent variable (Y) definition and measurement
   - Core conclusion (quantified if possible)
   - Theoretical mechanism
   - Data source
   - Identification strategy
   - Heterogeneity dimensions
   - Research limitations

## Output Format

Please output in JSON format with the following fields:
```json
{{
  "authors": "Authors (format: Name1, Name2, & Name3)",
  "year": year_number,
  "title": "Paper title",
  "journal": "Journal name",
  "abstract": "Abstract",
  "keywords": ["keyword1", "keyword2"],
  "doi": "DOI (if available)",
  "url": "URL (if available)",
  "variable_x_definition": "X variable definition",
  "variable_x_measurement": "X variable measurement",
  "variable_y_definition": "Y variable definition",
  "variable_y_measurement": "Y variable measurement",
  "core_conclusion": "Core conclusion",
  "theoretical_mechanism": ["mechanism1", "mechanism2"],
  "data_source": "Data source",
  "identification_strategy": "Identification strategy",
  "heterogeneity_dimensions": ["dimension1", "dimension2"],
  "limitations": ["limitation1", "limitation2"],
  "tags": ["suggested_tag1", "suggested_tag2"]
}}
```
"""


def _get_add_prompt(literature_info: dict = None, **kwargs) -> str:
    """Prompt for adding literature"""
    info_str = str(literature_info) if literature_info else "{}"
    return f"""# Literature Addition Task

Please verify and standardize the following literature information, ensuring format correctness and information completeness.

## Input Information

{info_str}

## Standardization Requirements

1. **Author format**: Use "Name1, Name2, & Name3" format
2. **Year**: Ensure 4-digit number
3. **Title**: Title case, remove extra spaces
4. **Journal**: Use standard full journal name
5. **Keywords**: Lowercase, deduplicated

## Output Format

Please output standardized literature information in JSON format, same structure as input. If any issues are found, note them in the "notes" field.
"""


def _get_search_prompt(query: str = "", context: str = "", **kwargs) -> str:
    """Prompt for searching literature"""
    return f"""# Literature Search Task

The user is searching for related literature.

## Search Query

{query}

## Existing Literature Database Context

{context}

## Task Requirements

1. Analyze the user's search intent
2. Extract key search terms (English)
3. Suggest search strategy
4. If literature database context is provided, assess match quality

## Output Format

```json
{{
  "search_intent": "Analysis of user search intent",
  "keywords_english": ["English keyword 1", "English keyword 2"],
  "search_strategy": "Suggested search strategy",
  "recommended_filters": {{
    "year_range": [start_year, end_year],
    "journals": ["Recommended journal 1", "Recommended journal 2"],
    "methods": ["Recommended method 1"]
  }}
}}
```
"""


def _get_recommend_prompt(topic: str = "", existing_literature: list = None, **kwargs) -> str:
    """Prompt for recommending literature"""
    existing_str = str(existing_literature) if existing_literature else "[]"
    return f"""# Literature Recommendation Task

Recommend related academic literature based on the current research topic.

## Research Topic

{topic}

## Existing Literature

{existing_str}

## Recommendation Requirements

1. Recommend classic literature highly relevant to the topic
2. Recommend important new developments from the past 5 years
3. Consider methodological complementarity
4. Avoid duplication with existing literature

## Output Format

```json
{{
  "recommendations": [
    {{
      "authors": "Authors",
      "year": year,
      "title": "Paper title",
      "journal": "Journal",
      "relevance_reason": "Reason for recommendation",
      "relevance_score": relevance_score(1-10)
    }}
  ],
  "research_gaps": ["Research gap 1", "Research gap 2"],
  "suggested_directions": ["Suggested direction 1", "Suggested direction 2"]
}}
```
"""


def _get_summarize_prompt(literature_list: list = None, focus: str = "", **kwargs) -> str:
    """Prompt for summarizing literature"""
    lit_str = str(literature_list) if literature_list else "[]"
    return f"""# Literature Summary Task

Please provide a systematic summary of the following literature.

## Literature List

{lit_str}

## Focus Area

{focus if focus else "Comprehensive summary"}

## Summary Requirements

1. **Main Findings**: Synthesize core conclusions from the literature
2. **Methodological Review**: Summarize main research methods used
3. **Theoretical Contributions**: Organize main theoretical frameworks and mechanisms
4. **Data Characteristics**: Summarize data sources and sample characteristics
5. **Research Trends**: Identify research development trends
6. **Research Gaps**: Identify shortcomings in existing research

## Output Format

```json
{{
  "main_findings": [
    {{
      "finding": "Finding content",
      "supporting_papers": ["Paper1", "Paper2"]
    }}
  ],
  "methodological_summary": {{
    "common_methods": ["Method 1", "Method 2"],
    "identification_strategies": ["Strategy 1", "Strategy 2"],
    "data_sources": ["Data source 1", "Data source 2"]
  }},
  "theoretical_contributions": [
    {{
      "theory": "Theory name",
      "application": "Application method"
    }}
  ],
  "research_trends": ["Trend 1", "Trend 2"],
  "research_gaps": ["Gap 1", "Gap 2"],
  "future_directions": ["Direction 1", "Direction 2"]
}}
```
"""


def _get_default_prompt(**kwargs) -> str:
    """Default prompt"""
    return """# Literature Management Task

Please handle literature-related tasks based on the user's needs.

## Output Format

Please output processing results in JSON format.
"""
