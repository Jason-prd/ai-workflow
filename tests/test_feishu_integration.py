"""
飞书集成测试
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestFeishuMessageTrigger:
    """飞书消息触发器测试"""
    
    def test_trigger_config_from_dict(self):
        """测试从配置字典创建触发器配置"""
        from app.integrations.feishu_trigger import FeishuMessageTriggerConfig
        
        config = FeishuMessageTriggerConfig.from_config({
            "trigger_config": {
                "keywords": ["hello", "help"],
                "chat_ids": ["oc_123"],
                "chat_types": ["group"],
                "exclude_keywords": ["spam"]
            }
        })
        
        assert config.keywords == ["hello", "help"]
        assert config.chat_ids == ["oc_123"]
        assert config.chat_types == ["group"]
        assert config.exclude_keywords == ["spam"]
    
    def test_trigger_config_match_keywords(self):
        """测试关键词匹配"""
        from app.integrations.feishu_trigger import FeishuMessageTriggerConfig
        
        config = FeishuMessageTriggerConfig(keywords=["hello", "test"])
        
        # 匹配
        message = {"chat_type": "p2p", "text": "hello world"}
        assert config.match(message) is True
        
        # 不匹配
        message = {"chat_type": "p2p", "text": "goodbye"}
        assert config.match(message) is False
    
    def test_trigger_config_match_exclude_keywords(self):
        """测试排除关键词"""
        from app.integrations.feishu_trigger import FeishuMessageTriggerConfig
        
        config = FeishuMessageTriggerConfig(
            keywords=["hello"],
            exclude_keywords=["spam", "bad"]
        )
        
        # 包含排除关键词
        message = {"chat_type": "p2p", "text": "hello spam"}
        assert config.match(message) is False
        
        # 不包含排除关键词
        message = {"chat_type": "p2p", "text": "hello world"}
        assert config.match(message) is True
    
    def test_trigger_config_match_chat_types(self):
        """测试聊天类型过滤"""
        from app.integrations.feishu_trigger import FeishuMessageTriggerConfig
        
        config = FeishuMessageTriggerConfig(chat_types=["group"])
        
        # 匹配
        message = {"chat_type": "group", "text": "hello"}
        assert config.match(message) is True
        
        # 不匹配
        message = {"chat_type": "p2p", "text": "hello"}
        assert config.match(message) is False
    
    def test_trigger_config_match_chat_ids(self):
        """测试群ID白名单"""
        from app.integrations.feishu_trigger import FeishuMessageTriggerConfig
        
        config = FeishuMessageTriggerConfig(
            chat_ids=["oc_123", "oc_456"]
        )
        
        # 匹配
        message = {"chat_type": "group", "chat_id": "oc_123", "text": "hello"}
        assert config.match(message) is True
        
        # 不匹配（不在白名单）
        message = {"chat_type": "group", "chat_id": "oc_999", "text": "hello"}
        assert config.match(message) is False
    
    def test_trigger_config_no_keywords_means_any(self):
        """测试空关键词表示匹配所有"""
        from app.integrations.feishu_trigger import FeishuMessageTriggerConfig
        
        config = FeishuMessageTriggerConfig(keywords=[])
        
        message = {"chat_type": "p2p", "text": "anything"}
        assert config.match(message) is True


class TestFeishuCalendarTriggerConfig:
    """飞书日历触发器配置测试"""
    
    def test_trigger_config_from_dict(self):
        """测试从配置字典创建日历触发器配置"""
        from app.integrations.feishu_calendar_trigger import FeishuCalendarTriggerConfig
        
        config = FeishuCalendarTriggerConfig.from_config({
            "trigger_config": {
                "calendar_id": "primary",
                "remind_minutes_before": 10,
                "keywords": ["会议", "评审"]
            }
        })
        
        assert config.calendar_id == "primary"
        assert config.remind_minutes_before == 10
        assert config.keywords == ["会议", "评审"]
    
    def test_trigger_config_match_keywords(self):
        """测试日历事件关键词匹配"""
        from app.integrations.feishu_calendar_trigger import (
            FeishuCalendarTriggerConfig,
            CalendarEvent
        )
        
        config = FeishuCalendarTriggerConfig(keywords=["会议", "评审"])
        
        event = CalendarEvent(
            event_id="evt_123",
            summary="产品评审会议",
            start_time="2024-01-01T10:00:00Z"
        )
        assert config.match(event) is True
        
        event = CalendarEvent(
            event_id="evt_456",
            summary="日常同步",
            start_time="2024-01-01T10:00:00Z"
        )
        assert config.match(event) is False
    
    def test_trigger_config_no_keywords_matches_all(self):
        """测试空关键词表示匹配所有"""
        from app.integrations.feishu_calendar_trigger import (
            FeishuCalendarTriggerConfig,
            CalendarEvent
        )
        
        config = FeishuCalendarTriggerConfig(keywords=[])
        
        event = CalendarEvent(
            event_id="evt_123",
            summary="任何事件",
            start_time="2024-01-01T10:00:00Z"
        )
        assert config.match(event) is True


class TestFeishuNotificationBuilder:
    """飞书通知消息构建器测试"""
    
    def test_build_execution_result_card_success(self):
        """测试构建成功状态卡片"""
        from app.integrations.feishu_notification import FeishuNotificationBuilder
        
        card = FeishuNotificationBuilder.build_execution_result_card(
            workflow_name="周报生成器",
            status="success",
            execution_id=123,
            trigger_type="manual",
            duration_ms=5000,
            started_at="2024-01-01T09:00:00Z",
            ended_at="2024-01-01T09:00:05Z",
        )
        
        assert card["msg_type"] == "interactive"
        assert card["card"]["header"]["template"] == "green"
        assert "周报生成器" in card["card"]["elements"][0]["content"]
    
    def test_build_execution_result_card_failed(self):
        """测试构建失败状态卡片"""
        from app.integrations.feishu_notification import FeishuNotificationBuilder
        
        card = FeishuNotificationBuilder.build_execution_result_card(
            workflow_name="周报生成器",
            status="failed",
            execution_id=123,
            trigger_type="cron",
            error_message="API调用超时",
        )
        
        assert card["card"]["header"]["template"] == "red"
        assert "❌" in card["card"]["elements"][1]["content"]
        assert "API调用超时" in card["card"]["elements"][-2]["content"]
    
    def test_build_execution_result_card_with_outputs(self):
        """测试构建带输出的卡片"""
        from app.integrations.feishu_notification import FeishuNotificationBuilder
        
        card = FeishuNotificationBuilder.build_execution_result_card(
            workflow_name="周报生成器",
            status="success",
            execution_id=123,
            trigger_type="feishu_message",
            key_outputs={
                "result": "本周GMV增长5%",
                "summary": "完成"
            },
            logs_url="https://example.com/logs/123"
        )
        
        # 验证输出被包含
        content_str = json.dumps(card)
        assert "本周GMV增长5%" in content_str
        assert "查看执行详情" in content_str


class TestFeishuEventHandler:
    """飞书事件处理器测试"""
    
    def test_duplicate_detection(self):
        """测试消息去重"""
        from app.integrations.feishu_event_handler import FeishuEventHandler
        
        handler = FeishuEventHandler()
        
        message_id = "om_123456"
        
        # 第一次应该不是重复
        assert handler._is_duplicate(message_id) is False
        
        # 第二次应该识别为重复
        assert handler._is_duplicate(message_id) is True
    
    def test_extract_plain_text_from_text_message(self):
        """测试从文本消息提取纯文本"""
        from app.integrations.feishu_event_handler import FeishuEventHandler
        
        handler = FeishuEventHandler()
        
        content = json.dumps({"text": "Hello, World!"})
        text = handler._extract_plain_text("text", content)
        assert text == "Hello, World!"
    
    def test_extract_plain_text_from_unknown_type(self):
        """测试未知类型返回原始内容"""
        from app.integrations.feishu_event_handler import FeishuEventHandler
        
        handler = FeishuEventHandler()
        
        text = handler._extract_plain_text("unknown", "some content")
        assert text == "some content"


class TestTriggerEvent:
    """触发器事件测试"""
    
    def test_trigger_event_to_dict(self):
        """测试触发事件序列化"""
        from app.integrations.feishu_trigger import TriggerEvent
        
        event = TriggerEvent(
            trigger_type="feishu_message",
            event_id="msg_123",
            timestamp="2024-01-01T09:00:00Z",
            data={"text": "hello"}
        )
        
        result = event.to_dict()
        
        assert result["trigger_type"] == "feishu_message"
        assert result["event_id"] == "msg_123"
        assert result["data"]["text"] == "hello"


class TestFeishuBotWebhook:
    """飞书机器人 Webhook 测试"""
    
    @pytest.mark.asyncio
    async def test_webhook_verify_endpoint(self):
        """测试 Webhook 验证接口"""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # 验证 challenge 请求
        response = client.get(
            "/api/integrations/feishu/webhook",
            params={"challenge": "test_challenge"}
        )
        
        assert response.status_code == 200
        assert response.json()["challenge"] == "test_challenge"
    
    @pytest.mark.asyncio
    async def test_webhook_missing_challenge(self):
        """测试缺少 challenge 的验证请求"""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        response = client.get("/api/integrations/feishu/webhook")
        
        # 没有 challenge 应该返回错误
        assert response.status_code == 400


# ==================== 集成测试 ====================


class TestFeishuIntegrationE2E:
    """飞书集成端到端测试"""
    
    @pytest.mark.asyncio
    async def test_push_workflow_result_to_feishu_text(self):
        """测试推送工作流结果（文本模式）"""
        from app.integrations.feishu_notification import push_workflow_result_to_feishu
        
        mock_service = AsyncMock()
        mock_service.send_message = AsyncMock(return_value={"message_id": "om_test"})
        
        result = await push_workflow_result_to_feishu(
            receive_id="oc_123",
            receive_id_type="chat_id",
            workflow_name="测试工作流",
            status="success",
            execution_id=1,
            trigger_type="manual",
            duration_ms=3000,
            use_card=False,
            feishu_service=mock_service
        )
        
        assert result["status"] == "success"
        assert result["message_id"] == "om_test"
        mock_service.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_push_workflow_result_to_feishu_card(self):
        """测试推送工作流结果（卡片模式）"""
        from app.integrations.feishu_notification import push_workflow_result_to_feishu
        
        mock_service = AsyncMock()
        mock_service.send_message = AsyncMock(return_value={"message_id": "om_test"})
        
        result = await push_workflow_result_to_feishu(
            receive_id="oc_123",
            receive_id_type="chat_id",
            workflow_name="测试工作流",
            status="failed",
            execution_id=1,
            trigger_type="feishu_message",
            error_message="API超时",
            use_card=True,
            feishu_service=mock_service
        )
        
        assert result["status"] == "success"
        assert result["type"] == "card"
    
    @pytest.mark.asyncio
    async def test_message_trigger_check(self):
        """测试消息触发器检查"""
        from app.integrations.feishu_trigger import FeishuMessageTrigger, FeishuMessageTriggerConfig
        
        config = FeishuMessageTriggerConfig(keywords=["hello"])
        trigger = FeishuMessageTrigger(config)
        
        message = {
            "message_id": "msg_001",
            "chat_type": "p2p",
            "text": "hello world"
        }
        
        events = await trigger.check(message)
        
        assert len(events) == 1
        assert events[0].trigger_type == "feishu_message"
        assert events[0].data["text"] == "hello world"
    
    @pytest.mark.asyncio
    async def test_message_trigger_check_no_match(self):
        """测试消息触发器不匹配"""
        from app.integrations.feishu_trigger import FeishuMessageTrigger, FeishuMessageTriggerConfig
        
        config = FeishuMessageTriggerConfig(keywords=["hello"])
        trigger = FeishuMessageTrigger(config)
        
        message = {
            "message_id": "msg_002",
            "chat_type": "p2p",
            "text": "goodbye world"
        }
        
        events = await trigger.check(message)
        
        assert len(events) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
