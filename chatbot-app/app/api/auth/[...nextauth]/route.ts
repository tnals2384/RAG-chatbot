import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  callbacks: {
    async signIn({ user, account, profile }) {
      // 로그인 성공 시 회원정보 저장 API 호출 및 데이터베이스 users.id 가져오기
      if (account?.provider === "google" && user.email) {
        try {
          const response = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/users`,
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                email: user.email,
                name: user.name || "",
                image: user.image || "",
                provider: "google",
                provider_id: account.providerAccountId,
              }),
            }
          );

          if (response.ok) {
            const data = await response.json();
            // 데이터베이스에서 반환된 users.id를 user 객체에 저장
            if (data.user && data.user.id) {
              user.id = String(data.user.id); // JWT 토큰에 저장하기 위해 문자열로 변환
            }
          } else {
            console.error("회원정보 저장 실패:", await response.text());
          }
        } catch (error) {
          console.error("회원정보 저장 중 오류:", error);
        }
      }
      return true;
    },
    async session({ session, token }) {
      // JWT 토큰에 저장된 데이터베이스 users.id를 세션에 포함
      if (session.user && token.dbUserId) {
        session.user.id = String(token.dbUserId);
      }
      return session;
    },
    async jwt({ token, user, account }) {
      // signIn 콜백에서 설정한 user.id를 JWT 토큰에 저장
      if (user?.id) {
        token.dbUserId = parseInt(user.id, 10); // 숫자로 저장
      }
      return token;
    },
  },
  pages: { // 인증이 필요한 페이지에 접근할 때, 에러가 발생했을 때 해당 경로로 이동
    signIn: "/", 
  },
});

export const { GET, POST } = handlers;
