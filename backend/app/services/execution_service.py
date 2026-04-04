"""
执行服务
工作流执行引擎 - 顺序执行所有节点
"""
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.execution import Execution, ExecutionLog, ExecutionStatus
from app.models.workflow import Workflow
from app.services import ai_service, feishu_service, http_service
from app.config import settings


async def execute_workflow(
    db: Session,
    workflow: Workflow,
    trigger_type: str = "manual",
    trigger_input: Optional[Dict[str, Any]] = None
) -> Execution:
    """
    执行工作流
    
    Args:
        db: 数据库会话
        workflow: 工作流实例
        trigger_type: 触发类型（manual/cron）
        trigger_input: 触发输入数据
    
    Returns:
        执行记录
    """
    # 创建执行记录
    execution = Execution(
        workflow_id=workflow.id,
        trigger_type=trigger_type,
        status=ExecutionStatus.RUNNING.value,
        started_at=datetime.utcnow(),
        trigger_input=json.dumps(trigger_input) if trigger_input else None
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    try:
        # 解析节点配置
        nodes = json.loads(workflow.nodes) if workflow.nodes else []
        if not nodes:
            raise ValueError("工作流没有配置节点")
        
        # 按顺序执行节点
        node_outputs = {}  # 存储每个节点的输出，供后续节点使用
        
        # 添加触发器输出
        node_outputs["trigger"] = {
            "triggered": True,
            "trigger_type": trigger_type,
            "trigger_time": datetime.utcnow().isoformat(),
            **(trigger_input or {})
        }
        
        for i, node in enumerate(nodes):
            node_id = node.get("id", str(i))
            node_type = node.get("type")
            node_name = node.get("name", f"节点{i+1}")
            node_config = node.get("config", {})
            
            # 创建执行日志
            log = ExecutionLog(
                execution_id=execution.id,
                node_id=node_id,
                node_type=node_type,
                node_name=node_name,
                status=ExecutionStatus.RUNNING.value,
                input_data=json.dumps(node_outputs.get(node_type, {}))
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            
            try:
                start_time = time.time()
                
                # 根据节点类型执行
                if node_type == "trigger":
                    # 触发器节点 - 直接使用配置作为输出
                    output = {
                        "triggered": True,
                        "trigger_type": node_config.get("type", "manual"),
                        "trigger_time": datetime.utcnow().isoformat()
                    }
                
                elif node_type == "ai_task":
                    # AI任务节点
                    output = await ai_service.execute_ai_task(
                        node_config=node_config,
                        input_data=node_outputs.get("trigger", {})
                    )
                
                elif node_type == "tool":
                    # 工具节点
                    tool_type = node_config.get("tool_type")
                    
                    if tool_type == "feishu_message":
                        # 飞书消息
                        output = await feishu_service.send_message(
                            receive_id=node_config.get("receive_id"),
                            receive_id_type=node_config.get("receive_id_type", "chat_id"),
                            text=node_config.get("text")
                        )
                    
                    elif tool_type == "feishu_doc":
                        # 飞书文档
                        output = await feishu_service.create_document(
                            title=node_config.get("title", "新文档"),
                            content=node_config.get("content")
                        )
                    
                    elif tool_type == "http_request":
                        # HTTP请求
                        output = await http_service.execute_http_request(
                            url=node_config.get("url"),
                            method=node_config.get("method", "GET"),
                            headers=node_config.get("headers"),
                            body=node_config.get("body"),
                            timeout=node_config.get("timeout", 30)
                        )
                    
                    else:
                        raise ValueError(f"不支持的工具类型: {tool_type}")
                
                elif node_type == "condition":
                    # 条件节点（简化处理：评估条件表达式）
                    condition = node_config.get("condition", "")
                    expression = node_config.get("expression", "")
                    
                    # 简单的条件判断
                    input_data = node_outputs.get("trigger", {})
                    condition_result = evaluate_condition(condition, expression, input_data)
                    
                    output = {
                        "condition_met": condition_result,
                        "branch": "true" if condition_result else "false"
                    }
                
                else:
                    raise ValueError(f"不支持的节点类型: {node_type}")
                
                # 计算执行时间
                duration_ms = int((time.time() - start_time) * 1000)
                
                # 更新日志
                log.output_data = json.dumps(output)
                log.status = ExecutionStatus.SUCCESS.value
                log.duration_ms = duration_ms
                db.commit()
                
                # 保存输出供后续节点使用
                node_outputs[node_type] = output
                node_outputs[node_id] = output  # 也按ID保存
                
            except Exception as e:
                # 节点执行失败
                duration_ms = int((time.time() - start_time) * 1000) if 'start_time' in locals() else 0
                log.status = ExecutionStatus.FAILED.value
                log.error = str(e)
                log.duration_ms = duration_ms
                db.commit()
                
                # 更新执行状态为失败
                execution.status = ExecutionStatus.FAILED.value
                execution.error_message = f"节点 {node_name} 执行失败: {str(e)}"
                execution.ended_at = datetime.utcnow()
                db.commit()
                
                return execution
        
        # 所有节点执行完成
        execution.status = ExecutionStatus.SUCCESS.value
        execution.ended_at = datetime.utcnow()
        db.commit()
        
        # 清理旧的执行日志（MVP：保留最近100条）
        await cleanup_old_executions(db, workflow.user_id)
        
        # 推送执行结果通知（如果配置了飞书通知）
        await _push_execution_notification(db, workflow, execution, trigger_type, trigger_input)
        
        return execution
        
    except Exception as e:
        execution.status = ExecutionStatus.FAILED.value
        execution.error_message = str(e)
        execution.ended_at = datetime.utcnow()
        db.commit()
        
        # 推送失败通知（如果配置了飞书通知）
        await _push_execution_notification(db, workflow, execution, trigger_type, trigger_input)
        
        return execution


async def _push_execution_notification(
    db: Session,
    workflow: Workflow,
    execution: Execution,
    trigger_type: str,
    trigger_input: Optional[Dict[str, Any]]
):
    """
    推送执行结果通知到飞书
    
    Args:
        db: 数据库会话
        workflow: 工作流实例
        execution: 执行记录
        trigger_type: 触发类型
        trigger_input: 触发输入数据
    """
    try:
        # 解析工作流的触发器配置
        trigger_config = json.loads(workflow.trigger_config) if workflow.trigger_config else {}
        
        # 检查是否配置了飞书通知
        notify_config = trigger_config.get("notification", {})
        if not notify_config.get("enabled"):
            return
        
        receive_id = notify_config.get("receive_id")
        receive_id_type = notify_config.get("receive_id_type", "chat_id")
        
        if not receive_id:
            return
        
        # 计算执行耗时
        duration_ms = None
        if execution.started_at and execution.ended_at:
            delta = execution.ended_at - execution.started_at
            duration_ms = int(delta.total_seconds() * 1000)
        
        # 获取关键输出（最后节点的输出）
        key_outputs = None
        logs = db.query(ExecutionLog).filter(
            ExecutionLog.execution_id == execution.id,
            ExecutionLog.status == ExecutionStatus.SUCCESS.value
        ).order_by(ExecutionLog.created_at.desc()).limit(3).all()
        
        if logs:
            try:
                last_output = json.loads(logs[0].output_data) if logs[0].output_data else {}
                if last_output:
                    key_outputs = {k: v for k, v in list(last_output.items())[:3]}
            except Exception:
                pass
        
        # 推送通知
        from app.integrations.feishu_notification import push_workflow_result_to_feishu
        await push_workflow_result_to_feishu(
            receive_id=receive_id,
            receive_id_type=receive_id_type,
            workflow_name=workflow.name,
            status=execution.status,
            execution_id=execution.id,
            trigger_type=trigger_type,
            started_at=execution.started_at.isoformat() if execution.started_at else None,
            ended_at=execution.ended_at.isoformat() if execution.ended_at else None,
            duration_ms=duration_ms,
            error_message=execution.error_message,
            key_outputs=key_outputs,
        )
    
    except Exception as e:
        print(f"Failed to push execution notification: {e}")


def evaluate_condition(condition: str, expression: str, data: Dict[str, Any]) -> bool:
    """
    评估条件表达式
    
    Args:
        condition: 条件类型（simple/expression）
        expression: 表达式
        data: 上下文数据
    
    Returns:
        条件是否满足
    """
    if condition == "simple":
        # 简单条件：key operator value
        # 例如: trigger.status equals success
        parts = expression.split()
        if len(parts) >= 3:
            key = parts[0]
            operator = parts[1]
            value = " ".join(parts[2:])
            
            # 获取数据中的值
            data_value = data.get(key, "")
            
            if operator == "equals":
                return str(data_value).lower() == value.lower()
            elif operator == "contains":
                return value.lower() in str(data_value).lower()
            elif operator == "starts_with":
                return str(data_value).lower().startswith(value.lower())
            elif operator == "ends_with":
                return str(data_value).lower().endswith(value.lower())
    
    # 默认返回True（条件节点直接通过）
    return True


async def cleanup_old_executions(db: Session, user_id: int):
    """
    清理旧的执行记录
    保留最近 MAX_EXECUTION_LOGS 条
    """
    # 获取用户的执行记录
    from app.models.workflow import Workflow
    
    user_workflows = db.query(Workflow).filter(Workflow.user_id == user_id).all()
    workflow_ids = [w.id for w in user_workflows]
    
    if not workflow_ids:
        return
    
    # 统计每个工作流的执行记录数
    for workflow_id in workflow_ids:
        executions = db.query(Execution).filter(
            Execution.workflow_id == workflow_id
        ).order_by(Execution.created_at.desc()).all()
        
        if len(executions) > settings.MAX_EXECUTION_LOGS:
            # 删除超出的记录
            old_executions = executions[settings.MAX_EXECUTION_LOGS:]
            for exec_record in old_executions:
                # 删除关联的日志
                db.query(ExecutionLog).filter(
                    ExecutionLog.execution_id == exec_record.id
                ).delete()
                db.delete(exec_record)
            
            db.commit()


def get_execution_logs(db: Session, execution_id: int) -> List[ExecutionLog]:
    """获取执行日志列表"""
    return db.query(ExecutionLog).filter(
        ExecutionLog.execution_id == execution_id
    ).order_by(ExecutionLog.created_at.asc()).all()
