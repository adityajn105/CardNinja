from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from pathlib import Path
import uvicorn
import json
import uuid
import os
import shutil

from config import config

# Session log file
CHAT_LOG_FILE = config.DATA_DIR / "chat_sessions.json"
from credit_cards import (
    get_best_card_for_query, get_top_cards_for_category, 
    categories, credit_cards, reload_cards, get_cards_last_updated
)
from llm import get_llm_response

app = FastAPI(title="CardNinja API")

# CORS for frontend (using config)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[list] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    card_recommendation: Optional[dict] = None
    session_id: str


class NewSessionResponse(BaseModel):
    session_id: str
    message: str


class CategoryRequest(BaseModel):
    category_id: str


def load_chat_sessions() -> dict:
    """Load existing chat sessions from file"""
    if CHAT_LOG_FILE.exists():
        try:
            with open(CHAT_LOG_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"sessions": {}}
    return {"sessions": {}}


def save_chat_sessions(data: dict):
    """Save chat sessions to file"""
    with open(CHAT_LOG_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def log_chat_message(session_id: str, role: str, content: str, model: str = None):
    """Log a chat message to the session"""
    sessions = load_chat_sessions()
    
    if session_id not in sessions["sessions"]:
        sessions["sessions"][session_id] = {
            "created_at": datetime.now().isoformat(),
            "model": model or f"{config.LLM_PROVIDER}/{config.LLM_MODEL}",
            "messages": []
        }
    
    message_entry = {
        "timestamp": datetime.now().isoformat(),
        "role": role,
        "content": content
    }
    
    # Add model info for assistant responses
    if role == "assistant" and model:
        message_entry["model"] = model
    
    sessions["sessions"][session_id]["messages"].append(message_entry)
    sessions["sessions"][session_id]["last_activity"] = datetime.now().isoformat()
    
    save_chat_sessions(sessions)


@app.get("/")
def root():
    return {"message": "CardNinja API", "version": "1.0.0"}


@app.get("/api/categories")
def get_categories():
    """Get all spending categories"""
    return [
        {"id": c["id"], "name": c["name"], "icon": c["icon"]}
        for c in categories
        if c["id"] != "other"
    ]


@app.get("/api/cards")
def get_cards():
    """Get all credit cards"""
    return credit_cards


@app.get("/api/cards/status")
def get_cards_status():
    """Get credit card data status"""
    return {
        "count": len(credit_cards),
        "last_updated": get_cards_last_updated(),
        "has_data": len(credit_cards) > 0
    }


@app.post("/api/cards/reload")
def reload_card_data():
    """Reload credit card data from JSON file"""
    cards = reload_cards()
    return {
        "success": True,
        "count": len(cards),
        "last_updated": get_cards_last_updated()
    }


@app.get("/api/cards/{category_id}")
def get_cards_for_category(category_id: str, limit: int = 3):
    """Get top cards for a specific category"""
    top_cards = get_top_cards_for_category(category_id, limit)
    return {
        "category_id": category_id,
        "cards": top_cards
    }


@app.post("/api/chat/new", response_model=NewSessionResponse)
async def new_session():
    """Start a new chat session"""
    session_id = str(uuid.uuid4())[:8]
    
    # Initialize session in log
    sessions = load_chat_sessions()
    sessions["sessions"][session_id] = {
        "created_at": datetime.now().isoformat(),
        "messages": []
    }
    save_chat_sessions(sessions)
    
    return NewSessionResponse(
        session_id=session_id,
        message="New session started"
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with the LLM assistant"""
    message = request.message
    history = request.conversation_history or []
    
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())[:8]
    
    # Get current model info
    current_model = f"{config.LLM_PROVIDER}/{config.LLM_MODEL}"
    
    # Log user message
    log_chat_message(session_id, "user", message, model=current_model)
    
    # Get card recommendation context
    recommendation = get_best_card_for_query(message)
    
    # Build context for LLM with user query included
    context = build_context(recommendation, message)
    
    # Get LLM response
    llm_response = await get_llm_response(message, context, history)
    
    # Log assistant response with model info
    log_chat_message(session_id, "assistant", llm_response, model=current_model)
    
    return ChatResponse(
        response=llm_response,
        card_recommendation={
            "card_name": recommendation["card"]["name"],
            "issuer": recommendation["card"]["issuer"],
            "cashback": recommendation["cashback"],
            "category": recommendation["category"]["name"]
        },
        session_id=session_id
    )


def build_context(recommendation: dict, user_query: str) -> str:
    """Build context string for LLM from recommendation data"""
    category = recommendation["category"]
    
    # Build card list with rewards for detected category
    cards_list = []
    for card in credit_cards:
        rewards = []
        # Get top categories for this card (above 1%)
        top_cats = sorted(
            [(cat_id, rate) for cat_id, rate in card.get("categories", {}).items() if rate > 1],
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        for cat_id, rate in top_cats:
            cat_name = next((c["name"] for c in categories if c["id"] == cat_id), cat_id)
            rewards.append(f"{rate}% on {cat_name}")
        
        # Add base rate
        base_rate = card.get("categories", {}).get("other", 1)
        rewards.append(f"{base_rate}% on everything else")
        
        # Add point value info
        point_value = card.get("point_value", {})
        reward_type = card.get("reward_type", "cashback")
        best_value = point_value.get("best_value", 1.0)
        best_redemption = point_value.get("best_redemption", "Statement credit")
        
        point_info = ""
        if reward_type == "points" and best_value > 1.0:
            point_info = f" [Points worth up to {best_value}¢ via {best_redemption}]"
        elif reward_type == "miles" and best_value > 1.0:
            point_info = f" [Miles worth up to {best_value}¢ via {best_redemption}]"
        
        # Add exclusions info
        exclusions = card.get("exclusions", {})
        exclusion_info = ""
        if exclusions:
            all_exclusions = []
            for cat, exc_list in exclusions.items():
                if exc_list:
                    all_exclusions.extend(exc_list[:2])  # Limit to avoid too long
            if all_exclusions:
                exclusion_info = f" ⚠️ EXCLUDES: {'; '.join(all_exclusions[:3])}"
        
        # Add spending caps
        caps = card.get("spending_caps", {})
        cap_info = ""
        if caps:
            cap_list = [f"{cat}: {cap}" for cat, cap in caps.items()]
            if cap_list:
                cap_info = f" [Caps: {', '.join(cap_list[:2])}]"
        
        # Add category details (what's covered/not covered)
        category_details = card.get("category_details", {})
        details_info = ""
        if category_details:
            details_parts = []
            for cat, details in category_details.items():
                not_covered = details.get("not_covered", [])
                if not_covered:
                    details_parts.append(f"{cat} NOT covered: {', '.join(not_covered[:3])}")
            if details_parts:
                details_info = f" 🚫 {'; '.join(details_parts)}"
        
        # Add important notes
        notes = card.get("notes", "")
        notes_info = f" ℹ️ {notes}" if notes and len(notes) < 100 else ""
        
        # Add source URL
        source_url = card.get("source_url", "")
        url_info = f" | URL: {source_url}" if source_url else ""
        
        cards_list.append(f"- {card['issuer']} {card['name']}: {', '.join(rewards)}.{point_info}{cap_info}{exclusion_info}{details_info}{notes_info}{url_info}")
    
    cards_text = "\n".join(cards_list)
    
    context = f"""### Role
You are a credit card rewards optimization expert called "CardNinja". Your goal is to help maximize cash back or points for every dollar spent based on the available credit cards.

### IMPORTANT - STAY ON TOPIC
You are CardNinja - a credit card rewards specialist. You ONLY answer questions about:
- Credit cards, rewards, points, cash back
- Card recommendations for purchases
- Card benefits, perks, and annual fees
- Spending categories and bonus rates
- Point redemption strategies

If someone asks about ANYTHING ELSE (politics, weather, coding, recipes, general knowledge, etc.), respond with:
"🥷 I'm CardNinja, your credit card rewards expert! I specialize in helping you maximize points and cash back on your purchases. Ask me about which card to use for groceries, travel, dining, or any other spending category!"

### Available Credit Cards
{cards_text}

### The Question
{user_query}

### Detected Category
Based on the query, the most likely spending category is: {category['name']}

### Instructions
1. First, check if the question is about credit cards/rewards. If NOT, politely redirect (see above).
2. Identify which card has the highest reward rate for this specific merchant or category.
3. Calculate the estimated rewards percentage and effective value (considering point valuations).
4. **CRITICAL - CHECK COVERAGE**: Look at the "NOT covered" notes for each card. For example:
   - Chase Sapphire 5x travel is ONLY through Chase Travel portal - Airbnb is NOT available there
   - Some grocery bonuses exclude Target, Walmart, wholesale clubs
   - If a merchant is NOT covered, DO NOT recommend that card for that bonus rate
5. If the recommended card doesn't actually cover the merchant, WARN the user and suggest an alternative.
6. Mention any spending caps that might affect the recommendation.
7. Briefly explain why this card is the best choice (e.g., category match, point value, special offers).
8. Mention the best way to redeem points for maximum value if applicable.
9. Mention a runner-up card as a backup option.
10. Keep your response concise, friendly, and actionable.
11. If the category is unclear, ask for clarification about what they're buying.

**IMPORTANT FACTS TO REMEMBER:**
- Chase Travel portal does NOT include Airbnb, VRBO, or vacation rentals
- Chase Sapphire earns 5x ONLY on Chase Travel portal bookings, 2x on direct travel purchases
- Amex grocery 4x excludes Target, Walmart, and wholesale clubs (Costco, Sam's Club)
- Discover/Citi rotating categories must be activated each quarter
"""
    
    return context


@app.get("/api/health")
async def health_check():
    """Check API and LLM health"""
    from llm import check_llm_health
    llm_status = await check_llm_health()
    return {
        "api": "healthy",
        "llm": llm_status
    }


@app.get("/api/llm-status")
async def llm_status():
    """Get current LLM status and model name"""
    from llm import check_llm_health, LLM_MODEL, LLM_PROVIDER
    health = await check_llm_health()
    
    if health.get("status") == "healthy":
        return {
            "available": True,
            "name": LLM_MODEL,
            "provider": LLM_PROVIDER
        }
    else:
        return {
            "available": False,
            "name": "IntelliAgent",
            "provider": "fallback"
        }


# ===================
# Admin Endpoints (Password Protected)
# ===================

UPDATE_LOG_FILE = config.DATA_DIR / "update_log.txt"
CARD_SOURCES_FILE = config.CARD_SOURCES_FILE


class AdminAuthRequest(BaseModel):
    password: str


class CardSourcesUpdateRequest(BaseModel):
    password: str
    content: dict


def verify_admin_password(password: str) -> bool:
    """Verify admin password"""
    if not config.ADMIN_PASSWORD:
        return False  # No password set = access denied
    return password == config.ADMIN_PASSWORD


@app.post("/api/admin/verify")
def verify_admin(request: AdminAuthRequest):
    """Verify admin password"""
    if verify_admin_password(request.password):
        return {"success": True, "message": "Access granted"}
    return JSONResponse(
        status_code=401,
        content={"success": False, "error": "Invalid password"}
    )


@app.post("/api/admin/logs/update")
def download_update_log(request: AdminAuthRequest):
    """Download the update log file (password protected)"""
    if not verify_admin_password(request.password):
        return JSONResponse(status_code=401, content={"error": "Invalid password"})
    
    if UPDATE_LOG_FILE.exists():
        content = UPDATE_LOG_FILE.read_text()
        return {"success": True, "content": content, "filename": "update_log.txt"}
    return JSONResponse(
        status_code=404,
        content={"error": "Update log file not found"}
    )


@app.post("/api/admin/logs/chat")
def download_chat_sessions(request: AdminAuthRequest):
    """Download the chat sessions file (password protected)"""
    if not verify_admin_password(request.password):
        return JSONResponse(status_code=401, content={"error": "Invalid password"})
    
    if CHAT_LOG_FILE.exists():
        with open(CHAT_LOG_FILE, 'r') as f:
            content = json.load(f)
        return {"success": True, "content": content, "filename": "chat_sessions.json"}
    return JSONResponse(
        status_code=404,
        content={"error": "Chat sessions file not found"}
    )


@app.post("/api/admin/clear/update")
def clear_update_log(request: AdminAuthRequest):
    """Clear the update log file (password protected)"""
    if not verify_admin_password(request.password):
        return JSONResponse(status_code=401, content={"error": "Invalid password"})
    
    try:
        if UPDATE_LOG_FILE.exists():
            backup_content = UPDATE_LOG_FILE.read_text()
            lines = len(backup_content.strip().split('\n')) if backup_content.strip() else 0
            UPDATE_LOG_FILE.write_text("")
            return {"success": True, "message": f"Update log cleared ({lines} lines removed)"}
        return {"success": True, "message": "Update log was already empty"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to clear update log: {str(e)}"}
        )


@app.post("/api/admin/clear/chat")
def clear_chat_sessions(request: AdminAuthRequest):
    """Clear the chat sessions file (password protected)"""
    if not verify_admin_password(request.password):
        return JSONResponse(status_code=401, content={"error": "Invalid password"})
    
    try:
        if CHAT_LOG_FILE.exists():
            with open(CHAT_LOG_FILE, 'r') as f:
                data = json.load(f)
            sessions_count = len(data.get('sessions', []))
            with open(CHAT_LOG_FILE, 'w') as f:
                json.dump({"sessions": []}, f, indent=2)
            return {"success": True, "message": f"Chat sessions cleared ({sessions_count} sessions removed)"}
        else:
            with open(CHAT_LOG_FILE, 'w') as f:
                json.dump({"sessions": []}, f, indent=2)
            return {"success": True, "message": "Chat sessions file created (was empty)"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to clear chat sessions: {str(e)}"}
        )


# Card Sources Management
@app.post("/api/admin/card-sources")
def get_card_sources(request: AdminAuthRequest):
    """Get card sources JSON (password protected)"""
    if not verify_admin_password(request.password):
        return JSONResponse(status_code=401, content={"error": "Invalid password"})
    
    try:
        if CARD_SOURCES_FILE.exists():
            with open(CARD_SOURCES_FILE, 'r') as f:
                content = json.load(f)
            return {"success": True, "content": content}
        return JSONResponse(
            status_code=404,
            content={"error": "Card sources file not found"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to read card sources: {str(e)}"}
        )


@app.post("/api/admin/card-sources/update")
def update_card_sources(request: CardSourcesUpdateRequest):
    """Update card sources JSON (password protected)"""
    if not verify_admin_password(request.password):
        return JSONResponse(status_code=401, content={"error": "Invalid password"})
    
    try:
        # Validate the content structure
        if "cards" not in request.content:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid format: missing 'cards' array"}
            )
        
        # Create backup
        if CARD_SOURCES_FILE.exists():
            backup_file = CARD_SOURCES_FILE.with_suffix('.json.backup')
            with open(CARD_SOURCES_FILE, 'r') as f:
                backup_content = f.read()
            with open(backup_file, 'w') as f:
                f.write(backup_content)
        
        # Save new content
        with open(CARD_SOURCES_FILE, 'w') as f:
            json.dump(request.content, f, indent=2)
        
        return {
            "success": True,
            "message": f"Card sources updated ({len(request.content['cards'])} cards)"
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to update card sources: {str(e)}"}
        )


# Card images directory
CARD_IMAGES_DIR = Path(__file__).parent.parent / "public" / "card-images"


@app.post("/api/admin/upload-card-image")
async def upload_card_image(
    password: str = Form(...),
    image: UploadFile = File(...),
    filename: str = Form(...)
):
    """Upload a card image (password protected)"""
    if not verify_admin_password(password):
        return JSONResponse(status_code=401, content={"error": "Invalid password"})
    
    try:
        # Ensure directory exists
        CARD_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        
        # Get file extension from uploaded file
        ext = Path(image.filename).suffix.lower() if image.filename else '.png'
        if ext not in ['.png', '.jpg', '.jpeg', '.webp', '.gif']:
            ext = '.png'
        
        # Clean filename and add extension
        clean_filename = filename.lower().replace(' ', '-').replace('_', '-')
        if not clean_filename.endswith(ext):
            clean_filename = f"{clean_filename}{ext}"
        
        # Save file
        file_path = CARD_IMAGES_DIR / clean_filename
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(image.file, f)
        
        # Return the path to use in card_sources.json
        image_url = f"/card-images/{clean_filename}"
        
        return {
            "success": True,
            "message": f"Image uploaded successfully",
            "image_path": image_url
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to upload image: {str(e)}"}
        )


if __name__ == "__main__":
    # Print config on startup
    config.print_config()
    errors = config.validate()
    if errors:
        print("\n⚠️  Configuration warnings:")
        for error in errors:
            print(f"   - {error}")
        print()
    
    uvicorn.run("main:app", host=config.API_HOST, port=config.API_PORT, reload=True)
