import crypto from "crypto";
import { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import GoogleProvider from "next-auth/providers/google";
import { createUser, findUserByEmail, hashPassword } from "@/lib/store";

export const authOptions: NextAuthOptions = {
  secret: process.env.NEXTAUTH_SECRET,
  session: {
    strategy: "jwt",
  },
  pages: {
    signIn: "/",
  },
  providers: [
    ...(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET
      ? [
          GoogleProvider({
            clientId: process.env.GOOGLE_CLIENT_ID,
            clientSecret: process.env.GOOGLE_CLIENT_SECRET,
          }),
        ]
      : []),
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        const user = await findUserByEmail(String(credentials.email));
        if (!user || !user.passwordHash) {
          return null;
        }

        if (user.passwordHash !== hashPassword(String(credentials.password))) {
          return null;
        }

        return {
          id: user.id,
          email: user.email,
          name: user.name,
          image: user.image,
        };
      },
    }),
  ],
  callbacks: {
    async signIn({ user, account }) {
      if (account?.provider === "google" && user.email) {
        const existing = await findUserByEmail(user.email);
        if (!existing) {
          await createUser({
            id: crypto.randomUUID(),
            name: user.name || user.email.split("@")[0],
            email: user.email,
            provider: "google",
            emailVerified: true,
            createdAt: new Date().toISOString(),
          });
        }
      }
      return true;
    },
    async jwt({ token, user }) {
      if (user && "id" in user) {
        token.userId = user.id;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        const dynamicSession = session as typeof session & { user: { id?: string } };
        dynamicSession.user.id = String(token.userId ?? session.user.email ?? "guest");
      }
      return session;
    },
  },
};
