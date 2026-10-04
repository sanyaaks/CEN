"use client";

import { useEffect, useState } from "react";
import { ExternalLink } from "lucide-react";
import { getApiBaseUrl } from "@/lib/api";

export default function Footer() {
  const iconColor = "#1E2A44"; // Executive Navy in Light Theme
  const [apiBase, setApiBase] = useState<string>("http://localhost:8000");

  useEffect(() => {
    setApiBase(getApiBaseUrl());
  }, []);

  return (
    <footer className="w-full app-bg-surface border-t app-border transition-colors duration-200 mt-auto overflow-hidden">
      <div className="max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 xl:px-12 py-3.5 sm:py-4 space-y-2.5 sm:space-y-3">
        {/* Top Row: Follow Us on Left, Action Pill Buttons on Right */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pb-3 border-b app-border-subtle w-full text-center sm:text-left">
          {/* Follow Us & Social Links */}
          <div className="flex items-center justify-center sm:justify-start gap-3 w-full sm:w-auto">
            <span className="text-sm sm:text-base font-extrabold tracking-tight app-text-primary whitespace-nowrap">
              Follow us
            </span>
            <div className="flex items-center justify-center gap-3.5">
              {/* Facebook */}
              <a
                href="https://www.facebook.com/GoIStats/?modal=admin_todo_tour"
                target="_blank"
                rel="noreferrer"
                aria-label="Official MoSPI Facebook"
                className="hover:scale-115 transition-all flex items-center justify-center"
                style={{ color: iconColor }}
              >
                <svg className="w-4.5 h-4.5 sm:w-5 sm:h-5" fill={iconColor} viewBox="0 0 24 24">
                  <path d="M14 13.5h2.5l1-4H14v-2c0-1.03.7-1.5 1.75-1.5H17.5V2.3c-.6-.08-1.57-.15-2.65-.15-2.73 0-4.6 1.66-4.6 4.75V9.5H7.5v4h2.75V22h3.75V13.5z" />
                </svg>
              </a>

              {/* Instagram */}
              <a
                href="https://www.instagram.com/goistats/?igshid=1ea2ccd5gsb85"
                target="_blank"
                rel="noreferrer"
                aria-label="Official MoSPI Instagram"
                className="hover:scale-115 transition-all flex items-center justify-center"
                style={{ color: iconColor }}
              >
                <svg className="w-4.5 h-4.5 sm:w-5 sm:h-5" fill="none" stroke={iconColor} strokeWidth="2.3" viewBox="0 0 24 24" strokeLinecap="round" strokeLinejoin="round">
                  <rect width="20" height="20" x="2" y="2" rx="5.5" ry="5.5" />
                  <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
                  <circle cx="17.5" cy="6.5" r="1" fill={iconColor} />
                </svg>
              </a>

              {/* X (formerly Twitter) */}
              <a
                href="https://x.com/GoIStats?s=08"
                target="_blank"
                rel="noreferrer"
                aria-label="Official MoSPI X"
                className="hover:scale-115 transition-all flex items-center justify-center"
                style={{ color: iconColor }}
              >
                <svg className="w-4.5 h-4.5 sm:w-5 sm:h-5" fill={iconColor} viewBox="0 0 24 24">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                </svg>
              </a>

              {/* YouTube */}
              <a
                href="https://www.youtube.com/channel/UCS5_qdc_flpyStB3ngvvgZw"
                target="_blank"
                rel="noreferrer"
                aria-label="Official MoSPI YouTube"
                className="hover:scale-115 transition-all flex items-center justify-center"
                style={{ color: iconColor }}
              >
                <svg className="w-4.5 h-4.5 sm:w-5 sm:h-5" fill={iconColor} viewBox="0 0 24 24">
                  <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
                </svg>
              </a>

              {/* LinkedIn */}
              <a
                href="https://www.linkedin.com/company/ministry-of-statistics-and-programme-implementation"
                target="_blank"
                rel="noreferrer"
                aria-label="Official MoSPI LinkedIn"
                className="hover:scale-115 transition-all flex items-center justify-center"
                style={{ color: iconColor }}
              >
                <svg className="w-4.5 h-4.5 sm:w-5 sm:h-5" fill={iconColor} viewBox="0 0 24 24">
                  <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v8.37H9.2V10.9H6.46M7.83 6.64a1.64 1.64 0 1 0 0 3.28 1.64 1.64 0 0 0 0-3.28z" />
                </svg>
              </a>
            </div>
          </div>

          {/* Quick Action Pill Buttons */}
          <div className="flex items-center justify-center sm:justify-end gap-2.5 w-full sm:w-auto max-w-sm sm:max-w-none">
            <a
              href={`${apiBase}/docs`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg app-bg-card hover:app-bg-card-hover border app-border text-xs font-medium app-text-primary transition-all shadow-sm flex-1 sm:flex-initial"
            >
              <span>API Documentation</span>
              <ExternalLink className="w-3 h-3 app-text-muted flex-shrink-0" />
            </a>
            <a
              href={`${apiBase}/export?format=json`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg app-bg-card hover:app-bg-card-hover border app-border text-xs font-medium app-text-primary transition-all shadow-sm flex-1 sm:flex-initial"
            >
              <span>Export CPI JSON</span>
              <ExternalLink className="w-3 h-3 app-text-muted flex-shrink-0" />
            </a>
          </div>
        </div>

        {/* Policy & Governance Links */}
        <div className="text-[11.5px] sm:text-xs app-text-secondary text-center max-w-2xl mx-auto py-1">
          {/* Mobile 2-line layout */}
          <div className="flex sm:hidden flex-col items-center justify-center gap-1.5">
            <div className="flex flex-wrap items-center justify-center gap-2">
              <a
                href="https://www.mospi.gov.in/PrivacyPolicy"
                target="_blank"
                rel="noreferrer"
                className="hover:app-text-primary hover:underline transition-colors"
              >
                Privacy Policy
              </a>
              <span className="opacity-35 text-[10px]">•</span>
              <a
                href="https://www.mospi.gov.in/terms-condition"
                target="_blank"
                rel="noreferrer"
                className="hover:app-text-primary hover:underline transition-colors"
              >
                Terms & Conditions
              </a>
              <span className="opacity-35 text-[10px]">•</span>
              <a
                href="https://www.mospi.gov.in/CopyrightPolicy"
                target="_blank"
                rel="noreferrer"
                className="hover:app-text-primary hover:underline transition-colors"
              >
                Copyright Policy
              </a>
            </div>
            <div className="flex items-center justify-center gap-2">
              <a
                href="https://www.mospi.gov.in/help"
                target="_blank"
                rel="noreferrer"
                className="hover:app-text-primary hover:underline transition-colors"
              >
                Help
              </a>
              <span className="opacity-35 text-[10px]">•</span>
              <a
                href="https://www.mospi.gov.in/Disclaimer"
                target="_blank"
                rel="noreferrer"
                className="hover:app-text-primary hover:underline transition-colors"
              >
                Disclaimer
              </a>
            </div>
          </div>

          {/* Desktop Single Line layout */}
          <div className="hidden sm:flex items-center justify-center gap-3.5">
            <a
              href="https://www.mospi.gov.in/PrivacyPolicy"
              target="_blank"
              rel="noreferrer"
              className="hover:app-text-primary hover:underline transition-colors"
            >
              Privacy Policy
            </a>
            <span className="opacity-35 text-[10px]">•</span>
            <a
              href="https://www.mospi.gov.in/terms-condition"
              target="_blank"
              rel="noreferrer"
              className="hover:app-text-primary hover:underline transition-colors"
            >
              Terms & Conditions
            </a>
            <span className="opacity-35 text-[10px]">•</span>
            <a
              href="https://www.mospi.gov.in/CopyrightPolicy"
              target="_blank"
              rel="noreferrer"
              className="hover:app-text-primary hover:underline transition-colors"
            >
              Copyright Policy
            </a>
            <span className="opacity-35 text-[10px]">•</span>
            <a
              href="https://www.mospi.gov.in/help"
              target="_blank"
              rel="noreferrer"
              className="hover:app-text-primary hover:underline transition-colors"
            >
              Help
            </a>
            <span className="opacity-35 text-[10px]">•</span>
            <a
              href="https://www.mospi.gov.in/Disclaimer"
              target="_blank"
              rel="noreferrer"
              className="hover:app-text-primary hover:underline transition-colors"
            >
              Disclaimer
            </a>
          </div>
        </div>

        {/* Data Attribution & Copyright Bar */}
        <div className="flex flex-col items-center justify-center text-xs text-center w-full pt-1 pb-1 space-y-1">
          <p className="text-[10px] sm:text-[11px] app-text-muted max-w-4xl text-center leading-relaxed">
            Route weighting data sourced from <strong className="app-text-primary font-medium">DGCA (Directorate General of Civil Aviation)</strong> via the india-aviation-traffic open dataset (ODbL license), aggregated from official Monthly Statistics (Domestic Air Transport) reports.
          </p>
          <p className="app-text-muted text-center w-full flex flex-col sm:flex-row items-center justify-center gap-0.5 sm:gap-1.5 leading-relaxed pt-0.5">
            <span>
              © 2026 <strong className="app-text-primary font-semibold">Government of India</strong>
            </span>
            <span className="hidden sm:inline opacity-40">•</span>
            <span className="text-[11px] sm:text-xs">Ministry of Statistics & Programme Implementation</span>
          </p>
        </div>
      </div>
    </footer>
  );
}
