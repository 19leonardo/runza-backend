"""
Servicio de Chat - Lógica de negocio para mensajería.
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func
from typing import List, Optional
from datetime import datetime, timezone

from app.models.user import User, user_contacts
from app.models.chat import Conversation, ConversationParticipant, Message
from app.schemas.chat import (
    ContactResponse, 
    MessageResponse, 
    ConversationResponse,
    SearchUserResponse
)


class ChatService:
    
    @staticmethod
    def search_users(db: Session, query: str, current_user_id: int, limit: int = 10) -> List[SearchUserResponse]:
        """Buscar usuarios por email o nombre"""
        users = db.query(User).filter(
            User.id != current_user_id,
            User.is_active == True,
            or_(
                User.email.ilike(f"%{query}%"),
                User.full_name.ilike(f"%{query}%")
            )
        ).limit(limit).all()
        
        # Obtener contactos del usuario actual
        current_user = db.query(User).filter(User.id == current_user_id).first()
        contact_ids = [c.id for c in current_user.contacts] if current_user else []
        
        return [
            SearchUserResponse(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                avatar_url=u.avatar_url,
                is_contact=u.id in contact_ids
            )
            for u in users
        ]
    
    @staticmethod
    def add_contact(db: Session, user_id: int, contact_email: str) -> Optional[User]:
        """Agregar un contacto por email"""
        contact = db.query(User).filter(
            User.email == contact_email,
            User.is_active == True
        ).first()
        
        if not contact or contact.id == user_id:
            return None
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Verificar si ya es contacto
        if contact in user.contacts:
            return contact
        
        # Agregar contacto (bidireccional)
        user.contacts.append(contact)
        contact.contacts.append(user)
        db.commit()
        
        return contact
    
    @staticmethod
    def _normalize_datetime(dt: Optional[datetime]) -> datetime:
        """Normalizar datetime para comparación (agregar timezone si no tiene)"""
        if dt is None:
            return datetime.min.replace(tzinfo=timezone.utc)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    
    @staticmethod
    def get_contacts(db: Session, user_id: int) -> List[ContactResponse]:
        """Obtener lista de contactos con info de último mensaje"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        contacts_response = []
        
        for contact in user.contacts:
            # Buscar conversación entre ambos usuarios
            conversation = ChatService._get_or_create_conversation(db, user_id, contact.id, create=False)
            
            last_message = None
            last_message_time = None
            unread_count = 0
            conversation_id = None
            
            if conversation:
                conversation_id = conversation.id
                # Último mensaje
                last_msg = db.query(Message).filter(
                    Message.conversation_id == conversation.id
                ).order_by(desc(Message.created_at)).first()
                
                if last_msg:
                    last_message = last_msg.content[:50]
                    last_message_time = last_msg.created_at
                
                # Contar no leídos
                participant = db.query(ConversationParticipant).filter(
                    ConversationParticipant.conversation_id == conversation.id,
                    ConversationParticipant.user_id == user_id
                ).first()
                
                if participant:
                    last_read = participant.last_read_at or datetime.min.replace(tzinfo=timezone.utc)
                    # Normalizar last_read si no tiene timezone
                    if last_read.tzinfo is None:
                        last_read = last_read.replace(tzinfo=timezone.utc)
                    
                    unread_count = db.query(Message).filter(
                        Message.conversation_id == conversation.id,
                        Message.sender_id != user_id,
                        Message.created_at > last_read
                    ).count()
            
            contacts_response.append(ContactResponse(
                id=contact.id,
                email=contact.email,
                full_name=contact.full_name,
                avatar_url=contact.avatar_url,
                is_online=contact.is_online if contact.is_online is not None else False,
                last_seen=contact.last_seen,
                last_message=last_message,
                last_message_time=last_message_time,
                unread_count=unread_count,
                conversation_id=conversation_id
            ))
        
        # Ordenar por último mensaje (usando función de normalización)
        contacts_response.sort(
            key=lambda x: ChatService._normalize_datetime(x.last_message_time),
            reverse=True
        )
        
        return contacts_response
    
    @staticmethod
    def _get_or_create_conversation(
        db: Session, 
        user1_id: int, 
        user2_id: int, 
        create: bool = True
    ) -> Optional[Conversation]:
        """Obtener o crear conversación entre dos usuarios"""
        # Buscar conversación existente
        subquery = db.query(ConversationParticipant.conversation_id).filter(
            ConversationParticipant.user_id.in_([user1_id, user2_id])
        ).group_by(
            ConversationParticipant.conversation_id
        ).having(
            func.count(ConversationParticipant.user_id) == 2
        ).subquery()
        
        conversation = db.query(Conversation).filter(
            Conversation.id.in_(subquery),
            Conversation.is_group == False
        ).first()
        
        if conversation:
            return conversation
        
        if not create:
            return None
        
        # Crear nueva conversación
        conversation = Conversation(is_group=False)
        db.add(conversation)
        db.flush()
        
        # Agregar participantes
        for uid in [user1_id, user2_id]:
            participant = ConversationParticipant(
                conversation_id=conversation.id,
                user_id=uid
            )
            db.add(participant)
        
        db.commit()
        db.refresh(conversation)
        
        return conversation
    
    @staticmethod
    def get_or_create_conversation(db: Session, user_id: int, other_user_id: int) -> Optional[Conversation]:
        """Obtener o crear conversación (método público)"""
        return ChatService._get_or_create_conversation(db, user_id, other_user_id, create=True)
    
    @staticmethod
    def get_messages(
        db: Session, 
        conversation_id: int, 
        user_id: int,
        limit: int = 50,
        before_id: Optional[int] = None
    ) -> List[MessageResponse]:
        """Obtener mensajes de una conversación"""
        # Verificar que el usuario es participante
        participant = db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == user_id
        ).first()
        
        if not participant:
            return []
        
        query = db.query(Message).filter(Message.conversation_id == conversation_id)
        
        if before_id:
            query = query.filter(Message.id < before_id)
        
        messages = query.order_by(desc(Message.created_at)).limit(limit).all()
        messages.reverse()  # Ordenar de más antiguo a más nuevo
        
        # Marcar como leídos
        participant.last_read_at = datetime.now(timezone.utc)
        db.commit()
        
        return [
            MessageResponse(
                id=m.id,
                conversation_id=m.conversation_id,
                sender_id=m.sender_id,
                sender_name=m.sender.full_name,
                sender_email=m.sender.email,
                content=m.content,
                created_at=m.created_at,
                is_me=m.sender_id == user_id
            )
            for m in messages
        ]
    
    @staticmethod
    def send_message(
        db: Session, 
        conversation_id: int, 
        sender_id: int, 
        content: str
    ) -> Optional[MessageResponse]:
        """Enviar un mensaje"""
        # Verificar que el usuario es participante
        participant = db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == sender_id
        ).first()
        
        if not participant:
            return None
        
        # Crear mensaje
        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content
        )
        db.add(message)
        
        # Actualizar timestamp de conversación
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            conversation.updated_at = datetime.now(timezone.utc)
        
        # Actualizar last_read del sender
        participant.last_read_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(message)
        
        sender = db.query(User).filter(User.id == sender_id).first()
        
        return MessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            sender_id=message.sender_id,
            sender_name=sender.full_name if sender else None,
            sender_email=sender.email if sender else "",
            content=message.content,
            created_at=message.created_at,
            is_me=True
        )
    
    @staticmethod
    def update_user_online_status(db: Session, user_id: int, is_online: bool):
        """Actualizar estado online del usuario"""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_online = is_online
            user.last_seen = datetime.now(timezone.utc)
            db.commit()