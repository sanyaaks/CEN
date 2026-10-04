"use client";

import React, { useState } from "react";
import Image from "next/image";

interface AirlineLogoProps {
  airline: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

interface AirlineBrandInfo {
  code: string;
  name: string;
  bg: string;
  textColor: string;
  border: string;
  shortCode: string;
}

const BRAND_CONFIGS: Record<string, AirlineBrandInfo> = {
  "6E": {
    code: "6E",
    name: "IndiGo",
    bg: "#001B94",
    textColor: "#FFFFFF",
    border: "#0033CC",
    shortCode: "6E",
  },
  "AI": {
    code: "AI",
    name: "Air India",
    bg: "#D91B24",
    textColor: "#FFF0D4",
    border: "#E5B869",
    shortCode: "AI",
  },
  "IX": {
    code: "IX",
    name: "Air India Express",
    bg: "#B71234",
    textColor: "#FFFFFF",
    border: "#008080",
    shortCode: "IX",
  },
  "SG": {
    code: "SG",
    name: "SpiceJet",
    bg: "#ED1C24",
    textColor: "#FFFFFF",
    border: "#FF9900",
    shortCode: "SG",
  },
  "UK": {
    code: "UK",
    name: "Vistara",
    bg: "#582C4D",
    textColor: "#E5B869",
    border: "#D4AF37",
    shortCode: "UK",
  },
  "QP": {
    code: "QP",
    name: "Akasa Air",
    bg: "#E65100",
    textColor: "#FFFFFF",
    border: "#FF8F00",
    shortCode: "QP",
  },
  "EK": {
    code: "EK",
    name: "Emirates",
    bg: "#D71921",
    textColor: "#FFFFFF",
    border: "#FF4D4D",
    shortCode: "EK",
  },
  "TG": {
    code: "TG",
    name: "Thai Airways",
    bg: "#4B286D",
    textColor: "#E5B869",
    border: "#9C27B0",
    shortCode: "TG",
  },
  "UL": {
    code: "UL",
    name: "SriLankan Airlines",
    bg: "#006837",
    textColor: "#FFFFFF",
    border: "#2E7D32",
    shortCode: "UL",
  },
  "WY": {
    code: "WY",
    name: "Oman Air",
    bg: "#1A4D6B",
    textColor: "#E5B869",
    border: "#D4AF37",
    shortCode: "WY",
  },
};

export default function AirlineLogo({ airline, size = "md", className = "" }: AirlineLogoProps) {
  const [imgError, setImgError] = useState(false);
  const norm = (airline || "").trim().toUpperCase();

  // Find matching brand code
  let brandCode = "";
  if (norm.includes("AIR INDIA EXPRESS") || norm === "IX") brandCode = "IX";
  else if (norm.includes("AKASA") || norm === "QP") brandCode = "QP";
  else if (norm.includes("SPICEJET") || norm === "SG") brandCode = "SG";
  else if (norm.includes("VISTARA") || norm === "UK") brandCode = "UK";
  else if (norm.includes("INDIGO") || norm === "6E") brandCode = "6E";
  else if (norm.includes("EMIRATES") || norm === "EK") brandCode = "EK";
  else if (norm.includes("THAI") || norm === "TG") brandCode = "TG";
  else if (norm.includes("SRILANKAN") || norm === "UL") brandCode = "UL";
  else if (norm.includes("OMAN") || norm === "WY") brandCode = "WY";
  else if (norm === "AI" || norm.startsWith("AIR INDIA ") || norm === "AIR INDIA") brandCode = "AI";

  const brand = BRAND_CONFIGS[brandCode];

  const sizeClasses = {
    sm: "h-7 w-10 min-w-[40px]",
    md: "h-9 w-14 min-w-[56px]",
    lg: "h-11 w-16 min-w-[64px]",
  }[size];

  // If we have an official brand, display high-contrast container with official logo
  if (!imgError && brandCode) {
    return (
      <div
        className={`${sizeClasses} ${className} relative rounded-lg bg-white p-1 border border-slate-200/90 shadow-sm flex items-center justify-center flex-shrink-0 overflow-hidden group transition-transform group-hover:scale-105`}
        title={brand?.name || airline}
      >
        <Image
          src={`/airlines/${brandCode}_hd.png`}
          alt={brand?.name || airline}
          width={70}
          height={38}
          className="object-contain w-full h-full max-h-full"
          onError={() => setImgError(true)}
          unoptimized
        />
      </div>
    );
  }

  // High-contrast branded vector badge fallback
  if (brand) {
    return (
      <div
        className={`${sizeClasses} ${className} rounded flex items-center justify-center font-mono font-black text-xs shadow-sm flex-shrink-0 border`}
        style={{
          backgroundColor: brand.bg,
          color: brand.textColor,
          borderColor: brand.border,
        }}
        title={brand.name}
      >
        {brand.shortCode}
      </div>
    );
  }

  // General fallback
  const initials = norm.split(" ").map((w) => w[0]).join("").slice(0, 2) || "FL";
  return (
    <div
      className={`${sizeClasses} ${className} rounded bg-slate-800 text-white border border-slate-700 flex items-center justify-center font-mono font-bold text-xs shadow-sm flex-shrink-0`}
      title={airline}
    >
      {initials}
    </div>
  );
}
