"""
飞书日历事件触发器
基于飞书日历事件触发工作流执行
"""
from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from app.services.feishu_service import FeishuService
from app.config import settings

if TYPE_CHECKING:
    from app.integrations.feishu_trigger import TriggerEvent


@dataclass
class CalendarEvent:
    """日历事件"""
    event_id: str
    summary: str  # 日程标题
    description: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[Dict[str, Any]]] = None
    calendar_id: Optional[str] = None


class FeishuCalendarTriggerConfig:
    """飞书日历触发器配置"""
    
    def __init__(
        self,
        calendar_id: Optional[str] = None,  # 监听特定日历，None 表示主日历
        remind_minutes_before: int = 5,  # 提前提醒分钟数
        keywords: Optional[List[str]] = None,  # 标题关键词过滤
    ):
        self.calendar_id = calendar_id
        self.remind_minutes_before = remind_minutes_before
        self.keywords = keywords or []
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "FeishuCalendarTriggerConfig":
        """从工作流节点配置创建"""
        trigger_config = config.get("trigger_config", {})
        return cls(
            calendar_id=trigger_config.get("calendar_id"),
            remind_minutes_before=trigger_config.get("remind_minutes_before", 5),
            keywords=trigger_config.get("keywords", []),
        )
    
    def match(self, event: CalendarEvent) -> bool:
        """检查事件是否匹配触发条件"""
        # 关键词过滤
        if self.keywords:
            for keyword in self.keywords:
                if keyword in event.summary:
                    return True
            return False
        return True


class FeishuCalendarTrigger:
    """飞书日历事件触发器"""
    
    def __init__(
        self,
        config: FeishuCalendarTriggerConfig,
        feishu_service: Optional[FeishuService] = None
    ):
        self.config = config
        self.feishu_service = feishu_service or FeishuService()
        # 已触发的日程ID集合（避免重复触发）
        self._triggered_event_ids: Set[str] = set()
        # 已发送提醒的日程ID集合
        self._reminded_event_ids: Set[str] = set()
    
    @property
    def trigger_type(self) -> str:
        return "feishu_calendar"
    
    async def get_upcoming_events(self, minutes_ahead: int = 60) -> List[CalendarEvent]:
        """
        获取即将开始的日程
        
        Args:
            minutes_ahead: 向前查看的分钟数
        
        Returns:
            日程列表
        """
        now = datetime.utcnow()
        time_min = now.isoformat() + "Z"
        time_max = (now + timedelta(minutes=minutes_ahead)).isoformat() + "Z"
        
        try:
            # 查询日历事件
            events = await self.feishu_service.get_calendar_events(
                start_time=time_min,
                end_time=time_max,
                calendar_id=self.config.calendar_id
            )
            
            calendar_events = []
            for event_data in events:
                # 跳过已触发的日程
                event_id = event_data.get("event_id", "")
                if event_id in self._triggered_event_ids:
                    continue
                
                # 解析日程数据
                start_time = event_data.get("start_time", {})
                end_time = event_data.get("end_time", {})
                
                event = CalendarEvent(
                    event_id=event_id,
                    summary=event_data.get("summary", "无标题"),
                    description=event_data.get("description"),
                    start_time=start_time.get("timestamp") if isinstance(start_time, dict) else start_time,
                    end_time=end_time.get("timestamp") if isinstance(end_time, dict) else end_time,
                    location=event_data.get("location", {}).get("name") if isinstance(event_data.get("location"), dict) else None,
                    attendees=event_data.get("attendees", {}).get("items", []),
                    calendar_id=event_data.get("calendar_id"),
                )
                
                calendar_events.append(event)
            
            return calendar_events
        
        except Exception as e:
            print(f"Failed to get calendar events: {e}")
            return []
    
    async def check(self) -> List[TriggerEvent]:
        """
        检查是否有即将开始的日程触发事件
        
        Returns:
            触发事件列表
        """
        from app.integrations.feishu_trigger import TriggerEvent
        
        # 获取即将开始的日程
        events = await self.get_upcoming_events(minutes_ahead=60)
        
        trigger_events = []
        now = datetime.utcnow()
        
        for event in events:
            # 解析开始时间
            if not event.start_time:
                continue
            
            # 计算距离开始的分钟数
            try:
                if isinstance(event.start_time, str) and event.start_time.isdigit():
                    start_dt = datetime.fromtimestamp(int(event.start_time) / 1000)
                else:
                    start_dt = datetime.fromisoformat(event.start_time.replace("Z", "+00:00"))
                
                minutes_until_start = (start_dt - now).total_seconds() / 60
                
                # 检查是否在提醒范围内
                if minutes_until_start <= self.config.remind_minutes_before and minutes_until_start > 0:
                    # 检查关键词匹配
                    if self.config.match(event):
                        # 标记为已提醒
                        self._reminded_event_ids.add(event.event_id)
                        self._triggered_event_ids.add(event.event_id)
                        
                        # 构建触发事件
                        trigger_event = TriggerEvent(
                            trigger_type="feishu_calendar",
                            event_id=f"calendar_{event.event_id}",
                            timestamp=now.isoformat(),
                            data={
                                "event_id": event.event_id,
                                "summary": event.summary,
                                "description": event.description,
                                "start_time": event.start_time,
                                "end_time": event.end_time,
                                "location": event.location,
                                "attendees": event.attendees,
                                "minutes_until_start": int(minutes_until_start),
                            }
                        )
                        trigger_events.append(trigger_event)
            
            except Exception as e:
                print(f"Failed to parse event time: {e}")
                continue
        
        return trigger_events
    
    async def execute(self, workflow_id: int, event: TriggerEvent, db=None):
        """
        执行指定工作流
        
        Args:
            workflow_id: 工作流ID
            event: 触发事件
            db: 数据库会话
        """
        from app.services.execution_service import execute_workflow
        from app.models.workflow import Workflow
        
        if db is None:
            from app.database import SessionLocal
            db = SessionLocal()
        
        try:
            workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            execution = await execute_workflow(
                db=db,
                workflow=workflow,
                trigger_type="feishu_calendar",
                trigger_input=event.data
            )
            
            return execution
        finally:
            if db:
                db.close()


# ==================== 日历轮询任务 ====================


class FeishuCalendarPoller:
    """飞书日历轮询器 - 定期检查日历事件"""
    
    def __init__(self):
        self._running = False
        self._poll_interval_seconds = settings.FEISHU_CALENDAR_POLL_INTERVAL_SECONDS
    
    async def poll(self) -> List[Dict[str, Any]]:
        """
        执行一次轮询
        从数据库加载所有配置了飞书日历触发器的工作流并检查触发条件
        
        Returns:
            触发的日程事件列表
        """
        from app.database import SessionLocal
        from app.models.workflow import Workflow
        from app.integrations.feishu_trigger import TriggerEvent
        
        db = SessionLocal()
        all_triggered_events = []
        
        try:
            # 从数据库加载所有已发布的、配置了飞书日历触发器的工作流
            workflows = db.query(Workflow).filter(
                Workflow.status == "published"
            ).all()
            
            for workflow in workflows:
                try:
                    # 解析触发器配置
                    trigger_config = json.loads(workflow.trigger_config) if workflow.trigger_config else {}
                    
                    # 检查是否是飞书日历触发器
                    if trigger_config.get("type") != "feishu_calendar":
                        continue
                    
                    # 创建触发器实例
                    calendar_config = FeishuCalendarTriggerConfig.from_config(trigger_config)
                    trigger = FeishuCalendarTrigger(calendar_config)
                    
                    # 检查是否有触发的日程
                    events = await trigger.check()
                    
                    for event in events:
                        # 执行工作流
                        await trigger.execute(workflow.id, event, db)
                        all_triggered_events.append(event.to_dict())
                        
                        # 发送执行结果通知
                        await self._notify_execution_result(workflow, db)
                
                except Exception as e:
                    print(f"Error polling calendar workflow {workflow.id}: {e}")
                    continue
        
        finally:
            db.close()
        
        return all_triggered_events
    
    async def _notify_execution_result(self, workflow, db):
        """
        发送执行结果通知到飞书
        
        Args:
            workflow: 工作流实例
            db: 数据库会话
        """
        try:
            from app.models.execution import Execution
            from app.integrations.feishu_notification import push_workflow_result_to_feishu
            
            # 获取最新的执行记录
            latest_execution = db.query(Execution).filter(
                Execution.workflow_id == workflow.id
            ).order_by(Execution.created_at.desc()).first()
            
            if latest_execution:
                # 计算耗时
                duration_ms = None
                if latest_execution.started_at and latest_execution.ended_at:
                    delta = latest_execution.ended_at - latest_execution.started_at
                    duration_ms = int(delta.total_seconds() * 1000)
                
                # TODO: 获取通知的接收者chat_id - 可以从工作流配置中读取
                # 目前暂时不推送，等待飞书用户绑定功能实现
                # receive_id = trigger_config.get("notify_chat_id")
                pass
        
        except Exception as e:
            print(f"Failed to send calendar execution notification: {e}")
    
    async def start(self):
        """启动轮询任务"""
        import asyncio
        self._running = True
        
        while self._running:
            try:
                triggered = await self.poll()
                if triggered:
                    print(f"Calendar poller triggered {len(triggered)} events")
            except Exception as e:
                print(f"Error in calendar poller: {e}")
            
            await asyncio.sleep(self._poll_interval_seconds)
    
    def stop(self):
        """停止轮询任务"""
        self._running = False


# 全局日历轮询器实例
feishu_calendar_poller = FeishuCalendarPoller()
