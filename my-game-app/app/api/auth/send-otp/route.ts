import { NextRequest, NextResponse } from "next/server";
import { generateOTP, sendOTPEmail } from "@/lib/otp";
import { findUserByEmail, saveOTP } from "@/lib/store";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const email = String(body.email || "").trim().toLowerCase();
  const name = String(body.name || "").trim() || "Người chơi";
  const password = String(body.password || "").trim();

  if (!email || !name || !password) {
    return NextResponse.json({ error: "Thiếu thông tin" }, { status: 400 });
  }

  if (password.length < 6) {
    return NextResponse.json({ error: "Mật khẩu tối thiểu 6 ký tự" }, { status: 400 });
  }

  if (await findUserByEmail(email)) {
    return NextResponse.json({ error: "Email đã tồn tại" }, { status: 409 });
  }

  const otp = generateOTP();
  const result = await sendOTPEmail(email, name, otp);

  if (!result.sent) {
    return NextResponse.json({ error: result.reason || "Không thể gửi mã xác nhận" }, { status: 500 });
  }

  await saveOTP({
    email,
    name,
    passwordHash: require("crypto").createHash("sha256").update(password.trim()).digest("hex"),
    otp,
    expiresAt: Date.now() + 10 * 60 * 1000,
    createdAt: Date.now(),
  });

  return NextResponse.json({ ok: true, message: "Mã xác nhận đã gửi tới email" });
}
