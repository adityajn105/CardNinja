"""LLM integration for local and cloud language models"""

import httpx
from typing import Optional

from config import config

# Use centralized config
LLM_PROVIDER = config.LLM_PROVIDER
LLM_BASE_URL = config.LLM_BASE_URL
LLM_MODEL = config.LLM_MODEL
GEMINI_API_KEY = config.GEMINI_API_KEY
GROQ_API_KEY = config.GROQ_API_KEY
MISTRAL_API_KEY = config.MISTRAL_API_KEY


async def get_llm_response(
    user_message: str,
    context: str,
    conversation_history: Optional[list] = None
) -> str:
    """Get response from LLM (local or cloud)"""
    
    if LLM_PROVIDER == "gemini":
        return await _gemini_chat(user_message, context, conversation_history)
    elif LLM_PROVIDER == "groq":
        return await _groq_chat(user_message, context, conversation_history)
    elif LLM_PROVIDER == "mistral":
        return await _mistral_chat(user_message, context, conversation_history)
    elif LLM_PROVIDER == "ollama":
        return await _ollama_chat(user_message, context, conversation_history)
    elif LLM_PROVIDER == "llamacpp":
        return await _llamacpp_chat(user_message, context, conversation_history)
    elif LLM_PROVIDER == "lmstudio":
        return await _openai_compatible_chat(user_message, context, conversation_history)
    else:
        # Fallback to simple response if no LLM available
        return _fallback_response(user_message, context)


async def _gemini_chat(
    user_message: str,
    context: str,
    conversation_history: Optional[list] = None
) -> str:
    """Chat using Google Gemini - FREE tier"""
    
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY not set")
        return _fallback_response(user_message, context)
    
    # Build conversation
    contents = []
    
    # Add system context as first user message
    contents.append({"role": "user", "parts": [{"text": context}]})
    contents.append({"role": "model", "parts": [{"text": "I understand. I'm CardNinja, ready to help you maximize your credit card rewards."}]})
    
    # Add conversation history
    if conversation_history:
        for msg in conversation_history[-6:]:
            role = "user" if msg.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})
    
    # Add current message
    contents.append({"role": "user", "parts": [{"text": user_message}]})
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{LLM_MODEL}:generateContent?key={GEMINI_API_KEY}",
                json={
                    "contents": contents,
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 1024,
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"Gemini error: {e}")
        return _fallback_response(user_message, context)


async def _groq_chat(
    user_message: str,
    context: str,
    conversation_history: Optional[list] = None
) -> str:
    """Chat using Groq - FREE tier, very fast"""
    
    if not GROQ_API_KEY:
        print("GROQ_API_KEY not set")
        return _fallback_response(user_message, context)
    
    messages = [{"role": "system", "content": context}]
    
    if conversation_history:
        for msg in conversation_history[-6:]:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
    
    messages.append({"role": "user", "content": user_message})
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={
                    "model": LLM_MODEL or "llama-3.1-70b-versatile",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1024
                }
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Groq error: {e}")
        return _fallback_response(user_message, context)


async def _mistral_chat(
    user_message: str,
    context: str,
    conversation_history: Optional[list] = None
) -> str:
    """Chat using Mistral AI - Free tier available"""
    
    if not MISTRAL_API_KEY:
        print("MISTRAL_API_KEY not set")
        return _fallback_response(user_message, context)
    
    messages = [{"role": "system", "content": context}]
    
    if conversation_history:
        for msg in conversation_history[-6:]:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
    
    messages.append({"role": "user", "content": user_message})
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {MISTRAL_API_KEY}"},
                json={
                    "model": LLM_MODEL or "mistral-small-latest",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1024
                }
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Mistral error: {e}")
        return _fallback_response(user_message, context)


async def _ollama_chat(
    user_message: str,
    context: str,
    conversation_history: Optional[list] = None
) -> str:
    """Chat using Ollama API"""
    
    messages = [{"role": "system", "content": context}]
    
    # Add conversation history
    if conversation_history:
        for msg in conversation_history[-6:]:  # Last 6 messages for context
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
    
    messages.append({"role": "user", "content": user_message})
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{LLM_BASE_URL}/api/chat",
                json={
                    "model": LLM_MODEL,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", _fallback_response(user_message, context))
    except Exception as e:
        print(f"Ollama error: {e}")
        return _fallback_response(user_message, context)


async def _llamacpp_chat(
    user_message: str,
    context: str,
    conversation_history: Optional[list] = None
) -> str:
    """Chat using llama.cpp server API"""
    
    # Build prompt
    prompt = f"{context}\n\n"
    
    if conversation_history:
        for msg in conversation_history[-6:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt += f"{role.capitalize()}: {content}\n"
    
    prompt += f"User: {user_message}\nAssistant:"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{LLM_BASE_URL}/completion",
                json={
                    "prompt": prompt,
                    "n_predict": 256,
                    "temperature": 0.7,
                    "stop": ["User:", "\n\n"]
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("content", _fallback_response(user_message, context))
    except Exception as e:
        print(f"llama.cpp error: {e}")
        return _fallback_response(user_message, context)


async def _openai_compatible_chat(
    user_message: str,
    context: str,
    conversation_history: Optional[list] = None
) -> str:
    """Chat using OpenAI-compatible API (LM Studio, vLLM, etc.)"""
    
    messages = [{"role": "system", "content": context}]
    
    if conversation_history:
        for msg in conversation_history[-6:]:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
    
    messages.append({"role": "user", "content": user_message})
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{LLM_BASE_URL}/v1/chat/completions",
                json={
                    "model": LLM_MODEL,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 256
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"OpenAI-compatible API error: {e}")
        return _fallback_response(user_message, context)


def _fallback_response(user_message: str, context: str) -> str:
    """Generate a simple fallback response when LLM is unavailable"""
    from credit_cards import get_best_card_for_query, get_top_cards_for_category
    
    # Check if query is about credit cards
    credit_keywords = [
        'card', 'credit', 'cash back', 'cashback', 'points', 'rewards', 'miles',
        'purchase', 'buy', 'spend', 'grocery', 'groceries', 'dining', 'restaurant',
        'travel', 'hotel', 'flight', 'gas', 'fuel', 'amazon', 'online', 'shopping',
        'streaming', 'netflix', 'uber', 'lyft', 'transit', 'drugstore', 'pharmacy',
        'best card', 'which card', 'recommend', 'annual fee', 'bonus', 'offer'
    ]
    
    user_lower = user_message.lower()
    is_credit_related = any(keyword in user_lower for keyword in credit_keywords)
    
    if not is_credit_related:
        return "🥷 I'm CardNinja, your credit card rewards expert! I specialize in helping you maximize points and cash back on your purchases. Ask me about which card to use for groceries, travel, dining, or any other spending category!"
    
    # Get recommendation from credit cards module
    recommendation = get_best_card_for_query(user_message)
    card = recommendation["card"]
    category = recommendation["category"]
    cashback = recommendation["cashback"]
    
    if category["id"] == "other":
        return "I'd be happy to help you find the best credit card! Could you tell me more specifically what you're looking to purchase? For example, is it groceries, dining, gas, travel, or online shopping?"
    
    # Get point value info
    point_value = card.get("point_value", {})
    reward_type = card.get("reward_type", "cashback")
    best_value = point_value.get("best_value", 1.0)
    best_redemption = point_value.get("best_redemption", "")
    
    # Get exclusions for this category
    exclusions = card.get("exclusions", {}).get(category["id"], [])
    spending_caps = card.get("spending_caps", {})
    
    # Check if user query mentions an excluded merchant
    excluded_merchants = ["target", "walmart", "costco", "sam's club", "bj's", "wholesale"]
    mentioned_exclusion = None
    for merchant in excluded_merchants:
        if merchant in user_lower:
            for exc in exclusions:
                if merchant in exc.lower():
                    mentioned_exclusion = merchant.title()
                    break
    
    # Get runner-up card
    top_cards = get_top_cards_for_category(category["id"], 2)
    runner_up = top_cards[1] if len(top_cards) > 1 else None
    
    # Build response
    if reward_type == "points" or reward_type == "miles":
        response = f"For **{category['name']}** purchases, I recommend the **{card['issuer']} {card['name']}** — you'll earn **{cashback}x {reward_type}**!\n\n"
    else:
        response = f"For **{category['name']}** purchases, I recommend the **{card['issuer']} {card['name']}** — you'll earn **{cashback}% cash back**!\n\n"
    
    # Warn about exclusion if detected
    if mentioned_exclusion:
        response += f"**⚠️ Warning:** {mentioned_exclusion} is typically **excluded** from this card's {category['name']} bonus! You'll only earn the base rate (1%).\n\n"
        if runner_up:
            runner_up_cashback = runner_up.get("categories", {}).get(category["id"], 1)
            response += f"**Better option for {mentioned_exclusion}:** Consider using **{runner_up['issuer']} {runner_up['name']}** or a flat-rate card instead.\n\n"
    else:
        response += f"**Why this card?** It offers the highest rewards rate in the {category['name']} category among your available cards."
    
    # Add exclusions warning
    if exclusions and not mentioned_exclusion:
        response += f"\n\n**⚠️ Note:** This card excludes: {', '.join(exclusions[:2])}."
    
    # Add spending cap warning
    cap_for_category = spending_caps.get(category["id"]) or spending_caps.get("top_category")
    if cap_for_category:
        response += f"\n\n**📊 Spending cap:** {cap_for_category}"
    
    # Add point value tip
    if best_value > 1.0 and best_redemption and not mentioned_exclusion:
        effective_rate = cashback * best_value
        response += f"\n\n**💡 Pro tip:** These {reward_type} can be worth up to **{best_value}¢ each** ({effective_rate}% effective return) when you {best_redemption.lower()}."
    
    if runner_up and not mentioned_exclusion:
        runner_up_cashback = runner_up.get("categories", {}).get(category["id"], 1)
        response += f"\n\n**Runner-up:** {runner_up['issuer']} {runner_up['name']} at {runner_up_cashback}% — a solid backup if the primary card is declined."
    
    return response


# Health check for LLM connection
async def check_llm_health() -> dict:
    """Check if the LLM backend is available"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            if LLM_PROVIDER == "gemini":
                if not GEMINI_API_KEY:
                    return {"status": "unhealthy", "error": "GEMINI_API_KEY not set", "provider": LLM_PROVIDER}
                # Quick test call
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{LLM_MODEL}:generateContent?key={GEMINI_API_KEY}",
                    json={"contents": [{"parts": [{"text": "Hi"}]}]}
                )
                response.raise_for_status()
                return {"status": "healthy", "provider": LLM_PROVIDER, "current_model": LLM_MODEL}
                
            elif LLM_PROVIDER == "groq":
                if not GROQ_API_KEY:
                    return {"status": "unhealthy", "error": "GROQ_API_KEY not set", "provider": LLM_PROVIDER}
                response = await client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {GROQ_API_KEY}"}
                )
                response.raise_for_status()
                return {"status": "healthy", "provider": LLM_PROVIDER, "current_model": LLM_MODEL}
                
            elif LLM_PROVIDER == "mistral":
                if not MISTRAL_API_KEY:
                    return {"status": "unhealthy", "error": "MISTRAL_API_KEY not set", "provider": LLM_PROVIDER}
                response = await client.get(
                    "https://api.mistral.ai/v1/models",
                    headers={"Authorization": f"Bearer {MISTRAL_API_KEY}"}
                )
                response.raise_for_status()
                return {"status": "healthy", "provider": LLM_PROVIDER, "current_model": LLM_MODEL}
                
            elif LLM_PROVIDER == "ollama":
                response = await client.get(f"{LLM_BASE_URL}/api/tags")
                response.raise_for_status()
                models = response.json().get("models", [])
                return {
                    "status": "healthy",
                    "provider": LLM_PROVIDER,
                    "models": [m["name"] for m in models],
                    "current_model": LLM_MODEL
                }
            else:
                response = await client.get(f"{LLM_BASE_URL}/health")
                return {"status": "healthy", "provider": LLM_PROVIDER}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "provider": LLM_PROVIDER}
