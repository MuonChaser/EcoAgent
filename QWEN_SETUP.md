# 阿里云通义千问配置完成说明

## ✅ 已完成的配置

### 1. API配置更新
- ✅ 已在 `.env` 文件中添加阿里云API Key
- ✅ 配置了阿里云API Base URL
- ✅ 设置默认模型为 `qwen-plus`

### 2. 代码更新
- ✅ 更新 `config/config.py` 支持阿里云配置
- ✅ 更新 `agents/base_agent.py` 使用新的API配置
- ✅ 修复了 LangChain 导入问题（`langchain.schema` -> `langchain_core.messages`）

### 3. 文档更新
- ✅ 更新 `.env.template` 添加阿里云配置说明
- ✅ 更新 `README.md` 添加阿里云使用指南
- ✅ 添加模型选择说明和常见问题

### 4. 测试工具
- ✅ 创建 `test_qwen.py` - 测试阿里云API连接
- ✅ 创建 `quick_start.py` - 快速开始示例

## 🎯 当前配置

```env
DASHSCOPE_API_KEY=sk-13487e6596b54bdabf441e1a50f0f1e8
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DEFAULT_MODEL=qwen-plus
```

## 📊 可用的通义千问模型

| 模型 | 特点 | 推荐场景 |
|-----|------|---------|
| qwen-turbo | 速度最快，成本最低 | 快速测试、简单任务 |
| qwen-plus | **当前使用**，性能均衡 | 大多数研究任务 |
| qwen-max | 能力最强 | 复杂分析、高质量写作 |
| qwen-max-longcontext | 支持长文本 | 长文献分析 |

## 🚀 使用方法

### 1. 测试连接
```bash
python test_qwen.py
```

### 2. 快速开始
```bash
python quick_start.py
```

### 3. 完整示例
```bash
python examples/advanced_usage.py
```

## 🔄 切换模型

编辑 `.env` 文件中的 `DEFAULT_MODEL`：

```env
# 使用最快模型
DEFAULT_MODEL=qwen-turbo

# 使用平衡模型（推荐）
DEFAULT_MODEL=qwen-plus

# 使用最强模型
DEFAULT_MODEL=qwen-max

# 使用长文本模型
DEFAULT_MODEL=qwen-max-longcontext
```

## 💡 优势

1. **国内访问稳定**：无需VPN，直接访问
2. **中文能力强**：针对中文优化，处理中文文献效果更好
3. **成本更低**：相比OpenAI更经济实惠
4. **响应速度快**：国内服务器，延迟更低
5. **兼容OpenAI API**：无需修改代码逻辑

## 📝 注意事项

1. 系统会自动优先使用阿里云配置（如果 DASHSCOPE_API_KEY 存在）
2. 如需切换回OpenAI，注释掉 DASHSCOPE_API_KEY 即可
3. 不同模型的计费标准不同，请参考阿里云百炼官网
4. API Key 请妥善保管，不要泄露

## 🆕 新增文件

- `test_qwen.py` - API连接测试脚本
- `quick_start.py` - 快速开始示例
- `QWEN_SETUP.md` - 本说明文档（此文件）

## 📖 相关文档

- [阿里云百炼平台](https://bailian.console.aliyun.com/)
- [通义千问API文档](https://help.aliyun.com/zh/dashscope/)
- [项目README](README.md)

---

**配置完成时间**: 2026年1月22日
**配置状态**: ✅ 已完成并测试通过
