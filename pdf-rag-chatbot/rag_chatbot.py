"""
LlamaIndex + ChromaDB + OpenAI를 활용한 PDF 기반 RAG 챗봇
"""
import os
from pathlib import Path
from dotenv import load_dotenv

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.storage.storage_context import StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
import chromadb

# 환경 변수 로드
load_dotenv()
\
class RAGChatbot:
    def __init__(self, pdf_directory: str = "pdfs", persist_dir: str = "./chroma_db"):
        """
        RAG 챗봇 초기화
        
        Args:
            pdf_directory: PDF 파일이 있는 디렉토리 경로
            persist_dir: ChromaDB 데이터를 저장할 디렉토리 경로
        """
        # OpenAI API 키 확인
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY 환경 변수를 설정해주세요.")
        
        # LLM 및 Embedding 모델 설정 (Rate Limit 처리 포함)
        self.llm = OpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY"),
            max_retries=10,  # 최대 10번 재시도
            timeout=120.0  # 타임아웃 120초
        )
        
        self.embed_model = OpenAIEmbedding(
            model="text-embedding-3-small",
            api_key=os.getenv("OPENAI_API_KEY"),
            max_retries=10,  # 최대 10번 재시도
            timeout=120.0  # 타임아웃 120초
        )
        
        # Settings에 LLM과 Embedding 모델 설정
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model
        
        # 비용 절약을 위한 청크 크기 설정 (더 큰 청크 = 더 적은 embedding 요청)
        # 기본값: chunk_size=1024, chunk_overlap=20
        # 2048로 늘리면 embedding 요청이 약 절반으로 줄어듭니다
        Settings.chunk_size = 2048
        Settings.chunk_overlap = 200
        
        # ChromaDB 클라이언트 초기화
        self.persist_dir = persist_dir
        self.chroma_client = chromadb.PersistentClient(path=persist_dir)
        
        # 벡터 스토어 및 인덱스 초기화
        self.index = None
        self._initialize_index(pdf_directory)
    
    def _initialize_index(self, pdf_directory: str):
        """인덱스 초기화 또는 로드"""
        collection_name = "pdf_documents"
        
        try:
            # 기존 컬렉션이 있는지 확인
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name
            )
            
            # 기존 인덱스가 있는지 확인 (컬렉션에 문서가 있는지)
            if collection.count() > 0:
                print(f"기존 인덱스를 로드합니다. (문서 수: {collection.count()})")
                # 기존 벡터 스토어 로드
                chroma_collection = self.chroma_client.get_collection(collection_name)
                vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
                storage_context = StorageContext.from_defaults(
                    vector_store=vector_store
                )
                self.index = VectorStoreIndex.from_vector_store(
                    vector_store=vector_store,
                    storage_context=storage_context
                )
            else:
                # 새 인덱스 생성
                print("새 인덱스를 생성합니다...")
                self._create_index(pdf_directory, collection_name)
        except Exception as e:
            print(f"인덱스 로드 중 오류 발생: {e}")
            print("새 인덱스를 생성합니다...")
            self._create_index(pdf_directory, collection_name)
    
    def _create_index(self, pdf_directory: str, collection_name: str):
        """PDF 파일에서 새 인덱스 생성"""
        pdf_path = Path(pdf_directory)
        
        if not pdf_path.exists():
            print(f"경고: {pdf_directory} 디렉토리가 존재하지 않습니다.")
            print("빈 인덱스를 생성합니다. PDF 파일을 추가하려면 ingest_pdfs() 메서드를 사용하세요.")
            # 빈 컬렉션 생성
            chroma_collection = self.chroma_client.get_or_create_collection(
                name=collection_name
            )
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store
            )
            self.index = VectorStoreIndex([], storage_context=storage_context)
            return
        
        # PDF 파일 읽기
        pdf_files = list(pdf_path.glob("*.pdf"))
        if not pdf_files:
            print(f"경고: {pdf_directory} 디렉토리에 PDF 파일이 없습니다.")
            chroma_collection = self.chroma_client.get_or_create_collection(
                name=collection_name
            )
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store
            )
            self.index = VectorStoreIndex([], storage_context=storage_context)
            return
        
        print(f"{len(pdf_files)}개의 PDF 파일을 발견했습니다.")
        
        # PDF 문서 로드
        documents = SimpleDirectoryReader(
            input_dir=pdf_directory,
            required_exts=[".pdf"]
        ).load_data()
        
        print(f"{len(documents)}개의 문서 청크를 로드했습니다.")
        
        # ChromaDB 벡터 스토어 생성
        chroma_collection = self.chroma_client.get_or_create_collection(
            name=collection_name
        )
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store
        )
        
        # 인덱스 생성 (Rate Limit 자동 처리)
        print("인덱스를 생성하는 중입니다...")
        print("⚠️  많은 문서가 있으면 시간이 걸릴 수 있습니다.")
        print("⚠️  Rate Limit 에러가 발생하면 자동으로 재시도합니다.")
        
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                self.index = VectorStoreIndex.from_documents(
                    documents,
                    storage_context=storage_context,
                    show_progress=True
                )
                print("✅ 인덱스 생성이 완료되었습니다!")
                break
            except Exception as e:
                error_str = str(e).lower()
                if "429" in str(e) or "rate limit" in error_str or "too many requests" in error_str:
                    if attempt < max_attempts - 1:
                        wait_time = (attempt + 1) * 30  # 30초, 60초, 90초... 점진적 대기
                        print(f"\n⚠️  Rate Limit 에러 발생. {wait_time}초 후 재시도합니다... (시도 {attempt + 1}/{max_attempts})")
                        time.sleep(wait_time)
                    else:
                        print(f"\n❌ Rate Limit 에러가 계속 발생합니다.")
                        print("   몇 분(5-10분) 기다린 후 다시 실행해주세요.")
                        raise
                else:
                    # Rate Limit이 아닌 다른 에러는 즉시 발생
                    raise
    
    def ingest_pdfs(self, pdf_directory: str):
        """추가 PDF 파일을 인덱스에 추가"""
        pdf_path = Path(pdf_directory)
        
        if not pdf_path.exists():
            raise ValueError(f"{pdf_directory} 디렉토리가 존재하지 않습니다.")
        
        pdf_files = list(pdf_path.glob("*.pdf"))
        if not pdf_files:
            raise ValueError(f"{pdf_directory} 디렉토리에 PDF 파일이 없습니다.")
        
        print(f"{len(pdf_files)}개의 PDF 파일을 발견했습니다.")
        
        # PDF 문서 로드
        documents = SimpleDirectoryReader(
            input_dir=pdf_directory,
            required_exts=[".pdf"]
        ).load_data()
        
        print(f"{len(documents)}개의 문서 청크를 로드했습니다.")
        
        # 기존 인덱스에 문서 추가
        for doc in documents:
            self.index.insert(doc)
        
        print("문서 추가가 완료되었습니다!")
    
    def query(self, question: str, similarity_top_k: int = 5):
        """
        질문에 대한 답변 생성
        
        Args:
            question: 사용자 질문
            similarity_top_k: 유사한 문서를 몇 개까지 검색할지
        
        Returns:
            답변 문자열
        """
        if self.index is None:
            raise ValueError("인덱스가 초기화되지 않았습니다.")
        
        # 쿼리 엔진 생성
        query_engine = self.index.as_query_engine(
            similarity_top_k=similarity_top_k
        )
        
        # 질문 실행 (Rate Limit 자동 재시도)
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = query_engine.query(question)
                return str(response)
            except Exception as e:
                error_str = str(e).lower()
                if "429" in str(e) or "rate limit" in error_str or "too many requests" in error_str:
                    if attempt < max_attempts - 1:
                        wait_time = (attempt + 1) * 10  # 10초, 20초 대기
                        print(f"⚠️  Rate Limit 에러. {wait_time}초 후 재시도합니다...")
                        time.sleep(wait_time)
                    else:
                        raise Exception("Rate Limit 에러가 계속 발생합니다. 잠시 후 다시 시도해주세요.")
                else:
                    raise
    
    def chat(self, question: str, chat_history: list = None):
        """
        대화형 챗봇 인터페이스
        
        Args:
            question: 사용자 질문
            chat_history: 이전 대화 기록 (선택사항)
        
        Returns:
            답변 문자열
        """
        if self.index is None:
            raise ValueError("인덱스가 초기화되지 않았습니다.")
        
        # 채팅 엔진 생성 (대화 기록 지원)
        chat_engine = self.index.as_chat_engine(
            chat_mode="context",
            similarity_top_k=5
        )
        
        # 질문 실행 (Rate Limit 자동 재시도)
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = chat_engine.chat(question)
                return str(response)
            except Exception as e:
                error_str = str(e).lower()
                if "429" in str(e) or "rate limit" in error_str or "too many requests" in error_str:
                    if attempt < max_attempts - 1:
                        wait_time = (attempt + 1) * 10  # 10초, 20초 대기
                        print(f"⚠️  Rate Limit 에러. {wait_time}초 후 재시도합니다...")
                        time.sleep(wait_time)
                    else:
                        raise Exception("Rate Limit 에러가 계속 발생합니다. 잠시 후 다시 시도해주세요.")
                else:
                    raise


def main():
    """메인 실행 함수"""
    print("=" * 50)
    print("PDF 기반 RAG 챗봇")
    print("=" * 50)
    
    # 챗봇 초기화
    chatbot = RAGChatbot(pdf_directory="pdfs")
    
    print("\n챗봇이 준비되었습니다! 질문을 입력하세요.")
    print("종료하려면 'quit', 'exit', 또는 'q'를 입력하세요.\n")
    
    # 대화 루프
    while True:
        question = input("질문: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q', '종료']:
            print("챗봇을 종료합니다.")
            break
        
        if not question:
            continue
        
        try:
            answer = chatbot.query(question)
            print(f"\n답변: {answer}\n")
        except Exception as e:
            print(f"오류 발생: {e}\n")


if __name__ == "__main__":
    main()

