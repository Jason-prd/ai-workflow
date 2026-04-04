"""
节点类型元数据 API
提供工作流设计器所需的节点类型定义、配置Schema和默认值
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


router = APIRouter(prefix="/api", tags=["节点元数据"])


class NodeTypeField(BaseModel):
    """节点配置字段定义"""
    name: str
    type: str  # string / number / boolean / select / textarea / json
    label: str
    required: bool = False
    default: Optional[Any] = None
    options: Optional[List[Dict[str, str]]] = None  # [{"label": "A", "value": "a"}]
    placeholder: Optional[str] = None
    description: Optional[str] = None


class NodeTypeDefinition(BaseModel):
    """节点类型定义"""
    type: str  # trigger / ai_task / tool / condition
    name: str
    description: str
    icon: str  # emoji or icon name
    color: str  # hex color
    category: str  # 分类：触发器 / AI任务 / 工具 / 逻辑
    fields: List[NodeTypeField]
    has_position: bool = True  # 是否在设计器中显示位置


# 节点类型元数据（硬编码MVP版本）
NODE_TYPE_DEFINITIONS: List[NodeTypeDefinition] = [
    # ==================== 触发器 ====================
    NodeTypeDefinition(
        type="trigger",
        name="触发器",
        description="工作流启动条件，支持手动触发和定时触发",
        icon="⚡",
        color="#FF6B35",
        category="触发器",
        fields=[
            NodeTypeField(name="type", type="select", label="触发方式", required=True,
                          options=[
                              {"label": "手动触发", "value": "manual"},
                              {"label": "定时触发（Cron）", "value": "cron"},
                          ],
                          default="manual"),
            NodeTypeField(name="cron_expression", type="string", label="Cron表达式",
                          placeholder="0 9 * * *",
                          description="标准Cron格式：分 时 日 月 周，例如 0 9 * * * 表示每天9点执行"),
            NodeTypeField(name="timezone", type="string", label="时区",
                          default="Asia/Shanghai"),
        ]
    ),

    # ==================== AI 任务 ====================
    NodeTypeDefinition(
        type="ai_task",
        name="AI 任务",
        description="调用大语言模型处理任务，输入文本并获得AI生成的结果",
        icon="🤖",
        color="#4ECDC4",
        category="AI任务",
        fields=[
            NodeTypeField(name="prompt", type="textarea", label="提示词", required=True,
                          placeholder="你是一个专业的助手，请{{input}}",
                          description="支持 {{variable}} 语法引用变量"),
            NodeTypeField(name="model", type="select", label="模型",
                          options=[
                              {"label": "GPT-4o-mini（推荐）", "value": "gpt-4o-mini"},
                              {"label": "GPT-4o", "value": "gpt-4o"},
                              {"label": "GPT-4-turbo", "value": "gpt-4-turbo"},
                          ],
                          default="gpt-4o-mini"),
            NodeTypeField(name="temperature", type="number", label="温度参数",
                          default=0.7,
                          description="控制随机性，0=确定输出，1=最大随机"),
            NodeTypeField(name="max_tokens", type="number", label="最大Token数",
                          default=2000),
        ]
    ),

    # ==================== 工具节点 ====================
    NodeTypeDefinition(
        type="tool",
        name="工具",
        description="执行具体操作：发送飞书消息、创建文档、HTTP请求等",
        icon="🔧",
        color="#45B7D1",
        category="工具",
        fields=[
            NodeTypeField(name="tool_type", type="select", label="工具类型", required=True,
                          options=[
                              {"label": "飞书消息", "value": "feishu_message"},
                              {"label": "飞书文档", "value": "feishu_doc"},
                              {"label": "HTTP请求", "value": "http_request"},
                          ],
                          default="feishu_message"),
            # 飞书消息配置
            NodeTypeField(name="receive_id", type="string", label="接收者ID",
                          description="群聊ID或用户open_id"),
            NodeTypeField(name="receive_id_type", type="select", label="接收者ID类型",
                          options=[
                              {"label": "群聊ID", "value": "chat_id"},
                              {"label": "用户open_id", "value": "open_id"},
                          ],
                          default="chat_id"),
            NodeTypeField(name="text", type="textarea", label="消息内容",
                          placeholder="请输入消息内容，支持 {{variable}} 变量"),
            # HTTP请求配置
            NodeTypeField(name="url", type="string", label="请求URL",
                          placeholder="https://api.example.com/endpoint"),
            NodeTypeField(name="method", type="select", label="HTTP方法",
                          options=[
                              {"label": "GET", "value": "GET"},
                              {"label": "POST", "value": "POST"},
                              {"label": "PUT", "value": "PUT"},
                              {"label": "DELETE", "value": "DELETE"},
                          ],
                          default="GET"),
            NodeTypeField(name="headers", type="json", label="请求头（JSON）",
                          placeholder='{"Authorization": "Bearer xxx"}'),
            NodeTypeField(name="body", type="json", label="请求体（JSON）",
                          placeholder='{"key": "value"}'),
            NodeTypeField(name="timeout", type="number", label="超时（秒）",
                          default=30),
            # 飞书文档配置
            NodeTypeField(name="title", type="string", label="文档标题",
                          placeholder="新文档"),
            NodeTypeField(name="content", type="textarea", label="文档内容",
                          placeholder="文档正文内容，支持 {{variable}} 变量"),
        ]
    ),

    # ==================== 条件判断 ====================
    NodeTypeDefinition(
        type="condition",
        name="条件判断",
        description="根据条件表达式的结果，决定工作流的执行分支",
        icon="🔀",
        color="#96CEB4",
        category="逻辑",
        fields=[
            NodeTypeField(name="condition", type="select", label="条件类型",
                          options=[
                              {"label": "简单条件", "value": "simple"},
                          ],
                          default="simple"),
            NodeTypeField(name="expression", type="string", label="条件表达式",
                          placeholder="trigger.status equals success",
                          description="格式: key operator value，operator: equals / contains / starts_with / ends_with"),
        ]
    ),
]


@router.get("/node-types", response_model=List[NodeTypeDefinition])
async def get_node_types(
    current_user: User = Depends(get_current_user)
):
    """
    获取所有可用的节点类型定义
    用于工作流设计器的节点面板
    """
    return NODE_TYPE_DEFINITIONS


@router.get("/node-types/{node_type}", response_model=NodeTypeDefinition)
async def get_node_type(
    node_type: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取指定节点类型的定义
    """
    for definition in NODE_TYPE_DEFINITIONS:
        if definition.type == node_type:
            return definition
    
    from fastapi import HTTPException, status
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"未知的节点类型: {node_type}"
    )
