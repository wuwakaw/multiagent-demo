"""
基于 LangGraph 的多智能体系统示例

本示例展示了如何使用 LangGraph 框架构建一个多智能体协作系统，
包含产品经理、架构师、开发工程师和测试工程师四个角色，
通过监督者模式协调各智能体的工作流程。
"""

import os
from typing import TypedDict, Annotated, Literal
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import tool

# 加载环境变量
load_dotenv()

# 确保设置了 OpenAI API Key
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("请设置 OPENAI_API_KEY 环境变量")


# ==================== 状态定义 ====================
class AgentState(TypedDict):
    """多智能体系统的状态定义"""
    messages: Annotated[list, lambda x, y: x + y]  # 消息历史
    current_agent: str  # 当前执行的智能体
    task: str  # 当前任务描述
    iteration: int  # 迭代次数
    final_result: str  # 最终结果


# ==================== 工具定义 ====================
@tool
def search_documentation(query: str) -> str:
    """搜索技术文档工具"""
    # 这里可以集成真实的文档搜索功能
    return f"根据查询 '{query}' 找到的相关文档内容..."


@tool
def code_review(code: str) -> str:
    """代码审查工具"""
    return f"代码审查结果：代码质量良好，建议优化性能..."


# ==================== 智能体定义 ====================
class MultiAgentSystem:
    """多智能体系统类"""
    
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.7):
        """初始化多智能体系统"""
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.memory = MemorySaver()
        
        # 定义各智能体的系统提示
        self.agent_prompts = {
            "product_manager": """你是一位经验丰富的产品经理。你的职责是：
1. 分析用户需求，明确产品功能
2. 定义产品规格和验收标准
3. 与架构师协作，确保需求的技术可行性
4. 输出清晰、可执行的产品需求文档

请用中文回复，保持专业和清晰。""",
            
            "architect": """你是一位资深的技术架构师。你的职责是：
1. 根据产品需求设计技术架构
2. 选择合适的技术栈和框架
3. 定义系统模块和接口规范
4. 与开发工程师协作，确保架构的可实现性

请用中文回复，提供详细的技术方案。""",
            
            "developer": """你是一位优秀的开发工程师。你的职责是：
1. 根据架构设计实现具体功能
2. 编写高质量的代码
3. 进行单元测试和代码审查
4. 与测试工程师协作，确保代码质量

请用中文回复，提供具体的实现方案。""",
            
            "tester": """你是一位专业的测试工程师。你的职责是：
1. 设计测试用例和测试策略
2. 执行功能测试和集成测试
3. 发现和报告缺陷
4. 确保产品质量符合标准

请用中文回复，提供详细的测试报告。"""
        }
        
        # 构建工作流图
        self.graph = self._build_graph()
    
    def _get_agent_response(self, agent_name: str, state: AgentState) -> dict:
        """获取指定智能体的响应"""
        system_prompt = self.agent_prompts.get(agent_name, "")
        
        # 构建消息列表
        messages = [SystemMessage(content=system_prompt)]
        
        # 添加任务描述
        if state["task"]:
            messages.append(HumanMessage(
                content=f"任务描述：{state['task']}"
            ))
        
        # 添加历史消息，让智能体了解之前的讨论
        if state["messages"]:
            messages.extend(state["messages"])
        
        # 添加当前提示
        messages.append(HumanMessage(
            content="请根据你的角色职责，基于上述信息提供专业的分析和建议。"
        ))
        
        # 调用 LLM
        response = self.llm.invoke(messages)
        
        return {
            "messages": [response],
            "current_agent": agent_name,
            "iteration": state.get("iteration", 0) + 1
        }
    
    def product_manager_agent(self, state: AgentState) -> dict:
        """产品经理智能体"""
        return self._get_agent_response("product_manager", state)
    
    def architect_agent(self, state: AgentState) -> dict:
        """架构师智能体"""
        return self._get_agent_response("architect", state)
    
    def developer_agent(self, state: AgentState) -> dict:
        """开发工程师智能体"""
        return self._get_agent_response("developer", state)
    
    def tester_agent(self, state: AgentState) -> dict:
        """测试工程师智能体"""
        return self._get_agent_response("tester", state)
    
    def supervisor(self, state: AgentState) -> Literal["product_manager", "architect", "developer", "tester", "end"]:
        """监督者：决定下一个执行的智能体"""
        current_agent = state.get("current_agent", "")
        
        # 定义工作流程：产品经理 -> 架构师 -> 开发工程师 -> 测试工程师 -> 结束
        workflow_map = {
            "product_manager": "architect",
            "architect": "developer",
            "developer": "tester",
            "tester": "end",
            "": "product_manager"  # 初始状态
        }
        
        # 根据当前智能体决定下一个智能体
        next_agent = workflow_map.get(current_agent, "end")
        return next_agent
    
    def finalize(self, state: AgentState) -> dict:
        """生成最终结果"""
        # 汇总所有智能体的输出
        all_messages = state.get("messages", [])
        summary = "\n\n".join([
            f"{msg.content}" for msg in all_messages if hasattr(msg, 'content')
        ])
        
        final_result = f"""多智能体协作完成报告
========================

任务：{state.get('task', '未指定')}

协作流程：
{summary}

所有智能体已完成各自的工作，项目可以进入下一阶段。
"""
        
        return {
            "final_result": final_result,
            "messages": [AIMessage(content=final_result)]
        }
    
    def _build_graph(self) -> StateGraph:
        """构建工作流图"""
        # 创建状态图
        workflow = StateGraph(AgentState)
        
        # 添加节点
        workflow.add_node("product_manager", self.product_manager_agent)
        workflow.add_node("architect", self.architect_agent)
        workflow.add_node("developer", self.developer_agent)
        workflow.add_node("tester", self.tester_agent)
        workflow.add_node("finalize", self.finalize)
        
        # 设置入口点
        workflow.set_entry_point("product_manager")
        
        # 添加条件边：监督者决定下一个节点
        # 产品经理 -> 架构师
        workflow.add_conditional_edges(
            "product_manager",
            self.supervisor,
            {
                "architect": "architect",
                "end": "finalize"
            }
        )
        
        # 架构师 -> 开发工程师
        workflow.add_conditional_edges(
            "architect",
            self.supervisor,
            {
                "developer": "developer",
                "end": "finalize"
            }
        )
        
        # 开发工程师 -> 测试工程师
        workflow.add_conditional_edges(
            "developer",
            self.supervisor,
            {
                "tester": "tester",
                "end": "finalize"
            }
        )
        
        # 测试工程师 -> 结束
        workflow.add_conditional_edges(
            "tester",
            self.supervisor,
            {
                "end": "finalize"
            }
        )
        
        # 最终节点连接到结束
        workflow.add_edge("finalize", END)
        
        # 编译图（启用检查点以支持记忆）
        return workflow.compile(checkpointer=self.memory)
    
    def run(self, task: str, config: dict = None) -> dict:
        """运行多智能体系统"""
        if config is None:
            config = {"configurable": {"thread_id": "1"}}
        
        initial_state = {
            "messages": [],
            "current_agent": "",
            "task": task,
            "iteration": 0,
            "final_result": ""
        }
        
        print(f"\n{'='*60}")
        print(f"开始执行任务：{task}")
        print(f"{'='*60}\n")
        
        # 运行图
        final_state = None
        for state in self.graph.stream(initial_state, config):
            # 打印每个节点的输出
            for node_name, node_state in state.items():
                if node_name != "__end__" and node_state.get("messages"):
                    last_message = node_state["messages"][-1]
                    if hasattr(last_message, 'content'):
                        agent_name = node_state.get("current_agent", node_name)
                        print(f"[{agent_name.upper()}]")
                        print(f"{last_message.content}\n")
                        print("-" * 60)
                        print()
            
            final_state = state
        
        # 返回最终状态
        if final_state and "finalize" in final_state:
            print("\n" + "="*60)
            print("最终结果：")
            print("="*60)
            print(final_state["finalize"]["final_result"])
        
        return final_state


# ==================== 主程序 ====================
def main():
    """主函数：演示多智能体系统"""
    
    # 创建多智能体系统
    system = MultiAgentSystem(model_name="gpt-4o-mini", temperature=0.7)
    
    # 定义任务
    task = """
    设计并开发一个在线待办事项管理系统，需要包含以下功能：
    1. 用户注册和登录
    2. 创建、编辑、删除待办事项
    3. 待办事项的分类和优先级设置
    4. 任务完成状态跟踪
    5. 数据持久化存储
    
    请各智能体协作完成从需求分析到测试的完整流程。
    """
    
    # 运行系统
    result = system.run(task)
    
    return result


if __name__ == "__main__":
    main()

