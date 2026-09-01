import nodemailer from "nodemailer";

export function generateOTP() {
  return Math.floor(100000 + Math.random() * 900000).toString();
}

export async function sendOTPEmail(email: string, name: string, otp: string) {
  const host = process.env.EMAIL_HOST || "smtp.gmail.com";
  const port = Number(process.env.EMAIL_PORT || 587);
  const user = process.env.EMAIL_USER;
  const pass = process.env.EMAIL_PASS;

  if (!user || !pass) {
    return {
      sent: false,
      reason: "EMAIL_USER and EMAIL_PASS are not configured",
    };
  }

  const transporter = nodemailer.createTransport({
    host,
    port,
    secure: false,
    auth: {
      user,
      pass,
    },
  });

  await transporter.sendMail({
    from: process.env.EMAIL_FROM || user,
    to: email,
    subject: "Xác nhận tài khoản game của bạn",
    html: `
      <div style="font-family: Arial, sans-serif; line-height: 1.6;">
        <h2>Xin chào ${name}</h2>
        <p>Mã xác nhận của bạn là:</p>
        <div style="font-size: 30px; font-weight: bold; letter-spacing: 4px; margin: 20px 0; color: #111827;">${otp}</div>
        <p>Mã này có hiệu lực trong 10 phút.</p>
      </div>
    `,
  });

  return { sent: true };
}
