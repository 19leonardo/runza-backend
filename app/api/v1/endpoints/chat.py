"""
Endpoints de Chat - API REST para mensajería.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.base import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.chat_service import ChatService
from app.schemas.chat import (
    ContactResponse,
    AddContactRequest,
    SearchUserResponse,
    MessageCreate,
    MessageResponse,
    ConversationResponse
)

router = APIRouter()


@router.get("/search", response_model=List[SearchUserResponse])
def search_users(
    q: str = Query(..., min_length=1, description="Buscar por email o nombre"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Buscar usuarios para agregar como contacto"""
    return ChatService.search_users(db, q, current_user.id)


@router.get("/contacts", response_model=List[ContactResponse])
def get_contacts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener lista de contactos del usuario"""
    return ChatService.get_contacts(db, current_user.id)


@router.post("/contacts", response_model=ContactResponse)
def add_contact(
    request: AddContactRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Agregar un nuevo contacto por email"""
    contact = ChatService.add_contact(db, current_user.id, request.email)
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado o no disponible"
        )
    
    # Obtener info completa del contacto
    contacts = ChatService.get_contacts(db, current_user.id)
    contact_response = next((c for c in contacts if c.id == contact.id), None)
    
    if not contact_response:
        return ContactResponse(
            id=contact.id,
            email=contact.email,
            full_name=contact.full_name,
            avatar_url=contact.avatar_url,
            is_online=contact.is_online,
            last_seen=contact.last_seen,
            unread_count=0
        )
    
    return contact_response


@router.get("/conversations/{contact_id}", response_model=List[MessageResponse])
def get_conversation(
    contact_id: int,
    before_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener mensajes de una conversación con un contacto"""
    # Obtener o crear conversación
    conversation = ChatService.get_or_create_conversation(db, current_user.id, contact_id)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se pudo obtener la conversación"
        )
    
    return ChatService.get_messages(db, conversation.id, current_user.id, before_id=before_id)


@router.post("/conversations/{contact_id}/messages", response_model=MessageResponse)
def send_message(
    contact_id: int,
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enviar un mensaje a un contacto"""
    # Obtener o crear conversación
    conversation = ChatService.get_or_create_conversation(db, current_user.id, contact_id)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se pudo obtener la conversación"
        )
    
    result = ChatService.send_message(db, conversation.id, current_user.id, message.content)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo enviar el mensaje"
        )
    
    return result


@router.post("/online")
def set_online(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marcar usuario como online"""
    ChatService.update_user_online_status(db, current_user.id, True)
    return {"status": "online"}


@router.post("/offline")
def set_offline(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marcar usuario como offline"""
    ChatService.update_user_online_status(db, current_user.id, False)
    return {"status": "offline"}