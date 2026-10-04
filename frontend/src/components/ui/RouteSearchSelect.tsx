"use client";

import React, { useState, useRef, useEffect } from "react";
import { Search, ChevronDown, Check, Plane } from "lucide-react";

export interface RouteOption {
  code: string;
  name: string;
  cityFrom: string;
  cityTo: string;
}

export const ALL_DOMESTIC_ROUTES: RouteOption[] = [
  { code: "DEL-BOM", name: "Delhi → Mumbai", cityFrom: "Delhi (DEL)", cityTo: "Mumbai (BOM)" },
  { code: "BOM-BLR", name: "Mumbai → Bengaluru", cityFrom: "Mumbai (BOM)", cityTo: "Bengaluru (BLR)" },
  { code: "DEL-BLR", name: "Delhi → Bengaluru", cityFrom: "Delhi (DEL)", cityTo: "Bengaluru (BLR)" },
  { code: "DEL-MAA", name: "Delhi → Chennai", cityFrom: "Delhi (DEL)", cityTo: "Chennai (MAA)" },
  { code: "DEL-CCU", name: "Delhi → Kolkata", cityFrom: "Delhi (DEL)", cityTo: "Kolkata (CCU)" },
  { code: "HYD-MAA", name: "Hyderabad → Chennai", cityFrom: "Hyderabad (HYD)", cityTo: "Chennai (MAA)" },
  { code: "BLR-DEL", name: "Bengaluru → Delhi", cityFrom: "Bengaluru (BLR)", cityTo: "Delhi (DEL)" },
  { code: "BOM-GOI", name: "Mumbai → Goa", cityFrom: "Mumbai (BOM)", cityTo: "Goa (GOI)" },
  { code: "BLR-MAA", name: "Bengaluru → Chennai", cityFrom: "Bengaluru (BLR)", cityTo: "Chennai (MAA)" },
];

interface RouteSearchSelectProps {
  value: string;
  onChange: (route: string) => void;
  disabled?: boolean;
  className?: string;
  compact?: boolean;
}

export default function RouteSearchSelect({
  value,
  onChange,
  disabled = false,
  className = "",
  compact = false,
}: RouteSearchSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const selectedRouteObj = ALL_DOMESTIC_ROUTES.find((r) => r.code === value) || {
    code: value,
    name: `${value} Corridor`,
    cityFrom: value.split("-")[0] || value,
    cityTo: value.split("-")[1] || "",
  };

  const filteredRoutes = ALL_DOMESTIC_ROUTES.filter((r) => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return true;
    return (
      r.code.toLowerCase().includes(q) ||
      r.name.toLowerCase().includes(q) ||
      r.cityFrom.toLowerCase().includes(q) ||
      r.cityTo.toLowerCase().includes(q)
    );
  });

  // Handle clicking outside to close
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchQuery("");
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Focus search input when opening
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      setTimeout(() => {
        searchInputRef.current?.focus();
      }, 50);
    }
  }, [isOpen]);

  const handleSelect = (routeCode: string) => {
    onChange(routeCode);
    setIsOpen(false);
    setSearchQuery("");
  };

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`w-full flex items-center justify-between gap-2 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-[#1E2A44] transition-all shadow-xs focus:outline-none focus:ring-2 focus:ring-[#2E4A6B]/20 ${
          compact ? "px-3 py-1.5" : "px-3.5 py-2.5"
        } ${disabled ? "opacity-60 cursor-not-allowed bg-slate-100" : "cursor-pointer"}`}
      >
        <div className="flex items-center gap-2 truncate">
          <Plane className="w-3.5 h-3.5 text-[#2E4A6B] shrink-0" />
          <span className="font-mono font-bold">{selectedRouteObj.code}</span>
          <span className="text-[#7D8CA3] font-normal truncate hidden sm:inline">
            • {selectedRouteObj.name}
          </span>
        </div>
        <ChevronDown
          className={`w-3.5 h-3.5 text-[#7D8CA3] shrink-0 transition-transform duration-200 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* Dropdown Menu with Search Input */}
      {isOpen && (
        <div className="absolute z-50 mt-1 w-full min-w-[280px] sm:min-w-[320px] bg-white rounded-xl border border-slate-200 shadow-lg overflow-hidden animate-in fade-in zoom-in-95 duration-100 right-0 sm:left-0 sm:right-auto">
          {/* Search Box */}
          <div className="p-2 border-b border-slate-100 bg-slate-50">
            <div className="relative flex items-center">
              <Search className="w-3.5 h-3.5 absolute left-2.5 text-[#7D8CA3] pointer-events-none" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search route (e.g. Mumbai, DEL, Goa)..."
                className="w-full pl-8 pr-3 py-1.5 bg-white border border-slate-200 rounded-md text-xs text-[#1E2A44] placeholder-[#7D8CA3] focus:outline-none focus:ring-1 focus:ring-[#2E4A6B] focus:border-[#2E4A6B]"
              />
            </div>
          </div>

          {/* List of Corridors */}
          <div className="max-h-60 overflow-y-auto py-1 divide-y divide-slate-50">
            {filteredRoutes.length === 0 ? (
              <div className="p-4 text-center text-xs text-[#7D8CA3]">
                No flight routes found matching &quot;{searchQuery}&quot;
              </div>
            ) : (
              filteredRoutes.map((route) => {
                const isSelected = route.code === value;
                return (
                  <button
                    key={route.code}
                    type="button"
                    onClick={() => handleSelect(route.code)}
                    className={`w-full px-3.5 py-2.5 text-left text-xs flex items-center justify-between transition-colors ${
                      isSelected
                        ? "bg-slate-50 text-[#1E2A44] font-semibold"
                        : "hover:bg-slate-50/80 text-slate-700 font-medium"
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <div className="font-mono font-bold text-[#1E2A44] px-1.5 py-0.5 bg-slate-100 rounded text-[11px]">
                        {route.code}
                      </div>
                      <div className="flex flex-col">
                        <span className="text-[#1E2A44] font-semibold">{route.name}</span>
                        <span className="text-[10px] text-[#7D8CA3]">
                          {route.cityFrom} ⇄ {route.cityTo}
                        </span>
                      </div>
                    </div>
                    {isSelected && (
                      <Check className="w-4 h-4 text-[#2E4A6B] shrink-0 font-bold" />
                    )}
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
