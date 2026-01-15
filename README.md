# CardNinja 🥷

A minimalist web app to maximize your credit card rewards, powered by AI.

## Features

- **Category Selection**: Browse purchase categories (Dining, Groceries, Travel, Gas, etc.) to see the best cards ranked by cashback
- **AI Assistant**: Chat interface powered by LLM (Gemini, Groq, or local models) to ask natural language questions
- **10+ Credit Cards**: Database of popular rewards cards with accurate cashback rates
- **Minimalist Design**: Dark theme with elegant typography and smooth animations

## Quick Start

### 1. Install Dependencies

```bash
# Frontend
npm install

# Backend
cd backend
pip install -r requirements.txt
```

### 2. Set Up LLM

Choose one of these options:

**Option A: Free Cloud APIs (Recommended)**
```bash
# 1. Get a free API key from one of:
#    - Gemini: https://aistudio.google.com/apikey
#    - Groq: https://console.groq.com/keys

# 2. Configure backend
cd backend
cp config.example.env .env
# Edit .env and add your API key
```

**Option B: Ollama (Local)**
```bash
# Install Ollama from https://ollama.ai
# Then pull a model:
ollama pull llama3.2
```

**Option C: LM Studio**
- Download from https://lmstudio.ai
- Load a model and start the server

### 3. Configure Backend

Create `backend/.env` to customize:
```
LLM_PROVIDER=groq
GROQ_API_KEY=your_key_here
LLM_MODEL=llama-3.3-70b-versatile
```

### 4. Run the App

```bash
# Terminal 1: Start backend
cd backend
python main.py

# Terminal 2: Start frontend
npm run dev
```

Visit **http://localhost:3000**

## Architecture

```
CardNinja/
├── backend/
│   ├── main.py              # API endpoints
│   ├── credit_cards.py      # Card logic (reads from JSON)
│   ├── llm.py               # LLM integration
│   ├── config.py            # Configuration
│   ├── data/
│   │   ├── cards.json       # Credit card data (auto-updated)
│   │   ├── card_sources.json # Card URLs for scraping
│   │   ├── chat_sessions.json # Chat logs
│   │   └── update_log.txt   # Update history
│   └── scripts/
│       └── update_cards.py  # Scraper script
├── src/                     # React frontend
│   ├── components/          # UI components
│   └── api/                 # API client
└── package.json
```

## Updating Card Data

Card reward data is stored in `backend/data/cards.json`. To update it with fresh data from issuer websites:

```bash
cd backend
python scripts/update_cards.py
```

This script:
1. Reads card URLs from `data/card_sources.json`
2. Scrapes each issuer's website (including sub-pages)
3. Uses LLM to extract reward percentages, exclusions, and caps
4. Saves structured data to `data/cards.json`
5. Logs update results to `data/update_log.txt`

**Add a new card:**
1. Edit `backend/data/card_sources.json`
2. Add card info with URL
3. Run `python scripts/update_cards.py`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/categories` | List all spending categories |
| GET | `/api/cards` | List all credit cards |
| GET | `/api/cards/{category_id}` | Get top cards for a category |
| POST | `/api/chat` | Chat with LLM assistant |
| POST | `/api/chat/new` | Start new chat session |
| GET | `/api/llm-status` | Get LLM model info |
| GET | `/api/health` | Check API and LLM status |

## Supported LLM Providers

### ☁️ Free Cloud APIs (Recommended)

| Provider | Free Tier | How to Get Key |
|----------|-----------|----------------|
| **Google Gemini** | 15 RPM, 1M tokens/day | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| **Groq** | Very fast, generous limits | [console.groq.com/keys](https://console.groq.com/keys) |
| **Mistral AI** | Free tier available | [console.mistral.ai](https://console.mistral.ai/) |

**Setup:**
```bash
# 1. Copy the example config
cd backend
cp config.example.env .env

# 2. Edit .env and add your API key
# For Groq (recommended):
GROQ_API_KEY=your_key_here
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
```

### 🖥️ Local Models

| Provider | Default URL | Config |
|----------|-------------|--------|
| Ollama | `http://localhost:11434` | `LLM_PROVIDER=ollama` |
| LM Studio | `http://localhost:1234` | `LLM_PROVIDER=lmstudio` |
| llama.cpp | `http://localhost:8080` | `LLM_PROVIDER=llamacpp` |

## Credit Cards Included

- Chase Sapphire Preferred
- American Express Gold
- Citi Custom Cash
- Discover it
- Amex Blue Cash Preferred
- Capital One Savor
- Amazon Prime Visa
- Chase Freedom Unlimited
- Wells Fargo Autograph
- U.S. Bank Altitude Go

## Usage Examples

Click any category button or ask the assistant:
- "What card for Amazon?"
- "Best card for restaurants?"
- "Which card should I use at Costco?"
- "I'm buying gas, what should I use?"

## Tech Stack

- **Frontend**: React 18, TypeScript, Vite
- **Backend**: Python, FastAPI, httpx
- **LLM**: Gemini / Groq / Mistral / Ollama

---

Built with 🥷 for maximizing rewards
