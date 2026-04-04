"""
应用配置模块
从环境变量或 .env 文件加载配置
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置类"""
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./ai_workflow.db"
    
    # JWT密钥（生产环境应使用复杂的随机密钥）
    SECRET_KEY: str = "ai-workflow-secret-key-change-in-production"
    
    # JWT算法
    ALGORITHM: str = "HS256"
    
    # 访问令牌过期时间（分钟）
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时
    
    # OpenAI API配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.7
    
    # 飞书配置
    FEISHU_APP_ID: Optional[str] = None
    FEISHU_APP_SECRET: Optional[str] = None
    # 飞书事件订阅配置
    FEISHU_VERIFICATION_TOKEN: Optional[str] = None  # 飞书事件订阅的 Verification Token
    FEISHU_ENCRYPT_KEY: Optional[str] = None  # 飞书事件加密密钥
    FEISHU_WEBHOOK_PATH: str = "/api/integrations/feishu/webhook"  # Webhook 路径
    # 飞书日历轮询配置
    FEISHU_CALENDAR_POLL_INTERVAL_SECONDS: int = 60  # 日历轮询间隔（秒）
    FEISHU_CALENDAR_REMIND_MINUTES: int = 5  # 日历提醒提前分钟数
    
    # 工作流执行配置
    MAX_NODES_PER_WORKFLOW: int = 20
    MAX_CONCURRENT_EXECUTIONS: int = 5
    EXECUTION_TIMEOUT_SECONDS: int = 60
    
    # 执行日志保留配置
    MAX_EXECUTION_LOGS: int = 100
    LOG_RETENTION_DAYS: int = 7
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 创建全局配置实例
settings = Settings()
