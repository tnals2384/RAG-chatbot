"""
PostgreSQL 데이터베이스 연결 및 쿼리 모듈
"""
import os
import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


class Database:
    """데이터베이스 연결 및 쿼리 관리 클래스"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """데이터베이스 연결 풀 생성"""
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT")
        db_name = os.getenv("DB_NAME")
        database_url = os.getenv(
            "DATABASE_URL",
           f"postgresql://{db_host}:{db_port}/{db_name}"
        )
        
        # jdbc:postgresql:// 형식을 postgresql:// 형식으로 변환
        if database_url.startswith("jdbc:postgresql://"):
            database_url = database_url.replace("jdbc:postgresql://", "postgresql://")
        
        

        
        # 환경변수에서 직접 URL을 가져오지 않은 경우 구성
        if database_url == f"postgresql://{db_host}:{db_port}/{db_name}":
            if db_password:
                database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            else:
                database_url = f"postgresql://{db_user}@{db_host}:{db_port}/{db_name}"
        
        try:
            self.pool = await asyncpg.create_pool(
                database_url,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            print(f"✅ 데이터베이스 연결 성공: {db_host}:{db_port}/{db_name}")
        except Exception as e:
            print(f"❌ 데이터베이스 연결 실패: {e}")
            raise
    
    async def close(self):
        """데이터베이스 연결 풀 종료"""
        if self.pool:
            await self.pool.close()
    
    async def execute(self, query: str, *args):
        """쿼리 실행 (INSERT, UPDATE, DELETE)"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args):
        """쿼리 실행 후 여러 행 반환"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args):
        """쿼리 실행 후 단일 행 반환"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    # ==================== User 관련 메서드 ====================
    
    async def create_user(self, email: str, name: str, image: Optional[str] = None, provider: Optional[str] = None, provider_id: Optional[str] = None) -> Dict[str, Any]:
        """사용자 생성 또는 업데이트 (id는 시퀀스로 자동 생성)"""
        try:
            query = """
                INSERT INTO users (email, name, image, provider, provider_id)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (email) DO UPDATE
                SET name = EXCLUDED.name,
                    image = EXCLUDED.image,
                    provider = EXCLUDED.provider,
                    provider_id = EXCLUDED.provider_id,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id, email, name, image, provider, provider_id, created_at, updated_at
            """
            row = await self.fetchrow(query, email, name, image, provider, provider_id)
            if row:
                return dict(row)
            return None
        except Exception as e:
            print(f"❌ create_user 오류: {str(e)}")
            import traceback
            print(traceback.format_exc())
            raise
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """사용자 조회 (user_id는 INTEGER)"""
        query = "SELECT id, email, name, image, created_at, updated_at FROM users WHERE id = $1"
        row = await self.fetchrow(query, user_id)
        return dict(row) if row else None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """이메일로 사용자 조회"""
        query = "SELECT id, email, name, image, provider, provider_id, created_at, updated_at FROM users WHERE email = $1"
        row = await self.fetchrow(query, email)
        return dict(row) if row else None
    
    async def create_or_get_user_by_email(self, email: str, name: str, image: Optional[str] = None, provider: Optional[str] = None, provider_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """이메일로 사용자 조회 후 없으면 생성 (id는 시퀀스로 자동 생성)"""
        # create_user가 ON CONFLICT (email)을 사용하므로 자동으로 조회/생성/업데이트 처리
        return await self.create_user(email, name, image, provider, provider_id)
    
    # ==================== Chat 관련 메서드 ====================
    
    async def create_chat(self, chat_id: str, title: str, user_id: int, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """새 채팅 생성 및 메시지 저장 (user_id는 INTEGER)"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # 채팅 생성
                chat_query = """
                    INSERT INTO chats (id, title, user_id)
                    VALUES ($1, $2, $3)
                    RETURNING id, title, user_id, created_at, updated_at
                """
                chat_row = await conn.fetchrow(chat_query, chat_id, title, user_id)
                
                if not chat_row:
                    return None
                
                # 메시지들 저장
                if messages:
                    message_query = """
                        INSERT INTO messages (chat_id, role, content)
                        VALUES ($1, $2, $3)
                    """
                    for msg in messages:
                        await conn.execute(
                            message_query,
                            chat_id,
                            msg['role'],
                            msg['content']
                        )
                
                result = dict(chat_row)
                result['messages'] = messages
                return result
    
    async def get_chat(self, chat_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """특정 채팅 조회 (메시지 포함, user_id는 INTEGER)"""
        query = """
            SELECT c.id, c.title, c.user_id, c.created_at, c.updated_at,
                   m.id as message_id, m.role, m.content, m.created_at as message_created_at
            FROM chats c
            LEFT JOIN messages m ON c.id = m.chat_id
            WHERE c.id = $1 AND c.user_id = $2
            ORDER BY m.created_at ASC
        """
        rows = await self.fetch(query, chat_id, user_id)
        
        if not rows:
            return None
        
        # 첫 번째 행에서 채팅 정보 추출
        first_row = dict(rows[0])
        messages = []
        
        for row in rows:
            if row['message_id']:  # 메시지가 있는 경우
                messages.append({
                    'role': row['role'],
                    'content': row['content']
                })
        
        return {
            'id': first_row['id'],
            'title': first_row['title'],
            'user_id': first_row['user_id'],
            'created_at': first_row['created_at'],
            'updated_at': first_row['updated_at'],
            'messages': messages
        }
    
    async def get_chats_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """사용자의 모든 채팅 목록 조회 (최신순, 메시지 제외, user_id는 INTEGER)"""
        query = """
            SELECT id, title, user_id, created_at, updated_at
            FROM chats
            WHERE user_id = $1
            ORDER BY updated_at DESC
        """
        rows = await self.fetch(query, user_id)
        return [dict(row) for row in rows]
    
    async def add_message(self, chat_id: str, role: str, content: str) -> bool:
        """채팅에 메시지 추가"""
        query = """
            INSERT INTO messages (chat_id, role, content)
            VALUES ($1, $2, $3)
        """
        await self.execute(query, chat_id, role, content)
        
        # 채팅의 updated_at 업데이트
        update_query = """
            UPDATE chats
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
        """
        await self.execute(update_query, chat_id)
        return True
    
    async def update_chat(self, chat_id: str, user_id: int, title: Optional[str] = None, messages: Optional[List[Dict[str, str]]] = None) -> Optional[Dict[str, Any]]:
        """채팅 업데이트 (user_id는 INTEGER)"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # 제목 업데이트
                if title is not None:
                    update_query = """
                        UPDATE chats
                        SET title = $1, updated_at = CURRENT_TIMESTAMP
                        WHERE id = $2 AND user_id = $3
                    """
                    await conn.execute(update_query, title, chat_id, user_id)
                
                # 메시지 전체 교체 (기존 메시지 삭제 후 새로 추가)
                if messages is not None:
                    # 기존 메시지 삭제
                    delete_query = "DELETE FROM messages WHERE chat_id = $1"
                    await conn.execute(delete_query, chat_id)
                    
                    # 새 메시지 추가
                    if messages:
                        insert_query = """
                            INSERT INTO messages (chat_id, role, content)
                            VALUES ($1, $2, $3)
                        """
                        for msg in messages:
                            await conn.execute(
                                insert_query,
                                chat_id,
                                msg['role'],
                                msg['content']
                            )
                    
                    # 채팅의 updated_at 업데이트
                    update_query = """
                        UPDATE chats
                        SET updated_at = CURRENT_TIMESTAMP
                        WHERE id = $1
                    """
                    await conn.execute(update_query, chat_id)
        
        return await self.get_chat(chat_id, user_id)
    
    async def delete_chat(self, chat_id: str, user_id: int) -> bool:
        """채팅 삭제 (CASCADE로 메시지도 자동 삭제됨, user_id는 INTEGER)"""
        query = "DELETE FROM chats WHERE id = $1 AND user_id = $2"
        result = await self.execute(query, chat_id, user_id)
        return result == "DELETE 1"


# 전역 데이터베이스 인스턴스
db = Database()
