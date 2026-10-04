"use client";

import React, { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import LoginPage from "@/app/login/page";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (isClient && !isLoading) {
      if (!isAuthenticated && pathname !== "/login") {
        router.replace("/login");
      } else if (isAuthenticated && pathname === "/login") {
        router.replace("/");
      }
    }
  }, [isClient, isAuthenticated, isLoading, pathname, router]);

  // Loading state while verifying token
  if (isLoading || !isClient) {
    return (
      <div className="min-h-[80vh] flex flex-col items-center justify-center app-bg-primary text-center p-6">
        <div className="w-10 h-10 border-2 border-[#1E2A44] border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-xs font-bold app-text-primary tracking-wide">
          Verifying Official Authorization...
        </p>
        <p className="text-[11px] app-text-muted mt-1">
          Government of India • Ministry of Statistics & Programme Implementation
        </p>
      </div>
    );
  }

  // If unauthenticated on /login page, show the Login Page
  if (!isAuthenticated && pathname === "/login") {
    return <>{children}</>;
  }

  // If unauthenticated on root (localhost:3000) or any other route, immediately render Login Page
  if (!isAuthenticated) {
    return <LoginPage />;
  }

  // If authenticated and visiting /login, show brief redirecting state
  if (isAuthenticated && pathname === "/login") {
    return (
      <div className="min-h-[80vh] flex flex-col items-center justify-center app-bg-primary text-center p-6">
        <div className="w-10 h-10 border-2 border-[#1E2A44] border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-xs font-bold app-text-primary tracking-wide">
          Redirecting to Official Dashboard...
        </p>
      </div>
    );
  }

  // Authenticated user accessing protected routes
  return <>{children}</>;
}
