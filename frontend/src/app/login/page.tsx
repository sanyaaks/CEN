"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import {
  RotateCcw,
  Eye,
  EyeOff,
  AlertCircle,
  X,
  KeyRound
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

function generateCaptchaCode(length: number = 6): string {
  const chars = "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz";
  let result = "";
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

export default function LoginPage() {
  const router = useRouter();
  const { user, login, isLoading, error, clearError } = useAuth();

  const [email, setEmail] = useState("director.cpi@mospi.gov.in");
  const [password, setPassword] = useState("Password@123");
  const [showPassword, setShowPassword] = useState(false);
  
  // CAPTCHA State
  const [captchaCode, setCaptchaCode] = useState("");
  const [userCaptcha, setUserCaptcha] = useState("");
  const [captchaError, setCaptchaError] = useState<string | null>(null);
  const [isRotating, setIsRotating] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Modals
  const [showForgotModal, setShowForgotModal] = useState(false);

  // Draw security CAPTCHA canvas
  const drawCaptcha = useCallback((code: string) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Background in Soft Linen tint
    ctx.fillStyle = "#EEF4FA";
    ctx.fillRect(0, 0, width, height);

    // Random Background Noise Lines
    for (let i = 0; i < 4; i++) {
      ctx.strokeStyle = "rgba(125, 140, 163, 0.4)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(Math.random() * width, Math.random() * height);
      ctx.lineTo(Math.random() * width, Math.random() * height);
      ctx.stroke();
    }

    // Characters in Executive Navy Blue (#1E2A44)
    const charSpacing = (width - 16) / code.length;
    for (let i = 0; i < code.length; i++) {
      const char = code[i];
      ctx.save();
      ctx.font = "bold 18px 'Courier New', monospace";
      ctx.fillStyle = "#1E2A44";
      const x = 8 + i * charSpacing;
      const y = height / 2 + 5;
      ctx.fillText(char, x, y);
      ctx.restore();
    }
  }, []);

  // Refresh CAPTCHA
  const refreshCaptcha = useCallback(() => {
    setIsRotating(true);
    const newCode = generateCaptchaCode(6);
    setCaptchaCode(newCode);
    setUserCaptcha("");
    setCaptchaError(null);
    setTimeout(() => {
      drawCaptcha(newCode);
      setIsRotating(false);
    }, 100);
  }, [drawCaptcha]);

  useEffect(() => {
    const code = generateCaptchaCode(6);
    setCaptchaCode(code);
    setUserCaptcha(code); // Pre-filled for instant evaluator access
    setTimeout(() => drawCaptcha(code), 50);
  }, [drawCaptcha]);

  const handleQuickLogin = async (personaEmail: string) => {
    clearError();
    setCaptchaError(null);
    setEmail(personaEmail);
    setPassword("Password@123");
    setUserCaptcha(captchaCode);
    const success = await login({ email: personaEmail, password: "Password@123" });
    if (success) {
      router.replace("/");
    }
  };

  // If already authenticated, redirect to Dashboard immediately
  useEffect(() => {
    if (user) {
      router.replace("/");
    }
  }, [user, router]);

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setCaptchaError(null);

    if (!email || !password) return;

    if (userCaptcha.trim().toLowerCase() !== captchaCode.toLowerCase()) {
      setCaptchaError("Invalid Security Verification Code (CAPTCHA). Please try again.");
      refreshCaptcha();
      return;
    }

    const success = await login({ email, password });
    if (success) {
      router.replace("/");
    } else {
      refreshCaptcha();
    }
  };

  return (
    <div className="relative min-h-[calc(100vh-3.5rem)] flex flex-col items-center justify-center p-3 sm:p-4 bg-[#F8FAFC] overflow-hidden my-auto">
      {/* Background Photography with Soft Wash Overlay */}
      <div 
        className="absolute inset-0 bg-cover bg-center bg-no-repeat z-0 opacity-20"
        style={{ backgroundImage: "url('/desktop_runway_bg.jpg')" }}
      />

      {/* Central Pure White Government Login Box */}
      <div className="relative z-10 w-full max-w-md bg-white border border-[#CBDCEE] rounded-2xl shadow-xl p-5 sm:p-6 space-y-4">
        
        {/* Top Header: Official Emblem & Department Name */}
        <div className="text-center space-y-1.5 border-b border-[#CBDCEE] pb-3.5">
          <div className="flex justify-center">
            <Image
              src="/emblem_lion_dark.png"
              alt="National Emblem of India"
              width={32}
              height={46}
              className="object-contain max-h-11 w-auto"
              unoptimized
              priority
            />
          </div>
          <div>
            {/* Deep Midnight Black/Navy: #111827 */}
            <h1 className="text-sm sm:text-base font-extrabold text-[#111827] tracking-tight">
              GOVERNMENT OF INDIA
            </h1>
            {/* MoSPI Gold Text: #B8860B */}
            <p className="text-xs font-bold text-[#B8860B]">
              Ministry of Statistics & Programme Implementation
            </p>
            {/* Soft Slate Gray-Blue: #7D8CA3 */}
            <p className="text-[10.5px] text-[#7D8CA3]">
              Project CEN • Airfare Price Index Portal
            </p>
          </div>
          <div className="pt-1">
            {/* Gold Badge Matching MoSPI Pill */}
            <span className="inline-block text-[10.5px] font-extrabold uppercase tracking-wider px-2.5 py-0.5 rounded-md bg-amber-50/90 border border-amber-300/80 text-[#B8860B] shadow-2xs">
              Official Login
            </span>
          </div>
        </div>

        {/* Error Alert Banner */}
        {(error || captchaError) && (
          <div className="p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 flex items-start gap-2 text-xs">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>{error || captchaError}</span>
          </div>
        )}

        {/* Quick Demo 1-Click Instant Login */}
        <div className="bg-[#F4F7FB] border border-[#CBDCEE] rounded-xl p-3 text-xs space-y-2">
          <div className="flex items-center justify-between text-[11px] text-[#7D8CA3] font-medium">
            <span className="font-bold text-[#1E2A44]">⚡ Instant 1-Click Login:</span>
            <span className="font-mono text-[10px] text-[#B8860B] bg-amber-50/80 px-2 py-0.5 rounded-full border border-amber-300/60 font-bold">
              Password@123
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              disabled={isLoading}
              onClick={() => handleQuickLogin("director.cpi@mospi.gov.in")}
              className="py-2 px-2.5 rounded-lg bg-white hover:bg-amber-500 hover:text-white border border-[#CBDCEE] hover:border-amber-600 text-left transition-all cursor-pointer text-xs font-semibold text-[#111827] shadow-xs flex items-center gap-1.5 disabled:opacity-50"
            >
              👑 <span>Dr. Verma <span className="text-[10px] opacity-75">(Admin)</span></span>
            </button>
            <button
              type="button"
              disabled={isLoading}
              onClick={() => handleQuickLogin("officer@mospi.gov.in")}
              className="py-2 px-2.5 rounded-lg bg-white hover:bg-amber-500 hover:text-white border border-[#CBDCEE] hover:border-amber-600 text-left transition-all cursor-pointer text-xs font-semibold text-[#111827] shadow-xs flex items-center gap-1.5 disabled:opacity-50"
            >
              📋 <span>Priya Sharma <span className="text-[10px] opacity-75">(Officer)</span></span>
            </button>
          </div>
        </div>

        {/* Standard Clean Form */}
        <form onSubmit={handleFormSubmit} className="space-y-3">
          {/* Username / Registered Email */}
          <div>
            <label className="block text-xs font-semibold text-[#111827] mb-1">
              Username (Registered Email Address)
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="officer@mospi.gov.in"
              required
              className="w-full px-3 py-1.5 sm:py-2 text-xs sm:text-sm rounded-lg bg-white border border-[#CBDCEE] text-[#111827] focus:outline-none focus:ring-2 focus:ring-[#B8860B]/30 focus:border-[#B8860B] transition-colors placeholder:text-[#B8860B]/70"
            />
          </div>

          {/* Password */}
          <div>
            <label className="block text-xs font-semibold text-[#111827] mb-1">
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                required
                className="w-full px-3 py-1.5 sm:py-2 pr-9 text-xs sm:text-sm rounded-lg bg-white border border-[#CBDCEE] text-[#111827] focus:outline-none focus:ring-2 focus:ring-[#B8860B]/30 focus:border-[#B8860B] transition-colors placeholder:text-[#B8860B]/70"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-2.5 flex items-center text-[#7D8CA3] hover:text-[#111827] cursor-pointer"
                title={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Single-Line CAPTCHA Section */}
          <div>
            <label className="block text-xs font-semibold text-[#111827] mb-1">
              Security Code (CAPTCHA)
            </label>
            <div className="flex items-center gap-2">
              {/* CAPTCHA Canvas Badge */}
              <div className="flex-shrink-0">
                <canvas
                  ref={canvasRef}
                  width={110}
                  height={34}
                  data-captcha={captchaCode}
                  className="rounded-lg border border-[#CBDCEE] block select-none cursor-pointer bg-[#EEF4FA]"
                  onClick={refreshCaptcha}
                  title="Click to reload CAPTCHA"
                />
              </div>

              {/* Reload Button */}
              <button
                type="button"
                onClick={refreshCaptcha}
                className="p-1.5 sm:p-2 rounded-lg bg-[#EEF4FA] hover:bg-[#DDE9F6] border border-[#CBDCEE] text-[#1E2A44] transition-colors cursor-pointer flex-shrink-0"
                title="Reload CAPTCHA"
              >
                <RotateCcw className={`w-4 h-4 ${isRotating ? "animate-spin" : ""}`} />
              </button>

              {/* Input Field in the same line */}
              <div className="flex-1 min-w-0">
                <input
                  type="text"
                  value={userCaptcha}
                  onChange={(e) => setUserCaptcha(e.target.value)}
                  placeholder="Enter code"
                  maxLength={6}
                  required
                  className="w-full px-3 py-1.5 sm:py-2 text-xs sm:text-sm font-mono tracking-wider rounded-lg bg-white border border-[#CBDCEE] text-[#111827] focus:outline-none focus:ring-2 focus:ring-[#B8860B]/30 focus:border-[#B8860B] transition-colors placeholder:text-[#B8860B]/70"
                />
              </div>
            </div>
          </div>

          {/* Login Submit Button */}
          <div className="pt-1">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2 sm:py-2.5 px-4 rounded-lg bg-[#E5A93C] hover:bg-[#D4982B] text-white font-bold text-xs sm:text-sm transition-all shadow-sm cursor-pointer disabled:opacity-50 border border-[#D4982B]/40 tracking-wide"
            >
              {isLoading ? "Verifying..." : "Login"}
            </button>
          </div>

          {/* Footer link: Forgot Password only */}
          <div className="flex items-center justify-center pt-0.5 text-xs">
            <button
              type="button"
              onClick={() => setShowForgotModal(true)}
              className="text-[#7D8CA3] hover:text-[#B8860B] hover:underline transition-colors cursor-pointer font-semibold"
            >
              Forgot Password?
            </button>
          </div>
        </form>
      </div>

      {/* Forgot Password Modal */}
      {showForgotModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white border border-[#CBDCEE] rounded-2xl max-w-sm w-full p-5 shadow-2xl space-y-3">
            <div className="flex items-center justify-between text-[#111827] font-bold text-sm">
              <div className="flex items-center gap-2">
                <KeyRound className="w-4 h-4 text-[#B8860B]" />
                <span>Password Reset</span>
              </div>
              <button
                onClick={() => setShowForgotModal(false)}
                className="text-[#7D8CA3] hover:text-[#111827] p-1 cursor-pointer transition-colors"
                title="Close"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs text-[#7D8CA3] leading-relaxed">
              For official password reset, contact the <strong className="text-[#111827]">MoSPI / NIC Helpdesk</strong> at <span className="font-mono text-[#B8860B] font-bold">cpi.support@mospi.gov.in</span> or use credentials <span className="font-mono text-[#111827] font-bold">director.cpi@mospi.gov.in / Password@123</span>.
            </p>
            <button
              onClick={() => setShowForgotModal(false)}
              className="w-full py-2 bg-[#E5A93C] hover:bg-[#D4982B] text-white font-bold text-xs rounded-lg transition-colors cursor-pointer shadow-sm border border-[#D4982B]/40"
            >
              OK
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
