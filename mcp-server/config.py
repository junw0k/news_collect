# config.py
from __future__ import annotations

import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Settings(BaseModel):
    """네이버 뉴스 API 통신에 필요한 기본 설정."""

    client_id: str = Field(default_factory=lambda: os.getenv("NAVER_CLIENT_ID", ""))
    client_secret: str = Field(default_factory=lambda: os.getenv("NAVER_CLIENT_SECRET", ""))
    search_url: str = "https://openapi.naver.com/v1/search/news.json"
    default_display: int = 3
    default_sort: str = "sim"
    request_timeout: float = 15.0
    user_agent: str = "Mozilla/5.0 (CollectorBot)"



settings = Settings()
