"""
Schemas de Chat - Validación de datos para el sistema de mensajería.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# === Usuarios/Contactos ===
class UserBasic(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_online: bool = False
    last_seen: Optional[datetime] = None

    class Config:
        from_attributes = True


class ContactResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_online: bool = False
    last_seen: Optional[datetime] = None
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None
    unread_count: int = 0
    conversation_id: Optional[int] = None

    class Config:
        from_attributes = True


class AddContactRequest(BaseModel):
    email: str


class SearchUserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_contact: bool = False

    class Config:
        from_attributes = True


# === Mensajes ===
class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    sender_name: Optional[str] = None
    sender_email: str
    content: str
    created_at: datetime
    is_me: bool = False

    class Config:
        from_attributes = True


# === Conversaciones ===
class ConversationCreate(BaseModel):
    participant_ids: List[int]
    is_group: bool = False
    name: Optional[str] = None


class ConversationResponse(BaseModel):
    id: int
    is_group: bool
    name: Optional[str] = None
    participants: List[UserBasic]
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None
    unread_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationWithMessages(BaseModel):
    id: int
    is_group: bool
    name: Optional[str] = None
    participants: List[UserBasic]
    messages: List[MessageResponse]

    class Config:
        from_attributes = True