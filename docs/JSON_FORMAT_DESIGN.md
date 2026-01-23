# JSON 格式化输出设计文档

## 设计目标

为所有智能体强制实施JSON格式化输出，实现以下目标：

1. **避免表格混乱**：不再输出Markdown表格或其他不规则格式
2. **结构化数据传递**：智能体间传递明确的JSON对象，不是文本字符串
3. **易于程序处理**：下游智能体可以直接访问字段，无需正则匹配或文本解析
4. **符合工程规范**：提高代码可维护性和系统鲁棒性

## 实现机制

### 1. BaseAgent 强制 JSON 输出

所有智能体继承自 `BaseAgent`，通过以下机制强制JSON输出：

```python
class BaseAgent(ABC):
    @abstractmethod
    def get_output_schema(self) -> Dict[str, Any]:
        """子类必须实现，定义输出的JSON schema"""
        pass
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """从LLM输出中提取JSON，支持3种格式"""
        # 策略1: 提取 ```json ... ``` 代码块
        # 策略2: 提取 ``` ... ``` 代码块
        # 策略3: 查找大括号包围的JSON对象
        pass
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # 在prompt末尾添加JSON schema指令
        schema = self.get_output_schema()
        schema_prompt = f"\n\n请按照以下JSON格式输出:\n```json\n{json.dumps(schema, indent=2, ensure_ascii=False)}\n```"
        
        # 调用LLM
        response = self.llm.invoke(messages)
        
        # 提取JSON
        parsed_data = self._extract_json(response.content)
        
        return {
            "raw_output": response.content,
            "parsed_data": parsed_data  # 结构化数据
        }
```

### 2. 中心化 Schema 定义

在 `agents/schemas.py` 中定义所有智能体的JSON schema：

```python
# 输入解析智能体
INPUT_PARSER_SCHEMA = {
    "research_topic": "研究主题",
    "variable_x": {
        "name": "自变量名称",
        "nature": "政策|行为|特征",
        "chinese": "中文术语",
        "english": "英文术语",
        "related_concepts": ["相关概念1", "相关概念2"],
        "measurement_dimensions": ["测量维度1"]
    },
    "variable_y": {...},
    "keywords": {...}
}

# 文献收集智能体
LITERATURE_COLLECTOR_SCHEMA = {
    "literature_list": [
        {
            "id": 1,
            "authors": "作者姓名",
            "year": 2023,
            "title": "论文标题",
            # ... 12个字段
        }
    ]
}

# ... 其他智能体的schema
```

优点：
- 一处修改，全局生效
- 便于维护和版本控制
- 可以生成API文档

### 3. 智能体实现模式

每个智能体遵循统一模式：

```python
from .base_agent import BaseAgent
from .schemas import XXX_SCHEMA

class XXXAgent(BaseAgent):
    def get_output_schema(self) -> Dict[str, Any]:
        return XXX_SCHEMA
    
    def process_output(self, raw_output: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        result = super().process_output(raw_output, input_data)
        
        # 提取结构化数据
        parsed = result.get("parsed_data", {})
        
        # 添加到结果中
        result["xxx_data"] = parsed
        result["research_topic"] = input_data.get("research_topic")
        
        return result
```

## 各智能体 Schema 详解

### InputParserAgent

**作用**：解析用户输入"我想研究X对Y的影响"

**输出结构**：
```json
{
  "research_topic": "绿色债券对企业业绩的影响",
  "variable_x": {
    "name": "绿色债券发行",
    "nature": "行为",
    "chinese": "绿色债券",
    "english": "Green Bond",
    "related_concepts": ["绿色金融", "ESG债券", "可持续债券"],
    "measurement_dimensions": ["发行规模", "发行频率", "债券评级"]
  },
  "variable_y": {
    "name": "企业业绩",
    "nature": "特征",
    "chinese": "企业业绩",
    "english": "Firm Performance",
    "related_concepts": ["财务绩效", "盈利能力", "经营效率"],
    "measurement_dimensions": ["ROA", "ROE", "净利润率", "托宾Q"]
  },
  "relationship": "影响",
  "research_context": "绿色金融政策背景下，企业绿色债券发行对财务表现的因果效应",
  "keywords": {
    "group_a": {
      "chinese": ["绿色债券", "绿色金融", "ESG债券"],
      "english": ["Green Bond", "Green Finance", "ESG Bond"]
    },
    "group_b": {
      "chinese": ["企业业绩", "财务绩效", "盈利能力"],
      "english": ["Firm Performance", "Financial Performance", "Profitability"]
    }
  }
}
```

### LiteratureCollectorAgent

**作用**：搜集和分析相关文献

**输出结构**：
```json
{
  "literature_list": [
    {
      "id": 1,
      "authors": "张三, 李四",
      "year": 2023,
      "title": "绿色债券与企业价值：来自中国上市公司的证据",
      "journal": "经济研究",
      "variable_x_definition": "企业是否发行绿色债券（0-1虚拟变量）",
      "variable_y_definition": "托宾Q（企业市场价值/资产重置成本）",
      "core_conclusion": "发行绿色债券显著提升企业市场价值约15%",
      "theoretical_mechanism": "信号传递理论：绿色债券发行向市场传递企业环保承诺信号，降低信息不对称",
      "data_source": "2015-2020年中国A股上市公司，N=5000",
      "heterogeneity_dimensions": ["企业所有制", "地区环保政策强度", "行业污染程度"],
      "identification_strategy": "双重差分法（DID）+ 倾向得分匹配（PSM）",
      "limitations": ["可能存在反向因果", "样本期较短", "外部效度有限"]
    },
    {
      "id": 2,
      "authors": "Wang, X., & Li, Y.",
      "year": 2022,
      "title": "Green bonds and corporate financial performance",
      "journal": "Journal of Finance",
      // ... 同样12个字段
    }
    // ... 更多文献
  ]
}
```

### VariableDesignerAgent

**作用**：设计完整变量体系

**输出结构**：
```json
{
  "core_variables": {
    "independent": {
      "name": "绿色债券发行",
      "proxy_variables": [
        {
          "variable_name": "GreenBond",
          "definition": "企业当年是否发行绿色债券（0-1虚拟变量）",
          "measurement": "若企业i在年份t发行至少一只绿色债券，则GreenBond=1，否则为0",
          "data_source": "Wind数据库绿色债券板块 + 人工核查",
          "justification": "最直接的度量方式，与现有文献一致"
        },
        {
          "variable_name": "GreenBondScale",
          "definition": "绿色债券发行规模（亿元，取对数）",
          "measurement": "ln(企业i在年份t发行的绿色债券总金额+1)",
          "data_source": "Wind数据库",
          "justification": "强度指标，反映发行规模的异质性"
        }
      ]
    },
    "dependent": {
      "name": "企业业绩",
      "proxy_variables": [
        {
          "variable_name": "ROA",
          "definition": "总资产收益率（%）",
          "measurement": "净利润 / 总资产 × 100%",
          "data_source": "CSMAR数据库",
          "justification": "会计利润角度，反映资产使用效率"
        },
        {
          "variable_name": "TobinQ",
          "definition": "托宾Q值",
          "measurement": "(股票市值 + 负债账面价值) / 总资产账面价值",
          "data_source": "CSMAR数据库",
          "justification": "市场价值角度，反映企业成长性和市场预期"
        }
      ]
    }
  },
  "mediating_moderating_variables": [
    {
      "type": "mediator",
      "name": "融资成本",
      "rationale": "绿色债券可能通过降低融资成本提升业绩",
      "proxy_variables": [
        {
          "variable_name": "FinancingCost",
          "definition": "企业综合融资成本（%）",
          "measurement": "(财务费用 / 总负债) × 100%",
          "data_source": "CSMAR数据库"
        }
      ]
    }
  ],
  "control_variables": [
    {
      "variable_name": "Size",
      "definition": "企业规模",
      "measurement": "ln(总资产)",
      "rationale": "控制规模效应",
      "data_source": "CSMAR"
    },
    {
      "variable_name": "Leverage",
      "definition": "资产负债率",
      "measurement": "总负债 / 总资产",
      "rationale": "控制财务杠杆",
      "data_source": "CSMAR"
    }
    // ... 更多控制变量
  ],
  "variable_relationships": "GreenBond → FinancingCost → ROA/TobinQ",
  "justification": "基于文献综述和理论推导，符合绿色金融理论框架和数据可得性"
}
```

### TheoryDesignerAgent

**作用**：构建理论框架和假设

**输出结构**：
```json
{
  "theoretical_framework": [
    {
      "theory_name": "信号传递理论（Signaling Theory）",
      "core_arguments": "信息不对称环境下，企业通过可信的信号向外部传递自身质量信息",
      "application": "绿色债券发行是企业向市场传递环保承诺和长期可持续发展能力的积极信号，降低投资者不确定性",
      "references": ["Spence (1973)", "Flannery et al. (2012)"]
    },
    {
      "theory_name": "资源基础理论（Resource-Based View）",
      "core_arguments": "企业竞争优势源于其拥有的独特资源和能力",
      "application": "绿色债券募集资金用于环保项目，构建绿色资源和能力，形成差异化竞争优势",
      "references": ["Barney (1991)", "Hart (1995)"]
    }
  ],
  "research_hypotheses": [
    {
      "hypothesis_id": "H1",
      "statement": "企业发行绿色债券对企业业绩有显著正向影响",
      "theoretical_basis": "基于信号传递理论和资源基础理论",
      "expected_direction": "positive",
      "mechanism": "降低信息不对称 + 构建绿色资源"
    },
    {
      "hypothesis_id": "H2",
      "statement": "融资成本在绿色债券与企业业绩关系中起中介作用",
      "theoretical_basis": "信号传递理论：积极信号降低风险溢价",
      "expected_direction": "negative_mediation",
      "mechanism": "绿色债券 → 降低融资成本 → 提升业绩"
    }
  ],
  "potential_mechanisms": [
    {
      "mechanism_name": "融资成本机制",
      "path": "绿色债券发行 → 降低融资成本 → 增加净利润 → 提升业绩",
      "testable": true,
      "test_method": "中介效应检验（Sobel test或Bootstrap）"
    },
    {
      "mechanism_name": "声誉机制",
      "path": "绿色债券发行 → 提升企业声誉 → 吸引ESG投资者 → 提升市值",
      "testable": true,
      "test_method": "使用企业社会责任评级作为代理变量"
    }
  ]
}
```

### ModelDesignerAgent

**作用**：设计计量模型

**输出结构**：
```json
{
  "baseline_model": {
    "model_type": "双向固定效应模型（Two-way Fixed Effects）",
    "equation": "Y_{it} = \\alpha + \\beta GreenBond_{it} + \\gamma X_{it} + \\mu_i + \\lambda_t + \\varepsilon_{it}",
    "variables": {
      "Y_{it}": "企业i在t期的业绩指标（ROA或TobinQ）",
      "GreenBond_{it}": "企业i在t期的绿色债券发行变量",
      "X_{it}": "控制变量向量",
      "\\mu_i": "企业固定效应",
      "\\lambda_t": "时间固定效应",
      "\\varepsilon_{it}": "随机误差项"
    },
    "key_coefficient": "\\beta",
    "coefficient_interpretation": "若β显著为正，则支持H1：绿色债券发行对企业业绩有正向影响",
    "estimation_method": "最小二乘法（OLS）with clustered standard errors at firm level",
    "econometric_concerns": [
      "内生性：可能存在反向因果（业绩好的企业更愿意发行绿色债券）",
      "遗漏变量偏误：未观测的企业特征可能同时影响发行决策和业绩"
    ]
  },
  "mechanism_models": [
    {
      "mechanism": "融资成本中介效应",
      "model_equations": [
        "FinancingCost_{it} = \\alpha_1 + \\beta_1 GreenBond_{it} + \\gamma_1 X_{it} + \\mu_i + \\lambda_t + \\varepsilon_{1,it}",
        "Y_{it} = \\alpha_2 + \\beta_2 GreenBond_{it} + \\beta_3 FinancingCost_{it} + \\gamma_2 X_{it} + \\mu_i + \\lambda_t + \\varepsilon_{2,it}"
      ],
      "test_method": "Bootstrap中介效应检验",
      "expected_result": "β1<0（绿色债券降低融资成本），β3<0（融资成本负向影响业绩），β1×β3显著"
    }
  ],
  "heterogeneity_models": [
    {
      "dimension": "企业所有制",
      "model": "Y_{it} = \\alpha + \\beta_1 GreenBond_{it} + \\beta_2 (GreenBond_{it} \\times SOE_{it}) + \\gamma X_{it} + \\mu_i + \\lambda_t + \\varepsilon_{it}",
      "interpretation": "β2显著则说明国有企业与非国有企业的效应存在差异"
    }
  ],
  "robustness_checks": [
    {
      "method": "倾向得分匹配（PSM-DID）",
      "purpose": "缓解选择性偏误",
      "procedure": "1) PSM匹配发行与未发行企业；2) 在匹配样本上进行DID估计"
    },
    {
      "method": "工具变量法（IV）",
      "purpose": "解决内生性问题",
      "instrument": "行业平均绿色债券发行率（排除本企业）",
      "justification": "满足相关性（同行业企业面临相似政策环境）和外生性（其他企业发行不直接影响本企业业绩）"
    },
    {
      "method": "更换被解释变量",
      "alternatives": ["ROE", "营业利润率", "净资产收益率"],
      "purpose": "检验结果对指标选择的稳健性"
    },
    {
      "method": "改变样本期",
      "alternatives": ["去掉2020年（疫情）", "只保留2017-2021年"],
      "purpose": "排除特殊时期干扰"
    }
  ],
  "econometric_specifications": {
    "cluster_level": "firm",
    "standard_errors": "clustered at firm level",
    "fixed_effects": ["firm", "year"],
    "additional_controls": "可选加入行业×年份固定效应"
  }
}
```

### DataAnalystAgent

**作用**：执行数据分析

**输出结构**：
```json
{
  "preprocessing": {
    "sample_selection": {
      "criteria": [
        "剔除金融类企业",
        "剔除ST/PT企业",
        "剔除缺失主要变量的观测值"
      ],
      "final_sample": {
        "firms": 1200,
        "observations": 7200,
        "period": "2015-2021"
      }
    },
    "winsorization": {
      "method": "1%和99%分位数缩尾",
      "variables": ["ROA", "TobinQ", "Size", "Leverage"]
    },
    "missing_values": "线性插值法（少于5%缺失）"
  },
  "descriptive_statistics": {
    "summary_table": {
      "ROA": {"mean": 5.23, "std": 4.67, "min": -15.2, "max": 28.4, "N": 7200},
      "TobinQ": {"mean": 2.15, "std": 1.34, "min": 0.62, "max": 8.91, "N": 7200},
      "GreenBond": {"mean": 0.18, "std": 0.38, "min": 0, "max": 1, "N": 7200}
    },
    "correlation_matrix": {
      "ROA_TobinQ": 0.42,
      "GreenBond_ROA": 0.15,
      "GreenBond_TobinQ": 0.23
    },
    "group_comparison": {
      "treated": {"mean_ROA": 6.12, "mean_TobinQ": 2.45, "N": 1296},
      "control": {"mean_ROA": 4.98, "mean_TobinQ": 2.08, "N": 5904},
      "t_test": {"ROA": {"t": 5.67, "p": 0.000}, "TobinQ": {"t": 7.23, "p": 0.000}}
    }
  },
  "baseline_regression": {
    "model_1": {
      "dependent_var": "ROA",
      "coefficients": {
        "GreenBond": {"coef": 1.23, "se": 0.34, "t": 3.62, "p": 0.000, "significance": "***"},
        "Size": {"coef": 0.56, "se": 0.12, "t": 4.67, "p": 0.000, "significance": "***"},
        "Leverage": {"coef": -2.34, "se": 0.45, "t": -5.20, "p": 0.000, "significance": "***"}
      },
      "R_squared": 0.345,
      "Adj_R_squared": 0.338,
      "N": 7200,
      "Fixed_Effects": ["Firm", "Year"]
    },
    "model_2": {
      "dependent_var": "TobinQ",
      "coefficients": {
        "GreenBond": {"coef": 0.287, "se": 0.068, "t": 4.22, "p": 0.000, "significance": "***"}
      },
      "R_squared": 0.412,
      "N": 7200
    },
    "interpretation": "绿色债券发行对ROA的影响为1.23个百分点（p<0.01），对TobinQ的影响为0.287（p<0.01），均显著为正，支持H1"
  },
  "mechanism_analysis": [
    {
      "mechanism": "融资成本",
      "step1": {
        "equation": "FinancingCost ~ GreenBond",
        "coefficient": {"GreenBond": {"coef": -0.45, "se": 0.12, "p": 0.000}}
      },
      "step2": {
        "equation": "ROA ~ GreenBond + FinancingCost",
        "coefficients": {
          "GreenBond": {"coef": 0.89, "se": 0.31, "p": 0.004},
          "FinancingCost": {"coef": -0.76, "se": 0.18, "p": 0.000}
        }
      },
      "mediation_test": {
        "indirect_effect": 0.342,
        "bootstrap_CI": [0.18, 0.51],
        "conclusion": "融资成本的中介效应显著（95% CI不包含0），中介效应占比27.8%"
      }
    }
  ],
  "heterogeneity_analysis": [
    {
      "dimension": "企业所有制",
      "SOE": {"GreenBond_coef": 0.89, "se": 0.42, "p": 0.034, "N": 3200},
      "non_SOE": {"GreenBond_coef": 1.56, "se": 0.48, "p": 0.001, "N": 4000},
      "group_diff_test": {"F": 4.23, "p": 0.040},
      "interpretation": "非国有企业的正向效应更强，可能因为市场化程度更高"
    }
  ],
  "robustness_checks": [
    {
      "method": "PSM-DID",
      "matching": {"method": "1:3 nearest neighbor", "caliper": 0.01, "balanced": true},
      "result": {"GreenBond_coef": 1.18, "se": 0.39, "p": 0.003},
      "conclusion": "与基准回归一致，系数略有下降但仍显著"
    },
    {
      "method": "IV估计",
      "instrument": "行业平均绿色债券发行率",
      "first_stage": {"F": 28.4, "p": 0.000, "comment": "工具变量强度足够"},
      "second_stage": {"GreenBond_coef": 1.67, "se": 0.58, "p": 0.004},
      "conclusion": "内生性调整后系数增大，说明OLS可能低估效应"
    }
  ],
  "conclusions": "基准回归表明绿色债券发行显著提升企业业绩；机制检验证实融资成本降低是重要中介路径；异质性分析显示非国有企业效应更强；多种稳健性检验均支持主要结论"
}
```

### ReviewerAgent

**作用**：评审研究质量

**输出结构**：
```json
{
  "overall_assessment": "本研究选题有意义，理论框架清晰，实证设计基本规范，但存在一些可改进之处。总体评价：有条件接受（Minor Revision）",
  "qualitative_analysis": {
    "endogeneity_rating": "C",
    "endogeneity_explanation": "内生性问题较为严重：(1) 反向因果：业绩好的企业更有能力发行绿色债券；(2) 遗漏变量：企业环保投入意愿等未观测特征可能同时影响发行和业绩；(3) 虽然使用了IV和PSM-DID，但工具变量的外生性存疑（行业平均可能受宏观政策影响）",
    "main_concerns": [
      "内生性处理不够充分，工具变量的外生性论证不足",
      "样本期较短（仅2015-2021），无法观察长期效应",
      "机制检验较薄弱，仅验证了融资成本一个渠道",
      "对政策背景的讨论不足，未考虑政策变化的影响"
    ],
    "strengths": [
      "选题契合绿色金融热点，具有现实意义",
      "理论框架完整，信号传递理论和资源基础理论的结合较好",
      "变量设计合理，控制变量较全面",
      "稳健性检验种类较多，PSM-DID和IV的使用提升了可信度",
      "异质性分析有启发性"
    ]
  },
  "quantitative_analysis": {
    "total_score": 78,
    "rating": "良好（B+）",
    "dimension_scores": {
      "research_question": {
        "score": 8,
        "comments": "选题有意义但新颖性一般，已有较多类似研究"
      },
      "literature_review": {
        "score": 7,
        "comments": "文献覆盖较全但深度不够，未充分梳理理论争议"
      },
      "theoretical_framework": {
        "score": 8,
        "comments": "理论适配性好，但机制推导可以更深入"
      },
      "research_design": {
        "score": 7,
        "comments": "设计基本合理，但内生性处理存在不足"
      },
      "data_quality": {
        "score": 8,
        "comments": "数据来源可靠，样本量充足，但时间跨度偏短"
      },
      "empirical_methods": {
        "score": 7,
        "comments": "方法选择恰当，但IV的外生性有待进一步论证"
      },
      "results_robustness": {
        "score": 8,
        "comments": "多种稳健性检验，结果一致性较好"
      },
      "interpretation": {
        "score": 8,
        "comments": "结果解释合理，经济意义讨论充分"
      },
      "writing_quality": {
        "score": 9,
        "comments": "结构清晰，表达规范，图表呈现专业"
      },
      "innovation": {
        "score": 7,
        "comments": "增量贡献有限，主要是验证性研究"
      }
    },
    "score_distribution": {
      "excellent_90_100": 0,
      "good_80_89": 3,
      "fair_70_79": 6,
      "poor_60_69": 1,
      "fail_below_60": 0
    }
  },
  "revision_suggestions": [
    {
      "priority": "high",
      "aspect": "内生性处理",
      "suggestion": "建议采用更有说服力的外生冲击作为工具变量，如地区绿色金融改革试验区政策（地理工具变量）或企业层面的外生事件（如管理层变更）",
      "references": ["Imbens & Wooldridge (2009)", "Roberts & Whited (2013)"]
    },
    {
      "priority": "high",
      "aspect": "机制检验",
      "suggestion": "补充其他机制渠道的检验，如声誉机制（使用ESG评级）、融资约束缓解机制（KZ指数）等，形成更完整的机制图谱",
      "references": []
    },
    {
      "priority": "medium",
      "aspect": "样本期扩展",
      "suggestion": "如果数据允许，建议将样本期延长至2022-2023年，观察疫情后的长期效应",
      "references": []
    },
    {
      "priority": "medium",
      "aspect": "理论深化",
      "suggestion": "可以讨论绿色债券可能的负面效应（如漂绿风险、资源配置扭曲），使理论分析更全面",
      "references": []
    },
    {
      "priority": "low",
      "aspect": "文献综述",
      "suggestion": "补充国际顶刊（JF、JFE、RFS）的最新研究，对比中外差异",
      "references": []
    },
    {
      "priority": "low",
      "aspect": "政策建议",
      "suggestion": "结论部分可增加针对性的政策建议，如绿色债券发行激励机制设计、防范漂绿风险的监管建议等",
      "references": []
    }
  ],
  "decision_recommendation": "Minor Revision（小修）",
  "estimated_revision_time": "1-2个月"
}
```

## 数据流转示例

完整流程的数据传递：

```python
# 步骤0: 输入解析
input_result = input_parser.run({"user_input": "我想研究绿色债券对企业业绩的影响"})
parsed_data = input_result["parsed_data"]
# parsed_data = {
#   "research_topic": "...",
#   "variable_x": {...},
#   "variable_y": {...},
#   "keywords": {...}
# }

# 步骤1: 文献收集（使用parsed_data中的关键词）
literature_result = literature_collector.run({
    "research_topic": parsed_data["research_topic"],
    "keyword_group_a": parsed_data["keywords"]["group_a"]["chinese"],
    "keyword_group_b": parsed_data["keywords"]["group_b"]["chinese"]
})
literature_list = literature_result["parsed_data"]["literature_list"]  # 结构化文献列表

# 步骤2: 变量设计（接收X/Y变量对象）
variable_result = variable_designer.run({
    "research_topic": parsed_data["research_topic"],
    "variable_x": parsed_data["variable_x"],  # 结构化对象
    "variable_y": parsed_data["variable_y"],  # 结构化对象
    "literature_summary": str(literature_list)  # 或传递literature_list本身
})
variable_system = variable_result["parsed_data"]  # 完整变量体系JSON

# 步骤3-6: 后续步骤类似，都传递结构化数据

# 最终所有parsed_data都可以直接用json.dump保存
import json
with open("results.json", "w") as f:
    json.dump({
        "input": parsed_data,
        "literature": literature_list,
        "variables": variable_system,
        # ...
    }, f, indent=2, ensure_ascii=False)
```

## 优势总结

1. **类型安全**：下游智能体知道期望的数据结构
2. **易于调试**：可以直接检查JSON对象，不用解析文本
3. **可扩展**：添加新字段只需更新schema定义
4. **可测试**：可以编写单元测试验证schema compliance
5. **文档化**：schema本身就是最好的API文档

## 测试方法

使用 `test_json_format.py` 测试：

```bash
python test_json_format.py
```

测试内容：
1. 单个智能体JSON输出格式
2. 完整流程每步的parsed_data验证
3. 必要字段检查（assert关键字段存在）
4. JSON序列化能力（确保可以json.dumps）

## 未来改进

1. **Schema 验证**：使用jsonschema库进行严格的schema验证
2. **类型提示**：使用Pydantic定义数据模型，自动验证和类型检查
3. **错误处理**：当JSON解析失败时，记录日志并尝试回退策略
4. **性能优化**：对于大型JSON，使用流式解析减少内存占用
