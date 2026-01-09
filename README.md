## CAMEL 多智能体系统示例

本示例基于 CAMEL (Communicative Agents for "Mind" Exploration of Large Language Model Society) 框架，演示多智能体协作场景。

**版本：camel-ai 0.2.82**

### CAMEL 框架简介

CAMEL 是一个开源的多智能体框架，旨在探索大规模语言模型社会中智能体的协作与扩展规律。该框架通过角色扮演和标准化流程，解决了单智能体在复杂任务中的局限性。

### 功能特性

本示例包含两种多智能体协作模式：

1. **角色扮演模式**：产品经理与架构师的双角色协作
   - 产品经理：分析需求，定义功能
   - 架构师：设计技术架构，提供实现方案
   - 两个智能体通过多轮对话协作完成技术架构设计任务

2. **多角色协作模式**：包含四个专业角色的链式协作
   - 第一轮：产品经理 ↔ 架构师（需求分析与架构设计）
   - 第二轮：架构师 ↔ 开发工程师（架构实现与功能开发）
   - 第三轮：开发工程师 ↔ 测试工程师（功能测试与质量保证）
   - 通过多个角色扮演会话实现完整的开发流程

### 1. 环境准备

1. 安装 Python 3.10+（推荐使用虚拟环境）
2. 安装依赖：

```bash
pip install -r requirements.txt
```

或者直接安装指定版本：

```bash
pip install camel-ai==0.2.82 openai python-dotenv
```

3. 配置 OpenAI API Key：

在 PowerShell 中设置环境变量：

```powershell
$env:OPENAI_API_KEY="你的_API_Key"
```

或者创建 `.env` 文件：

```
OPENAI_API_KEY=你的_API_Key
```

### 2. 运行多智能体系统

```bash
python camel_multi_agents.py
```

脚本会启动 CAMEL 多智能体系统，智能体之间会进行协作对话，完成指定的任务。

### 3. 代码说明

- `camel_multi_agents.py`：主程序文件，包含两种多智能体协作模式的实现
  - `role_playing_example()`：双角色协作模式
  - `multi_role_playing_example()`：多角色链式协作模式
- `requirements.txt`：项目依赖包列表（camel-ai==0.2.82）
- `.env`：环境变量配置文件（需要自行创建）

### 4. API 使用说明

camel-ai 0.2.82 版本使用 `role_playing` 函数创建角色扮演会话：

```python
from camel.societies import role_playing

role_play_session = role_playing(
    assistant_role_name="架构师",
    user_role_name="产品经理",
    task_prompt="任务描述",
)

# 执行对话步骤
assistant_response, user_response = role_play_session.step()
```

### 5. 扩展开发

你可以根据需要：
- 修改智能体的角色定义和任务描述
- 调整对话轮数（`chat_turn_limit`）
- 添加更多角色扮演会话实现复杂的协作流程
- 集成外部工具和记忆模块

### 参考资源

- [CAMEL GitHub 仓库](https://github.com/camel-ai/camel)
- [CAMEL 官方文档](https://camel-ai.readthedocs.io/)
- [CAMEL 论文](https://arxiv.org/abs/2303.17760)


