"""
基于 CrewAI 框架的多智能体系统示例
CrewAI: 一个用于编排角色扮演 AI 智能体的框架
版本: 最新版 CrewAI
"""

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

# 加载环境变量
load_dotenv()

# 检查 API Key
if not os.getenv("OPENAI_API_KEY"):
    print(
        "警告：未检测到 OPENAI_API_KEY 环境变量。\n"
        "请先在系统环境变量或 .env 文件中配置有效的 OpenAI API Key。\n"
        "示例（PowerShell）: $env:OPENAI_API_KEY='your-api-key'"
    )


# 定义自定义工具
@tool("分析技术需求")
def analyze_technical_requirements(requirements: str) -> str:
    """
    分析技术需求并提取关键信息
    
    Args:
        requirements: 需求描述文本
        
    Returns:
        分析结果
    """
    return f"已分析需求：{requirements}，提取了关键功能点和非功能需求。"


@tool("生成架构文档")
def generate_architecture_doc(architecture: str) -> str:
    """
    生成架构设计文档
    
    Args:
        architecture: 架构描述
        
    Returns:
        文档路径或内容
    """
    return f"已生成架构文档，包含：{architecture}"


def create_research_crew():
    """创建研究型多智能体团队：用于技术调研和分析"""
    
    # 定义智能体
    researcher = Agent(
        role='技术研究员',
        goal='深入调研和分析技术趋势，提供准确的技术信息',
        backstory=(
            '你是一位经验丰富的技术研究员，拥有10年的技术调研经验。'
            '你擅长从多个角度分析技术问题，能够快速找到可靠的技术资料和最佳实践。'
            '你的研究报告总是结构清晰、数据详实、结论明确。'
        ),
        verbose=True,
        allow_delegation=False
    )
    
    analyst = Agent(
        role='技术分析师',
        goal='分析技术方案的可行性和优劣，提供专业建议',
        backstory=(
            '你是一位资深的技术分析师，擅长评估技术方案的优缺点。'
            '你能够从性能、成本、可维护性、可扩展性等多个维度进行综合分析。'
            '你的分析报告总是客观、全面、具有可操作性。'
        ),
        verbose=True,
        allow_delegation=False
    )
    
    # 定义任务
    research_task = Task(
        description=(
            '调研多智能体系统的技术架构方案。'
            '需要涵盖：1）主流的多智能体框架对比；'
            '2）通信机制和协调策略；'
            '3）关键技术选型建议；'
            '4）实际应用案例。'
            '请提供详细的技术调研报告。'
        ),
        agent=researcher,
        expected_output='一份结构化的技术调研报告，包含框架对比、技术选型建议和应用案例'
    )
    
    analysis_task = Task(
        description=(
            '基于研究员提供的技术调研报告，进行深入分析。'
            '评估不同技术方案的优劣，给出推荐方案和理由。'
            '分析应该包括：性能对比、实施难度、维护成本等维度。'
        ),
        agent=analyst,
        expected_output='一份技术分析报告，包含方案对比、评估结果和推荐建议'
    )
    
    # 创建团队
    crew = Crew(
        agents=[researcher, analyst],
        tasks=[research_task, analysis_task],
        process=Process.sequential,  # 顺序执行
        verbose=True
    )
    
    return crew


def create_development_crew():
    """创建开发型多智能体团队：用于软件开发和协作"""
    
    # 定义智能体
    product_manager = Agent(
        role='产品经理',
        goal='明确产品需求，定义功能规格，协调开发进度',
        backstory=(
            '你是一位经验丰富的产品经理，擅长将业务需求转化为清晰的技术需求。'
            '你能够与技术人员有效沟通，平衡用户需求和开发成本。'
            '你的需求文档总是详细、准确、可执行。'
        ),
        verbose=True,
        allow_delegation=True
    )
    
    architect = Agent(
        role='系统架构师',
        goal='设计系统架构，制定技术方案，确保系统的可扩展性和可维护性',
        backstory=(
            '你是一位资深系统架构师，拥有15年的架构设计经验。'
            '你熟悉各种架构模式，能够设计出既满足当前需求又具备良好扩展性的系统。'
            '你的架构设计总是考虑全面、文档清晰、易于实现。'
        ),
        verbose=True,
        allow_delegation=True,
        tools=[analyze_technical_requirements, generate_architecture_doc]
    )
    
    developer = Agent(
        role='高级开发工程师',
        goal='实现功能模块，编写高质量代码，确保代码的可维护性',
        backstory=(
            '你是一位高级开发工程师，精通多种编程语言和开发框架。'
            '你编写的代码总是结构清晰、注释完善、遵循最佳实践。'
            '你能够快速理解架构设计并高效实现功能。'
        ),
        verbose=True,
        allow_delegation=False
    )
    
    tester = Agent(
        role='测试工程师',
        goal='设计测试策略，编写测试用例，确保产品质量',
        backstory=(
            '你是一位专业的测试工程师，擅长设计全面的测试方案。'
            '你能够从功能、性能、安全等多个维度进行测试设计。'
            '你的测试用例总是覆盖全面、边界清晰、易于执行。'
        ),
        verbose=True,
        allow_delegation=False
    )
    
    # 定义任务
    requirement_task = Task(
        description=(
            '作为产品经理，分析并定义多智能体协作平台的核心需求。'
            '需求应该包括：1）核心功能列表；'
            '2）用户场景描述；'
            '3）非功能需求（性能、可用性等）；'
            '4）优先级排序。'
            '输出详细的产品需求文档。'
        ),
        agent=product_manager,
        expected_output='一份完整的产品需求文档，包含功能需求、非功能需求和优先级'
    )
    
    architecture_task = Task(
        description=(
            '基于产品经理提供的需求文档，设计系统技术架构。'
            '架构设计应该包括：1）系统整体架构图（文字描述）；'
            '2）核心模块划分；'
            '3）技术栈选型；'
            '4）数据流和通信机制；'
            '5）部署方案。'
            '使用提供的工具生成架构文档。'
        ),
        agent=architect,
        expected_output='一份完整的系统架构设计文档，包含架构图、模块设计和技术选型'
    )
    
    development_task = Task(
        description=(
            '基于架构师提供的架构设计，实现核心功能模块。'
            '需要实现：1）智能体管理模块；'
            '2）任务分配和协调模块；'
            '3）通信机制模块。'
            '提供代码实现方案和关键代码片段。'
        ),
        agent=developer,
        expected_output='功能实现方案和关键代码，包含模块设计和代码示例'
    )
    
    testing_task = Task(
        description=(
            '基于开发工程师提供的功能实现，设计完整的测试方案。'
            '测试方案应该包括：1）单元测试策略；'
            '2）集成测试策略；'
            '3）性能测试方案；'
            '4）测试用例示例。'
        ),
        agent=tester,
        expected_output='一份完整的测试方案文档，包含测试策略和测试用例'
    )
    
    # 创建团队
    crew = Crew(
        agents=[product_manager, architect, developer, tester],
        tasks=[requirement_task, architecture_task, development_task, testing_task],
        process=Process.sequential,  # 顺序执行，模拟真实开发流程
        verbose=True
    )
    
    return crew


def create_content_creation_crew():
    """创建内容创作型多智能体团队：用于协作创作内容"""
    
    # 定义智能体
    writer = Agent(
        role='技术写作者',
        goal='撰写高质量的技术文章，内容准确、结构清晰、易于理解',
        backstory=(
            '你是一位资深技术写作者，擅长将复杂的技术概念转化为通俗易懂的文章。'
            '你的文章总是结构清晰、逻辑严密、案例丰富。'
            '你能够根据目标受众调整写作风格和深度。'
        ),
        verbose=True,
        allow_delegation=False
    )
    
    editor = Agent(
        role='技术编辑',
        goal='审阅和优化文章内容，确保质量、准确性和可读性',
        backstory=(
            '你是一位严格的技术编辑，对文章质量要求极高。'
            '你能够发现文章中的逻辑问题、表述不清和错误信息。'
            '你的修改建议总是具体、可操作、能够显著提升文章质量。'
        ),
        verbose=True,
        allow_delegation=False
    )
    
    reviewer = Agent(
        role='技术评审员',
        goal='从技术准确性角度评审文章，确保技术内容的正确性',
        backstory=(
            '你是一位技术专家，拥有深厚的技术背景。'
            '你能够识别文章中的技术错误、过时信息和不准确表述。'
            '你的评审意见总是专业、准确、有助于提升文章的技术质量。'
        ),
        verbose=True,
        allow_delegation=False
    )
    
    # 定义任务
    writing_task = Task(
        description=(
            '撰写一篇关于"多智能体系统在软件开发中的应用"的技术文章。'
            '文章要求：1）字数约800-1000字；'
            '2）包含引言、正文（至少3个小节）、总结；'
            '3）正文中至少包含2个实际应用案例；'
            '4）面向技术开发人员，风格专业但易懂。'
        ),
        agent=writer,
        expected_output='一篇完整的技术文章初稿，包含引言、正文和总结'
    )
    
    editing_task = Task(
        description=(
            '审阅写作者提供的文章初稿，从结构和可读性角度进行优化。'
            '检查：1）文章结构是否清晰；'
            '2）段落逻辑是否连贯；'
            '3）表述是否清晰易懂；'
            '4）是否有冗余或缺失内容。'
            '提供修改建议和优化后的版本。'
        ),
        agent=editor,
        expected_output='优化后的文章版本和详细的修改说明'
    )
    
    review_task = Task(
        description=(
            '从技术准确性角度评审编辑后的文章。'
            '检查：1）技术概念是否准确；'
            '2）案例是否真实可靠；'
            '3）技术细节是否正确；'
            '4）是否有过时或错误信息。'
            '提供技术评审意见和最终版本。'
        ),
        agent=reviewer,
        expected_output='技术评审报告和最终定稿的文章'
    )
    
    # 创建团队
    crew = Crew(
        agents=[writer, editor, reviewer],
        tasks=[writing_task, editing_task, review_task],
        process=Process.sequential,
        verbose=True
    )
    
    return crew


def main():
    """主函数：演示不同的多智能体团队"""
    
    print("=" * 80)
    print("CrewAI 多智能体系统演示")
    print("=" * 80)
    print("\n请选择要运行的智能体团队：")
    print("1. 研究型团队（技术研究员 + 技术分析师）")
    print("2. 开发型团队（产品经理 + 架构师 + 开发工程师 + 测试工程师）")
    print("3. 内容创作团队（写作者 + 编辑 + 评审员）")
    print("\n默认运行：开发型团队")
    print("=" * 80)
    
    # 默认运行开发型团队
    choice = input("\n请输入选项 (1/2/3，直接回车使用默认): ").strip() or "2"
    
    if choice == "1":
        print("\n启动研究型团队...")
        crew = create_research_crew()
        result = crew.kickoff()
        print("\n" + "=" * 80)
        print("研究型团队执行完成")
        print("=" * 80)
        print("\n执行结果：")
        print(result)
        
    elif choice == "2":
        print("\n启动开发型团队...")
        crew = create_development_crew()
        result = crew.kickoff()
        print("\n" + "=" * 80)
        print("开发型团队执行完成")
        print("=" * 80)
        print("\n执行结果：")
        print(result)
        
    elif choice == "3":
        print("\n启动内容创作团队...")
        crew = create_content_creation_crew()
        result = crew.kickoff()
        print("\n" + "=" * 80)
        print("内容创作团队执行完成")
        print("=" * 80)
        print("\n执行结果：")
        print(result)
        
    else:
        print("无效选项，使用默认选项（开发型团队）")
        crew = create_development_crew()
        result = crew.kickoff()
        print("\n执行结果：")
        print(result)


if __name__ == "__main__":
    main()
