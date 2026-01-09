"""
基于 LangGraph 实现的 Activepieces 工作流：营销v2.0_邮件模板生成

将 Activepieces 的 JSON 工作流转换为 LangGraph 实现
工作流步骤：
1. Catch Webhook (trigger)
2. 生成 SQL 查询 (step_4)
3. 执行 MySQL 查询 (step_3)
4. 获取销售大脑实体列表 (step_5)
5. 处理卖方信息 (step_7)
6. 生成提示词 (step_1)
7. 调用子流程生成模板 (step_2)
8. 预览邮件模板 (step_6)
9. 返回前端 (step_8, 可选)
10. 停止流程 (step_55)
"""

import os
import json
from typing import TypedDict, Annotated, Literal, Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import requests
import pymysql
from pymysql.cursors import DictCursor

# 加载环境变量
load_dotenv()

# 确保设置了必要的环境变量
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("请设置 OPENAI_API_KEY 环境变量")


# ==================== 状态定义 ====================
class WorkflowState(TypedDict):
    """工作流状态定义"""
    # Webhook 输入数据
    webhook_body: dict
    
    # 步骤 4: SQL 查询语句
    sql_query: Optional[str]
    is_test_message: Optional[bool]
    email_template_round_version_id: Optional[str]
    
    # 步骤 3: MySQL 查询结果
    template_version_data: Optional[dict]
    
    # 步骤 5: HTTP 请求结果
    sales_brain_data: Optional[dict]
    
    # 步骤 7: 卖方信息
    seller_info: Optional[dict]
    
    # 步骤 1: 生成的提示词
    prompt: Optional[str]
    
    # 步骤 2: LLM 生成的模板结构
    template_structure: Optional[dict]
    
    # 步骤 6: 预览结果
    preview_result: Optional[dict]
    
    # 步骤 8: 返回前端的结果
    final_result: Optional[dict]
    
    # 错误信息
    error: Optional[str]
    
    # 当前步骤
    current_step: str


# ==================== 工具函数 ====================
def execute_mysql_query(query: str, args: list = None, connection_config: dict = None) -> dict:
    """
    执行 MySQL 查询
    
    Args:
        query: SQL 查询语句
        args: 查询参数
        connection_config: 数据库连接配置
        
    Returns:
        查询结果
    """
    if connection_config is None:
        # 从环境变量获取数据库配置
        connection_config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'database': os.getenv('MYSQL_DATABASE', 'test'),
            'charset': 'utf8mb4'
        }
    
    try:
        connection = pymysql.connect(**connection_config)
        cursor = connection.cursor(DictCursor)
        
        if args:
            cursor.execute(query, args)
        else:
            cursor.execute(query)
        
        result = cursor.fetchall()
        connection.close()
        
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_http_request(url: str, method: str = "GET", headers: dict = None, 
                     params: dict = None, body: dict = None) -> dict:
    """
    发送 HTTP 请求
    
    Args:
        url: 请求 URL
        method: HTTP 方法
        headers: 请求头
        params: 查询参数
        body: 请求体
        
    Returns:
        响应结果
    """
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=body, params=params, timeout=30)
        else:
            return {"success": False, "error": f"Unsupported method: {method}"}
        
        response.raise_for_status()
        return {"success": True, "body": response.json(), "status_code": response.status_code}
    except Exception as e:
        return {"success": False, "error": str(e)}


def render_template_variables(template: str, variables: dict) -> str:
    """
    渲染模板变量（模拟 Activepieces 的 {{variable}} 语法）
    
    Args:
        template: 包含变量的模板字符串
        variables: 变量字典
        
    Returns:
        渲染后的字符串
    """
    result = template
    for key, value in variables.items():
        # 支持嵌套访问，如 trigger['body']['payload']['userId']
        if isinstance(value, dict):
            # 处理嵌套字典访问
            for nested_key, nested_value in value.items():
                result = result.replace(f"{{{{trigger['body']['{nested_key}']}}}}", str(nested_value))
        result = result.replace(f"{{{{{key}}}}}", str(value))
    
    return result


# ==================== 工作流节点 ====================
class EmailTemplateWorkflow:
    """邮件模板生成工作流"""
    
    def __init__(self, model_name: str = "gpt-5", temperature: float = 0.7):
        """初始化工作流"""
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.memory = MemorySaver()
        self.graph = self._build_graph()
    
    # ==================== 节点函数 ====================
    
    def trigger_node(self, state: WorkflowState) -> dict:
        """触发器节点：接收 Webhook 数据"""
        print("\n[TRIGGER] 接收 Webhook 请求")
        print(f"Webhook Body: {json.dumps(state.get('webhook_body', {}), indent=2, ensure_ascii=False)}")
        
        return {
            "current_step": "trigger",
            "webhook_body": state.get("webhook_body", {})
        }
    
    def step_4_generate_sql(self, state: WorkflowState) -> dict:
        """步骤 4: 根据条件生成 SQL 查询"""
        print("\n[STEP_4] 生成 SQL 查询")
        
        webhook_body = state.get("webhook_body", {})
        
        # 提取输入参数
        is_test_message = webhook_body.get("body", {}).get("options", {}).get("testMessage", False)
        email_template_round_version_id = webhook_body.get("body", {}).get("payload", {}).get("emailTemplateRoundVersionId")
        
        # 根据 is_test_message 生成不同的 SQL
        if is_test_message:
            sql_query = f"""
                SELECT * 
                FROM zoe_ai_email_template_round_version 
                WHERE id = {email_template_round_version_id}
                  AND status = 0 
                  AND del_flag = 0 
                ORDER BY create_time DESC 
                LIMIT 1
            """
        else:
            sql_query = """
                SELECT * 
                FROM zoe_ai_email_template_round_version 
                WHERE id = (
                  select current_version_id 
                  from zoe_ai_email_template_round 
                  where template_id = ? 
                    and round_order = ? 
                    and round_type = 0
                    and del_time = 0
                ) 
                  AND status = 1
                  and del_flag = 0
            """
        
        print(f"生成的 SQL: {sql_query}")
        
        return {
            "current_step": "step_4",
            "sql_query": sql_query,
            "is_test_message": is_test_message,
            "email_template_round_version_id": email_template_round_version_id
        }
    
    def step_3_execute_mysql(self, state: WorkflowState) -> dict:
        """步骤 3: 执行 MySQL 查询"""
        print("\n[STEP_3] 执行 MySQL 查询")
        
        sql_query = state.get("sql_query", "")
        webhook_body = state.get("webhook_body", {})
        
        # 提取查询参数
        email_template_id = webhook_body.get("body", {}).get("payload", {}).get("emailTemplateId")
        seq = webhook_body.get("body", {}).get("payload", {}).get("seq")
        
        # 执行查询
        args = [email_template_id, seq] if email_template_id and seq else None
        result = execute_mysql_query(sql_query, args)
        
        if result.get("success"):
            template_data = result.get("data", [])
            print(f"查询成功，返回 {len(template_data)} 条记录")
            return {
                "current_step": "step_3",
                "template_version_data": template_data[0] if template_data else {}
            }
        else:
            print(f"查询失败: {result.get('error')}")
            return {
                "current_step": "step_3",
                "error": result.get("error"),
                "template_version_data": {}
            }
    
    def step_5_get_sales_brain(self, state: WorkflowState) -> dict:
        """步骤 5: 获取销售大脑实体列表"""
        print("\n[STEP_5] 获取销售大脑实体列表")
        
        webhook_body = state.get("webhook_body", {})
        user_id = webhook_body.get("body", {}).get("messageGenerateReqDTO", {}).get("payload", {}).get("userId")
        
        url = "https://stage.qianxing-ai.com/api/customer/sales_brain/getConfirmedSalesBrainEntityListForUser"
        headers = {
            "X-Caller": "activepieces",
            "Authorization": os.getenv("BACKEND_CALLBACK_AUTH", "")
        }
        params = {"userId": user_id}
        
        result = send_http_request(url, method="GET", headers=headers, params=params)
        
        if result.get("success"):
            print("获取销售大脑数据成功")
            return {
                "current_step": "step_5",
                "sales_brain_data": result.get("body", {})
            }
        else:
            print(f"获取失败: {result.get('error')}")
            return {
                "current_step": "step_5",
                "error": result.get("error"),
                "sales_brain_data": {}
            }
    
    def step_7_process_seller_info(self, state: WorkflowState) -> dict:
        """步骤 7: 处理卖方信息"""
        print("\n[STEP_7] 处理卖方信息")
        
        webhook_body = state.get("webhook_body", {})
        seller_info = webhook_body.get("body", {}).get("messageGenerateReqDTO", {}).get("sellerInfo", {})
        
        # 提取卖方信息
        seller_data = {
            "sellerCompanyName": seller_info.get("baseInfo", {}).get("companyName", ""),
            "sellerCompanyIntro": seller_info.get("baseInfo", {}).get("companyIntro", ""),
            "sellerMainProduct": seller_info.get("baseInfo", {}).get("mainProduct", ""),
            "sellerWebsite": seller_info.get("baseInfo", {}).get("website", ""),
            "sellerContact": seller_info.get("contact", "")
        }
        
        print(f"卖方信息: {json.dumps(seller_data, indent=2, ensure_ascii=False)}")
        
        return {
            "current_step": "step_7",
            "seller_info": seller_data
        }
    
    def step_1_generate_prompt(self, state: WorkflowState) -> dict:
        """步骤 1: 生成提示词"""
        print("\n[STEP_1] 生成提示词")
        
        webhook_body = state.get("webhook_body", {})
        chat_content = webhook_body.get("body", {}).get("chatContent", "")
        market_info = state.get("sales_brain_data", {}).get("data", {})
        seller_info = state.get("seller_info", {})
        
        # 构建提示词（从 JSON 中的代码提取）
        prompt = f"""
# Role
你是一位 B2B 商务邮件结构设计专家，
擅长在严格事实与合规约束下，
为不同业务场景设计【自然、有情商、可规模化复用的邮件模版结构】。

你不预设邮件类型。
邮件可能是（但不限于）：
- 营销 / 冷启动 / 客户触达
- 老客户跟进
- 节日或问候类沟通
- 关系维护
- 信息同步或业务通知
- 其他由用户明确说明的商务沟通场景

邮件的具体场景、目的与使用语境，
**完全以 User Input 为准。**

你的任务不是直接写一封完整邮件，
而是输出一个【可被程序安全拼装的邮件模版结构】，
用于后续根据不同客户与场景进行个性化生成。

---

# 全局语言强制规则（最高优先级）

- 本 Prompt 的所有输出内容 **必须使用中文**
- 包括但不限于：
  - Type 1 的邮件正文
  - Type 2 的策略指令
  - 标题策略、钩子策略、执行说明
- 所有内容必须符合自然商务沟通习惯

---

# Knowledge Base（我方事实唯一来源）

## marketinfo_json_data
用于存储市场或行业层面的通用信息，
如公司优势、解决方案方向等（仅限其中明确写明的内容）。

## sellerscompanybaseinfo_json_data
卖方企业基础信息：
- sellerCompanyName: {seller_info.get('sellerCompanyName', '')}
- sellerCompanyIntro: {seller_info.get('sellerCompanyIntro', '')}
- sellerMainProduct: {seller_info.get('sellerMainProduct', '')}
- sellerWebsite: {seller_info.get('sellerWebsite', '')}

---

# User Input

{chat_content}

---

# Output Format（严格）

仅输出 JSON，不得包含任何解释性文字。
**所有 content 字段必须使用中文表达。**

```json
{{
  "template_structure": [
    {{
      "sectionId": 1,
      "type": 2,
      "content": "策略：基于邮件场景与目标客户角色，从对方视角出发，生成一个信息量较低、语气试探、带有不确定性的标题，用于引导对方产生打开邮件的兴趣。",
      "fact_sources": ["buyer_context"]
    }}
  ]
}}
```

# Knowledge Base 内容
[MARKET_INFO_START]
{json.dumps(market_info, indent=2, ensure_ascii=False)}
[MARKET_INFO_END]

[COMPANY_BASE_INFO_START]
{json.dumps(seller_info, indent=2, ensure_ascii=False)}
[COMPANY_BASE_INFO_END]
"""
        
        print("提示词生成完成")
        
        return {
            "current_step": "step_1",
            "prompt": prompt
        }
    
    def step_2_call_llm(self, state: WorkflowState) -> dict:
        """步骤 2: 调用 LLM 生成模板结构"""
        print("\n[STEP_2] 调用 LLM 生成模板结构")
        
        prompt = state.get("prompt", "")
        webhook_body = state.get("webhook_body", {})
        chat_content = webhook_body.get("body", {}).get("chatContent", "")
        
        # 构建 LLM 输入
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=chat_content)
        ]
        
        try:
            # 调用 LLM
            response = self.llm.invoke(messages)
            
            # 解析 JSON 响应
            content = response.content
            
            # 尝试提取 JSON 部分
            json_content = None
            
            # 方法1: 查找 ```json 代码块
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                if json_end > json_start:
                    json_content = content[json_start:json_end].strip()
            
            # 方法2: 查找 ``` 代码块
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                if json_end > json_start:
                    json_content = content[json_start:json_end].strip()
            
            # 方法3: 查找 { 和 } 之间的内容
            if not json_content:
                start_brace = content.find("{")
                end_brace = content.rfind("}")
                if start_brace >= 0 and end_brace > start_brace:
                    json_content = content[start_brace:end_brace + 1].strip()
            
            # 如果还是找不到，使用整个内容
            if not json_content:
                json_content = content.strip()
            
            # 解析 JSON
            template_structure = json.loads(json_content)
            
            print("LLM 生成模板结构成功")
            print(f"模板结构: {json.dumps(template_structure, indent=2, ensure_ascii=False)}")
            
            return {
                "current_step": "step_2",
                "template_structure": template_structure
            }
        except json.JSONDecodeError as e:
            print(f"JSON 解析失败: {str(e)}")
            print(f"原始内容: {content[:500]}...")  # 打印前500个字符用于调试
            return {
                "current_step": "step_2",
                "error": f"JSON 解析失败: {str(e)}",
                "template_structure": {}
            }
        except Exception as e:
            print(f"LLM 调用失败: {str(e)}")
            return {
                "current_step": "step_2",
                "error": str(e),
                "template_structure": {}
            }
    
    def step_6_preview_template(self, state: WorkflowState) -> dict:
        """步骤 6: 预览邮件模板"""
        print("\n[STEP_6] 预览邮件模板")
        
        webhook_body = state.get("webhook_body", {})
        template_structure = state.get("template_structure", {})
        
        payload = webhook_body.get("body", {}).get("messageGenerateReqDTO", {}).get("payload", {})
        
        # 构建请求数据
        request_data = {
            "step": 1,
            "userId": payload.get("userId", ""),
            "content": "",
            "subject": "",
            "modelAnalysis": "",
            "conversationId": payload.get("conversationId", ""),
            "sessionId": payload.get("sessionId", ""),
            "status": 0,
            "emailTemplateList": template_structure.get("template_structure", [])
        }
        
        url = "http://111.229.132.67/api/v2/flow/previewEmailTemplate"
        headers = {
            "X-Caller": "activepieces",
            "Content-Type": "application/json"
        }
        
        result = send_http_request(url, method="POST", headers=headers, body=request_data)
        
        if result.get("success"):
            print("预览邮件模板成功")
            return {
                "current_step": "step_6",
                "preview_result": result.get("body", {})
            }
        else:
            print(f"预览失败: {result.get('error')}")
            return {
                "current_step": "step_6",
                "error": result.get("error"),
                "preview_result": {}
            }
    
    def step_8_return_result(self, state: WorkflowState) -> dict:
        """步骤 8: 返回前端结果（可选步骤）"""
        print("\n[STEP_8] 返回前端结果")
        
        preview_result = state.get("preview_result", {})
        
        return {
            "current_step": "step_8",
            "final_result": preview_result
        }
    
    def step_55_stop_flow(self, state: WorkflowState) -> dict:
        """步骤 55: 停止流程"""
        print("\n[STEP_55] 停止流程")
        
        return {
            "current_step": "step_55"
        }
    
    # ==================== 路由函数 ====================
    
    def should_continue(self, state: WorkflowState) -> Literal["step_3", "step_5", "end"]:
        """决定下一步"""
        current_step = state.get("current_step", "")
        error = state.get("error")
        
        # 如果有错误，直接结束
        if error:
            return "end"
        
        # 根据当前步骤决定下一步
        if current_step == "step_4":
            return "step_3"
        elif current_step == "step_3":
            return "step_5"
        elif current_step == "step_55":
            return "end"
        else:
            return "end"
    
    # ==================== 构建工作流图 ====================
    
    def _build_graph(self) -> StateGraph:
        """构建工作流图"""
        workflow = StateGraph(WorkflowState)
        
        # 添加节点
        workflow.add_node("trigger", self.trigger_node)
        workflow.add_node("step_4", self.step_4_generate_sql)
        workflow.add_node("step_3", self.step_3_execute_mysql)
        workflow.add_node("step_5", self.step_5_get_sales_brain)
        workflow.add_node("step_7", self.step_7_process_seller_info)
        workflow.add_node("step_1", self.step_1_generate_prompt)
        workflow.add_node("step_2", self.step_2_call_llm)
        workflow.add_node("step_6", self.step_6_preview_template)
        workflow.add_node("step_8", self.step_8_return_result)
        workflow.add_node("step_55", self.step_55_stop_flow)
        
        # 设置入口点
        workflow.set_entry_point("trigger")
        
        # 添加边（顺序执行）
        workflow.add_edge("trigger", "step_4")
        workflow.add_edge("step_4", "step_3")
        workflow.add_edge("step_3", "step_5")
        workflow.add_edge("step_5", "step_7")
        workflow.add_edge("step_7", "step_1")
        workflow.add_edge("step_1", "step_2")
        workflow.add_edge("step_2", "step_6")
        workflow.add_edge("step_6", "step_8")
        workflow.add_edge("step_8", "step_55")
        workflow.add_edge("step_55", END)
        
        # 编译图
        return workflow.compile(checkpointer=self.memory)
    
    # ==================== 运行工作流 ====================
    
    def run(self, webhook_body: dict, config: dict = None) -> dict:
        """
        运行工作流
        
        Args:
            webhook_body: Webhook 请求体
            config: 配置信息
            
        Returns:
            最终状态
        """
        if config is None:
            config = {"configurable": {"thread_id": "1"}}
        
        initial_state = {
            "webhook_body": webhook_body,
            "current_step": "",
            "sql_query": None,
            "is_test_message": None,
            "email_template_round_version_id": None,
            "template_version_data": None,
            "sales_brain_data": None,
            "seller_info": None,
            "prompt": None,
            "template_structure": None,
            "preview_result": None,
            "final_result": None,
            "error": None
        }
        
        print("=" * 80)
        print("开始执行邮件模板生成工作流")
        print("=" * 80)
        
        # 运行工作流
        final_state = None
        for state in self.graph.stream(initial_state, config):
            # 打印每个节点的输出
            for node_name, node_state in state.items():
                if node_name != "__end__" and node_state.get("current_step"):
                    step_name = node_state.get("current_step", node_name)
                    print(f"\n{'='*80}")
                    print(f"步骤完成: {step_name}")
                    print(f"{'='*80}")
            
            final_state = state
        
        # 返回最终结果
        if final_state and "step_55" in final_state:
            print("\n" + "="*80)
            print("工作流执行完成")
            print("="*80)
            print(f"\n最终结果: {json.dumps(final_state['step_55'].get('final_result', {}), indent=2, ensure_ascii=False)}")
        
        return final_state


# ==================== 主程序 ====================
def main():
    """主函数：演示工作流"""
    
    # 创建工作流实例
    workflow = EmailTemplateWorkflow(model_name="gpt-4o-mini", temperature=0.7)
    
    # 模拟 Webhook 请求体（根据实际需求修改）
    webhook_body = {
        "body": {
            "options": {
                "testMessage": False
            },
            "payload": {
                "seq": 1
            },
            "messageGenerateReqDTO": {
                "payload": {
                    "userId": "113",
                    "conversationId": "ZusBkKukTK4a",
                    "sessionId": "bec29db0-a970-4fe2-4ac0-55a88eda3d2a"
                },
                "sellerInfo": {
                    "baseInfo": {
                        "companyName": "示例公司",
                        "companyIntro": "一家专业的 B2B 服务提供商",
                        "mainProduct": "定制化解决方案",
                        "website": "https://example.com"
                    },
                    "contact": "contact@example.com"
                }
            },
            "chatContent": "请帮我生成一封营销邮件，用于向潜在客户介绍我们的产品和服务。"
        }
    }
    
    # 运行工作流
    result = workflow.run(webhook_body)
    
    return result


if __name__ == "__main__":
    main()

