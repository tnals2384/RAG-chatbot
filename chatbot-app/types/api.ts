export interface ChatRequest {
  question: string;
  session_id?: string;
}

export interface ChatResponse {
  success: boolean;
  answer: string;
  session_id: string;
  message: string;
}

export interface QueryRequest {
  question: string;
  similarity_top_k?: number;
}

export interface QueryResponse {
  success: boolean;
  answer: string;
  message: string;
}

export interface ErrorResponse {
  success: false;
  message: string;
  error: string;
  detail?: string;
}

export interface HealthResponse {
  status: string;
  chatbot_initialized: boolean;
  message: string;
}

export interface ResetSessionRequest {
  session_id: string;
}

export interface ResetSessionResponse {
  success: boolean;
  session_id: string;
  message: string;
}

