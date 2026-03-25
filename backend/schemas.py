from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TouchCreate(BaseModel):
    name: str
    description: Optional[str] = None


class TouchUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class TouchRead(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    method_file_path: Optional[str]
    n_bells: Optional[int]
    rounds_rows: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class PerformanceCreate(BaseModel):
    label: str
    order_index: int = 0


class PerformanceUpdate(BaseModel):
    label: Optional[str] = None
    order_index: Optional[int] = None


class PerformanceRead(BaseModel):
    id: int
    touch_id: int
    label: str
    timing_file_path: Optional[str]
    order_index: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PerformanceReorder(BaseModel):
    id: int
    order_index: int


class CharacteristicFeedbackCreate(BaseModel):
    characteristic_name: str
    is_useful: bool
    notes: Optional[str] = None


class CharacteristicFeedbackRead(BaseModel):
    id: int
    user_id: int
    characteristic_name: str
    is_useful: bool
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisResult(BaseModel):
    data: dict[str, Any]
