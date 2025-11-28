from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class CreateNotificationIn(BaseModel):
    type: str = Field(..., description="Tipo de notificación: INFO, WARNING, SUCCESS, ERROR")
    title: str = Field(..., min_length=1, max_length=200, description="Título de la notificación")
    message: str = Field(..., min_length=1, description="Mensaje de la notificación")

class CreateNotificationOut(BaseModel):
    notification_id: int
    type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime

class NotificationItemOut(BaseModel):
    notification_id: int
    type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime

class NotificationListOut(BaseModel):
    notifications: List[NotificationItemOut]
    total: int
    unread_count: int

class MarkAsReadOut(BaseModel):
    notification_id: int
    is_read: bool
    message: str

class MarkAllAsReadOut(BaseModel):
    marked_count: int
    total_read: int
    read_notifications: List[NotificationItemOut]
    message: str
