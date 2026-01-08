# 헤이플 - RAG 챗봇 애플리케이션

PDF 기반 RAG(Retrieval-Augmented Generation) 챗봇 애플리케이션입니다.

## 주요 기능

- 📄 PDF 문서 기반 질의응답
- 🔐 Google 소셜 로그인 (NextAuth)
- 💬 채팅 기록 저장 및 불러오기
- 📱 반응형 디자인

## 설치 및 설정

### 1. 패키지 설치

```bash
npm install
npm install next-auth@beta
```

### 2. 환경 변수 설정

`.env.local` 파일을 생성하고 다음 환경 변수를 설정하세요:

```env
# NextAuth 설정
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key-here

# Google OAuth 설정
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Google OAuth 설정

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. "API 및 서비스" > "사용자 인증 정보"로 이동
4. "사용자 인증 정보 만들기" > "OAuth 클라이언트 ID" 선택
5. 애플리케이션 유형: "웹 애플리케이션"
6. 승인된 리디렉션 URI 추가: `http://localhost:3000/api/auth/callback/google`
7. 생성된 Client ID와 Client Secret을 `.env.local`에 설정

### 4. NEXTAUTH_SECRET 생성

다음 명령어로 시크릿 키를 생성할 수 있습니다:

```bash
openssl rand -base64 32
```

또는 온라인 생성기를 사용하세요: https://generate-secret.vercel.app/32

## 개발 서버 실행

```bash
npm run dev
```

브라우저에서 [http://localhost:3000](http://localhost:3000)을 열어 확인하세요.

## 백엔드 API 요구사항

이 애플리케이션은 다음 API 엔드포인트를 필요로 합니다:

### 사용자 관리
- `POST /api/users` - 회원정보 저장

### 채팅 관리
- `GET /api/chats?userId={userId}` - 채팅 목록 조회
- `GET /api/chats/{chatId}?userId={userId}` - 특정 채팅 조회
- `POST /api/chats` - 새 채팅 생성
- `PUT /api/chats` - 채팅 업데이트
- `DELETE /api/chats/{chatId}?userId={userId}` - 채팅 삭제

### RAG 챗봇
- `POST /api/chat` - 채팅 메시지 전송
- `DELETE /api/chat/session/{sessionId}` - 세션 초기화

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
