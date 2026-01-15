"""Credit card data and recommendation logic"""

import json
from config import config

DATA_DIR = config.DATA_DIR
CARDS_FILE = config.CARDS_FILE

# Categories we track
categories = [
    {
        "id": "dining",
        "name": "Dining",
        "icon": "🍽️",
        "keywords": ["restaurant", "food", "eat", "dining", "cafe", "coffee", "doordash", 
                    "ubereats", "grubhub", "chipotle", "starbucks", "mcdonald", "lunch", "dinner"]
    },
    {
        "id": "groceries",
        "name": "Groceries",
        "icon": "🛒",
        "keywords": ["grocery", "groceries", "supermarket", "whole foods", "trader joe", 
                    "safeway", "kroger", "costco", "walmart grocery", "target grocery", "food store"]
    },
    {
        "id": "travel",
        "name": "Travel",
        "icon": "✈️",
        "keywords": ["flight", "airline", "hotel", "airbnb", "travel", "vacation", "delta", 
                    "united", "american airlines", "southwest", "marriott", "hilton", "expedia", "booking"]
    },
    {
        "id": "gas",
        "name": "Gas",
        "icon": "⛽",
        "keywords": ["gas", "fuel", "gas station", "shell", "chevron", "exxon", "mobil", "bp", "costco gas"]
    },
    {
        "id": "streaming",
        "name": "Streaming",
        "icon": "📺",
        "keywords": ["netflix", "hulu", "disney", "hbo", "spotify", "apple music", "youtube", 
                    "streaming", "subscription", "amazon prime video"]
    },
    {
        "id": "online_shopping",
        "name": "Online Shopping",
        "icon": "🛍️",
        "keywords": ["amazon", "online", "ebay", "etsy", "wayfair", "target", "walmart", 
                    "best buy", "macy", "nordstrom", "zappos", "shopping", "ecommerce"]
    },
    {
        "id": "transit",
        "name": "Transit",
        "icon": "🚇",
        "keywords": ["uber", "lyft", "taxi", "transit", "subway", "metro", "bus", "train", "commute", "rideshare"]
    },
    {
        "id": "entertainment",
        "name": "Entertainment",
        "icon": "🎬",
        "keywords": ["movie", "theater", "concert", "entertainment", "event", "ticket", 
                    "ticketmaster", "stubhub", "amc", "regal"]
    },
    {
        "id": "drugstore",
        "name": "Drugstore",
        "icon": "💊",
        "keywords": ["cvs", "walgreens", "pharmacy", "drugstore", "rite aid", "medicine", "health"]
    },
    {
        "id": "other",
        "name": "Other",
        "icon": "💳",
        "keywords": []
    }
]


def load_credit_cards() -> list:
    """Load credit cards from JSON file"""
    try:
        with open(CARDS_FILE, 'r') as f:
            data = json.load(f)
            return data.get("cards", [])
    except FileNotFoundError:
        print(f"Warning: {CARDS_FILE} not found. Run 'python scripts/update_cards.py' to fetch card data.")
        return []
    except json.JSONDecodeError:
        print(f"Warning: {CARDS_FILE} is invalid JSON.")
        return []


def get_cards_last_updated() -> str:
    """Get the last updated timestamp from cards.json"""
    try:
        with open(CARDS_FILE, 'r') as f:
            data = json.load(f)
            return data.get("last_updated")
    except:
        return None


# Load cards on module import
credit_cards = load_credit_cards()


def reload_cards():
    """Reload cards from JSON file (useful after running update script)"""
    global credit_cards
    credit_cards = load_credit_cards()
    return credit_cards


def detect_category(query: str) -> dict:
    """Detect the spending category from a user query"""
    lower_query = query.lower()
    
    for category in categories:
        for keyword in category["keywords"]:
            if keyword.lower() in lower_query:
                return category
    
    return next(c for c in categories if c["id"] == "other")


def get_top_cards_for_category(category_id: str, limit: int = 3) -> list:
    """Get the top cards for a specific category, sorted by cashback"""
    if not credit_cards:
        return []
    
    sorted_cards = sorted(
        credit_cards,
        key=lambda c: c.get("categories", {}).get(category_id, 0),
        reverse=True
    )
    return sorted_cards[:limit]


def get_best_card_for_query(query: str) -> dict:
    """Get the best card recommendation for a user query"""
    category = detect_category(query)
    top_cards = get_top_cards_for_category(category["id"], 1)
    
    if not top_cards:
        return {
            "card": {
                "id": "none",
                "name": "No cards available",
                "issuer": "N/A",
                "categories": {},
                "annual_fee": 0
            },
            "category": category,
            "cashback": 0
        }
    
    card = top_cards[0]
    
    return {
        "card": card,
        "category": category,
        "cashback": card.get("categories", {}).get(category["id"], 1)
    }
