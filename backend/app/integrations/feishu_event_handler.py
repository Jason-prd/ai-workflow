"""
飞书事件处理器
统一处理各类飞书事件
"""
import json
from typing import Dict, Any, List, Optional, Set
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.feishu_service import feishu_service


class FeishuEventHandler:
    """飞书事件处理器"""
    
    def __init__(self):
        # 已处理的消息ID集合（用于去重），实际生产环境应使用 Redis
        self._processed_message_ids: Set[str] = set()
        self._max_cache_size = 1000
    
    def _is_duplicate(self, message_id: str) -> bool:
        """检查是否是重复消息"""
        if message_id in self._processed_message_ids:
            return True
        
        # 添加到缓存
        self._processed_message_ids.add(message_id)
        
        # 清理缓存
        if len(self._processed_message_ids) > self._max_cache_size:
            # 简单的 FIFO 清理
            self._processed_message_ids = set(list(self._processed_message_ids)[-self._max_cache_size//2:])
        
        return False
    
    def _extract_plain_text(self, message_type: str, content: str) -> str:
        """提取消息纯文本"""
        try:
            content_dict = json.loads(content) if isinstance(content, str) else content
        except Exception:
            return content
        
        if message_type == "text":
            return content_dict.get("text", "")
        elif message_type == "post":
            # 尝试从富文本中提取文本
            text_parts = []
            content_data = content_dict.get("zh_cn", content_dict.get("en_us", {}))
            if isinstance(content_data, dict):
                for section in content_data.get("content", []):
                    for item in section:
                        if item.get("tag") == "text":
                            text_parts.append(item.get("text", ""))
                        elif item.get("tag") == "at":
                            text_parts.append(f"@{item.get('uid', '')}")
            return "".join(text_parts)
        
        return content
    
    async def handle_message_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理消息接收事件
        
        Args:
            event: 飞书消息事件
        
        Returns:
            处理结果
        """
        # 提取消息信息
        message = event.get("message", {})
        message_id = message.get("message_id", "")
        message_type = message.get("message_type", "")
        content = message.get("content", "{}")
        chat_id = message.get("chat_id", "")
        chat_type = message.get("chat_type", "")  # p2p 或 group
        
        sender = event.get("sender", {})
        sender_id = sender.get("sender_id", {}).get("open_id", "")
        sender_type = sender.get("sender_type", "")  # user 或 bot
        
        # 去重
        if self._is_duplicate(message_id):
            return {"status": "duplicate", "message_id": message_id}
        
        # 忽略机器人自己的消息
        if sender_type == "bot":
            return {"status": "ignored", "reason": "Message from bot"}
        
        # 解析消息内容
        text = self._extract_plain_text(message_type, content)
        
        # 构建统一消息格式
        unified_message = {
            "message_id": message_id,
            "chat_id": chat_id,
            "chat_type": chat_type,  # p2p / group
            "sender_id": sender_id,
            "sender_type": sender_type,
            "message_type": message_type,
            "text": text,
            "raw_content": content,
            "create_time": event.get("create_time", ""),
        }
        
        # 处理命令
        if text.startswith("/"):
            result = await self._handle_command(text, unified_message)
            if result:
                return result
        
        # 触发工作流（异步处理）
        await self._trigger_workflows(unified_message)
        
        return {"status": "ok", "message_id": message_id}
    
    async def _handle_command(self, text: str, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        处理命令
        
        Args:
            text: 命令文本
            message: 消息对象
        
        Returns:
            如果是需要回复的命令，返回回复内容；否则返回 None
        """
        text = text.strip().lower()
        
        if text == "/help":
            reply_text = (
                "🤖 AI自动化工作流机器人\n\n"
                "📋 支持以下命令：\n"
                "/start - 启动机器人\n"
                "/help - 显示帮助\n"
                "/list - 查看我的工作流\n"
                "/status - 查看工作流状态\n\n"
                "💬 直接发送消息将触发工作流执行"
            )
            await self._send_reply(message["chat_id"], message["message_id"], text=reply_text)
            return {"status": "command_handled", "command": text}
        
        elif text == "/start":
            reply_text = (
                "👋 欢迎使用AI自动化工作流！\n\n"
                "发送任意消息将触发工作流执行。"
            )
            await self._send_reply(message["chat_id"], message["message_id"], text=reply_text)
            return {"status": "command_handled", "command": text}
        
        elif text == "/status":
            reply_text = "✅ 机器人正常运行中"
            await self._send_reply(message["chat_id"], message["message_id"], text=reply_text)
            return {"status": "command_handled", "command": text}
        
        elif text == "/list":
            reply_text = (
                "📋 查看工作流列表请访问 Web 端\n\n"
                "💡 提示：首次使用请先在 Web 端登录并创建工作流，"
                "然后配置飞书消息触发器即可通过机器人触发执行。"
            )
            await self._send_reply(message["chat_id"], message["message_id"], text=reply_text)
            return {"status": "command_handled", "command": text}
        
        return None
    
    async def _send_reply(
        self, 
        chat_id: str, 
        root_id: Optional[str] = None,
        text: Optional[str] = None,
        content: Optional[Dict[str, Any]] = None
    ):
        """
        发送回复消息
        
        Args:
            chat_id: 聊天ID
            root_id: 根消息ID（用于回复话题）
            text: 文本内容
            content: 富文本内容
        """
        try:
            await feishu_service.send_message(
                receive_id_type="chat_id",
                receive_id=chat_id,
                msg_type="text" if text else "post",
                text=text,
                content=content
            )
        except Exception as e:
            print(f"Failed to send reply: {e}")
    
    async def _trigger_workflows(self, message: Dict[str, Any]):
        """
        触发相关工作流
        
        Args:
            message: 统一格式的消息对象
        """
        db = SessionLocal()
        try:
            # 1. 查询所有配置了飞书消息触发器的工作流
            from app.models.workflow import Workflow
            from app.integrations.feishu_trigger import FeishuMessageTrigger, FeishuMessageTriggerConfig
            
            # 查询已发布的工作流（排除草稿）
            workflows = db.query(Workflow).filter(
                Workflow.status == "published"
            ).all()
            
            triggered_count = 0
            for workflow in workflows:
                try:
                    # 解析触发器配置
                    trigger_config = json.loads(workflow.trigger_config) if workflow.trigger_config else {}
                    
                    # 检查是否是飞书消息触发器
                    if trigger_config.get("type") != "feishu_message":
                        continue
                    
                    # 创建触发器实例
                    feishu_config = FeishuMessageTriggerConfig.from_config(trigger_config)
                    trigger = FeishuMessageTrigger(feishu_config)
                    
                    # 检查消息是否匹配触发条件
                    events = await trigger.check(message)
                    
                    for event in events:
                        # 执行工作流
                        await trigger.execute(workflow.id, event, db)
                        triggered_count += 1
                        
                        # 发送执行结果通知
                        await self._notify_execution_result(workflow, message["chat_id"])
                
                except Exception as e:
                    print(f"Error triggering workflow {workflow.id}: {e}")
                    continue
            
            print(f"Triggered {triggered_count} workflows for message {message.get('message_id')}")
        
        finally:
            db.close()
    
    async def _notify_execution_result(self, workflow, chat_id: str):
        """
        发送执行结果通知到飞书
        
        Args:
            workflow: 工作流实例
            chat_id: 飞书聊天ID
        """
        try:
            from app.integrations.feishu_notification import push_workflow_result_to_feishu
            
            # 获取最新的执行记录
            db = SessionLocal()
            try:
                from app.models.execution import Execution, ExecutionStatus
                latest_execution = db.query(Execution).filter(
                    Execution.workflow_id == workflow.id
                ).order_by(Execution.created_at.desc()).first()
                
                if latest_execution:
                    # 计算耗时
                    duration_ms = None
                    if latest_execution.started_at and latest_execution.ended_at:
                        delta = latest_execution.ended_at - latest_execution.started_at
                        duration_ms = int(delta.total_seconds() * 1000)
                    
                    await push_workflow_result_to_feishu(
                        receive_id=chat_id,
                        receive_id_type="chat_id",
                        workflow_name=workflow.name,
                        status=latest_execution.status,
                        execution_id=latest_execution.id,
                        trigger_type=latest_execution.trigger_type,
                        started_at=latest_execution.started_at.isoformat() if latest_execution.started_at else None,
                        ended_at=latest_execution.ended_at.isoformat() if latest_execution.ended_at else None,
                        duration_ms=duration_ms,
                        error_message=latest_execution.error_message,
                    )
            finally:
                db.close()
        except Exception as e:
            print(f"Failed to send execution notification: {e}")
    
    async def _get_user_workflows(self, sender_id: str) -> List[Dict[str, Any]]:
        """
        获取用户的工作流列表
        
        Note: 当前实现需要用户先在系统中绑定飞书账号。
        如果用户未绑定飞书open_id，返回空列表。
        后续可以通过飞书授权登录功能建立用户绑定。
        
        Args:
            sender_id: 用户 open_id
        
        Returns:
            工作流列表
        """
        # TODO: 实现飞书账号绑定后，通过 open_id 查找对应用户的工作流
        # 目前阶段，/list 命令暂不可用，返回友好提示
        return []


def create_event_handler() -> FeishuEventHandler:
    """创建事件处理器实例"""
    return FeishuEventHandler()
