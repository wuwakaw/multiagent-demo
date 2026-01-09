"""
基于CAMEL框架的多智能体系统示例
CAMEL: Communicative Agents for "Mind" Exploration of Large Language Model Society
版本: camel-ai 0.2.82
"""

import os

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 根据 camel-ai 0.2.82 的 API 导入
try:
    # role_playing 是一个模块，需要从中导入 RolePlaying 类
    from camel.societies.role_playing import RolePlaying
    from camel.utils import print_text_animated
except ImportError:
    # 尝试其他可能的导入方式
    try:
        from camel.societies import role_playing
        # 如果 role_playing 是模块，尝试从中获取 RolePlaying
        if hasattr(role_playing, 'RolePlaying'):
            RolePlaying = role_playing.RolePlaying
        else:
            raise ImportError("无法从 role_playing 模块中找到 RolePlaying 类")
    except ImportError as e:
        try:
            from camel.societies import RolePlaying
        except ImportError:
            print(f"导入错误: {e}")
            print("请确保已安装 camel-ai==0.2.82")
            raise
from camel.models import ModelFactory
from camel.types import TaskType, ModelType, ModelPlatformType
from camel.configs import ChatGPTConfig

model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI,
    model_type=ModelType.GPT_4O_MINI,
    model_config_dict=ChatGPTConfig(temperature=0.0).as_dict(), # [Optional] the config for model
)

def role_playing_example():
    """角色扮演模式：产品经理与架构师的双角色协作"""
    
    # 定义任务
    task_prompt = (
        "设计一个多智能体协作系统的技术架构。"
        "需要考虑：1）智能体之间的通信机制；"
        "2）任务分配和协调策略；"
        "3）系统的可扩展性和容错性；"
        "4）关键技术选型建议。"
    )
    
    print("=" * 80)
    print("CAMEL 多智能体系统 - 角色扮演模式")
    print("=" * 80)
    print(f"\n任务: {task_prompt}\n")
    print("-" * 80)
    
    # 创建角色扮演会话
    # camel-ai 0.2.82 使用 RolePlaying 类
    role_play_session = RolePlaying(
        assistant_role_name="高级软件架构师",
        user_role_name="技术产品经理",
        task_prompt=task_prompt,
    )
    
    # 开始对话
    print_text_animated("\n" + "=" * 80 + "\n")
    print("开始对话...\n")
    inputmsg = role_play_session.init_chat()
    chat_turn_limit, n = 3, 0
    while n < chat_turn_limit:
        n += 1
        try:
            assistant_response, user_response = role_play_session.step(inputmsg)
            
            if assistant_response.terminated or user_response.terminated:
                print("\n对话已终止。\n")
                break
            
            # 获取角色名称
            assistant_role = (
                role_play_session.assistant_sys_msg.role_name 
                if hasattr(role_play_session, 'assistant_sys_msg') 
                else "架构师"
            )
            user_role = (
                role_play_session.user_sys_msg.role_name 
                if hasattr(role_play_session, 'user_sys_msg') 
                else "产品经理"
            )
            
            print_text_animated(f"\n[{assistant_role}]:\n{assistant_response.msg.content}\n")
            print("-" * 80)
            print_text_animated(f"\n[{user_role}]:\n{user_response.msg.content}\n")
            print("=" * 80)
        except Exception as e:
            print(f"发生错误: {e}")
            break
    
    print("\n" + "=" * 80)
    print("对话完成")
    print("=" * 80)


def multi_role_playing_example():
    """多角色协作模式：使用多个角色扮演会话实现团队协作"""
    
    # 定义任务
    task_prompt = (
        "协作开发一个多智能体协作平台。"
        "产品经理先提出需求，架构师设计架构，"
        "开发工程师实现功能，测试工程师进行测试。"
    )
    
    print("=" * 80)
    print("CAMEL 多角色协作模式")
    print("=" * 80)
    print(f"\n任务: {task_prompt}\n")
    print("-" * 80)
    
    # 第一轮：产品经理与架构师协作
    print("\n【第一轮：产品经理与架构师】\n")
    role_play_1 = RolePlaying(
        assistant_role_name="软件架构师",
        user_role_name="技术产品经理",
        task_prompt="产品经理提出多智能体协作平台的需求，架构师设计技术架构方案。",
    )
    
    chat_turn_limit, n = 4, 0
    inputmsg = role_play_1.init_chat()

    while n < chat_turn_limit:
        n += 1
        try:
            assistant_response, user_response = role_play_1.step(inputmsg)
            if assistant_response.terminated or user_response.terminated:
                break
            assistant_role = (
                role_play_1.assistant_sys_msg.role_name 
                if hasattr(role_play_1, 'assistant_sys_msg') 
                else "架构师"
            )
            user_role = (
                role_play_1.user_sys_msg.role_name 
                if hasattr(role_play_1, 'user_sys_msg') 
                else "产品经理"
            )
            print_text_animated(f"\n[{assistant_role}]:\n{assistant_response.msg.content}\n")
            print("-" * 80)
            print_text_animated(f"\n[{user_role}]:\n{user_response.msg.content}\n")
            print("=" * 80)
        except Exception as e:
            print(f"执行步骤时出错: {e}")
            break
    
    # 第二轮：架构师与开发工程师协作
    print("\n【第二轮：架构师与开发工程师】\n")
    role_play_2 = RolePlaying(
        assistant_role_name="开发工程师",
        user_role_name="软件架构师",
        task_prompt="架构师向开发工程师说明架构设计，开发工程师实现具体功能模块。",
    )
    
    n = 0
    while n < chat_turn_limit:
        n += 1
        try:
            assistant_response, user_response = role_play_2.step(inputmsg)
            if assistant_response.terminated or user_response.terminated:
                break
            assistant_role = (
                role_play_2.assistant_sys_msg.role_name 
                if hasattr(role_play_2, 'assistant_sys_msg') 
                else "开发工程师"
            )
            user_role = (
                role_play_2.user_sys_msg.role_name 
                if hasattr(role_play_2, 'user_sys_msg') 
                else "架构师"
            )
            print_text_animated(f"\n[{assistant_role}]:\n{assistant_response.msg.content}\n")
            print("-" * 80)
            print_text_animated(f"\n[{user_role}]:\n{user_response.msg.content}\n")
            print("=" * 80)
        except Exception as e:
            print(f"执行步骤时出错: {e}")
            break
    
    # 第三轮：开发工程师与测试工程师协作
    print("\n【第三轮：开发工程师与测试工程师】\n")
    role_play_3 = RolePlaying(
        assistant_role_name="测试工程师",
        user_role_name="开发工程师",
        task_prompt="开发工程师向测试工程师说明实现的功能，测试工程师设计测试策略和测试用例。",
    )
    
    n = 0
    while n < chat_turn_limit:
        n += 1
        try:
            assistant_response, user_response = role_play_3.step(inputmsg)
            if assistant_response.terminated or user_response.terminated:
                break
            assistant_role = (
                role_play_3.assistant_sys_msg.role_name 
                if hasattr(role_play_3, 'assistant_sys_msg') 
                else "测试工程师"
            )
            user_role = (
                role_play_3.user_sys_msg.role_name 
                if hasattr(role_play_3, 'user_sys_msg') 
                else "开发工程师"
            )
            print_text_animated(f"\n[{assistant_role}]:\n{assistant_response.msg.content}\n")
            print("-" * 80)
            print_text_animated(f"\n[{user_role}]:\n{user_response.msg.content}\n")
            print("=" * 80)
        except Exception as e:
            print(f"执行步骤时出错: {e}")
            break
    
    print("\n" + "=" * 80)
    print("多角色协作完成")
    print("=" * 80)


def main():
    """主函数"""
    
    # 检查API密钥
    if not os.getenv("OPENAI_API_KEY"):
        print(
            "警告：未检测到 OPENAI_API_KEY 环境变量。\n"
            "请先在系统环境变量或 .env 文件中配置有效的 OpenAI API Key。\n"
            "示例（PowerShell）: $env:OPENAI_API_KEY='your-api-key'"
        )
        return
    
    print("\n选择运行模式：")
    print("1. 角色扮演模式（产品经理 vs 架构师）")
    print("2. 多角色协作模式（产品经理 -> 架构师 -> 开发工程师 -> 测试工程师）")
    print("\n默认运行模式1...\n")
    
    # 默认运行角色扮演模式
    mode = "2"
    
    if mode == "1":
        role_playing_example()
    else:
        multi_role_playing_example()


if __name__ == "__main__":
    main()
