"""
LlamaIndex + ChromaDB + Ollama를 활용한 PDF 기반 RAG 챗봇
"""
import os
from pathlib import Path
from dotenv import load_dotenv

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
import chromadb

# 환경 변수 로드
load_dotenv()

class RAGChatbot:
    def __init__(self, pdf_directory: str = "pdfs", persist_dir: str = "./chroma_db", model_name: str = "qwen2.5:1.5b"):
        """
        RAG 챗봇 초기화 (Ollama 사용)
        
        Args:
            pdf_directory: PDF 파일이 있는 디렉토리 경로
            persist_dir: ChromaDB 데이터를 저장할 디렉토리 경로
            model_name: 사용할 Ollama 모델 이름
        """
        # Ollama 서버 확인
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        print("Ollama LLM 모델을 로드하는 중입니다...")
        print(f"Ollama 서버가 {ollama_base_url}에서 실행 중이어야 합니다.")
        print(f"사용할 모델: {model_name}")
        print(f"모델이 없으면 다음 명령어로 다운로드하세요: ollama pull {model_name}")
        
        # LLM 설정 (Ollama 사용)
        try:
            self.llm = Ollama(
                model=model_name,
                base_url=ollama_base_url,
                temperature=0.8,  # 더 창의적이고 자세한 답변을 위해 증가 (0.7 -> 0.8)
                request_timeout=120.0
            )
            print(" Ollama LLM 모델 로드 완료!")
        except Exception as e:
            print(f" Ollama LLM 모델 로드 실패: {e}")
            print(f"\n 해결 방법:")
            print(f"   1. Ollama가 설치되어 있는지 확인: https://ollama.ai")
            print(f"   2. Ollama 서버 실행 확인: ollama serve")
            print(f"   3. 모델 다운로드 확인: ollama pull {model_name}")
            print(f"   4. 서버 URL 확인: {ollama_base_url}")
            raise
        
        # Embedding 모델 설정 (로컬 Hugging Face 모델 사용 - 무료)
        # 첫 실행 시 모델을 다운로드하므로 시간이 걸릴 수 있습니다
        print("Embedding 모델을 로드하는 중입니다... (첫 실행 시 다운로드가 필요합니다)")
        self.embed_model = HuggingFaceEmbedding(
            model_name="jhgan/ko-sroberta-multitask",  # 한국어 지원 embedding 모델
            device="cpu"  # GPU가 있으면 "cuda"로 변경 가능
        )
        
        # Settings에 LLM과 Embedding 모델 설정
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model
        
        # 청크 크기 설정 (한국어 텍스트에 맞게 조정)
        # 512로 줄여서 더 세밀하게 분할하고, 문장 단위로 분할하도록 개선
        Settings.chunk_size = 512
        Settings.chunk_overlap = 50
        
        # 문장 단위 분할기 사용 (한국어 문장 경계를 더 잘 인식)
        Settings.node_parser = SentenceSplitter(
            chunk_size=512,
            chunk_overlap=50,
            separator="\n\n"  # 문단 단위로 먼저 분할
        )
        
        # ChromaDB 클라이언트 초기화
        self.persist_dir = persist_dir
        self.chroma_client = chromadb.PersistentClient(path=persist_dir)
        
        # 벡터 스토어 및 인덱스 초기화
        self.index = None
        self._initialize_index(pdf_directory)
    
    def _initialize_index(self, pdf_directory: str):
        """
        벡터 인덱스 초기화 및 DB 저장
        - 서버 시작 시 pdfs 디렉토리의 모든 PDF를 자동으로 처리
        - PDF 읽기 → 텍스트 추출 → 청크 분할 → 벡터 변환 → ChromaDB 저장
        """
        collection_name = "pdf_documents"
        
        # 기존 컬렉션이 있으면 삭제하고 새로 생성 (항상 최신 PDF 반영)
        try:
            # 기존 컬렉션 삭제 (항상 최신 PDF 반영을 위해)
            try:
                self.chroma_client.delete_collection(name=collection_name)
                print(f"기존 ChromaDB 컬렉션 '{collection_name}'를 삭제했습니다.")
            except Exception:
                pass  # 컬렉션이 없어도 오류 무시
            
            # pdfs 디렉토리의 모든 PDF를 처리하여 벡터 인덱스 생성 및 DB 저장
            print("pdfs 디렉토리의 모든 PDF 파일을 처리하여 벡터 인덱스를 생성하고 ChromaDB에 저장합니다...")
            self._create_index(pdf_directory, collection_name)
        except Exception as e:
            print(f"인덱스 생성 중 오류 발생: {e}")
            print("새 인덱스를 생성합니다...")
            self._create_index(pdf_directory, collection_name)
    
    def _create_index(self, pdf_directory: str, collection_name: str):
        """
        PDF 파일에서 벡터 인덱스 생성 및 ChromaDB 저장
        - PDF 읽기 → 텍스트 추출 → 청크 분할 → 벡터 변환 → DB 저장
        """
        pdf_path = Path(pdf_directory)
        
        if not pdf_path.exists():
            print(f"경고: {pdf_directory} 디렉토리가 존재하지 않습니다.")
            print("빈 인덱스를 생성합니다. PDF 파일을 추가하려면 ingest_pdfs() 메서드를 사용하세요.")
            chroma_collection = self.chroma_client.get_or_create_collection(
                name=collection_name
            )
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store
            )
            self.index = VectorStoreIndex([], storage_context=storage_context)
            return
        
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
        # SimpleDirectoryReader().load_data()는:
        # - pdfs 디렉토리의 모든 PDF 파일을 읽음
        # - 각 PDF 파일을 텍스트로 변환
        # - Document 객체 리스트를 반환 (각 Document = 하나의 PDF 파일 또는 페이지)
        # - 아직 청크 분할은 안 됨 (전체 문서 단위)
        # - 청크 분할은 나중에 VectorStoreIndex.from_documents()에서 수행됨
        documents = SimpleDirectoryReader(
            input_dir=pdf_directory,
            required_exts=[".pdf"]
        ).load_data()
        
        # documents는 Document 객체들의 리스트
        # 예: [Document(text="PDF1 전체 내용..."), Document(text="PDF2 전체 내용..."), ...]
        # 각 Document 객체는 다음 속성을 가짐:
        # - text: PDF에서 추출한 텍스트 내용
        # - metadata: 파일명, 페이지 번호 등 메타데이터
        print(f"{len(documents)}개의 문서를 로드했습니다. (PDF 파일 수: {len(pdf_files)})")
        
        # ChromaDB 벡터 스토어 생성
        chroma_collection = self.chroma_client.get_or_create_collection(
            name=collection_name
        )
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store
        )
        
        # 벡터 인덱스 생성 및 ChromaDB 저장
        # VectorStoreIndex.from_documents()가 수행하는 작업:
        # 1. 문서를 청크로 분할 (chunk_size=1024)
        # 2. 각 청크를 벡터로 변환 (Embedding)
        # 3. 벡터 인덱스를 생성하고 ChromaDB에 저장
        # "인덱스"는 빠른 검색을 위한 데이터 구조를 의미합니다
        print("벡터 인덱스를 생성하고 ChromaDB에 저장하는 중입니다...")
        print("  (문서 분할 → 임베딩 생성 → DB 저장을 한꺼번에 수행)")
        print("  Embedding 모델이 로컬에서 실행되므로 시간이 걸릴 수 있습니다.")
        self.index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            show_progress=True
        )
        
        print(" 벡터 인덱스 생성 및 DB 저장이 완료되었습니다!")
    
    def ingest_pdfs(self, pdf_directory: str):
        """추가 PDF 파일을 인덱스에 추가"""
        pdf_path = Path(pdf_directory)
        
        if not pdf_path.exists():
            raise ValueError(f"{pdf_directory} 디렉토리가 존재하지 않습니다.")
        
        pdf_files = list(pdf_path.glob("*.pdf"))
        if not pdf_files:
            raise ValueError(f"{pdf_directory} 디렉토리에 PDF 파일이 없습니다.")
        
        print(f"{len(pdf_files)}개의 PDF 파일을 발견했습니다.")
        
        documents = SimpleDirectoryReader(
            input_dir=pdf_directory,
            required_exts=[".pdf"]
        ).load_data()
        
        print(f"{len(documents)}개의 문서 청크를 로드했습니다.")
        
        print("문서를 인덱스에 추가하는 중입니다...")
        for doc in documents:
            self.index.insert(doc)
        
        print("문서 추가가 완료되었습니다!")
    
    def query(self, question: str, similarity_top_k: int = 10):
        """
        질문에 대한 답변 생성
        
        Args:
            question: 사용자 질문
            similarity_top_k: 유사한 문서를 몇 개까지 검색할지 (기본값 10으로 증가)
        
        Returns:
            답변 문자열
        """
        if self.index is None:
            raise ValueError("인덱스가 초기화되지 않았습니다.")
        
        # 더 많은 컨텍스트를 제공하기 위해 similarity_top_k 증가
        query_engine = self.index.as_query_engine(
            similarity_top_k=similarity_top_k,
            response_mode="tree_summarize"  # compact -> tree_summarize로 변경 (더 나은 요약)
        )
        
        print("질문을 처리하는 중입니다...")
        try:
            response = query_engine.query(question)
            return str(response)
        except Exception as e:
            error_msg = f"질문 처리 중 오류 발생: {e}"
            if "connection" in str(e).lower() or "refused" in str(e).lower():
                error_msg += "\n Ollama 서버가 실행 중인지 확인하세요."
            raise Exception(error_msg) from e
    
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
        
        # 커스텀 시스템 프롬프트 (자세한 답변 유도)
        custom_prompt = (
            "당신은 친절하고 자세하게 답변하는 어시스턴트입니다.\n"
            "답변할 때 다음을 지켜주세요:\n"
            "1. 제공된 문서의 정보를 바탕으로 자세하고 친절하게 설명하세요.\n"
            "2. 가능한 한 구체적이고 실용적인 정보를 포함하세요.\n"
            "3. 단계별 설명이 필요한 경우 명확하게 나누어 설명하세요.\n"
            "4. 관련 정보가 없는 경우에만 \"죄송합니다. 해당 정보를 찾을 수 없습니다. 다른 질문을 해주시면 도와드리겠습니다.\"라고 답변하세요.\n"
        )
        
        chat_engine = self.index.as_chat_engine(
            chat_mode="context",
            similarity_top_k=12,  # 7 -> 12로 증가 (더 많은 컨텍스트)
            verbose=True,
            system_prompt=custom_prompt
        )
        
        print("질문을 처리하는 중입니다...")
        try:
            # 유사한 문서 검색하여 관련 정보 존재 여부 확인
            retriever = self.index.as_retriever(similarity_top_k=12)  # 5 -> 12로 증가
            nodes = retriever.retrieve(question)
            
            # 관련 문서가 없는 경우
            if not nodes or len(nodes) == 0:
                return "죄송합니다. 해당 정보를 찾을 수 없습니다. 다른 질문을 해주시면 도와드리겠습니다."
            
            
            # 정상적인 답변 생성
            response = chat_engine.chat(question)
            response_text = str(response)
            
            # 응답이 너무 짧거나 의미 없는 경우 재확인
            if len(response_text.strip()) < 10:
                return "죄송합니다. 해당 정보를 찾을 수 없습니다. 다른 질문을 해주시면 도와드리겠습니다."
            
            return response_text
        except Exception as e:
            error_msg = f"채팅 처리 중 오류 발생: {e}"
            if "connection" in str(e).lower() or "refused" in str(e).lower():
                error_msg += "\n Ollama 서버가 실행 중인지 확인하세요."
            raise Exception(error_msg) from e


def main():
    """메인 실행 함수"""
    print("=" * 50)
    print("PDF 기반 RAG 챗봇 (Ollama 사용)")
    print("=" * 50)
    print("\n  사전 준비:")
    print("   1. Ollama 설치: https://ollama.ai")
    print("   2. Ollama 서버 실행 (자동으로 시작됨)")
    print("   3. 모델 다운로드: ollama pull qwen2.5:1.5b")
    print("=" * 50)
    
    # 사용할 모델 선택 (환경 변수에서 가져오거나 기본값 사용)
    # 빠른 응답을 위한 작은 모델: qwen2.5:1.5b (약 1.5B 파라미터, 매우 빠름)
    model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
    
    try:
        chatbot = RAGChatbot(pdf_directory="pdfs", model_name=model_name)
        
        print("\n챗봇이 준비되었습니다! 질문을 입력하세요.")
        print("종료하려면 'quit', 'exit', 또는 'q'를 입력하세요.\n")
        
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
                if "connection" in str(e).lower() or "refused" in str(e).lower():
                    print(" Ollama 서버가 실행 중인지 확인하세요: ollama serve")
    except Exception as e:
        print(f"\n 초기화 실패: {e}")
        print("\n 해결 방법:")
        print("   1. Ollama가 설치되어 있는지 확인: https://ollama.ai")
        print("   2. Ollama 서버가 실행 중인지 확인")
        print("   3. 모델이 다운로드되어 있는지 확인: ollama list")


if __name__ == "__main__":
    main()

