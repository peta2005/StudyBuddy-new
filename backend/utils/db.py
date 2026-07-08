import os
import pymysql
import pymysql.cursors
from contextlib import contextmanager

def _get_config():
    return {
        "host":     os.getenv("DB_HOST", "localhost"),
        "port":     int(os.getenv("DB_PORT", "3306")),
        "user":     os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": False,
    }

@contextmanager
def get_connection():
    conn = pymysql.connect(**_get_config())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(36) PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash TEXT,
                    email_verified TINYINT(1) NOT NULL DEFAULT 0,
                    oauth_provider VARCHAR(50),
                    oauth_id VARCHAR(255),
                    created_at VARCHAR(50) NOT NULL,
                    UNIQUE KEY uq_oauth (oauth_provider, oauth_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS auth_tokens (
                    token_hash VARCHAR(64) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL,
                    token_type VARCHAR(20) NOT NULL,
                    expires_at VARCHAR(50) NOT NULL,
                    used TINYINT(1) NOT NULL DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS refresh_tokens (
                    token_hash VARCHAR(64) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL,
                    expires_at VARCHAR(50) NOT NULL,
                    revoked TINYINT(1) NOT NULL DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL,
                    session_id VARCHAR(36) NOT NULL,
                    session_title VARCHAR(255) NOT NULL DEFAULT 'New Chat',
                    role VARCHAR(20) NOT NULL,
                    content LONGTEXT NOT NULL,
                    sources JSON,
                    created_at VARCHAR(50) NOT NULL,
                    INDEX idx_chat_user (user_id),
                    INDEX idx_chat_session (session_id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
