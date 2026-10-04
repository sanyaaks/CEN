"use client";

import { useState, useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import {
  Menu,
  X,
  ChevronRight,
  ChevronDown,
  Download,
  Smartphone,
  Lock,
  LogOut,
} from "lucide-react";
import { usePwa } from "@/components/pwa/PwaProvider";
import { useAuth } from "@/context/AuthContext";
import GoogleTranslate from "@/components/common/GoogleTranslate";

const NAV_LINKS = [
  { name: "Dashboard", href: "/" },
  { name: "Routes", href: "/routes" },
  { name: "Booking Window", href: "/booking-window" },
  { name: "Airlines", href: "/airlines" },
  { name: "Data Quality", href: "/data-quality" },
  { name: "Validation", href: "/validation" },
  { name: "Audit", href: "/audit" },
  { name: "Collection", href: "/collection" },
];

export default function Navbar() {
  const pathname = usePathname();
  const isLoginPage = pathname === "/login";
  const { isInstallable, isStandalone, installPwa } = usePwa();
  const { user, isAuthenticated, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const userMenuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Close menus on route change
  useEffect(() => {
    setSidebarOpen(false);
    setUserMenuOpen(false);
  }, [pathname]);

  // Click outside to close user dropdown
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setUserMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // Lock body scroll when mobile sidebar is open
  useEffect(() => {
    if (sidebarOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [sidebarOpen]);

  return (
    <>
      <header className="w-full app-bg-surface border-b app-border sticky top-0 z-40 shadow-sm transition-colors duration-200 backdrop-blur-md bg-opacity-95">
        <div className="max-w-[1720px] w-full mx-auto px-3 sm:px-5 lg:px-6 xl:px-8">
          <div className="flex items-center justify-between h-16 gap-3 lg:gap-4">
            {/* Left: Official Government Brand Lockup */}
            <div className="flex items-center gap-2.5 sm:gap-3 flex-shrink-0">
              <Link href="/" className="flex items-center gap-2.5 sm:gap-3 group">
                {/* Crisp National Emblem of India */}
                <div className="relative h-9 w-6 sm:h-10 sm:w-7 flex items-center justify-center flex-shrink-0">
                  <Image
                    src="/emblem_lion_dark.png"
                    alt="National Emblem of India - MoSPI"
                    width={28}
                    height={44}
                    className="object-contain h-9 sm:h-10 w-auto opacity-95 group-hover:opacity-100 transition-opacity"
                    unoptimized
                    priority
                  />
                </div>

                {/* Stately Typography with Perfect Vertical Alignment */}
                <div className="flex flex-col justify-center">
                  <div className="flex items-center gap-1.5 sm:gap-2">
                    <span className="text-sm sm:text-base font-extrabold tracking-tight text-[#111827] leading-tight whitespace-nowrap">
                      Project: CEN
                    </span>
                    <span className="text-[9px] font-bold uppercase app-badge-gold px-1.5 py-0.5 rounded leading-none flex-shrink-0">
                      MoSPI
                    </span>
                  </div>
                  <span className="text-[9px] sm:text-[11px] font-medium text-[#7D8CA3] leading-tight mt-0.5 truncate block max-w-[170px] xs:max-w-[220px] sm:max-w-none">
                    Ministry of Statistics & Programme Implementation
                  </span>
                </div>
              </Link>
            </div>

            {/* Center: Desktop Navigation Tabs (Only shown when authenticated and not on login page) */}
            {!isLoginPage && isAuthenticated && (
              <nav className="hidden lg:flex items-center gap-1 xl:gap-1.5 justify-center flex-1 min-w-0 px-1">
                {NAV_LINKS.map((link) => {
                  const isActive = pathname === link.href;
                  return (
                    <Link
                      key={link.name}
                      href={link.href}
                      className={`px-2.5 xl:px-3 py-1.5 text-xs font-semibold rounded-lg whitespace-nowrap transition-all duration-150 ${
                        isActive
                          ? "bg-[#284269] text-[#F5F3EC] shadow-sm font-bold border border-[#1E2A44]"
                          : "text-[#284269] hover:bg-[#EEF4FA] hover:text-[#111827]"
                      }`}
                    >
                      {link.name}
                    </Link>
                  );
                })}
              </nav>
            )}

            {/* Right: Google Translate Widget, Official Auth & Hamburger */}
            <div className="flex items-center gap-2 sm:gap-2.5 flex-shrink-0">
              {/* Dynamic Google Translate Integration */}
              <GoogleTranslate />

              {/* Official User Dropdown with Down Arrow (Desktop Only, hidden on login page) */}
              {!isLoginPage && isAuthenticated && user && (
                <div className="relative hidden lg:block" ref={userMenuRef}>
                  <button
                    type="button"
                    onClick={() => setUserMenuOpen((prev) => !prev)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg app-bg-card hover:app-bg-card-hover border app-border text-xs font-semibold app-text-primary shadow-2xs transition-all cursor-pointer"
                    aria-expanded={userMenuOpen}
                  >
                    <span className="truncate max-w-[140px]">{user.full_name}</span>
                    <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform duration-200 ${userMenuOpen ? "rotate-180" : ""}`} />
                  </button>

                  {/* Dropdown Menu with Sign Out Option */}
                  {userMenuOpen && (
                    <div className="absolute right-0 mt-2 w-52 app-bg-surface border app-border rounded-xl shadow-2xl p-1.5 z-50 animate-in fade-in zoom-in-95 duration-150">
                      {/* Role Header (Clean & Minimal) */}
                      <div className="px-2.5 py-1.5 border-b app-border mb-1 flex items-center justify-between text-xs">
                        <span className="app-text-muted text-[11px] font-medium">Role</span>
                        <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded bg-[var(--color-gold)]/15 text-[var(--color-gold)] border border-[var(--color-gold)]/30 leading-none">
                          {user.role}
                        </span>
                      </div>

                      {/* Sign Out Option */}
                      <button
                        type="button"
                        onClick={() => {
                          setUserMenuOpen(false);
                          logout();
                        }}
                        className="w-full flex items-center gap-2 px-2.5 py-2 text-xs font-semibold text-rose-500 hover:bg-rose-500/10 rounded-lg transition-colors cursor-pointer text-left"
                      >
                        <LogOut className="w-4 h-4" />
                        <span>Sign Out</span>
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Three-Dashed Hamburger Menu Button (Mobile/Tablet Only, hidden on login page) */}
              {!isLoginPage && (
                <button
                  onClick={() => setSidebarOpen(true)}
                  aria-label="Open Navigation Menu"
                  className="lg:hidden p-2 rounded-md app-bg-card hover:app-bg-card-hover border app-border app-text-primary shadow-sm flex items-center justify-center transition-colors cursor-pointer flex-shrink-0"
                >
                  <Menu className="w-5 h-5 text-current" />
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Full-Screen Mobile Menu Drawer (Covers Entire Screen 100%) */}
      {!isLoginPage &&
        mounted &&
        sidebarOpen &&
        createPortal(
          <div className="fixed inset-0 z-[9999] h-screen w-screen overflow-hidden flex flex-col">
            {/* Full-Screen Menu Container */}
            <div
              className="relative w-full h-full flex flex-col z-10 animate-in fade-in duration-200 bg-white text-[#2C221E]"
              style={{
                backgroundImage:
                  "linear-gradient(rgba(255, 255, 255, 0.94), rgba(255, 255, 255, 0.97)), url('/mobile_dark_cabin_bg.png')",
                backgroundSize: "cover",
                backgroundPosition: "center center",
                backgroundRepeat: "no-repeat",
              }}
            >
              {/* Top Header Bar */}
              <div className="p-4 sm:p-5 border-b flex items-center justify-between backdrop-blur-md border-[#E2E8F0] bg-white/95">
                <div className="flex items-center gap-2.5">
                  <div className="relative h-8 w-6 flex items-center justify-center flex-shrink-0">
                    <Image
                      src="/emblem_lion_dark.png"
                      alt="MoSPI Emblem"
                      width={24}
                      height={34}
                      className="object-contain max-h-8 w-auto"
                      unoptimized
                    />
                  </div>
                  <div>
                    <div className="text-base font-extrabold text-[#111827]">
                      Project: CEN
                    </div>
                    <div className="text-xs font-medium text-[#7D8CA3]">
                      Ministry of Statistics & Programme Implementation
                    </div>
                  </div>
                </div>

                {/* Close Button */}
                <button
                  onClick={() => setSidebarOpen(false)}
                  aria-label="Close Menu"
                  className="p-2 rounded-md border transition-colors cursor-pointer shadow-sm bg-[#EEF4FA] hover:bg-[#E2E8F0] border-[#CBD7E6] text-[#1E2A44]"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Navigation Links (Full Width Grid & Scrollable) */}
              <nav className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-2 custom-scrollbar bg-[#F8FAFC]">
                <div className="flex items-center justify-between px-2 py-1">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-[#7D8CA3]">
                    Menu Navigation
                  </span>
                  {/* Google Translate in Mobile Drawer */}
                  <GoogleTranslate />
                </div>
                {NAV_LINKS.map((link) => {
                  const isActive = pathname === link.href;
                  return (
                    <Link
                      key={link.name}
                      href={link.href}
                      onClick={() => setSidebarOpen(false)}
                      className={`flex items-center justify-between px-4 py-3 rounded-lg text-sm font-semibold transition-all ${
                        isActive
                          ? "bg-[#284269] text-[#F5F3EC] shadow-md font-bold border border-[#1E2A44]"
                          : "bg-white text-[#111827] border border-[#E2E8F0] hover:border-[#CBD7E6] hover:bg-[#EEF4FA]"
                      }`}
                    >
                      <span>{link.name}</span>
                      <ChevronRight
                        className={`w-4 h-4 opacity-70 ${
                          isActive ? "text-[#F5F3EC]" : "text-[#7D8CA3]"
                        }`}
                      />
                    </Link>
                  );
                })}
              </nav>

              {/* PWA Install Action (Mobile) */}
              {isInstallable && !isStandalone && (
                <div className="p-3.5 mx-4 mb-2 rounded-xl border flex items-center justify-between gap-3 bg-amber-50/90 border-[var(--color-gold)]/40 text-slate-900">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="p-2 rounded-lg bg-[var(--color-gold)]/20 text-[var(--color-gold)] flex-shrink-0">
                      <Smartphone className="w-4 h-4" />
                    </div>
                    <div className="min-w-0">
                      <div className="text-xs font-bold truncate">Install AirIndex App</div>
                      <div className="text-[10px] text-slate-500 truncate">Add to Home Screen</div>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setSidebarOpen(false);
                      installPwa();
                    }}
                    className="px-3 py-1.5 bg-[var(--color-gold)] hover:bg-[var(--color-gold)]/90 text-slate-950 font-bold text-xs rounded-lg transition-colors shadow-sm flex items-center gap-1 cursor-pointer flex-shrink-0"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Install</span>
                  </button>
                </div>
              )}

              {/* Official Auth Section (Mobile) */}
              <div className="px-4 mb-3">
                {isAuthenticated && user ? (
                  <div className="p-3.5 rounded-xl border flex items-center justify-between gap-3 bg-slate-50 border-slate-200 text-slate-900">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="w-8 h-8 rounded-full bg-[var(--color-gold)]/20 text-[var(--color-gold)] flex items-center justify-center text-xs font-black flex-shrink-0">
                        {user.full_name?.charAt(0) || "U"}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs font-bold truncate">{user.full_name}</span>
                          <span className="text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded bg-[var(--color-gold)]/20 text-[var(--color-gold)] leading-none">
                            {user.role}
                          </span>
                        </div>
                        <p className="text-[10px] text-slate-500 truncate">{user.designation}</p>
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        logout();
                        setSidebarOpen(false);
                      }}
                      className="p-2 rounded-lg bg-rose-50 text-rose-600 hover:bg-rose-100 border border-rose-200 transition-colors flex items-center gap-1 text-xs font-bold cursor-pointer flex-shrink-0"
                      title="Sign Out"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                ) : (
                  <Link
                    href="/login"
                    onClick={() => setSidebarOpen(false)}
                    className="flex items-center justify-center gap-2 w-full py-3 px-4 rounded-xl bg-[var(--color-gold)] hover:bg-[var(--color-gold)]/90 text-slate-950 font-extrabold text-xs shadow-md transition-all"
                  >
                    <Lock className="w-4 h-4" />
                    <span>Official Portal Sign In</span>
                  </Link>
                )}
              </div>

              {/* Drawer Footer Tagline */}
              <div className="p-3.5 border-t text-center space-y-0.5 border-slate-200 bg-slate-50">
                <p className="text-xs font-semibold tracking-wide text-slate-900">
                  National Airfare Inflation Platform
                </p>
                <p className="text-[11px] font-medium text-slate-600">
                  MoSPI CPI 07.3.3.1
                </p>
              </div>
            </div>
          </div>,
          document.body
        )}
    </>
  );
}
