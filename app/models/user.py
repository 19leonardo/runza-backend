"""
Modelo de Usuario - Tabla principal de usuarios del sistema RunZa.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Date, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

# Tabla de asociación para contactos (relación muchos a muchos)
user_contacts = Table(
    'user_contacts',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('contact_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now())
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Perfil
    full_name = Column(String(100), nullable=True)
    birth_date = Column(Date, nullable=True)
    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Estado
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime(timezone=True), nullable=True)

    # Gamificación
    total_points = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    level = Column(Integer, default=1)

    # Estadísticas totales
    total_exercises = Column(Integer, default=0)
    total_meals_logged = Column(Integer, default=0)
    total_water_glasses = Column(Integer, default=0)
    total_wellness_activities = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_activity = Column(DateTime(timezone=True), nullable=True)

    # Relaciones
    activities = relationship("Activity", back_populates="user", cascade="all, delete-orphan")
    daily_stats = relationship("DailyStats", back_populates="user", cascade="all, delete-orphan")
    
    # Relaciones de chat
    contacts = relationship(
        "User",
        secondary=user_contacts,
        primaryjoin=id == user_contacts.c.user_id,
        secondaryjoin=id == user_contacts.c.contact_id,
        backref="contacted_by"
    )
    conversation_participants = relationship("ConversationParticipant", back_populates="user")
    sent_messages = relationship("Message", back_populates="sender")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"