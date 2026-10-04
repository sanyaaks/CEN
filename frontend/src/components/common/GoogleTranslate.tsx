"use client";

import React, { useEffect, useState, useRef } from "react";
import Script from "next/script";
import { Languages, ChevronDown, Check } from "lucide-react";

declare global {
  interface Window {
    google: any;
    googleTranslateElementInit: () => void;
  }
}

export default function GoogleTranslate() {
  const [selectedLang, setSelectedLang] = useState<string>("en");
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const dropdownRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    // Check saved language preference or cookie
    const savedLang = localStorage.getItem("cen_selected_lang");
    const match = document.cookie.match(/googtrans=\/en\/([a-z]{2})/i);
    
    if (savedLang) {
      setSelectedLang(savedLang);
    } else if (match && match[1]) {
      setSelectedLang(match[1].toLowerCase());
    }

    // Global Google Translate Init
    window.googleTranslateElementInit = () => {
      if (window.google && window.google.translate) {
        new window.google.translate.TranslateElement(
          {
            pageLanguage: "en",
            includedLanguages: "en,hi",
            autoDisplay: false,
          },
          "google_translate_element"
        );
      }
    };

    if (window.google && window.google.translate) {
      window.googleTranslateElementInit();
    }

    // Observer to forcefully strip Google banner frames and body top offset
    const observer = new MutationObserver(() => {
      if (document.body.style.top && document.body.style.top !== "0px") {
        document.body.style.top = "0px";
      }
      if (document.body.style.position && document.body.style.position !== "static") {
        document.body.style.position = "static";
      }
      const banners = document.querySelectorAll(
        ".goog-te-banner-frame, iframe.skiptranslate, body > .skiptranslate, iframe[id*=':']"
      );
      banners.forEach((banner) => {
        (banner as HTMLElement).style.setProperty("display", "none", "important");
        (banner as HTMLElement).style.setProperty("visibility", "hidden", "important");
        (banner as HTMLElement).style.setProperty("height", "0px", "important");
      });
    });

    observer.observe(document.body, { attributes: true, childList: true, subtree: false });

    // Click outside to close dropdown
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      observer.disconnect();
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const handleSelectLang = (langCode: string) => {
    setSelectedLang(langCode);
    setIsOpen(false);
    localStorage.setItem("cen_selected_lang", langCode);

    // Set cookie for Google Translate
    const cookieVal = `/en/${langCode}`;
    document.cookie = `googtrans=${cookieVal}; path=/;`;
    document.cookie = `googtrans=${cookieVal}; path=/; domain=${window.location.hostname};`;
    if (window.location.hostname.includes(".")) {
      document.cookie = `googtrans=${cookieVal}; path=/; domain=.${window.location.hostname};`;
    }

    // Also trigger the combo if already initialized in DOM
    const selectElem = document.querySelector(".goog-te-combo") as HTMLSelectElement | null;
    if (selectElem) {
      selectElem.value = langCode;
      selectElem.dispatchEvent(new Event("change"));
    }

    // Refresh page to apply Google Translation cleanly across the DOM
    setTimeout(() => {
      window.location.reload();
    }, 100);
  };

  return (
    <div className="relative notranslate" translate="no" ref={dropdownRef}>
      {/* Hidden Google Translate Target (Kept in DOM so script can render into it without showing) */}
      <div
        id="google_translate_element"
        style={{
          position: "fixed",
          top: "-9999px",
          left: "-9999px",
          width: "1px",
          height: "1px",
          opacity: 0,
          pointerEvents: "none",
        }}
      />

      {/* Custom Styled Dropdown Button */}
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg app-bg-card hover:app-bg-card-hover border app-border text-xs font-semibold app-text-primary shadow-sm transition-all cursor-pointer notranslate"
        translate="no"
        aria-expanded={isOpen}
      >
        <Languages className="w-3.5 h-3.5 text-[#2E4A6B] flex-shrink-0" />
        <span className="font-bold text-[#111827] notranslate" translate="no">
          {selectedLang === "hi" ? "हिन्दी" : "English"}
        </span>
        <ChevronDown
          className={`w-3.5 h-3.5 text-slate-400 transition-transform duration-200 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* Styled Dropdown Menu */}
      {isOpen && (
        <div
          className="absolute right-0 mt-2 w-40 app-bg-surface border app-border rounded-xl shadow-2xl p-1.5 z-50 animate-in fade-in zoom-in-95 duration-150 notranslate"
          translate="no"
        >
          <div
            className="px-2.5 py-1 text-[10px] font-extrabold uppercase text-[#7D8CA3] border-b app-border-subtle mb-1 notranslate"
            translate="no"
          >
            Language / भाषा
          </div>

          {/* English Option */}
          <button
            type="button"
            onClick={() => handleSelectLang("en")}
            className={`w-full flex items-center justify-between px-2.5 py-2 text-xs font-semibold rounded-lg transition-colors cursor-pointer text-left notranslate ${
              selectedLang === "en"
                ? "bg-[#1E2A44] text-[#F5F3EC]"
                : "text-[#111827] hover:bg-[#EEF4FA]"
            }`}
            translate="no"
          >
            <span className="notranslate" translate="no">English</span>
            {selectedLang === "en" && <Check className="w-3.5 h-3.5 text-[#F5F3EC]" />}
          </button>

          {/* Hindi Option */}
          <button
            type="button"
            onClick={() => handleSelectLang("hi")}
            className={`w-full flex items-center justify-between px-2.5 py-2 text-xs font-semibold rounded-lg transition-colors cursor-pointer text-left notranslate ${
              selectedLang === "hi"
                ? "bg-[#1E2A44] text-[#F5F3EC]"
                : "text-[#111827] hover:bg-[#EEF4FA]"
            }`}
            translate="no"
          >
            <span className="notranslate" translate="no">हिन्दी</span>
            {selectedLang === "hi" && <Check className="w-3.5 h-3.5 text-[#F5F3EC]" />}
          </button>
        </div>
      )}

      {/* Load Google Translate Script */}
      <Script
        src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"
        strategy="afterInteractive"
      />
    </div>
  );
}
