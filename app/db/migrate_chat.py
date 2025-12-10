"""
Script para crear las tablas de chat en la base de datos.
"""
from sqlalchemy import text
from app.db.base import engine

def migrate_chat_tables():
    """Crear tablas de chat si no existen"""
    
    with engine.connect() as conn:
        # Tabla user_contacts
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_contacts (
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                contact_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                PRIMARY KEY (user_id, contact_id)
            );
        """))
        
        # Tabla conversations
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                is_group BOOLEAN DEFAULT FALSE,
                name VARCHAR(100),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """))
        
        # Tabla conversation_participants
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS conversation_participants (
                id SERIAL PRIMARY KEY,
                conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_read_at TIMESTAMP WITH TIME ZONE
            );
        """))
        
        # Tabla messages
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
                sender_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """))
        
        # Agregar columnas nuevas a users si no existen
        conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='users' AND column_name='is_online') THEN
                    ALTER TABLE users ADD COLUMN is_online BOOLEAN DEFAULT FALSE;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='users' AND column_name='last_seen') THEN
                    ALTER TABLE users ADD COLUMN last_seen TIMESTAMP WITH TIME ZONE;
                END IF;
            END $$;
        """))
        
        conn.commit()
        print("✅ Tablas de chat creadas correctamente")

if __name__ == "__main__":
    migrate_chat_tables()