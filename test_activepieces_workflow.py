"""
测试 Activepieces 工作流的 LangGraph 实现

这是一个简化的测试脚本，用于验证工作流的基本功能
"""

import os
from dotenv import load_dotenv
from activepieces_langgraph_workflow import EmailTemplateWorkflow

# 加载环境变量
load_dotenv()


def test_workflow():
    """测试工作流"""
    
    # 创建工作流实例
    workflow = EmailTemplateWorkflow(model_name="gpt-5", temperature=0.7)
    
    # 模拟 Webhook 请求体
    webhook_body = {
        "body": {
            "options": {
                "testMessage": False
            },
            "payload": {
                "emailTemplateId": "123",
                "seq": 1,
                "emailTemplateRoundVersionId": "456"
            },
            "messageGenerateReqDTO": {
                "payload": {
                    "userId": "113",
                    "conversationId": "test_conv_123",
                    "sessionId": "test_session_456"
                },
                "sellerInfo": {
                    "baseInfo": {
                        "companyName": "咨询服务公司",
                        "companyIntro": "一家专业的 B2B 服务提供商，专注于为企业提供定制化解决方案。",
                        "mainProduct": "企业级软件解决方案",
                        "website": "https://test-company.com"
                    },
                    "contact": "contact@test-company.com"
                }
            },
            "chatContent": "请帮我生成一封营销邮件"
        }
    }
    
    print("=" * 80)
    print("开始测试工作流")
    print("=" * 80)
    
    try:
        # 运行工作流
        result = workflow.run(webhook_body)
        
        print("\n" + "=" * 80)
        print("测试完成")
        print("=" * 80)
        
        # 检查结果
        if result and "step_55" in result:
            final_state = result["step_55"]
            if final_state.get("error"):
                print(f"❌ 工作流执行出错: {final_state.get('error')}")
            else:
                print("✅ 工作流执行成功")
                if final_state.get("final_result"):
                    print("✅ 已生成最终结果")
        else:
            print("⚠️ 工作流未正常完成")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 检查必要的环境变量
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ 警告: 未设置 OPENAI_API_KEY 环境变量")
        print("请在 .env 文件中设置或使用环境变量")
        print("\n示例 .env 文件内容:")
        print("OPENAI_API_KEY=your-api-key-here")
        print("MYSQL_HOST=localhost")
        print("MYSQL_PORT=3306")
        print("MYSQL_USER=root")
        print("MYSQL_PASSWORD=your-password")
        print("MYSQL_DATABASE=your-database")
        print("BACKEND_CALLBACK_AUTH=your-auth-token")
    else:
        test_workflow()

