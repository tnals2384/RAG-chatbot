/**
 * Users 테이블 스키마 기반
 * SQL: id SERIAL (INTEGER), email VARCHAR(255), name VARCHAR(255), image TEXT,
 *      provider VARCHAR(255), provider_id VARCHAR(255),
 *      created_at TIMESTAMP, updated_at TIMESTAMP
 */
export interface User {
  id: number; // SERIAL로 자동 생성되는 정수
  email: string;
  name: string;
  image?: string;
  createdAt?: string;
  updatedAt?: string;
}

/**
 * Chats 테이블 스키마 기반 (채팅방 목록)
 * SQL: id VARCHAR(255), title VARCHAR(500), user_id INTEGER (users.id 참조),
 *      created_at TIMESTAMP, updated_at TIMESTAMP
 */
export interface Chat {
  id: string;
  title: string;
  userId: number; // users 테이블의 id (INTEGER) 참조
  createdAt: string;
  updatedAt: string;
}

/**
 * Messages 테이블 스키마 기반
 * SQL: id SERIAL, chat_id VARCHAR(255), role VARCHAR(10) CHECK (role IN ('user', 'bot')),
 *      content TEXT, created_at TIMESTAMP
 */
export interface Message {
  id?: number;
  chatId?: string;
  role: "user" | "bot";
  content: string;
  createdAt?: string;
}

/**
 * Chat + Messages 조합 (전체 채팅 기록)
 * chats 테이블과 messages 테이블을 조인한 결과
 */
export interface ChatHistory extends Chat {
  messages: Message[];
}
