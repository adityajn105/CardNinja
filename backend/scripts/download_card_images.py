#!/usr/bin/env python3
"""
CardNinja - Card Image Downloader

Downloads credit card images from issuer websites.
Falls back to placeholder if image cannot be found.

Usage:
    python scripts/download_card_images.py
"""

import json
import httpx
import asyncio
import re
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config

DATA_DIR = config.DATA_DIR
SOURCES_FILE = config.CARD_SOURCES_FILE
IMAGES_DIR = Path(__file__).parent.parent.parent / "public" / "card-images"

# Ensure images directory exists
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Common patterns for card images on issuer sites
IMAGE_PATTERNS = [
    r'card.*\.png',
    r'card.*\.jpg',
    r'card.*\.webp',
    r'credit.*card.*\.png',
    r'product.*\.png',
    r'hero.*\.png',
    r'primary.*\.png',
]

# User agent for requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


async def find_card_image_url(page_url: str, card_name: str) -> str | None:
    """Try to find a card image URL from the page"""
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(page_url, headers=HEADERS)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Strategy 1: Look for og:image meta tag (often has card image)
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                img_url = og_image['content']
                if 'card' in img_url.lower() or 'product' in img_url.lower():
                    return img_url
            
            # Strategy 2: Find images with card-related attributes
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                alt = (img.get('alt') or '').lower()
                cls = ' '.join(img.get('class', [])).lower()
                
                if not src:
                    continue
                
                # Check if this looks like a card image
                src_lower = src.lower()
                is_card_image = any([
                    'card' in src_lower and ('png' in src_lower or 'jpg' in src_lower or 'webp' in src_lower),
                    'card' in alt,
                    'card' in cls,
                    'product' in src_lower and 'card' in alt,
                    card_name.lower().replace(' ', '-') in src_lower,
                    card_name.lower().replace(' ', '_') in src_lower,
                ])
                
                if is_card_image:
                    # Make absolute URL
                    full_url = urljoin(page_url, src)
                    # Skip tiny images (likely icons)
                    width = img.get('width')
                    if width and int(width) < 100:
                        continue
                    return full_url
            
            # Strategy 3: Look for picture/source elements
            for picture in soup.find_all('picture'):
                for source in picture.find_all('source'):
                    srcset = source.get('srcset', '')
                    if 'card' in srcset.lower():
                        # Get first URL from srcset
                        first_url = srcset.split(',')[0].split()[0]
                        return urljoin(page_url, first_url)
            
            # Strategy 4: Look for background images in style attributes
            for elem in soup.find_all(style=True):
                style = elem.get('style', '')
                if 'card' in style.lower() and 'url(' in style:
                    match = re.search(r'url\(["\']?([^"\'()]+)["\']?\)', style)
                    if match:
                        return urljoin(page_url, match.group(1))
            
            return None
            
    except Exception as e:
        print(f"      Error fetching page: {e}")
        return None


async def download_image(url: str, save_path: Path) -> bool:
    """Download an image from URL and save it"""
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers=HEADERS)
            response.raise_for_status()
            
            # Check if it's actually an image
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                print(f"      Not an image: {content_type}")
                return False
            
            # Determine file extension
            if 'png' in content_type:
                ext = '.png'
            elif 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'webp' in content_type:
                ext = '.webp'
            else:
                ext = '.png'  # Default
            
            # Update save path with correct extension
            save_path = save_path.with_suffix(ext)
            
            # Check image size (skip if too small)
            if len(response.content) < 5000:  # Less than 5KB probably not a card image
                print(f"      Image too small: {len(response.content)} bytes")
                return False
            
            # Save image
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            print(f"      ✅ Saved: {save_path.name} ({len(response.content) // 1024}KB)")
            return True
            
    except Exception as e:
        print(f"      Error downloading: {e}")
        return False


async def process_card(card: dict) -> dict:
    """Process a single card - try to download its image"""
    card_id = card['id']
    card_name = card['name']
    issuer = card['issuer']
    url = card['url']
    
    print(f"\n📇 {issuer} {card_name}")
    print(f"   URL: {url}")
    
    # Check if we already have an image
    for ext in ['.png', '.jpg', '.webp']:
        existing = IMAGES_DIR / f"{card_id}{ext}"
        if existing.exists():
            print(f"   ✅ Image already exists: {existing.name}")
            return {**card, "image": f"/card-images/{existing.name}"}
    
    # Try to find and download card image
    print(f"   🔍 Searching for card image...")
    image_url = await find_card_image_url(url, card_name)
    
    if image_url:
        print(f"   📸 Found: {image_url[:80]}...")
        save_path = IMAGES_DIR / f"{card_id}.png"
        
        if await download_image(image_url, save_path):
            # Find the actual saved file (extension might have changed)
            for ext in ['.png', '.jpg', '.webp']:
                saved = IMAGES_DIR / f"{card_id}{ext}"
                if saved.exists():
                    return {**card, "image": f"/card-images/{saved.name}"}
    
    print(f"   ⚠️  No image found - will use CSS fallback")
    return {**card, "image": None}


async def main():
    """Main function to download all card images"""
    print("=" * 60)
    print("🥷 CardNinja - Card Image Downloader")
    print("=" * 60)
    
    # Load card sources
    print(f"\n📂 Loading card sources from: {SOURCES_FILE}")
    with open(SOURCES_FILE, 'r') as f:
        sources = json.load(f)
    
    cards = sources['cards']
    print(f"   Found {len(cards)} cards to process")
    
    # Process each card
    results = []
    downloaded = 0
    failed = 0
    
    for card in cards:
        result = await process_card(card)
        results.append(result)
        
        if result.get('image'):
            downloaded += 1
        else:
            failed += 1
        
        # Small delay between requests
        await asyncio.sleep(1.0)
    
    # Save updated sources with image paths
    updated_sources = {"cards": results}
    with open(SOURCES_FILE, 'w') as f:
        json.dump(updated_sources, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ Download complete!")
    print(f"   Downloaded: {downloaded} images")
    print(f"   Fallback (CSS): {failed} cards")
    print(f"   Images saved to: {IMAGES_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
