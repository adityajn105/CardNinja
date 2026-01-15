const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  response: string;
  card_recommendation?: {
    card_name: string;
    issuer: string;
    cashback: number;
    category: string;
  };
  session_id: string;
}

export interface NewSessionResponse {
  session_id: string;
  message: string;
}

export interface Category {
  id: string;
  name: string;
  icon: string;
}

export interface CreditCard {
  id: string;
  name: string;
  issuer: string;
  color: string;
  image?: string;
  annual_fee: number;
  categories: { [key: string]: number };
  special_offers?: string[];
  source_url?: string;
  reward_type?: string;
  point_value?: {
    base_value: number;
    best_value: number;
    best_redemption: string;
  };
}

export async function fetchCategories(): Promise<Category[]> {
  const response = await fetch(`${API_BASE_URL}/api/categories`);
  if (!response.ok) throw new Error('Failed to fetch categories');
  return response.json();
}

export async function fetchCardsForCategory(categoryId: string, limit: number = 3): Promise<{ category_id: string; cards: CreditCard[] }> {
  const response = await fetch(`${API_BASE_URL}/api/cards/${categoryId}?limit=${limit}`);
  if (!response.ok) throw new Error('Failed to fetch cards');
  return response.json();
}

export async function fetchAllCards(): Promise<CreditCard[]> {
  const response = await fetch(`${API_BASE_URL}/api/cards`);
  if (!response.ok) throw new Error('Failed to fetch all cards');
  return response.json();
}

export async function sendChatMessage(
  message: string,
  conversationHistory: ChatMessage[] = [],
  sessionId?: string
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      conversation_history: conversationHistory.map(msg => ({
        role: msg.role,
        content: msg.content
      })),
      session_id: sessionId
    }),
  });
  
  if (!response.ok) throw new Error('Failed to send message');
  return response.json();
}

export async function startNewSession(): Promise<NewSessionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat/new`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  if (!response.ok) throw new Error('Failed to start new session');
  return response.json();
}

export async function checkHealth(): Promise<{ api: string; llm: { status: string; provider?: string; models?: string[] } }> {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  if (!response.ok) throw new Error('Health check failed');
  return response.json();
}

export interface LLMStatus {
  available: boolean;
  name: string;
  provider: string;
}

export async function getLLMStatus(): Promise<LLMStatus> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/llm-status`);
    if (!response.ok) throw new Error('Failed to get LLM status');
    return response.json();
  } catch {
    return { available: false, name: 'IntelliAgent', provider: 'fallback' };
  }
}
