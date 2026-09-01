"use client";

import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function HomePage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleGoogle = async () => {
    await signIn("google", { callbackUrl: "/dashboard" });
  };

  const handleSendOTP = async () => {
    setLoading(true);
    setMessage("");

    const res = await fetch("/api/auth/send-otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password }),
    });

    const data = await res.json();
    setLoading(false);

    if (!res.ok) {
      setMessage(data.error || "Không thể gửi mã xác nhận");
      return;
    }

    setOtpSent(true);
    setMessage("Mã xác nhận đã được gửi tới email của bạn.");
  };

  const handleVerifyAndCreate = async () => {
    if (!otp.trim()) {
      setMessage("Vui lòng nhập mã xác nhận");
      return;
    }

    setLoading(true);
    setMessage("");

    const res = await fetch("/api/auth/verify-otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, otp }),
    });

    const data = await res.json();
    setLoading(false);

    if (!res.ok) {
      setMessage(data.error || "Xác nhận thất bại");
      return;
    }

    setMessage("Đăng ký thành công. Hãy đăng nhập.");
    setMode("login");
    setOtpSent(false);
    setOtp("");
  };

  const handleCredentialsLogin = async () => {
    setLoading(true);
    setMessage("");

    const res = await signIn("credentials", {
      email,
      password,
      redirect: false,
    });

    setLoading(false);

    if (res?.error) {
      setMessage("Email hoặc mật khẩu không đúng");
      return;
    }

    router.push("/dashboard");
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top,_#1e293b,_#020617_60%)] px-4">
      <div className="w-full max-w-md rounded-3xl border border-white/10 bg-slate-900/80 p-8 shadow-2xl backdrop-blur-xl">
        <div className="mb-6 flex gap-2 rounded-full bg-slate-800 p-1">
          <button
            type="button"
            onClick={() => setMode("login")}
            className={`flex-1 rounded-full px-4 py-2 font-medium ${mode === "login" ? "bg-amber-400 text-slate-950" : "text-slate-300"}`}
          >
            Đăng nhập
          </button>
          <button
            type="button"
            onClick={() => setMode("signup")}
            className={`flex-1 rounded-full px-4 py-2 font-medium ${mode === "signup" ? "bg-amber-400 text-slate-950" : "text-slate-300"}`}
          >
            Đăng ký
          </button>
        </div>

        <h1 className="mb-6 text-3xl font-bold text-white">Sòng bạc online</h1>

        {mode === "signup" && (
          <div className="space-y-3">
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Tên của bạn" className="w-full rounded-xl border border-white/10 bg-slate-800 px-4 py-3 text-white outline-none" />
            <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" type="email" className="w-full rounded-xl border border-white/10 bg-slate-800 px-4 py-3 text-white outline-none" />
            <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Mật khẩu" type="password" className="w-full rounded-xl border border-white/10 bg-slate-800 px-4 py-3 text-white outline-none" />

            {!otpSent ? (
              <button type="button" onClick={handleSendOTP} disabled={loading} className="w-full rounded-xl bg-amber-400 px-4 py-3 font-semibold text-slate-950 disabled:opacity-50">
                {loading ? "Đang gửi..." : "Gửi mã xác nhận"}
              </button>
            ) : (
              <>
                <input value={otp} onChange={(e) => setOtp(e.target.value)} placeholder="Nhập mã xác nhận" className="w-full rounded-xl border border-white/10 bg-slate-800 px-4 py-3 text-white outline-none" />
                <button type="button" onClick={handleVerifyAndCreate} disabled={loading} className="w-full rounded-xl bg-emerald-400 px-4 py-3 font-semibold text-slate-950 disabled:opacity-50">
                  {loading ? "Đang xác nhận..." : "Xác nhận & tạo tài khoản"}
                </button>
              </>
            )}
          </div>
        )}

        {mode === "login" && (
          <div className="space-y-3">
            <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" type="email" className="w-full rounded-xl border border-white/10 bg-slate-800 px-4 py-3 text-white outline-none" />
            <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Mật khẩu" type="password" className="w-full rounded-xl border border-white/10 bg-slate-800 px-4 py-3 text-white outline-none" />
            <button type="button" onClick={handleCredentialsLogin} disabled={loading} className="w-full rounded-xl bg-amber-400 px-4 py-3 font-semibold text-slate-950 disabled:opacity-50">
              {loading ? "Đang đăng nhập..." : "Đăng nhập"}
            </button>
          </div>
        )}

        <div className="my-4 border-t border-white/10" />

        <button
          type="button"
          onClick={handleGoogle}
          className="flex w-full items-center justify-center gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-3 font-medium text-white hover:bg-white/10"
        >
          Tiếp tục với Google
        </button>

        {message && <p className="mt-4 text-sm text-amber-300">{message}</p>}
      </div>
    </main>
  );
}
