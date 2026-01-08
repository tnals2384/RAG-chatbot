"""
PostgreSQL 데이터베이스 연결 및 쿼리 모듈 (SQLAlchemy + asyncpg)
"""
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, selectinload
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Index, select, delete, update, func
from sqlalchemy.dialects.postgresql import insert


class Base(DeclarativeBase):
    """SQLAlchemy Base 클래스"""
    pass


class User(Base):
    """사용자 모델"""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    image: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    provider: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provider_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 관계
    chats: Mapped[List["Chat"]] = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """모델을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "image": self.image,
            "provider": self.provider,
            "provider_id": self.provider_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class Chat(Base):
    """채팅 모델"""
    __tablename__ = "chats"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 관계
    user: Mapped["User"] = relationship("User", back_populates="chats")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="chat", cascade="all, delete-orphan", order_by="Message.created_at")
    
    def to_dict(self, include_messages: bool = False) -> Dict[str, Any]:
        """모델을 딕셔너리로 변환"""
        result = {
            "id": self.id,
            "title": self.title,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        if include_messages:
            result["messages"] = [msg.to_dict() for msg in self.messages]
        return result


class Message(Base):
    """메시지 모델"""
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[str] = mapped_column(String(255), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(10), nullable=False)  # 'user' or 'bot'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    
    # 관계
    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")
    
    def to_dict(self) -> Dict[str, Any]:
        """모델을 딕셔너리로 변환"""
        return {
            "role": self.role,
            "content": self.content
        }


class Database:
    """데이터베이스 연결 및 쿼리 관리 클래스 (SQLAlchemy + asyncpg)"""
    
    def __init__(self):
        self.engine = None
        self.async_session_maker: Optional[async_sessionmaker[AsyncSession]] = None
    
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
        
        # jdbc:postgresql:// 형식을 postgresql+asyncpg:// 형식으로 변환
        if database_url.startswith("jdbc:postgresql://"):
            database_url = database_url.replace("jdbc:postgresql://", "postgresql+asyncpg://")
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        # 환경변수에서 직접 URL을 가져오지 않은 경우 구성
        if database_url == f"postgresql+asyncpg://{db_host}:{db_port}/{db_name}":
            if db_password:
                database_url = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            else:
                database_url = f"postgresql+asyncpg://{db_user}@{db_host}:{db_port}/{db_name}"
        
        try:
            self.engine = create_async_engine(
                database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=False  # SQL 쿼리 로깅 (디버깅 시 True로 변경)
            )
            self.async_session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False
            )
            print(f"✅ 데이터베이스 연결 성공: {db_host}:{db_port}/{db_name}")
        except Exception as e:
            print(f"❌ 데이터베이스 연결 실패: {e}")
            raise
    
    async def close(self):
        """데이터베이스 연결 풀 종료"""
        if self.engine:
            await self.engine.dispose()
    
    def get_session(self) -> AsyncSession:
        """비동기 세션 생성"""
        if not self.async_session_maker:
            raise RuntimeError("데이터베이스가 연결되지 않았습니다. connect()를 먼저 호출하세요.")
        return self.async_session_maker()
    
    # ==================== User 관련 메서드 ====================
    
    async def create_user(self, email: str, name: str, image: Optional[str] = None, provider: Optional[str] = None, provider_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """사용자 생성 또는 업데이트 (id는 시퀀스로 자동 생성)"""
        try:
            async with self.get_session() as session:
                # PostgreSQL의 ON CONFLICT 사용
                from sqlalchemy.dialects.postgresql import insert as pg_insert
                
                insert_stmt = pg_insert(User).values(
                    email=email,
                    name=name,
                    image=image,
                    provider=provider,
                    provider_id=provider_id
                )
                
                upsert_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=['email'],
                    set_=dict(
                        name=insert_stmt.excluded.name,
                        image=insert_stmt.excluded.image,
                        provider=insert_stmt.excluded.provider,
                        provider_id=insert_stmt.excluded.provider_id,
                        updated_at=func.now()
                    )
                )
                
                stmt = upsert_stmt.returning(User)
                result = await session.execute(stmt)
                await session.commit()
                user = result.scalar_one()
                return user.to_dict()
        except Exception as e:
            print(f"❌ create_user 오류: {str(e)}")
            import traceback
            print(traceback.format_exc())
            raise
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """사용자 조회 (user_id는 INTEGER)"""
        async with self.get_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            return user.to_dict() if user else None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """이메일로 사용자 조회"""
        async with self.get_session() as session:
            stmt = select(User).where(User.email == email)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            return user.to_dict() if user else None
    
    async def create_or_get_user_by_email(self, email: str, name: str, image: Optional[str] = None, provider: Optional[str] = None, provider_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """이메일로 사용자 조회 후 없으면 생성 (id는 시퀀스로 자동 생성)"""
        # create_user가 ON CONFLICT (email)을 사용하므로 자동으로 조회/생성/업데이트 처리
        return await self.create_user(email, name, image, provider, provider_id)
    
    # ==================== Chat 관련 메서드 ====================
    
    async def create_chat(self, chat_id: str, title: str, user_id: int, messages: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """새 채팅 생성 및 메시지 저장 (user_id는 INTEGER)"""
        async with self.get_session() as session:
            try:
                # 채팅 생성
                chat = Chat(id=chat_id, title=title, user_id=user_id)
                session.add(chat)
                await session.flush()  # ID를 얻기 위해 flush
                
                # 메시지들 저장
                if messages:
                    for msg in messages:
                        message = Message(
                            chat_id=chat_id,
                            role=msg['role'],
                            content=msg['content']
                        )
                        session.add(message)
                
                await session.commit()
                
                # 채팅과 메시지를 다시 조회하여 반환
                await session.refresh(chat)
                stmt = select(Chat).where(Chat.id == chat_id).options(
                    selectinload(Chat.messages)
                )
                result = await session.execute(stmt)
                chat = result.scalar_one()
                
                chat_dict = chat.to_dict(include_messages=True)
                return chat_dict
            except Exception as e:
                await session.rollback()
                print(f"❌ create_chat 오류: {str(e)}")
                import traceback
                print(traceback.format_exc())
                raise
    
    async def get_chat(self, chat_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """특정 채팅 조회 (메시지 포함, user_id는 INTEGER)"""
        async with self.get_session() as session:
            stmt = (
                select(Chat)
                .where(Chat.id == chat_id, Chat.user_id == user_id)
                .options(selectinload(Chat.messages))
            )
            result = await session.execute(stmt)
            chat = result.scalar_one_or_none()
            return chat.to_dict(include_messages=True) if chat else None
    
    async def get_chats_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """사용자의 모든 채팅 목록 조회 (최신순, 메시지 제외, user_id는 INTEGER)"""
        async with self.get_session() as session:
            stmt = (
                select(Chat)
                .where(Chat.user_id == user_id)
                .order_by(Chat.updated_at.desc())
            )
            result = await session.execute(stmt)
            chats = result.scalars().all()
            return [chat.to_dict(include_messages=False) for chat in chats]
    
    async def add_message(self, chat_id: str, role: str, content: str) -> bool:
        """채팅에 메시지 추가"""
        async with self.get_session() as session:
            try:
                # 메시지 추가
                message = Message(chat_id=chat_id, role=role, content=content)
                session.add(message)
                
                # 채팅의 updated_at 업데이트
                stmt = (
                    update(Chat)
                    .where(Chat.id == chat_id)
                    .values(updated_at=func.now())
                )
                await session.execute(stmt)
                
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                print(f"❌ add_message 오류: {str(e)}")
                import traceback
                print(traceback.format_exc())
                raise
    
    async def update_chat(self, chat_id: str, user_id: int, title: Optional[str] = None, messages: Optional[List[Dict[str, str]]] = None) -> Optional[Dict[str, Any]]:
        """채팅 업데이트 (user_id는 INTEGER)"""
        async with self.get_session() as session:
            try:
                # 채팅 조회
                stmt = select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
                result = await session.execute(stmt)
                chat = result.scalar_one_or_none()
                
                if not chat:
                    return None
                
                # 제목 업데이트
                if title is not None:
                    chat.title = title
                
                # 메시지 전체 교체 (기존 메시지 삭제 후 새로 추가)
                if messages is not None:
                    # 기존 메시지 삭제
                    delete_stmt = delete(Message).where(Message.chat_id == chat_id)
                    await session.execute(delete_stmt)
                    
                    # 새 메시지 추가
                    for msg in messages:
                        message = Message(
                            chat_id=chat_id,
                            role=msg['role'],
                            content=msg['content']
                        )
                        session.add(message)
                
                await session.commit()
                
                # 업데이트된 채팅 조회
                stmt = select(Chat).where(Chat.id == chat_id).options(
                    selectinload(Chat.messages)
                )
                result = await session.execute(stmt)
                chat = result.scalar_one()
                return chat.to_dict(include_messages=True)
            except Exception as e:
                await session.rollback()
                print(f"❌ update_chat 오류: {str(e)}")
                import traceback
                print(traceback.format_exc())
                raise
    
    async def delete_chat(self, chat_id: str, user_id: int) -> bool:
        """채팅 삭제 (CASCADE로 메시지도 자동 삭제됨, user_id는 INTEGER)"""
        async with self.get_session() as session:
            try:
                stmt = delete(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
                result = await session.execute(stmt)
                await session.commit()
                
                # 삭제된 행 수 확인
                return result.rowcount > 0
            except Exception as e:
                await session.rollback()
                print(f"❌ delete_chat 오류: {str(e)}")
                import traceback
                print(traceback.format_exc())
                raise


# 전역 데이터베이스 인스턴스
db = Database()