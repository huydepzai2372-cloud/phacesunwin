import crypto from "crypto";
import { promises as fs } from "fs";
import path from "path";

export type StoredUser = {
  id: string;
  name: string;
  email: string;
  passwordHash?: string;
  image?: string;
  provider: "credentials" | "google";
  emailVerified: boolean;
  createdAt: string;
};

export type PendingOTP = {
  email: string;
  name: string;
  passwordHash: string;
  otp: string;
  expiresAt: number;
  createdAt: number;
};

const DATA_DIR = path.join(process.cwd(), "data");
const USERS_FILE = path.join(DATA_DIR, "users.json");
const OTP_FILE = path.join(DATA_DIR, "otp.json");

async function ensureFiles() {
  await fs.mkdir(DATA_DIR, { recursive: true });
  try {
    await fs.access(USERS_FILE);
  } catch {
    await fs.writeFile(USERS_FILE, "[]", "utf8");
  }
  try {
    await fs.access(OTP_FILE);
  } catch {
    await fs.writeFile(OTP_FILE, "[]", "utf8");
  }
}

export async function readUsers(): Promise<StoredUser[]> {
  await ensureFiles();
  const raw = await fs.readFile(USERS_FILE, "utf8");
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export async function writeUsers(users: StoredUser[]) {
  await ensureFiles();
  await fs.writeFile(USERS_FILE, JSON.stringify(users, null, 2), "utf8");
}

export async function readPendingOTP(): Promise<PendingOTP[]> {
  await ensureFiles();
  const raw = await fs.readFile(OTP_FILE, "utf8");
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export async function writePendingOTP(items: PendingOTP[]) {
  await ensureFiles();
  await fs.writeFile(OTP_FILE, JSON.stringify(items, null, 2), "utf8");
}

export function hashPassword(value: string) {
  return crypto.createHash("sha256").update(value.trim()).digest("hex");
}

export async function findUserByEmail(email: string) {
  const users = await readUsers();
  return users.find((user) => user.email.toLowerCase() === email.toLowerCase()) ?? null;
}

export async function createUser(user: StoredUser) {
  const users = await readUsers();
  const nextUsers = [...users.filter((item) => item.email.toLowerCase() !== user.email.toLowerCase()), user];
  await writeUsers(nextUsers);
  return user;
}

export async function saveOTP(item: PendingOTP) {
  const items = await readPendingOTP();
  const next = items.filter((entry) => entry.email.toLowerCase() !== item.email.toLowerCase());
  next.push(item);
  await writePendingOTP(next);
  return item;
}

export async function getOTPForEmail(email: string) {
  const items = await readPendingOTP();
  const match = items.find((item) => item.email.toLowerCase() === email.toLowerCase());
  if (!match) return null;
  if (Date.now() > match.expiresAt) {
    const remaining = items.filter((item) => item.email.toLowerCase() !== email.toLowerCase());
    await writePendingOTP(remaining);
    return null;
  }
  return match;
}

export async function removeOTPForEmail(email: string) {
  const items = await readPendingOTP();
  await writePendingOTP(items.filter((item) => item.email.toLowerCase() !== email.toLowerCase()));
}
