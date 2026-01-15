#!/usr/bin/env python3
"""
CardNinja - Card Data Updater

This script scrapes credit card information from issuer websites
and uses LLM to extract structured reward data.

Usage:
    python scripts/update_cards.py

Requirements:
    - LLM provider configured (Groq, Gemini, or local)
    - pip install httpx beautifulsoup4
"""

import json
import httpx
import asyncio
import sys
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config

# Use centralized config
LLM_PROVIDER = config.LLM_PROVIDER
LLM_BASE_URL = config.LLM_BASE_URL
LLM_MODEL = config.LLM_MODEL

# Get all API keys for the provider (supports multiple keys for rotation)
API_KEYS = config.get_api_keys()

DATA_DIR = config.DATA_DIR
SOURCES_FILE = config.CARD_SOURCES_FILE
OUTPUT_FILE = config.CARDS_FILE
LOG_FILE = DATA_DIR / "update_log.txt"

# Max links to follow per card page
MAX_DEEP_LINKS = 3
# Max content size per deep link (smaller to fit in context)
DEEP_LINK_CONTENT_SIZE = 1500
# Total max content for LLM (Groq has ~8k context limit)
MAX_TOTAL_CONTENT = 6000

# Categories we track
CATEGORIES = [
    "dining", "groceries", "travel", "gas", "streaming",
    "online_shopping", "transit", "entertainment", "drugstore", "other"
]

EXTRACTION_PROMPT = """You are a data extraction assistant. Extract credit card reward information from the following webpage content.
The content includes the main card page plus additional details from related sub-pages.

### Current Date: {current_date}
### Current Quarter: Q{current_quarter} ({quarter_months})

### Webpage Content:
{content}

### Card Information:
- Card Name: {card_name}
- Issuer: {issuer}

### Task:
Extract the cashback/rewards percentages and point value information. Return ONLY a valid JSON object with no additional text.

**IMPORTANT: For cards with ROTATING QUARTERLY CATEGORIES (like Discover it, Chase Freedom Flex):**
- Only include the bonus categories that are ACTIVE for the CURRENT QUARTER (Q{current_quarter})
- Set the bonus rate (e.g., 5%) for ONLY the current quarter's active categories
- Other categories should show 1% (base rate)
- Include details about what's active THIS quarter in the notes

Categories to extract:
- dining (restaurants, food delivery)
- groceries (supermarkets, grocery stores)
- travel (flights, hotels, travel bookings)
- gas (gas stations, fuel)
- streaming (Netflix, Spotify, subscriptions)
- online_shopping (Amazon, online retailers)
- transit (Uber, Lyft, public transit)
- entertainment (movies, concerts, events)
- drugstore (pharmacies, CVS, Walgreens)
- other (base rate for all other purchases)
- you can add more categories if you want to, but make sure to add them to the CATEGORIES list in JSON

### Required JSON Format:
{{
    "annual_fee": <number>,
    "categories": {{
        "dining": <number>,
        "groceries": <number>,
        "travel": <number>,
        "gas": <number>,
        "streaming": <number>,
        "online_shopping": <number>,
        "transit": <number>,
        "entertainment": <number>,
        "drugstore": <number>,
        "other": <number>
    }},
    "category_details": {{
        "dining": {{
            "rate": "<e.g. '4x points'>",
            "includes": ["restaurants", "food delivery apps", "takeout"],
            "excludes": ["<any exclusions>"],
            "conditions": "<e.g. 'Up to $50,000/year'>"
        }},
        "groceries": {{
            "rate": "<e.g. '4x points'>",
            "includes": ["supermarkets", "grocery stores"],
            "excludes": ["Target", "Walmart", "wholesale clubs like Costco"],
            "conditions": "<e.g. 'Up to $25,000/year'>"
        }},
        "travel": {{
            "rate": "<e.g. '5x points'>",
            "includes": ["flights", "hotels"],
            "excludes": ["<what's NOT included>"],
            "booking_requirement": "<e.g. 'Must book through Chase Travel portal' or 'Direct with airlines/hotels'>",
            "conditions": "<any limits>"
        }},
        "gas": {{
            "rate": "<rate>",
            "includes": ["gas stations"],
            "excludes": ["<exclusions>"],
            "conditions": "<limits>"
        }},
        "streaming": {{
            "rate": "<rate>",
            "includes": ["Netflix", "Spotify", "Disney+", "etc."],
            "excludes": [],
            "conditions": "<limits>"
        }},
        "transit": {{
            "rate": "<rate>",
            "includes": ["rideshare", "public transit", "parking"],
            "excludes": [],
            "conditions": "<limits>"
        }}
    }},
    "reward_type": "<points|cashback|miles>",
    "point_value": {{
        "base_value": <cents per point, e.g. 1.0>,
        "best_value": <highest cents per point when redeemed optimally>,
        "best_redemption": "<how to get best value, e.g. 'Chase Travel Portal', 'Transfer to Hyatt'>"
    }},
    "special_offers": ["<offer1>", "<offer2>"],
    "exclusions": {{
        "groceries": ["<excluded merchant 1>", "<excluded merchant 2>"],
        "dining": ["<excluded merchant>"],
        "travel": ["<excluded type>"],
        "gas": ["<excluded>"],
        "other": ["<any other exclusions>"]
    }},
    "spending_caps": {{
        "groceries": "<e.g. 'Up to $6,000/year, then 1%'>",
        "dining": "<cap if any>",
        "travel": "<cap if any>"
    }},
    "rotating_categories": {{
        "has_rotating": <true if card has quarterly rotating categories, false otherwise>,
        "current_quarter": "Q{current_quarter}",
        "current_bonus_categories": ["<category1>", "<category2>"],
        "current_bonus_rate": "<e.g. '5% cash back'>",
        "activation_required": <true/false>,
        "quarterly_cap": "<e.g. 'Up to $1,500/quarter'>"
    }},
    "credits": ["<annual credit 1>", "<annual credit 2>"],
    "notes": "<any important conditions or limits>"
}}

IMPORTANT CATEGORY DETAILS TO CAPTURE:
1. TRAVEL bonuses - specify if booking portal required:
   - Chase cards: 5x is ONLY through Chase Travel portal (NO Airbnb, VRBO)
   - Amex cards: May require Amex Travel or direct airline booking
   - Capital One: Usually direct bookings count
   
2. GROCERY exclusions are common:
   - Usually excludes: Target, Walmart, wholesale clubs (Costco, Sam's Club, BJ's)
   - Usually includes: Traditional supermarkets (Kroger, Safeway, Publix, Whole Foods)
   
3. DINING usually includes:
   - Restaurants, fast food, food delivery (DoorDash, Uber Eats, Grubhub)
   - May exclude certain prepaid/gift cards

4. Look for spending caps like:
   - "Up to $6,000/year, then 1%"
   - "Up to $500/month in top category"
   - "Up to $1,500/quarter"

5. QUARTERLY ROTATING CATEGORIES (Discover it, Chase Freedom Flex, etc.):
   - These cards change bonus categories every quarter
   - Q1 (Jan-Mar), Q2 (Apr-Jun), Q3 (Jul-Sep), Q4 (Oct-Dec)
   - Common quarterly categories: Gas, Groceries, Restaurants, Amazon, PayPal, Walmart, Target
   - ONLY show the 5% bonus for categories ACTIVE in the CURRENT quarter
   - Requires activation each quarter
   - Usually capped at $1,500/quarter

If a category is not mentioned, use 1 as the default value.
Return ONLY the JSON object, no explanation."""


def extract_relevant_links(soup: BeautifulSoup, base_url: str) -> list:
    """Extract relevant internal links from the page"""
    relevant_keywords = [
        'benefit', 'reward', 'earn', 'point', 'cashback', 'cash-back',
        'rate', 'category', 'bonus', 'offer', 'feature', 'detail',
        'fee', 'apr', 'term', 'condition', 'faq', 'exclusion'
    ]
    
    links = []
    seen_urls = set()
    base_domain = urlparse(base_url).netloc
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag.get('href', '')
        text = a_tag.get_text(strip=True).lower()
        
        # Skip empty, javascript, anchor, or external links
        if not href or href.startswith('#') or href.startswith('javascript:'):
            continue
        
        # Build absolute URL
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        
        # Only follow internal links (same domain)
        if parsed.netloc != base_domain:
            continue
        
        # Skip duplicate URLs
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)
        
        # Check if link text or URL contains relevant keywords
        url_lower = full_url.lower()
        if any(kw in text or kw in url_lower for kw in relevant_keywords):
            links.append({
                'url': full_url,
                'text': a_tag.get_text(strip=True)[:50]
            })
            
        if len(links) >= MAX_DEEP_LINKS:
            break
    
    return links


async def fetch_page_content(url: str, extract_links: bool = False) -> tuple:
    """Fetch and parse webpage content, optionally extract links"""
    headers = {
        "User-Agent": config.SCRAPE_USER_AGENT
    }
    
    try:
        async with httpx.AsyncClient(timeout=config.SCRAPE_TIMEOUT, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract links before removing elements
            links = []
            if extract_links:
                links = extract_relevant_links(soup, url)
            
            # Remove script and style elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
            
            # Get text content
            text = soup.get_text(separator=' ', strip=True)
            
            # Truncate to reasonable size for LLM
            return text[:4000], links
    except Exception as e:
        print(f"  ⚠️  Failed to fetch {url}: {e}")
        return "", []


async def fetch_deep_links(links: list) -> str:
    """Fetch content from sub-links and combine"""
    if not links:
        return ""
    
    combined_content = []
    
    for link_info in links:
        try:
            content, _ = await fetch_page_content(link_info['url'], extract_links=False)
            if content:
                # Truncate each deep link content
                truncated = content[:DEEP_LINK_CONTENT_SIZE]
                combined_content.append(f"\n--- {link_info['text']} ---\n{truncated}")
        except Exception as e:
            print(f"      ⚠️  Failed to fetch sub-link {link_info['url']}: {e}")
        
        # Small delay between deep link requests
        await asyncio.sleep(0.5)
    
    return "\n".join(combined_content)


async def call_llm_with_key(client: httpx.AsyncClient, prompt: str, api_key: str) -> str:
    """Make a single LLM API call with the given key. Returns response text or raises exception."""
    
    if LLM_PROVIDER.lower() == "gemini":
        model = LLM_MODEL if LLM_MODEL else "gemini-2.0-flash-exp"
        response = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 2048,
                }
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
        
    elif LLM_PROVIDER.lower() == "groq":
        # Use provided model or default to a known working model
        # Clean model name (remove any quotes or whitespace)
        model = LLM_MODEL.strip().strip('"').strip("'") if LLM_MODEL else "llama-3.3-70b-versatile"
        url = "https://api.groq.com/openai/v1/chat/completions"
        # Debug: print what we're sending (masked key)
        print(f"      [DEBUG] Groq URL: {url}")
        print(f"      [DEBUG] Model: '{model}'")
        print(f"      [DEBUG] Key prefix: {api_key[:10]}...")
        response = await client.post(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 2048
            }
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
        
    elif LLM_PROVIDER.lower() == "mistral":
        model = LLM_MODEL if LLM_MODEL else "mistral-small-latest"
        response = await client.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 2048
            }
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    elif LLM_PROVIDER.lower() == "ollama":
        response = await client.post(
            f"{LLM_BASE_URL}/api/generate",
            json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1}
            }
        )
        response.raise_for_status()
        return response.json().get("response", "")
        
    else:
        # OpenAI-compatible API (LM Studio, etc.)
        response = await client.post(
            f"{LLM_BASE_URL}/v1/chat/completions",
            json={
                "model": LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1
            }
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


async def extract_with_llm(content: str, card_name: str, issuer: str) -> dict:
    """Use LLM to extract structured data from webpage content.
    
    Rotates through multiple API keys on rate limits.
    If all keys are exhausted, returns None (card will be skipped).
    """
    
    if not content:
        return None
    
    # Check if we have API keys for cloud providers
    if config.is_cloud_provider() and not API_KEYS:
        print(f"  ⚠️  No API keys configured for {LLM_PROVIDER}. Add keys to backend/.env")
        return None
    
    # Get current quarter info
    now = datetime.now()
    current_quarter = (now.month - 1) // 3 + 1
    quarter_months = {
        1: "January-March",
        2: "April-June", 
        3: "July-September",
        4: "October-December"
    }[current_quarter]
    
    prompt = EXTRACTION_PROMPT.format(
        content=content,
        card_name=card_name,
        issuer=issuer,
        current_date=now.strftime("%B %d, %Y"),
        current_quarter=current_quarter,
        quarter_months=quarter_months
    )
    
    # For local providers, just use empty key
    keys_to_try = API_KEYS if config.is_cloud_provider() else [""]
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        for key_idx, api_key in enumerate(keys_to_try):
            key_label = f"key {key_idx + 1}/{len(keys_to_try)}" if len(keys_to_try) > 1 else "API"
            
            try:
                result = await call_llm_with_key(client, prompt, api_key)
                
                # Parse JSON from response
                result = result.strip()
                if result.startswith("```"):
                    # Remove markdown code blocks
                    lines = result.split("```")
                    if len(lines) > 1:
                        result = lines[1]
                        if result.startswith("json"):
                            result = result[4:]
                
                # Find JSON object in response
                start = result.find("{")
                end = result.rfind("}") + 1
                if start != -1 and end > start:
                    result = result[start:end]
                
                return json.loads(result)
                    
            except httpx.HTTPStatusError as e:
                error_body = ""
                try:
                    error_body = e.response.text[:200]
                except:
                    pass
                if e.response.status_code == 429:
                    # Rate limited - try next key immediately
                    print(f"  ⚠️  Rate limited ({key_label}), trying next key...")
                    continue
                elif e.response.status_code == 503:
                    # Service unavailable - try next key
                    print(f"  ⚠️  Service unavailable ({key_label}), trying next key...")
                    continue
                elif e.response.status_code == 404:
                    # Not found - print details for debugging
                    print(f"  ⚠️  404 Not Found ({key_label})")
                    print(f"      URL: {e.request.url}")
                    print(f"      Response: {error_body}")
                    continue
                else:
                    print(f"  ⚠️  HTTP error ({key_label}): {e}")
                    if error_body:
                        print(f"      Response: {error_body}")
                    continue
                    
            except httpx.TimeoutException:
                print(f"  ⚠️  Timeout ({key_label}), trying next key...")
                continue
                
            except json.JSONDecodeError as e:
                print(f"  ⚠️  Failed to parse LLM response as JSON: {e}")
                # Don't try next key for JSON errors - the response came back, just malformed
                return None
                
            except Exception as e:
                print(f"  ⚠️  LLM error ({key_label}): {e}")
                continue
        
        # All keys exhausted
        if len(keys_to_try) > 1:
            print(f"  ❌ All {len(keys_to_try)} API keys exhausted (rate limited/failed)")
        else:
            print(f"  ❌ LLM extraction failed")
            return None
    
    return None


def get_default_card_data(card_source: dict, existing_card: dict = None) -> dict:
    """Return card data when extraction fails.
    
    If existing_card is provided (has real data), return the existing card as-is
    so we don't lose good data. Its timestamp won't be updated, so it will be retried.
    
    If no existing card or existing card has default notes, return minimal default data.
    """
    # If we have existing card with real (non-default) data, preserve it entirely
    if existing_card and existing_card.get('notes') != "Data not available - using defaults":
        print(f"   ℹ️  Preserving existing card data (has real data)")
        return existing_card
    
    # If existing card has default data, also return it (preserves its old timestamp)
    if existing_card:
        print(f"   ℹ️  Preserving existing default data (will retry next time)")
        return existing_card
    
    # No existing card - create new default data with old timestamp
    default_data = {
        "id": card_source["id"],
        "name": card_source["name"],
        "issuer": card_source["issuer"],
        "color": card_source["color"],
        "annual_fee": 0,
        "categories": {cat: 1 for cat in CATEGORIES},
        "reward_type": "cashback",
        "point_value": {
            "base_value": 1.0,
            "best_value": 1.0,
            "best_redemption": "Statement credit"
        },
        "special_offers": [],
        "exclusions": {},
        "spending_caps": {},
        "credits": [],
        "notes": "Data not available - using defaults",
        "source_url": card_source["url"],
        # Set old date so it gets picked up next time
        "last_updated": "2020-01-01T00:00:00"
    }
    
    # Add image from card_source if available
    if card_source.get('image'):
        default_data['image'] = card_source['image']
    
    return default_data


async def update_card(card_source: dict, existing_card: dict = None) -> tuple:
    """Update a single card's data. Returns (card_data, success_bool)
    
    If fetch or LLM extraction fails, returns existing card data (if available)
    with its original timestamp so it will be retried next time.
    """
    print(f"\n📇 Processing: {card_source['issuer']} {card_source['name']}")
    print(f"   URL: {card_source['url']}")
    
    # Fetch webpage content and extract links
    print("   ⏳ Fetching main page...")
    content, links = await fetch_page_content(card_source["url"], extract_links=True)
    
    if not content:
        print("   ❌ Could not fetch page, keeping existing data (will retry next time)")
        return get_default_card_data(card_source, existing_card), False
    
    print(f"   ✅ Fetched {len(content)} characters from main page")
    
    # Fetch content from sub-links (one level deep)
    if links:
        print(f"   ⏳ Fetching {len(links)} sub-pages for more details...")
        for link in links[:3]:  # Show first 3
            print(f"      → {link['text']}")
        if len(links) > 3:
            print(f"      ... and {len(links) - 3} more")
        
        deep_content = await fetch_deep_links(links)
        if deep_content:
            # Combine main content with deep link content
            content = f"{content}\n\n=== ADDITIONAL DETAILS FROM SUB-PAGES ===\n{deep_content}"
            # Truncate to max content size for LLM context limits
            if len(content) > MAX_TOTAL_CONTENT:
                content = content[:MAX_TOTAL_CONTENT]
            print(f"   ✅ Total content: {len(content)} characters (with sub-pages)")
    
    # Extract data with LLM
    print("   ⏳ Extracting data with LLM...")
    extracted = await extract_with_llm(
        content,
        card_source["name"],
        card_source["issuer"]
    )
    
    if not extracted:
        print("   ❌ LLM extraction failed, keeping existing data (will retry next time)")
        return get_default_card_data(card_source, existing_card), False
    
    print("   ✅ Data extracted successfully")
    
    # Build final card data
    card_data = {
        "id": card_source["id"],
        "name": card_source["name"],
        "issuer": card_source["issuer"],
        "color": card_source["color"],
        "annual_fee": extracted.get("annual_fee", 0),
        "categories": {
            cat: extracted.get("categories", {}).get(cat, 1)
            for cat in CATEGORIES
        },
        "reward_type": extracted.get("reward_type", "cashback"),
        "point_value": extracted.get("point_value", {
            "base_value": 1.0,
            "best_value": 1.0,
            "best_redemption": "Statement credit"
        }),
        "special_offers": extracted.get("special_offers", [])[:5],
        "exclusions": extracted.get("exclusions", {}),
        "spending_caps": extracted.get("spending_caps", {}),
        "category_details": extracted.get("category_details", {}),
        "rotating_categories": extracted.get("rotating_categories", {}),
        "credits": extracted.get("credits", [])[:5],
        "notes": extracted.get("notes", ""),
        "source_url": card_source["url"],
        "last_updated": datetime.now().isoformat()
    }
    
    # Include image URL if available (from download_card_images.py)
    if card_source.get("image"):
        card_data["image"] = card_source["image"]
    
    return card_data, True


def write_update_log(updated_cards: list, failed_cards: list):
    """Write update log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = f"\n{'='*60}\n"
    log_entry += f"Update: {timestamp}\n"
    log_entry += f"Provider: {LLM_PROVIDER} / Model: {LLM_MODEL}\n"
    log_entry += f"{'='*60}\n"
    
    if updated_cards:
        log_entry += f"\n✅ Successfully Updated ({len(updated_cards)}):\n"
        for card in updated_cards:
            log_entry += f"   - {card['issuer']} {card['name']}\n"
    
    if failed_cards:
        log_entry += f"\n❌ Failed/Defaults ({len(failed_cards)}):\n"
        for card in failed_cards:
            log_entry += f"   - {card['issuer']} {card['name']}\n"
    
    log_entry += f"\nTotal: {len(updated_cards)} succeeded, {len(failed_cards)} failed\n"
    
    # Append to log file
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry)
    
    print(f"\n📝 Log written to: {LOG_FILE}")


def load_existing_cards() -> dict:
    """Load existing cards from JSON file, indexed by card ID"""
    try:
        with open(OUTPUT_FILE, 'r') as f:
            data = json.load(f)
            return {card['id']: card for card in data.get('cards', [])}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def is_updated_today(card_data: dict) -> bool:
    """Check if a card was already updated today"""
    last_updated = card_data.get('last_updated')
    if not last_updated:
        return False
    
    try:
        updated_date = datetime.fromisoformat(last_updated).date()
        today = datetime.now().date()
        return updated_date == today
    except (ValueError, TypeError):
        return False


async def main():
    """Main function to update all cards"""
    print("=" * 60)
    print("🥷 CardNinja Card Updater")
    print("=" * 60)
    
    # Print current config
    config.print_config()
    
    # Validate config
    errors = config.validate()
    if errors:
        print("\n❌ Configuration errors:")
        for error in errors:
            print(f"   - {error}")
        print("\n📝 To fix: Copy config.example.env to .env and add your API key")
        print("   cp config.example.env .env")
        return
    
    # Check LLM availability
    print(f"\n📡 LLM Provider: {LLM_PROVIDER}")
    print(f"   Model: {LLM_MODEL}")
    
    if config.is_cloud_provider():
        num_keys = len(API_KEYS)
        if num_keys > 1:
            print(f"   ✅ Using cloud API ({LLM_PROVIDER}) with {num_keys} API keys (rotation enabled)")
        elif num_keys == 1:
            print(f"   ✅ Using cloud API ({LLM_PROVIDER}) with 1 API key")
        else:
            print(f"   ❌ No API keys configured for {LLM_PROVIDER}")
            print(f"   Add {LLM_PROVIDER.upper()}_API_KEY or {LLM_PROVIDER.upper()}_API_KEYS to backend/.env")
            return
    else:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                if LLM_PROVIDER == "ollama":
                    response = await client.get(f"{LLM_BASE_URL}/api/tags")
                    response.raise_for_status()
                    print("   ✅ Local LLM is available")
                else:
                    response = await client.get(f"{LLM_BASE_URL}/v1/models")
                    print("   ✅ Local LLM is available")
        except Exception as e:
            print(f"   ❌ Local LLM not available: {e}")
            print("\n⚠️  Without LLM, will use default card data.")
            print("   Start Ollama with: ollama serve")
    
    # Load existing cards data
    existing_cards = load_existing_cards()
    if existing_cards:
        print(f"\n📦 Found {len(existing_cards)} existing cards in database")
    
    # Load card sources
    print(f"\n📂 Loading card sources from: {SOURCES_FILE}")
    with open(SOURCES_FILE, 'r') as f:
        sources = json.load(f)
    
    print(f"   Found {len(sources['cards'])} cards to process")
    
    # Process each card
    cards_data = []
    updated_cards = []
    failed_cards = []
    skipped_cards = []
    
    # Build initial cards_data with all existing cards (so we don't lose data if killed)
    all_card_ids = [c["id"] for c in sources["cards"]]
    for card_id in all_card_ids:
        if card_id in existing_cards:
            cards_data.append(existing_cards[card_id])
        else:
            cards_data.append(None)  # Placeholder
    
    for idx, card_source in enumerate(sources["cards"]):
        card_id = card_source["id"]
        existing_card = existing_cards.get(card_id)
        
        # Check if card was already updated today
        if existing_card and is_updated_today(existing_card):
            print(f"\n⏭️  Skipping: {card_source['issuer']} {card_source['name']} (already updated today)")
            skipped_cards.append(card_source)
            continue
        
        # Update the card (pass existing card so we can preserve data on failure)
        card_data, success = await update_card(card_source, existing_card)
        cards_data[idx] = card_data  # Update in place
        
        if success:
            updated_cards.append(card_source)
        else:
            failed_cards.append(card_source)
        
        # Save progress after each card (so we don't lose work if killed)
        output_data = {
            "last_updated": datetime.now().isoformat(),
            "cards": [c for c in cards_data if c is not None]
        }
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"   💾 Progress saved ({len(updated_cards)} updated, {len(failed_cards)} failed)")
        
        # Delay between requests
        # With multiple keys, we can use shorter delays since we rotate on rate limits
        delay = config.SCRAPE_DELAY
        if len(API_KEYS) > 1 and delay > 60:
            delay = 60  # Use 1 min delay when key rotation is available
        
        print(f"   ⏳ Waiting {delay}s before next card...")
        await asyncio.sleep(delay)
    
    # Final save
    output_data = {
        "last_updated": datetime.now().isoformat(),
        "cards": [c for c in cards_data if c is not None]
    }
    
    print(f"\n💾 Final save to: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    # Write update log (only if we actually updated something)
    if updated_cards or failed_cards:
        write_update_log(updated_cards, failed_cards)
    
    print("\n" + "=" * 60)
    print("✅ Update complete!")
    print(f"   Total cards: {len(cards_data)}")
    print(f"   Skipped (already updated today): {len(skipped_cards)}")
    print(f"   Refreshed: {len(updated_cards)} succeeded, {len(failed_cards)} failed")
    print(f"   Output: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
