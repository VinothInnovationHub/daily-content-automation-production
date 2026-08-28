from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class JobCreate(BaseModel):
    topic: str = Field(min_length=3, max_length=500)
    perspective: str = ""
    instructions: str = ""


class ContentUpdate(BaseModel):
    title: str | None = None
    body: str | None = None


class ContentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    channel: str
    title: str
    body: str
    status: str
    published_url: str


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    topic: str
    perspective: str
    instructions: str
    status: str
    rejection_reason: str
    created_at: datetime
    contents: list[ContentOut]


class HealthOut(BaseModel):
    status: str
    timezone: str
    daily_run: str
    llm_provider: str
