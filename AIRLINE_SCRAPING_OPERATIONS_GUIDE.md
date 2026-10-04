# ✈️ Project CEN — Airline Scraping Operations & Cost Guide

> **System**: Airfare Price Index Data Ingestion Pipeline (MoSPI)  
> **Engines**: Primary Fast HTTP Scraper + Autonomous AI Fallback (`browser-use`)  

---

## 1. 💰 Cost & Pricing Breakdown

| Scraping Method | Cost per Query (1 Route × 1 Date) | Daily Cost (30 Route-Horizons) | Monthly Cost | Cost Highlights |
| :--- | :---: | :---: | :---: | :--- |
| **Primary Fast Engine** (`flight_client.py`) | **$0.00 (₹0.00)** | **$0.00 (₹0.00)** | **$0.00 (₹0.00)** | 🟢 **100% Free & Unlimited** |
| **Local AI Agent** (`browser-use` + Gemini Flash) | **$0.0005 (₹0.04)** | **$0.015 (₹1.25)** | **$0.45 (₹38.00)** | 🟡 **Ultra-low cost** (Local Chrome) |
| **Browser Use Cloud SDK** (`BROWSER_USE_API_KEY`) | **$0.025 (₹2.10)** | **$0.75 (₹62.50)** | **$22.50 (₹1,875.00)** | 🔵 **Managed Cloud & Proxies** |

---

## 2. ⏱️ Execution Timing & Speed Comparison

| Scope | Primary Fast Engine (`flight_client.py`) | Autonomous AI Agent (`browser-use`) | Speed Advantage |
| :--- | :---: | :---: | :--- |
| **Single Route Query** (`DEL-BOM` T-1) | **⚡ 1.2 – 2.5 seconds** | **⏳ 2.0 – 3.5 minutes** | Fast Engine is **60× faster** |
| **Full Daily Harvest** (30 Queries, Sequential) | **⚡ 45 – 60 seconds** | **⏳ 60 – 90 minutes** | Fast Engine completes in **< 1 min** |
| **Full Daily Harvest** (5 Parallel Workers) | **⚡ 12 – 18 seconds** | **⏳ 15 – 20 minutes** | Efficient parallel collection |

---

## 3. 🕒 Recommended Scraping Schedule & Intervals

| Parameter | Recommended Setting | Purpose & Rule |
| :--- | :--- | :--- |
| **Primary Daily Run** | **`02:00 AM IST`** (Cron: `0 2 * * *`) | Lowest airline server load; avoids passenger booking rush. |
| **Intraday Spot Checks** | **`06:00 AM`, `02:00 PM`, `10:00 PM`** | Tracks peak business-hour dynamic pricing shifts. |
| **Inter-Request Delay** | **`3.0 – 5.0 seconds`** (Random Jitter) | Prevents triggering rate limiters on airline websites. |
| **Max Concurrency** | **`3 – 4 Parallel Workers`** | Complies with fair-usage connection caps. |

---

## 4. 🛡️ Platform Restrictions & Compliance Guardrails

| Constraint | Airline / OTA Policy | How Project CEN Complies |
| :--- | :--- | :--- |
| **Rate Limit** | Max **10–15 requests/min** per IP. | Automatic request throttling & exponential backoff. |
| **Anti-Bot WAF** | Akamai & Cloudflare Turnstile detection. | Indian proxy pools (`proxy_country_code="in"`) & clean headers. |
| **Data Scope** | Only **public fare information**. | Zero personal data or passenger accounts touched. |
| **Session Expiry** | 10–15 min cloud task limit. | Automatic browser teardown after quote extraction. |

---

## 5. 🌐 Supported Portals & Extraction Matrix

| Target Code | Website Name | Domain URL | Coverage |
| :--- | :--- | :--- | :--- |
| **`google_flights`** *(Default)* | Google Flights | `google.com/travel/flights` | Aggregates all Indian airlines in 1 query |
| **`indigo`** | IndiGo Official | `goindigo.in` | Direct Saver & Flexi fares |
| **`airindia`** | Air India Official | `airindia.com` | Direct & connecting flight fares |
| **`akasaair`** | Akasa Air Official | `akasaair.com` | Budget carrier direct fares |
| **`easemytrip`** | EaseMyTrip Portal | `easemytrip.com` | OTA comparison rates |

---

## 6. 🚀 Operational Commands Quick Reference

```powershell
# 1. Run Autonomous AI Scraper (from app folder)
cd app
python browser.py

# 2. Run Autonomous AI Scraper (from project root)
python -m app.browser

# 3. View Generated JSON Output
cat scraped_flights_output.json
```
