"""
飞书机器人 Webhook 处理
接收飞书事件订阅的消息事件
"""
import json
import hmac
import hashlib
import base64
import time
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from app.config import settings
from app.integrations.feishu_event_handler import FeishuEventHandler

router = APIRouter(prefix="/api/integrations/feishu", tags=["飞书机器人"])


class FeishuWebhookVerifyRequest(BaseModel):
    """飞书 URL 验证请求"""
    challenge: Optional[str] = None


class FeishuEventSchema(BaseModel):
    """飞书事件 schema（用于参数解析）"""
    schema_type: str
    event: Dict[str, Any]
    token: Optional[str] = None
    challenge: Optional[str] = None


def verify_feishu_sign(encrypt_key: str, timestamp: str, sign: str, body: bytes) -> bool:
    """
    验证飞书签名
    
    Args:
        encrypt_key: 加密密钥
        timestamp: 时间戳
        sign: 签名
        body: 请求体
    
    Returns:
        验证是否通过
    """
    if not encrypt_key:
        return True  # 未配置加密密钥时跳过验证
    
    # 构造签名字符串
    string_to_sign = f"{timestamp}\n{encrypt_key}"
    
    # 计算 HMAC-SHA256
    import secrets
    if len(string_to_sign) > 0:
        hmac_obj = hmac.new(
            string_to_sign.encode("utf-8"),
            body,
            hashlib.sha256
        )
        calculated_sign = base64.b64encode(hmac_obj.digest()).decode("utf-8")
    else:
        calculated_sign = ""
    
    return secrets.compare_digest(calculated_sign, sign)


def decrypt_feishu_encrypt(encrypt_key: str, encrypt_str: str) -> str:
    """
    解密飞书加密消息
    
    Args:
        encrypt_key: 加密密钥
        encrypt_str: 加密后的字符串
    
    Returns:
        解密后的 JSON 字符串
    """
    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import unpad
        
        # Base64 解码
        encrypted_data = base64.b64decode(encrypt_str)
        
        # AES 解密
        key_bytes = encrypt_key.encode("utf-8")[:32].ljust(32, b'\0')
        cipher = AES.new(key_bytes, AES.MODE_CBC, encrypted_data[:16])
        decrypted = unpad(cipher.decrypt(encrypted_data[16:]), 32)
        
        # 去掉 PKCS7 padding 后解析 JSON
        decrypted_str = decrypted.decode("utf-8")
        # 去掉末尾可能的 padding 字符
        decrypted_str = decrypted_str.rstrip('\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f')
        
        # 尝试解析 JSON
        return json.loads(decrypted_str)
    except Exception as e:
        raise ValueError(f"解密失败: {e}")


event_handler = FeishuEventHandler()


@router.get("/webhook")
async def verify_webhook_url(
    challenge: Optional[str] = None,
    verification_token: Optional[str] = None,
):
    """
    飞书 Webhook URL 验证
    飞书在创建事件订阅时会发送 GET 请求验证 URL 是否可用
    """
    if challenge:
        # 返回 challenge 表示验证通过
        return {"challenge": challenge}
    
    # 如果没有 challenge 参数，返回错误
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Missing challenge parameter"
    )


@router.post("/webhook")
async def handle_feishu_event(request: Request):
    """
    处理飞书事件
    支持加解密的消息事件
    """
    body = await request.body()
    headers = dict(request.headers)
    
    # 尝试获取 timestamp 和 sign
    timestamp = headers.get("X-Lark-Request-Timestamp", "")
    sign = headers.get("X-Lark-Request-Signature", "")
    
    # 验证签名
    encrypt_key = settings.FEISHU_ENCRYPT_KEY or ""
    if settings.FEISHU_VERIFICATION_TOKEN:
        # 飞书标准事件订阅验证
        token = headers.get("X-Lark-Request-Attestation-Token", "") or \
                headers.get("Authorization", "").replace("Bearer ", "")
        
        if token != settings.FEISHU_VERIFICATION_TOKEN:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid verification token"
            )
    
    # 解析请求体
    try:
        body_json = json.loads(body.decode("utf-8"))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON body: {e}"
        )
    
    # 处理加密消息
    if "encrypt" in body_json:
        # 加密模式
        encrypt_str = body_json.get("encrypt", "")
        try:
            body_json = decrypt_feishu_encrypt(encrypt_key, encrypt_str)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Decryption failed: {e}"
            )
    
    # 处理 URL 验证请求
    if "challenge" in body_json:
        return {"challenge": body_json.get("challenge")}
    
    # 事件类型
    event_type = body_json.get("event", {}).get("type") or body_json.get("header", {}).get("event_type")
    event_id = body_json.get("event", {}).get("message", {}).get("message_id") or \
               body_json.get("header", {}).get("event_id", "")
    
    # 处理事件
    try:
        if event_type == "im.message.receive_v1":
            # 消息接收事件
            message_event = body_json.get("event", {})
            result = await event_handler.handle_message_event(message_event)
            return result
        else:
            # 未知事件类型
            return {"status": "ignored", "reason": f"Unsupported event type: {event_type}"}
    
    except Exception as e:
        # 记录错误但不中断响应
        print(f"Error handling feishu event: {e}")
        return {"status": "error", "message": str(e)}


# ==================== 消息处理相关模型 ====================


class FeishuMessageReceivedEvent(BaseModel):
    """飞书消息接收事件"""
    message_id: str
    create_time: str
    chat_id: str
    chat_type: str  # p2p（私聊）/ group（群聊）
    sender: Dict[str, Any]  # sender: {sender_type: user/bot, id: open_id}
    message_type: str  # text/post/image/file/interactive
    content: str  # 消息内容（JSON格式）


def parse_message_content(message_type: str, content: str) -> Dict[str, Any]:
    """
    解析飞书消息内容
    
    Args:
        message_type: 消息类型
        content: 消息内容（JSON字符串）
    
    Returns:
        解析后的内容字典
    """
    try:
        content_dict = json.loads(content) if isinstance(content, str) else content
    except Exception:
        return {"raw": content}
    
    if message_type == "text":
        return {"text": content_dict.get("text", "")}
    elif message_type == "post":
        return {"post": content_dict}
    elif message_type == "image":
        return {"image_key": content_dict.get("image_key")}
    elif message_type == "file":
        return {"file_key": content_dict.get("file_key"), "file_name": content_dict.get("file_name")}
    elif message_type == "interactive":
        return {"card": content_dict}
    else:
        return content_dict


async def handle_bot_command(text: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理机器人命令
    
    Args:
        text: 消息文本
        event: 原始事件
    
    Returns:
        处理结果
    """
    text = text.strip()
    
    if text == "/help":
        return {
            "reply": "🤖 AI自动化工作流机器人\n\n"
                    "支持以下命令：\n"
                    "/start - 启动机器人\n"
                    "/help - 显示帮助\n"
                    "/status - 查看工作流状态\n"
                    "直接发送消息将触发工作流执行"
        }
    elif text == "/start":
        return {
            "reply": "👋 欢迎使用AI自动化工作流！\n"
                    "发送任意消息将触发工作流执行。"
        }
    elif text == "/status":
        return {
            "reply": "✅ 机器人正常运行中"
        }
    else:
        # 传递给工作流触发器
        return {"trigger_workflow": True, "text": text}
