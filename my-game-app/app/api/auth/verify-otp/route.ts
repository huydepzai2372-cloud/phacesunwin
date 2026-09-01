import crypto from "crypto";
import { NextRequest, NextResponse } from "next/server";
import { createUser, findUserByEmail, getOTPForEmail, removeOTPForEmail } from "@/lib/store";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const email = String(body.email || "").trim().toLowerCase();
  const otp = String(body.otp || "").trim();

  if (!email || !otp) {
    return NextResponse.json({ error: "Thiếu mã xác nhận" }, { status: 400 });
  }

  const pending = await getOTPForEmail(email);
  if (!pending) {
    return NextResponse.json({ error: "Mã xác nhận không hợp lệ hoặc đã hết hạn" }, { status: 400 });
  }

  if (pending.otp !== otp) {
    return NextResponse.json({ error: "Mã xác nhận sai" }, { status: 400 });
  }

  const existing = await findUserByEmail(email);
  if (existing) {
    await removeOTPForEmail(email);
    return NextResponse.json({ error: "Email đã tồn tại" }, { status: 409 });
  }

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
    name: pending.name,
    email,
    passwordHash: pending.passwordHash,
    provider: "credentials",
    emailVerified: true,
    createdAt: new Date().toISOString(),
  };

  await createUser(user);
  await removeOTPForEmail(email);

  return NextResponse.json({ ok: true, user: { id: user.id, email: user.email, name: user.name } });
}
