import { useState, useRef, useEffect, useCallback } from 'react'
import { sendChatMessage, ChatMessage, getLLMStatus, startNewSession } from '../api'
import './ChatAssistant.css'

const PLACEHOLDER_PROMPTS = [
  "Which card should I use for my weekly grocery run at Whole Foods?",
  "What is the best credit card for buying groceries at Trader Joe's or Kroger?",
  "Which card gives the highest cash back for household essentials at Walmart?",
  "Which card should I use for gas at Shell or Exxon to get the most points?",
  "What are the best credit card rewards for daily commuting on subways and buses?",
  "Which card is best for my morning tolls and parking garage fees?",
  "Which card should I use to book my upcoming stay at a Marriott or Hilton?",
  "What is the best credit card for booking international flights on United or Delta?",
  "Which card offers the best protection and rewards for booking an Airbnb?",
  "Which card should I use for concert tickets on Ticketmaster or Live Nation?",
  "What is the best card for dining out or ordering delivery through DoorDash?",
  "Which card gives the most rewards for a night out at the movie theater?",
  "Which card should I put my Netflix and Disney+ subscriptions on for maximum back?",
  "What is the best credit card for my monthly Spotify or Apple Music bill?",
  "Which card offers the best rewards for YouTube TV or Hulu + Live TV subscriptions?"
]

interface Message {
  id: number
  type: 'user' | 'assistant'
  content: string
}

function getRandomPrompts(count: number): string[] {
  const shuffled = [...PLACEHOLDER_PROMPTS].sort(() => Math.random() - 0.5)
  return shuffled.slice(0, count)
}

function getWelcomeMessage(): Message {
  const [example1, example2] = getRandomPrompts(2)
  return {
    id: 0,
    type: 'assistant',
    content: `Hey! I'm your CardNinja assistant. Ask me which card to use for any purchase — like "${example1}" or "${example2}"`
  }
}

function ChatAssistant() {
  const [isExpanded, setIsExpanded] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [chatSize, setChatSize] = useState({ width: 380, height: 520 })
  const [isResizing, setIsResizing] = useState(false)
  const [messages, setMessages] = useState<Message[]>([getWelcomeMessage()])
  const [conversationHistory, setConversationHistory] = useState<ChatMessage[]>([])
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [llmName, setLlmName] = useState<string>('IntelliAgent')
  const [isLlmAvailable, setIsLlmAvailable] = useState<boolean>(false)
  const [placeholder, setPlaceholder] = useState<string>('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const chatContainerRef = useRef<HTMLDivElement>(null)
  const resizeStartRef = useRef<{ x: number; y: number; width: number; height: number } | null>(null)

  // Set random placeholder on mount
  useEffect(() => {
    const randomIndex = Math.floor(Math.random() * PLACEHOLDER_PROMPTS.length)
    setPlaceholder(PLACEHOLDER_PROMPTS[randomIndex])
  }, [])

  // Fetch LLM status on mount and when chat expands
  useEffect(() => {
    if (isExpanded) {
      getLLMStatus().then(status => {
        setLlmName(status.name)
        setIsLlmAvailable(status.available)
      })
    }
  }, [isExpanded])

  useEffect(() => {
    if (isExpanded && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isExpanded])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Handle resize drag
  const handleResizeStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsResizing(true)
    resizeStartRef.current = {
      x: e.clientX,
      y: e.clientY,
      width: chatSize.width,
      height: chatSize.height
    }
  }, [chatSize])

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing || !resizeStartRef.current) return
      
      const deltaX = resizeStartRef.current.x - e.clientX
      const deltaY = resizeStartRef.current.y - e.clientY
      
      const newWidth = Math.max(320, Math.min(800, resizeStartRef.current.width + deltaX))
      const newHeight = Math.max(400, Math.min(900, resizeStartRef.current.height + deltaY))
      
      setChatSize({ width: newWidth, height: newHeight })
    }

    const handleMouseUp = () => {
      setIsResizing(false)
      resizeStartRef.current = null
    }

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isResizing])

  const toggleFullscreen = useCallback(() => {
    setIsFullscreen(prev => !prev)
  }, [])

  const handleNewSession = useCallback(async () => {
    try {
      const response = await startNewSession()
      setSessionId(response.session_id)
      setMessages([getWelcomeMessage()])
      setConversationHistory([])
      setError(null)
      setPlaceholder(PLACEHOLDER_PROMPTS[Math.floor(Math.random() * PLACEHOLDER_PROMPTS.length)])
    } catch (err) {
      console.error('Failed to start new session:', err)
      // Still clear locally even if backend fails
      setSessionId(null)
      setMessages([getWelcomeMessage()])
      setConversationHistory([])
      setError(null)
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isTyping) return

    const userMessage = input.trim()
    setInput('')
    setError(null)

    // Add user message to display
    const userMsg: Message = {
      id: Date.now(),
      type: 'user',
      content: userMessage
    }
    setMessages(prev => [...prev, userMsg])
    setIsTyping(true)

    // Update conversation history
    const newHistory: ChatMessage[] = [
      ...conversationHistory,
      { role: 'user', content: userMessage }
    ]

    try {
      // Call Python backend with session ID
      const response = await sendChatMessage(userMessage, conversationHistory, sessionId || undefined)
      
      // Store session ID from response
      if (response.session_id) {
        setSessionId(response.session_id)
      }
      
      // Add assistant response
      const assistantMsg: Message = {
        id: Date.now() + 1,
        type: 'assistant',
        content: response.response
      }
      setMessages(prev => [...prev, assistantMsg])

      // Update conversation history with assistant response
      setConversationHistory([
        ...newHistory,
        { role: 'assistant', content: response.response }
      ])
    } catch (err) {
      console.error('Chat error:', err)
      setError('Failed to connect to the server. Make sure the Python backend is running.')
      
      // Add error message to chat
      const errorMsg: Message = {
        id: Date.now() + 1,
        type: 'assistant',
        content: "I'm having trouble connecting to my brain right now. Please make sure the backend server is running (`python backend/main.py`)."
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setIsTyping(false)
    }
  }

  // Card URLs for hyperlinking card names (longer names first to avoid partial matches)
  const CARD_LINKS: Array<{ name: string; url: string }> = [
    { name: 'Chase Sapphire Preferred', url: 'https://creditcards.chase.com/rewards-credit-cards/sapphire/preferred' },
    { name: 'Amex Blue Cash Preferred', url: 'https://www.americanexpress.com/us/credit-cards/card/blue-cash-preferred/' },
    { name: 'Chase Freedom Unlimited', url: 'https://creditcards.chase.com/cash-back-credit-cards/freedom/unlimited' },
    { name: 'American Express Gold', url: 'https://www.americanexpress.com/us/credit-cards/card/gold-card/' },
    { name: 'U.S. Bank Altitude Go', url: 'https://www.usbank.com/credit-cards/altitude-go-visa-signature-credit-card.html' },
    { name: 'Wells Fargo Autograph', url: 'https://www.wellsfargo.com/credit-cards/autograph-card/' },
    { name: 'Blue Cash Preferred', url: 'https://www.americanexpress.com/us/credit-cards/card/blue-cash-preferred/' },
    { name: 'Capital One Savor', url: 'https://www.capitalone.com/credit-cards/savor-dining-rewards/' },
    { name: 'Sapphire Preferred', url: 'https://creditcards.chase.com/rewards-credit-cards/sapphire/preferred' },
    { name: 'Amazon Prime Visa', url: 'https://www.amazon.com/dp/B007URFTYI' },
    { name: 'Freedom Unlimited', url: 'https://creditcards.chase.com/cash-back-credit-cards/freedom/unlimited' },
    { name: 'Citi Custom Cash', url: 'https://www.citi.com/credit-cards/citi-custom-cash-credit-card' },
    { name: 'Savor Rewards', url: 'https://www.capitalone.com/credit-cards/savor-dining-rewards/' },
    { name: 'Altitude Go', url: 'https://www.usbank.com/credit-cards/altitude-go-visa-signature-credit-card.html' },
    { name: 'Custom Cash', url: 'https://www.citi.com/credit-cards/citi-custom-cash-credit-card' },
    { name: 'Prime Visa', url: 'https://www.amazon.com/dp/B007URFTYI' },
    { name: 'Discover it', url: 'https://www.discover.com/credit-cards/cash-back/it-card.html' },
    { name: 'Amex Gold', url: 'https://www.americanexpress.com/us/credit-cards/card/gold-card/' },
  ]

  const formatMessage = (content: string) => {
    let formatted = content
    
    // Remove any raw URLs that the LLM included
    formatted = formatted.replace(/https?:\/\/[^\s<>)\]"]+/g, '')
    
    // Clean up broken HTML fragments
    formatted = formatted.replace(/" target="_blank"[^>]*>/g, '')
    formatted = formatted.replace(/rel="noopener noreferrer">/g, '')
    
    // Convert markdown links [text](url) - but URLs were removed, so skip this
    formatted = formatted.replace(/\[([^\]]+)\]\(\s*\)/g, '$1')
    
    // Hyperlink card names
    for (const card of CARD_LINKS) {
      const escapedName = card.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      const regex = new RegExp(`(?<![">])\\b(${escapedName})\\b(?![^<]*<\\/a>)`, 'gi')
      formatted = formatted.replace(regex, `<a href="${card.url}" target="_blank" rel="noopener noreferrer">$1</a>`)
    }
    
    // Bold and italic
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    formatted = formatted.replace(/\*(.+?)\*/g, '<em>$1</em>')
    
    // Line breaks
    formatted = formatted.replace(/\n/g, '<br/>')
    
    return formatted
  }

  return (
    <div className={`chat-assistant ${isExpanded ? 'expanded' : ''} ${isFullscreen ? 'fullscreen' : ''}`}>
      {!isExpanded && (
        <button 
          className="chat-toggle"
          onClick={() => setIsExpanded(true)}
          aria-label="Open chat"
        >
          <span className="toggle-icon">💬</span>
          <span className="toggle-text">Ask me</span>
        </button>
      )}

      {isExpanded && (
        <div 
          ref={chatContainerRef}
          className={`chat-container ${isResizing ? 'resizing' : ''}`}
          style={!isFullscreen ? { width: chatSize.width, height: chatSize.height } : undefined}
        >
          {/* Resize handle (top-left corner) */}
          {!isFullscreen && (
            <div 
              className="resize-handle"
              onMouseDown={handleResizeStart}
            />
          )}
          
          {/* Header buttons - side by side */}
          <div className="header-buttons">
            <button 
              className="fullscreen-btn"
              onClick={toggleFullscreen}
              title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
            >
              {isFullscreen ? (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"/>
                </svg>
              ) : (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>
                </svg>
              )}
            </button>
            <button 
              className="chat-toggle"
              onClick={() => setIsExpanded(false)}
              aria-label="Close chat"
            >
              <span className="toggle-icon">×</span>
            </button>
          </div>
          
          <div className="chat-header">
            <div className="chat-title">
              <span className="assistant-avatar">🤖</span>
              <div>
                <h3>CardNinja Assistant</h3>
                <span className={`status ${isLlmAvailable ? 'online' : 'fallback'}`}>Powered by {llmName}</span>
              </div>
            </div>
          </div>

          <div className="messages-container">
            {messages.map((msg) => (
              <div 
                key={msg.id} 
                className={`message ${msg.type}`}
              >
                {msg.type === 'assistant' && (
                  <span className="message-avatar">🤖</span>
                )}
                <div 
                  className="message-content"
                  dangerouslySetInnerHTML={{ __html: formatMessage(msg.content) }}
                />
              </div>
            ))}
            
            {isTyping && (
              <div className="message assistant">
                <span className="message-avatar">🤖</span>
                <div className="message-content typing">
                  <span className="dot"></span>
                  <span className="dot"></span>
                  <span className="dot"></span>
                </div>
              </div>
            )}
            
            {error && (
              <div className="error-message">
                {error}
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          <form className="chat-input-form" onSubmit={handleSubmit}>
            <button 
              type="button"
              className="new-chat-btn"
              onClick={handleNewSession}
              title="Clear and start a new chat"
              disabled={isTyping}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 20h9"/>
                <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
              </svg>
              <span className="tooltip">Clear and start a new chat</span>
            </button>
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={placeholder}
              className="chat-input"
              disabled={isTyping}
            />
            <button type="submit" className="send-btn" disabled={!input.trim() || isTyping}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
              </svg>
            </button>
          </form>
        </div>
      )}
    </div>
  )
}

export default ChatAssistant
