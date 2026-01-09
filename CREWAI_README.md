# CrewAI 多智能体系统

基于最新版 CrewAI 框架开发的多智能体协作系统示例。

## 功能特性

本系统包含三种不同类型的多智能体团队：

### 1. 研究型团队
- **技术研究员**：负责技术调研和资料收集
- **技术分析师**：负责技术方案分析和评估
- **适用场景**：技术选型、市场调研、技术趋势分析

### 2. 开发型团队
- **产品经理**：定义产品需求
- **系统架构师**：设计系统架构
- **高级开发工程师**：实现功能模块
- **测试工程师**：设计测试方案
- **适用场景**：软件开发全流程协作

### 3. 内容创作团队
- **技术写作者**：撰写技术文章初稿
- **技术编辑**：优化文章结构和可读性
- **技术评审员**：确保技术内容准确性
- **适用场景**：技术文档编写、博客创作

## 安装依赖

```bash
pip install -r requirements.txt
```

或者单独安装 CrewAI：

```bash
pip install 'crewai[tools]'
```

## 配置环境变量

在项目根目录创建 `.env` 文件，或设置系统环境变量：

```bash
OPENAI_API_KEY=your-api-key-here
```

PowerShell 设置方式：
```powershell
$env:OPENAI_API_KEY="your-api-key-here"
```

## 运行系统

```bash
python crewai_multi_agents.py
```

运行后会提示选择要运行的智能体团队类型。

## 代码结构

- `crewai_multi_agents.py`：主程序文件
  - `create_research_crew()`：创建研究型团队
  - `create_development_crew()`：创建开发型团队
  - `create_content_creation_crew()`：创建内容创作团队
  - 自定义工具：`analyze_technical_requirements`、`generate_architecture_doc`

## CrewAI 核心概念

### Agent（智能体）
每个智能体具有：
- `role`：角色定义
- `goal`：目标
- `backstory`：背景故事
- `tools`：可用工具（可选）
- `allow_delegation`：是否允许委托任务

### Task（任务）
每个任务包含：
- `description`：任务描述
- `agent`：执行任务的智能体
- `expected_output`：期望输出

### Crew（团队）
团队配置：
- `agents`：智能体列表
- `tasks`：任务列表
- `process`：执行流程（sequential/hierarchical）

## 扩展开发

你可以根据需要：
1. 添加新的智能体角色
2. 创建自定义工具（使用 `@tool` 装饰器）
3. 定义新的任务流程
4. 调整智能体的协作方式（sequential/hierarchical）

## 参考资源

- [CrewAI 官方文档](https://docs.crewai.com/)
- [CrewAI GitHub](https://github.com/joaomdmoura/crewAI)

