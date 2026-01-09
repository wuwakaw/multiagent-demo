import os
import asyncio
import time

from autogen_agentchat.messages import TextMessage
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient

# 加载 .env 文件中的环境变量
load_dotenv()


async def main() -> None:
    """Run a demo multi-agent chat using the new autogen-agentchat API."""

    # 初始化大模型客户端（可根据需要调整模型名称）
    model_client = OpenAIChatCompletionClient(model="gpt-4o")

    # 用户代理（代表人类用户）
    user = UserProxyAgent(
        name="User",
    )

    # 写作代理：负责生成技术博客初稿
    writer = AssistantAgent(
        name="WriterAgent",
        model_client=model_client,
        system_message=(
            "你是一名中文技术写作者，擅长撰写结构清晰、内容深入的技术博客。"
            "输出时请包含：引言、正文（可分小节）、总结。"
        ),
    )

    # 审稿代理：负责评审并提出改进建议
    reviewer = AssistantAgent(
        name="ReviewerAgent",
        model_client=model_client,
        system_message=(
            "你是一名严格的技术编辑，负责审阅 WriterAgent 的草稿，"
            "检查逻辑性、结构性和表述清晰度，并给出具体修改建议（使用中文）。"
        ),
    )

    # 规划代理：根据用户需求先给出大纲，再协调写作方向
    planner = AssistantAgent(
        name="PlannerAgent",
        model_client=model_client,
        system_message=(
            "你是一名内容规划师。收到用户需求后，"
            "先用中文给出要写文章的大纲（项目符号列表），"
            "再根据大纲给 WriterAgent 提示，必要时回应 ReviewerAgent 的反馈。"
        ),
    )
    termination = MaxMessageTermination(3)

    # 多智能体团队：轮询式对话
    team = RoundRobinGroupChat(
        [user, planner, writer, reviewer],
        termination_condition=termination,
        max_turns=8,
    )

    # 启动团队对话
    task = "请围绕'多智能体协作的应用场景'写一篇约 200 字的中文技术博客，要求：1）有引言、正文、总结结构；2）正文中给出 1 个实际案例；3）整体风格偏技术向、面向开发者。"

    
    print("=" * 80)
    print("开始多智能体协作任务...")
    print("=" * 80)
    
    result = await team.run(task=task)
    for r in result.messages:
        if isinstance(r, TextMessage):
            print(r.content)
    print("=" * 80)



if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print(
            "警告：未检测到 OPENAI_API_KEY 环境变量。\n"
            "请先在系统环境变量或 .env 中配置有效的 OpenAI API Key。"
        )

    asyncio.run(main())

