# LaTeX 输出功能快速开始

## 🎯 5分钟快速体验

### 第1步：安装依赖（如已安装可跳过）

```bash
pip install -r requirements.txt
```

### 第2步：配置 API Key

```bash
# 编辑 .env 文件
cp .env.template .env
nano .env

# 设置你的 API Key
DASHSCOPE_API_KEY=sk-your-api-key-here
DEFAULT_MODEL=qwen-plus
```

### 第3步：运行测试

```bash
python test_latex_output.py full
```

这将：
1. ✅ 自动解析研究主题："数字化转型对企业创新绩效的影响"
2. ✅ 搜集相关文献（8篇）
3. ✅ 设计变量体系
4. ✅ 构建理论框架
5. ✅ 设计计量模型
6. ✅ 模拟数据分析
7. ✅ **生成12000字LaTeX论文**

### 第4步：查看结果

```bash
# 查看生成的文件
ls -lh output/research/

# 你会看到：
# paper_YYYYMMDD_HHMMSS.tex     <- LaTeX 论文（可编译为PDF）
# report_YYYYMMDD_HHMMSS.md     <- Markdown 备份
# report_YYYYMMDD_HHMMSS.json   <- JSON 数据
```

### 第5步：编译为 PDF

```bash
cd output/research
xelatex paper_YYYYMMDD_HHMMSS.tex
xelatex paper_YYYYMMDD_HHMMSS.tex  # 再次编译以生成目录和交叉引用
```

---

## 📝 自定义你的研究

### 示例1：研究碳交易政策

```python
from orchestrator import ResearchOrchestrator

orchestrator = ResearchOrchestrator()

results = orchestrator.run_full_pipeline(
    user_input="我想研究碳交易政策对企业绿色创新的影响，特别关注制造业上市公司",
    min_papers=12,
    word_count=15000,
)

print(f"LaTeX论文: {results['latex_path']}")
```

### 示例2：研究AI对劳动力市场的影响

```python
results = orchestrator.run_full_pipeline(
    research_topic="人工智能技术对劳动力市场结构的影响研究",
    keyword_group_a=["人工智能", "AI技术", "机器学习"],
    keyword_group_b=["劳动力市场", "就业结构", "工资水平"],
    min_papers=15,
    word_count=18000,
)
```

### 示例3：启用审稿功能

```python
results = orchestrator.run_full_pipeline(
    user_input="ESG投资对企业财务绩效的影响",
    enable_review=True,  # 自动进行审稿评审
    min_papers=10,
    word_count=12000,
)

# 查看审稿意见
print(results['review_report_data'])
```

---

## 🎨 生成的 LaTeX 论文特点

### ✅ 完整的文档结构
- 标题页（含作者、单位）
- 摘要、关键词、JEL分类号
- 自动生成目录
- 6个标准章节

### ✅ 符合经济学规范
- **因果识别策略**：单独章节详细论证
- **叙事化论证**：所有系数转化为经济意义
- **规范化表达**：参考《经济研究》格式

### ✅ 专业的排版
```latex
% 三线表
\begin{table}[htbp]
\caption{基准回归结果}
\begin{tabular}{lcccc}
\toprule
 & (1) & (2) & (3) & (4) \\
\midrule
$X$ & 0.245** & 0.312*** & ... \\
 & (0.098) & (0.087) & ... \\
\bottomrule
\end{tabular}
\end{table}

% 公式编号
\begin{equation}
Y_{it} = \alpha + \beta X_{it} + \gamma Controls_{it} + \mu_i + \lambda_t + \varepsilon_{it}
\label{eq:baseline}
\end{equation}

% 文献引用
根据 \citet{reference1} 的研究...
```

---

## 🔧 常用参数说明

| 参数 | 说明 | 默认值 | 推荐值 |
|------|------|--------|--------|
| `user_input` | 自然语言研究主题 | - | "我想研究..." |
| `research_topic` | 标准化研究主题 | - | "XX对YY的影响" |
| `min_papers` | 文献数量 | 10 | 10-15 |
| `word_count` | 论文字数 | 8000 | 12000-18000 |
| `enable_review` | 启用审稿 | False | True（推荐） |

---

## 📊 输出文件对比

| 格式 | 用途 | 优势 | 劣势 |
|------|------|------|------|
| **LaTeX (.tex)** | 投稿、打印 | 专业排版、可编译PDF | 需要LaTeX环境 |
| **Markdown (.md)** | 阅读、修改 | 易读、易编辑 | 格式简单 |
| **JSON (.json)** | 数据处理 | 结构化、可编程 | 不易阅读 |

---

## 🆘 遇到问题？

### LaTeX 编译错误

```bash
# 安装完整的 LaTeX 环境
# macOS
brew install --cask mactex

# Ubuntu
sudo apt-get install texlive-full

# Windows
# 下载并安装 MiKTeX 或 TeX Live
```

### API 调用超时

```python
# 使用更小的模型加快速度
# 编辑 .env
DEFAULT_MODEL=qwen-turbo  # 最快
# DEFAULT_MODEL=qwen-plus  # 推荐（平衡）
# DEFAULT_MODEL=qwen-max   # 最强
```

### 论文质量不满意

```python
# 1. 增加文献数量
min_papers=15

# 2. 增加论文字数
word_count=15000

# 3. 启用审稿功能
enable_review=True

# 4. 使用更强的模型
DEFAULT_MODEL=qwen-max
```

---

## 📚 下一步

1. **阅读完整文档**: [LATEX_OUTPUT_GUIDE.md](LATEX_OUTPUT_GUIDE.md)
2. **了解系统架构**: [README.md](README.md)
3. **查看API文档**: [docs/API.md](docs/API.md)
4. **加入讨论**: 提交 Issue 或 Pull Request

---

**开始你的第一篇AI生成的经济学论文吧！** 🚀

```bash
python test_latex_output.py full
```
