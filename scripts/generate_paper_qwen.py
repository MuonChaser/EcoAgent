#!/usr/bin/env python3
"""
使用 Qwen-Max 生成学术论文

直接调用阿里云通义千问 qwen-max 模型，生成关于
"环境监管对企业全要素生产率的影响" 的英文学术论文。

使用方法:
    python scripts/generate_paper_qwen.py

    # 指定输出文件
    python scripts/generate_paper_qwen.py --output my_paper.txt

    # 使用其他模型
    python scripts/generate_paper_qwen.py --model qwen-plus
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from loguru import logger
from config.logging_config import setup_logger

# 配置日志
LOG_FILE = setup_logger("generate_paper")

# 完整的英文提示词
SYSTEM_PROMPT = """You are a senior economist with extensive publication experience in top economics journals (AER, QJE, JPE, Econometrica, Journal of Political Economy) and leading Chinese journals (Economic Research Journal, Management World). Your task is to generate a complete, publication-ready academic paper.

## Core Competencies
- Deep expertise in empirical economics methodology
- Mastery of causal identification strategies (DID, IV, RDD, PSM, Fixed Effects)
- Rigorous academic writing following top journal conventions
- Strong theoretical foundation in economics

## Working Principles
- All arguments must be logically coherent and self-consistent
- Empirical design must address endogeneity concerns
- Variables must have clear economic meaning and data availability
- Follow the narrative style of top economics journals"""


USER_PROMPT = r"""# RESEARCH TOPIC

**"The Impact of Environmental Regulation on Firm Total Factor Productivity (TFP)"**

- Core Explanatory Variable (X): Environmental Regulation
- Dependent Variable (Y): Firm Total Factor Productivity (TFP)

---

# TASK 1: VARIABLE SYSTEM DESIGN

## 1.1 Core Explanatory Variable (X): Environmental Regulation

Provide at least **3 proxy variables** covering different measurement dimensions:

For each proxy variable, specify:
- **Definition**: Precise calculation method
- **Economic rationale**: How it reflects the core concept
- **Literature support**: 1-2 recent top-tier publications using this measure
- **Data source**: Specific databases (e.g., CSMAR, Wind, EPA databases, CEIC)
- **Statistical specifications**: Unit, time dimension, sample scope

Suggested dimensions:
- Policy intensity measures (e.g., pollution levy rates, emission standards stringency)
- Enforcement measures (e.g., environmental inspections, penalty frequency)
- Market-based instruments (e.g., emissions trading scheme participation)

## 1.2 Dependent Variable (Y): Total Factor Productivity

Provide **2 core proxy variables**:

Suggested measures:
- LP method (Levinsohn-Petrin)
- OP method (Olley-Pakes)
- Solow residual approach
- DEA-Malmquist productivity index

## 1.3 Mediating Variables (Z)

Identify 2-3 potential transmission channels:
- Technological innovation (R&D intensity, patent applications)
- Resource allocation efficiency
- Factor input structure adjustment
- Green transformation investment

## 1.4 Control Variables

Provide at least **8 control variables** at firm and regional levels:

**Firm-level:**
- Firm size (ln(total assets))
- Leverage ratio (debt/assets)
- Firm age
- Ownership structure (state-owned dummy)
- Profitability (ROA)

**Regional-level:**
- GDP per capita
- Industrial structure
- FDI intensity
- Infrastructure development

---

# TASK 2: THEORETICAL FRAMEWORK AND HYPOTHESES

## 2.1 Theory Selection

Select at least **3 core theories** from:

1. **Porter Hypothesis (1991)**
   - Core insight: Stringent environmental regulations can stimulate innovation and enhance competitiveness
   - Relevance: Explains positive effect pathway

2. **Compliance Cost Theory**
   - Core insight: Regulations impose additional costs that divert resources from productive activities
   - Relevance: Explains potential negative effects

3. **Resource Reallocation Theory**
   - Core insight: Regulations may induce resource reallocation from pollution-intensive to clean sectors
   - Relevance: Explains structural adjustment mechanisms

4. **Induced Innovation Theory (Hicks, 1932)**
   - Core insight: Factor price changes induce factor-saving innovation
   - Relevance: Explains technological response to environmental costs

For each theory, provide:
- Core theoretical content
- Adaptation logic to this research
- Literature support (2+ top-tier publications)

## 2.2 Research Hypotheses

Formulate testable hypotheses with clear derivation logic:

**H1 (Direct Effect):** Environmental regulation significantly affects firm TFP.
- H1a: Porter Hypothesis perspective (positive effect)
- H1b: Compliance cost perspective (negative effect)

**H2 (Mechanism):** Environmental regulation affects TFP through [mediating variable].
- H2a: Innovation channel
- H2b: Resource allocation channel

**H3 (Heterogeneity):** The effect varies across:
- Industry pollution intensity (heavy vs. light polluters)
- Firm ownership (SOE vs. private)
- Regional development level (eastern vs. central/western)
- Firm size (large vs. small)

---

# TASK 3: ECONOMETRIC MODEL DESIGN

## 3.1 Baseline Model

Design the benchmark specification using LaTeX notation:

$$TFP_{it} = \alpha + \beta_1 ER_{it} + \gamma X_{it} + \mu_i + \lambda_t + \varepsilon_{it}$$

Where:
- $TFP_{it}$: Total factor productivity of firm $i$ in year $t$
- $ER_{it}$: Environmental regulation intensity
- $X_{it}$: Control variables vector
- $\mu_i$: Firm fixed effects
- $\lambda_t$: Year fixed effects
- $\varepsilon_{it}$: Error term

**Model selection justification:**
- Explain why two-way fixed effects model is appropriate
- Discuss potential endogeneity sources
- Describe identification strategy

## 3.2 Causal Identification Strategy

Address endogeneity using:

1. **Instrumental Variable Approach:**
   - Proposed IVs: Upwind pollution from neighboring regions, historical environmental shocks
   - First-stage regression specification
   - Validity discussion (relevance and exclusion restriction)

2. **Difference-in-Differences Design (if applicable):**
   - Policy shock identification (e.g., new environmental law implementation)
   - Treatment and control group definition
   - Parallel trends assumption test

3. **Propensity Score Matching:**
   - Matching variables selection
   - Balance tests

## 3.3 Mechanism Analysis Models

**Step 1:** $M_{it} = \alpha + \beta_1 ER_{it} + \gamma X_{it} + \mu_i + \lambda_t + \varepsilon_{it}$

**Step 2:** $TFP_{it} = \alpha + \beta_1 ER_{it} + \beta_2 M_{it} + \gamma X_{it} + \mu_i + \lambda_t + \varepsilon_{it}$

**Step 3:** Sobel test and bootstrap confidence intervals

## 3.4 Heterogeneity Analysis

Subgroup regression by:
- Industry pollution intensity
- Ownership structure
- Regional development
- Firm size quartiles

## 3.5 Robustness Checks

Design at least **5 robustness tests:**
1. Alternative TFP measures (LP vs. OP vs. GMM)
2. Alternative environmental regulation measures
3. Sample period adjustment
4. Excluding outliers (winsorization at 1%/99%)
5. Placebo test (randomized treatment timing)
6. Instrumental variable estimation
7. Dynamic panel GMM estimation

---

# TASK 4: COMPLETE PAPER WRITING

Write a complete academic paper following this structure:

## Paper Structure (Target: 8,000-10,000 words)

### 1. Introduction (1,500 words)
- **Opening hook**: Start with compelling macro background on environmental challenges and productivity concerns
- **Research gap**: Clearly identify what existing literature fails to address
- **Research question**: State the core question precisely
- **Contribution**: List 3-4 specific marginal contributions
- **Methodology preview**: Briefly describe empirical approach
- **Structure outline**: Guide readers through paper organization

### 2. Institutional Background and Theoretical Framework (2,000 words)

**2.1 Institutional Background**
- China's environmental regulation evolution
- Key policy milestones
- Enforcement mechanisms

**2.2 Theoretical Analysis**
- Synthesize selected theories
- Develop logical chain from regulation to productivity
- Derive each hypothesis with clear theoretical reasoning

### 3. Research Design (1,500 words)

**3.1 Model Specification**
- Present all equations in LaTeX format
- Explain each variable's role
- Justify model choices

**3.2 Variable Definition and Measurement**
- Detailed variable table with definitions, sources, and expected signs
- Descriptive statistics table

**3.3 Data Sources and Sample**
- Data sources description
- Sample construction process
- Sample period and size

**3.4 Identification Strategy**
- Endogeneity discussion
- Identification approach justification

### 4. Empirical Results (2,500 words)

**4.1 Baseline Results**
- Main regression table
- Economic interpretation of coefficients
- Statistical significance discussion

**4.2 Robustness Checks**
- Systematic robustness test results
- Table summarizing all checks

**4.3 Endogeneity Treatment**
- IV estimation results
- First-stage F-statistics
- Overidentification tests

### 5. Mechanism Analysis and Heterogeneity (1,500 words)

**5.1 Mechanism Analysis**
- Channel-by-channel examination
- Mediation effect quantification
- Mechanism diagram

**5.2 Heterogeneity Analysis**
- Subgroup regression results
- Cross-group comparison
- Economic interpretation of heterogeneity

### 6. Conclusion and Policy Implications (800 words)

**6.1 Main Findings**
- Summarize core conclusions

**6.2 Policy Implications**
- Specific, actionable policy recommendations

**6.3 Limitations and Future Research**
- Acknowledge limitations honestly
- Suggest future research directions

---

# OUTPUT REQUIREMENTS

## Format Specifications

1. **Academic tone**: Follow top journal conventions, avoid colloquial expressions
2. **LaTeX equations**: All mathematical expressions in proper LaTeX format
3. **Tables**: Use professional three-line table format with clear notes
4. **Citations**: Use author-year format (e.g., Porter, 1991; Greenstone, 2002)
5. **References**: Include at least 30 references, prioritizing:
   - Top 5 economics journals (AER, QJE, JPE, Econometrica, ReStud)
   - Top field journals (JEEM, Journal of Environmental Economics)
   - Recent publications (2015-2024)

## Quality Standards

1. **Causal identification**: Explicitly address how you establish causality
2. **Economic interpretation**: Convert all coefficients to economic magnitudes
3. **Internal consistency**: Ensure theoretical predictions align with empirical tests
4. **Narrative coherence**: Each section should flow logically to the next

## Tables to Include

1. Descriptive Statistics
2. Correlation Matrix
3. Baseline Regression Results
4. Robustness Checks Summary
5. IV Estimation Results
6. Mechanism Analysis Results
7. Heterogeneity Analysis Results

---

# BEGIN PAPER GENERATION

Please generate the complete academic paper following all specifications above. Ensure the paper:

1. Demonstrates rigorous causal identification
2. Provides compelling economic narratives
3. Follows top journal formatting conventions
4. Includes all required tables and equations
5. Maintains logical coherence throughout

Start with the title, abstract (200-300 words), and keywords, then proceed section by section."""


def generate_paper(
    model: str = "qwen-max",
    output_file: str = None,
    temperature: float = 0.7
) -> str:
    """
    调用 Qwen 模型生成论文

    Args:
        model: 模型名称
        output_file: 输出文件路径
        temperature: 生成温度

    Returns:
        生成的论文内容
    """
    # 获取 API 配置
    api_key = os.getenv("DASHSCOPE_API_KEY")
    base_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

    if not api_key:
        raise ValueError("请设置 DASHSCOPE_API_KEY 环境变量")

    logger.info(f"使用模型: {model}")
    logger.info(f"API Base: {base_url}")
    logger.info(f"Temperature: {temperature}")

    # 初始化客户端
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    logger.info("开始生成论文，这可能需要几分钟...")

    # 调用 API
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT}
        ],
        temperature=temperature,
        stream=True  # 使用流式输出
    )

    # 收集流式响应
    content = ""
    print("\n" + "=" * 60)
    print("生成中...")
    print("=" * 60 + "\n")

    for chunk in response:
        if chunk.choices[0].delta.content:
            text = chunk.choices[0].delta.content
            content += text
            print(text, end="", flush=True)

    print("\n\n" + "=" * 60)
    logger.info(f"生成完成，共 {len(content)} 字符")

    # 保存到文件
    if output_file:
        output_path = Path(output_file)
    else:
        # 默认输出路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = project_root / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"paper_env_regulation_tfp_{timestamp}.txt"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"论文已保存到: {output_path}")
    logger.info(f"日志已保存到: {LOG_FILE}")

    return content


def main():
    parser = argparse.ArgumentParser(
        description="使用 Qwen-Max 生成学术论文",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python scripts/generate_paper_qwen.py
    python scripts/generate_paper_qwen.py --output my_paper.txt
    python scripts/generate_paper_qwen.py --model qwen-plus
        """
    )

    parser.add_argument(
        "--model", "-m",
        type=str,
        default="qwen-max",
        help="模型名称 (默认: qwen-max)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="输出文件路径"
    )
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=0.7,
        help="生成温度 (默认: 0.7)"
    )

    args = parser.parse_args()

    try:
        generate_paper(
            model=args.model,
            output_file=args.output,
            temperature=args.temperature
        )
    except Exception as e:
        logger.error(f"生成失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
