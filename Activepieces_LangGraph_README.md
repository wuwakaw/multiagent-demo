# Activepieces 工作流 LangGraph 实现

本文件将 Activepieces 的 JSON 工作流（`营销v2.0_邮件模板生成`）转换为 LangGraph 框架实现。

## 📋 工作流概述

这是一个邮件模板生成工作流，包含以下步骤：

1. **Catch Webhook** - 接收 Webhook 请求
2. **生成 SQL 查询** - 根据条件生成数据库查询语句
3. **执行 MySQL 查询** - 从数据库获取模板版本信息
4. **获取销售大脑数据** - 调用 API 获取销售实体列表
5. **处理卖方信息** - 提取和格式化卖方企业信息
6. **生成提示词** - 构建 LLM 提示词
7. **调用 LLM** - 使用 LLM 生成邮件模板结构
8. **预览邮件模板** - 调用 API 预览生成的模板
9. **返回结果** - 返回最终结果
10. **停止流程** - 结束工作流

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件或设置环境变量：

```bash
# OpenAI API Key（必需）
OPENAI_API_KEY=your-openai-api-key

# MySQL 数据库配置（如果需要执行数据库查询）
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=your-database

# 后端回调认证（用于 API 调用）
BACKEND_CALLBACK_AUTH=your-auth-token
```

### 3. 运行工作流

```bash
python activepieces_langgraph_workflow.py
```

## 📝 代码结构

### 状态定义

```python
class WorkflowState(TypedDict):
    webhook_body: dict              # Webhook 输入数据
    sql_query: Optional[str]        # SQL 查询语句
    template_version_data: Optional[dict]  # 模板版本数据
    sales_brain_data: Optional[dict]      # 销售大脑数据
    seller_info: Optional[dict]          # 卖方信息
    prompt: Optional[str]                # 生成的提示词
    template_structure: Optional[dict]    # 模板结构
    preview_result: Optional[dict]        # 预览结果
    final_result: Optional[dict]          # 最终结果
    error: Optional[str]                  # 错误信息
    current_step: str                     # 当前步骤
```

### 工作流节点

每个步骤都对应一个节点函数：

- `trigger_node()` - 接收 Webhook 数据
- `step_4_generate_sql()` - 生成 SQL 查询
- `step_3_execute_mysql()` - 执行 MySQL 查询
- `step_5_get_sales_brain()` - 获取销售大脑数据
- `step_7_process_seller_info()` - 处理卖方信息
- `step_1_generate_prompt()` - 生成提示词
- `step_2_call_llm()` - 调用 LLM
- `step_6_preview_template()` - 预览模板
- `step_8_return_result()` - 返回结果
- `step_55_stop_flow()` - 停止流程

### 工作流图

工作流按顺序执行：

```
trigger → step_4 → step_3 → step_5 → step_7 → step_1 → step_2 → step_6 → step_8 → step_55 → END
```

## 🔧 自定义使用

### 方式 1: 直接调用

```python
from activepieces_langgraph_workflow import EmailTemplateWorkflow

# 创建工作流实例
workflow = EmailTemplateWorkflow(model_name="gpt-4o-mini", temperature=0.7)

# 准备 Webhook 数据
webhook_body = {
    "body": {
        "options": {"testMessage": False},
        "payload": {
            "emailTemplateId": "123",
            "seq": 1
        },
        "messageGenerateReqDTO": {
            "payload": {
                "userId": "113",
                "conversationId": "xxx",
                "sessionId": "xxx"
            },
            "sellerInfo": {
                "baseInfo": {
                    "companyName": "示例公司",
                    "companyIntro": "公司介绍",
                    "mainProduct": "主要产品",
                    "website": "https://example.com"
                }
            }
        },
        "chatContent": "请生成一封营销邮件"
    }
}

# 运行工作流
result = workflow.run(webhook_body)
```

### 方式 2: 作为 API 服务

```python
from flask import Flask, request, jsonify
from activepieces_langgraph_workflow import EmailTemplateWorkflow

app = Flask(__name__)
workflow = EmailTemplateWorkflow()

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    webhook_body = request.json
    result = workflow.run(webhook_body)
    return jsonify(result)

if __name__ == '__main__':
    app.run(port=5000)
```

## 📊 与原 Activepieces 工作流的对应关系

| Activepieces 步骤 | LangGraph 节点 | 说明 |
|------------------|---------------|------|
| trigger | `trigger_node` | 接收 Webhook |
| step_4 | `step_4_generate_sql` | 生成 SQL 查询 |
| step_3 | `step_3_execute_mysql` | 执行 MySQL 查询 |
| step_5 | `step_5_get_sales_brain` | HTTP GET 请求 |
| step_7 | `step_7_process_seller_info` | 处理卖方信息 |
| step_1 | `step_1_generate_prompt` | 生成提示词 |
| step_2 | `step_2_call_llm` | 调用子流程（LLM） |
| step_6 | `step_6_preview_template` | HTTP POST 请求 |
| step_8 | `step_8_return_result` | 返回结果（可选） |
| step_55 | `step_55_stop_flow` | 停止流程 |

## 🔍 关键功能说明

### 1. 模板变量渲染

原 Activepieces 使用 `{{variable}}` 语法，本实现通过 `render_template_variables()` 函数模拟。

### 2. MySQL 查询

使用 `pymysql` 库执行数据库查询，支持参数化查询。

### 3. HTTP 请求

使用 `requests` 库发送 HTTP 请求，支持 GET 和 POST 方法。

### 4. LLM 调用

使用 LangChain 的 `ChatOpenAI` 调用 OpenAI API，支持 JSON 格式输出。

### 5. 错误处理

每个节点都包含错误处理逻辑，错误信息存储在状态中。

## ⚙️ 配置选项

### 模型配置

```python
workflow = EmailTemplateWorkflow(
    model_name="gpt-4o-mini",  # 模型名称
    temperature=0.7            # 温度参数
)
```

### 数据库配置

通过环境变量或直接传入 `execute_mysql_query()` 函数：

```python
connection_config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'password',
    'database': 'database_name',
    'charset': 'utf8mb4'
}
```

## 🐛 故障排除

### 1. MySQL 连接失败

- 检查数据库配置是否正确
- 确认数据库服务是否运行
- 检查网络连接

### 2. HTTP 请求失败

- 检查 URL 是否正确
- 确认认证信息是否有效
- 检查网络连接

### 3. LLM 调用失败

- 检查 OpenAI API Key 是否正确
- 确认 API 配额是否充足
- 检查网络连接

### 4. JSON 解析错误

- 检查 LLM 返回的 JSON 格式是否正确
- 可能需要调整提示词以确保输出格式正确

## 📚 扩展开发

### 添加新节点

```python
def new_step(self, state: WorkflowState) -> dict:
    """新步骤"""
    # 实现逻辑
    return {
        "current_step": "new_step",
        "result": "some_result"
    }

# 在 _build_graph() 中添加
workflow.add_node("new_step", self.new_step)
workflow.add_edge("previous_step", "new_step")
```

### 修改执行顺序

在 `_build_graph()` 中修改边的连接：

```python
# 修改执行顺序
workflow.add_edge("step_1", "new_step")
workflow.add_edge("new_step", "step_2")
```

### 添加条件分支

```python
def route_function(self, state: WorkflowState) -> Literal["path_a", "path_b"]:
    """路由函数"""
    if condition:
        return "path_a"
    else:
        return "path_b"

# 添加条件边
workflow.add_conditional_edges(
    "decision_node",
    self.route_function,
    {
        "path_a": "node_a",
        "path_b": "node_b"
    }
)
```

## 📄 许可证

本实现基于原 Activepieces 工作流转换而来，仅供学习和参考使用。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

