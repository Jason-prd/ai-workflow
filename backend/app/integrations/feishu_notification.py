"""
飞书执行结果推送
将工作流执行结果推送回飞书
"""
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.services.feishu_service import FeishuService


class FeishuNotificationBuilder:
    """飞书通知消息构建器"""
    
    @staticmethod
    def build_execution_result_card(
        workflow_name: str,
        status: str,  # success / failed / running
        execution_id: int,
        trigger_type: str,
        started_at: Optional[str] = None,
        ended_at: Optional[str] = None,
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        key_outputs: Optional[Dict[str, Any]] = None,
        logs_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        构建执行结果卡片消息
        
        Args:
            workflow_name: 工作流名称
            status: 执行状态
            execution_id: 执行ID
            trigger_type: 触发类型
            started_at: 开始时间
            ended_at: 结束时间
            duration_ms: 执行耗时（毫秒）
            error_message: 错误信息
            key_outputs: 关键输出
            logs_url: 日志链接
        
        Returns:
            飞书卡片消息格式
        """
        # 状态 emoji
        status_emoji = {
            "success": "✅",
            "failed": "❌",
            "running": "🔄"
        }.get(status, "❓")
        
        # 状态颜色
        status_color = {
            "success": "green",
            "failed": "red",
            "running": "yellow"
        }.get(status, "grey")
        
        # 格式化耗时
        if duration_ms:
            if duration_ms < 1000:
                duration_str = f"{duration_ms}ms"
            else:
                duration_str = f"{duration_ms/1000:.1f}s"
        else:
            duration_str = "-"
        
        # 格式化时间
        start_time_str = started_at or "-"
        end_time_str = ended_at or "-"
        
        # 构建卡片元素
        elements = [
            {
                "tag": "markdown",
                "content": f"**📋 工作流：** {workflow_name}"
            },
            {
                "tag": "markdown",
                "content": f"**🎯 状态：** {status_emoji} {status.upper()}"
            },
            {
                "tag": "markdown",
                "content": f"**⏱️ 耗时：** {duration_str}"
            },
            {
                "tag": "markdown",
                "content": f"**🕐 开始时间：** {start_time_str}"
            }
        ]
        
        # 添加触发类型
        trigger_type_display = {
            "manual": "手动触发",
            "cron": "定时触发",
            "feishu_message": "飞书消息触发",
            "feishu_calendar": "飞书日历触发"
        }.get(trigger_type, trigger_type)
        elements.append({
            "tag": "markdown",
            "content": f"**🔔 触发方式：** {trigger_type_display}"
        })
        
        # 添加错误信息
        if error_message:
            elements.append({
                "tag": "markdown",
                "content": f"**❌ 错误：** {error_message[:200]}"
            })
        
        # 添加关键输出
        if key_outputs:
            outputs_text = []
            for key, value in list(key_outputs.items())[:3]:  # 最多显示3个
                if isinstance(value, str) and len(value) > 50:
                    value = value[:50] + "..."
                outputs_text.append(f"**{key}:** {value}")
            
            if outputs_text:
                elements.append({"tag": "hr"})
                elements.append({
                    "tag": "markdown",
                    "content": "**📤 关键输出：**"
                })
                for text in outputs_text:
                    elements.append({
                        "tag": "markdown",
                        "content": text
                    })
        
        # 添加日志链接
        if logs_url:
            elements.append({"tag": "hr"})
            elements.append({
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "📊 查看执行详情"
                        },
                        "type": "primary",
                        "url": logs_url
                    }
                ]
            })
        
        # 构建完整卡片
        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"{status_emoji} 工作流执行结果"
                    },
                    "template": status_color
                },
                "elements": elements
            }
        }
        
        return card
    
    @staticmethod
    def build_execution_log_card(
        workflow_name: str,
        execution_id: int,
        node_logs: List[Dict[str, Any]],
        logs_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        构建执行日志卡片
        
        Args:
            workflow_name: 工作流名称
            execution_id: 执行ID
            node_logs: 节点日志列表
            logs_url: 日志链接
        
        Returns:
            飞书卡片消息格式
        """
        # 构建节点详情
        node_elements = []
        
        for i, node_log in enumerate(node_logs[:5], 1):  # 最多显示5个节点
            node_name = node_log.get("node_name", f"节点{i}")
            status = node_log.get("status", "unknown")
            duration_ms = node_log.get("duration_ms", 0)
            
            status_emoji = {
                "success": "✅",
                "failed": "❌",
                "running": "🔄"
            }.get(status, "❓")
            
            duration_str = f"{duration_ms}ms" if duration_ms else "-"
            
            node_elements.append({
                "tag": "markdown",
                "content": f"{status_emoji} **{node_name}** - {duration_str}"
            })
        
        # 构建卡片
        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "📋 执行日志"
                    },
                    "template": "blue"
                },
                "elements": [
                    {
                        "tag": "markdown",
                        "content": f"**📋 工作流：** {workflow_name}"
                    },
                    {
                        "tag": "markdown",
                        "content": f"**🔢 执行ID：** {execution_id}"
                    },
                    {"tag": "hr"},
                    {
                        "tag": "markdown",
                        "content": "**节点执行详情：**"
                    },
                    *node_elements
                ]
            }
        }
        
        # 添加日志链接
        if logs_url:
            card["card"]["elements"].append({"tag": "hr"})
            card["card"]["elements"].append({
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "📊 查看完整日志"
                        },
                        "type": "primary",
                        "url": logs_url
                    }
                ]
            })
        
        return card


async def push_workflow_result_to_feishu(
    receive_id: str,
    receive_id_type: str = "chat_id",
    workflow_name: str = "未知工作流",
    status: str = "success",
    execution_id: int = 0,
    trigger_type: str = "manual",
    started_at: Optional[str] = None,
    ended_at: Optional[str] = None,
    duration_ms: Optional[int] = None,
    error_message: Optional[str] = None,
    key_outputs: Optional[Dict[str, Any]] = None,
    logs_url: Optional[str] = None,
    use_card: bool = True,
    feishu_service: Optional[FeishuService] = None
) -> Dict[str, Any]:
    """
    推送工作流执行结果到飞书
    
    Args:
        receive_id: 接收者ID（群ID或用户open_id）
        receive_id_type: 接收者类型（chat_id / open_id）
        workflow_name: 工作流名称
        status: 执行状态（success / failed / running）
        execution_id: 执行ID
        trigger_type: 触发类型
        started_at: 开始时间
        ended_at: 结束时间
        duration_ms: 执行耗时
        error_message: 错误信息
        key_outputs: 关键输出
        logs_url: 日志链接
        use_card: 是否使用卡片消息
        feishu_service: 飞书服务实例
    
    Returns:
        推送结果
    """
    service = feishu_service or FeishuService()
    
    if use_card:
        # 构建卡片消息
        card_content = FeishuNotificationBuilder.build_execution_result_card(
            workflow_name=workflow_name,
            status=status,
            execution_id=execution_id,
            trigger_type=trigger_type,
            started_at=started_at,
            ended_at=ended_at,
            duration_ms=duration_ms,
            error_message=error_message,
            key_outputs=key_outputs,
            logs_url=logs_url
        )
        
        # 发送卡片消息
        try:
            result = await service.send_message(
                receive_id_type=receive_id_type,
                receive_id=receive_id,
                msg_type="interactive",
                content=card_content["card"]
            )
            return {
                "status": "success",
                "message_id": result.get("message_id"),
                "type": "card"
            }
        except Exception as e:
            # 卡片发送失败，降级为文本消息
            return await push_workflow_result_to_feishu(
                receive_id=receive_id,
                receive_id_type=receive_id_type,
                workflow_name=workflow_name,
                status=status,
                execution_id=execution_id,
                trigger_type=trigger_type,
                started_at=started_at,
                ended_at=ended_at,
                duration_ms=duration_ms,
                error_message=error_message,
                key_outputs=key_outputs,
                logs_url=logs_url,
                use_card=False,
                feishu_service=service
            )
    else:
        # 构建文本消息
        status_emoji = {
            "success": "✅",
            "failed": "❌",
            "running": "🔄"
        }.get(status, "❓")
        
        duration_str = f"{duration_ms}ms" if duration_ms else "-"
        if duration_ms and duration_ms >= 1000:
            duration_str = f"{duration_ms/1000:.1f}s"
        
        trigger_type_display = {
            "manual": "手动触发",
            "cron": "定时触发",
            "feishu_message": "飞书消息触发",
            "feishu_calendar": "飞书日历触发"
        }.get(trigger_type, trigger_type)
        
        text_parts = [
            f"{status_emoji} **工作流执行{status}**",
            f"📋 {workflow_name}",
            f"⏱️ 耗时: {duration_str}",
            f"🔔 触发: {trigger_type_display}"
        ]
        
        if error_message:
            text_parts.append(f"❌ {error_message[:100]}")
        
        if logs_url:
            text_parts.append(f"📊 详情: {logs_url}")
        
        text_content = "\n".join(text_parts)
        
        try:
            result = await service.send_message(
                receive_id_type=receive_id_type,
                receive_id=receive_id,
                msg_type="text",
                text=text_content
            )
            return {
                "status": "success",
                "message_id": result.get("message_id"),
                "type": "text"
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }


async def push_execution_log_to_feishu(
    receive_id: str,
    receive_id_type: str = "chat_id",
    workflow_name: str = "未知工作流",
    execution_id: int = 0,
    node_logs: Optional[List[Dict[str, Any]]] = None,
    logs_url: Optional[str] = None,
    feishu_service: Optional[FeishuService] = None
) -> Dict[str, Any]:
    """
    推送执行日志到飞书
    
    Args:
        receive_id: 接收者ID
        receive_id_type: 接收者类型
        workflow_name: 工作流名称
        execution_id: 执行ID
        node_logs: 节点日志列表
        logs_url: 日志链接
        feishu_service: 飞书服务实例
    
    Returns:
        推送结果
    """
    service = feishu_service or FeishuService()
    
    card_content = FeishuNotificationBuilder.build_execution_log_card(
        workflow_name=workflow_name,
        execution_id=execution_id,
        node_logs=node_logs or [],
        logs_url=logs_url
    )
    
    try:
        result = await service.send_message(
            receive_id_type=receive_id_type,
            receive_id=receive_id,
            msg_type="interactive",
            content=card_content["card"]
        )
        return {
            "status": "success",
            "message_id": result.get("message_id"),
            "type": "card"
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }
