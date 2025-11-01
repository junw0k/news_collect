# config.py
from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
import os


class Settings(BaseModel):
    """프로젝트 공통 설정 (네이버 API, 크롤링 옵션 등)."""

    client_id: str = Field(default_factory=lambda:
os.getenv("NAVER_CLIENT_ID", ""))
    client_secret: str = Field(default_factory=lambda:
os.getenv("NAVER_CLIENT_SECRET", ""))
    search_url: str = "https://openapi.naver.com/v1/search/news.json"
    article_base_url: str = "https://n.news.naver.com/mnews/article"
    articles_per_topic: int = 3
    request_timeout: float = 10.0
    user_agent: str = "Mozilla/5.0 (McpResourceBot)"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_dir: Path = Field(default_factory=lambda: Path.cwd() / "logs")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.log_dir.mkdir(parents=True, exist_ok=True)


# 싱글톤 인스턴스
settings = Settings()