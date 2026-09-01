import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import { signOut } from "next-auth/react";

import { authOptions } from "@/lib/auth";

export default async function DashboardPage() {
  const session = await getServerSession(authOptions);

  if (!session?.user) {
    redirect("/");
  }

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-12 text-white">
      <div className="mx-auto max-w-5xl rounded-2xl border border-white/10 bg-slate-900 p-8 shadow-2xl">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-[0.2em] text-amber-300">Game hub</p>
            <h1 className="mt-2 text-3xl font-bold">Xin chào, {session.user.name || "Người chơi"}</h1>
          </div>
          <button
            type="button"
            onClick={() => signOut({ callbackUrl: "/" })}
            className="rounded-full border border-white/10 bg-white/5 px-5 py-2 text-sm font-medium hover:bg-white/10"
          >
            Đăng xuất
          </button>
        </div>

        <div className="mt-8 grid gap-5 md:grid-cols-3">
          <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-5">
            <p className="text-sm text-emerald-200">Tài khoản</p>
            <p className="mt-2 text-2xl font-semibold">{session.user.email}</p>
          </div>
          <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/10 p-5">
            <p className="text-sm text-cyan-200">Trạng thái</p>
            <p className="mt-2 text-2xl font-semibold">Đã đăng nhập</p>
          </div>
          <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 p-5">
            <p className="text-sm text-violet-200">Nền tảng</p>
            <p className="mt-2 text-2xl font-semibold">Next.js + Vercel</p>
          </div>
        </div>
      </div>
    </main>
  );
}
