import crypto from "crypto";
import { NextRequest, NextResponse } from "next/server";
import { createUser, findUserByEmail, hashPassword, readUsers } from "@/lib/store";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const email = String(body.email || "").trim().toLowerCase();
  const name = String(body.name || "").trim();
  const password = String(body.password || "").trim();

  if (!email || !name || !password) {
    return NextResponse.json({ error: "Thiếu thông tin" }, { status: 400 });
  }

  if (password.length < 6) {
    return NextResponse.json({ error: "Mật khẩu tối thiểu 6 ký tự" }, { status: 400 });
  }

  const existing = await findUserByEmail(email);
  if (existing) {
    return NextResponse.json({ error: "Email đã tồn tại" }, { status: 409 });
  }

  const users = await readUsers();
  const user: {
    id: string;
    name: string;
    email: string;
    passwordHash: string;
    provider: "credentials" | "google";
    emailVerified: boolean;
    createdAt: string;
  } = {
    id: crypto.randomUUID(),
    name,
    email,
    passwordHash: hashPassword(password),
    provider: "credentials",
    emailVerified: false,
    createdAt: new Date().toISOString(),
  };

  users.push(user);
  await createUser(user);

  return NextResponse.json({ ok: true, user: { id: user.id, email: user.email, name: user.name } });
}
