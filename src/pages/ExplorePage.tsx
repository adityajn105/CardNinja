import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { fetchAllCards, CreditCard } from '../api'
import CompareModal from '../components/CompareModal'
import './ExplorePage.css'

interface IssuerGroup {
  issuer: string
  cards: CreditCard[]
}

function ExplorePage() {
  const [allCards, setAllCards] = useState<CreditCard[]>([])
  const [cardsByIssuer, setCardsByIssuer] = useState<IssuerGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [compareMode, setCompareMode] = useState(false)
  const [selectedCards, setSelectedCards] = useState<Set<string>>(new Set())
  const [showCompareModal, setShowCompareModal] = useState(false)
  const [toast, setToast] = useState<string | null>(null)

  useEffect(() => {
    const loadCards = async () => {
      try {
        const cards = await fetchAllCards()
        setAllCards(cards)
        
        // Group cards by issuer
        const grouped: { [key: string]: CreditCard[] } = {}
        cards.forEach(card => {
          if (!grouped[card.issuer]) {
            grouped[card.issuer] = []
          }
          grouped[card.issuer].push(card)
        })
        
        // Convert to array and sort by issuer name
        const issuerGroups = Object.entries(grouped)
          .map(([issuer, cards]) => ({ issuer, cards }))
          .sort((a, b) => a.issuer.localeCompare(b.issuer))
        
        setCardsByIssuer(issuerGroups)
      } catch (error) {
        console.error('Failed to load cards:', error)
      } finally {
        setLoading(false)
      }
    }
    loadCards()
  }, [])

  // Show toast notification
  const showToast = (message: string) => {
    setToast(message)
    setTimeout(() => setToast(null), 3000)
  }

  // Toggle card selection
  const toggleCardSelection = (cardId: string) => {
    const newSelected = new Set(selectedCards)
    
    if (newSelected.has(cardId)) {
      newSelected.delete(cardId)
    } else {
      if (newSelected.size >= 3) {
        showToast('Cannot select more than 3 cards for comparison')
        return
      }
      newSelected.add(cardId)
    }
    
    setSelectedCards(newSelected)
  }

  // Deselect all cards
  const deselectAll = () => {
    setSelectedCards(new Set())
  }

  // Exit compare mode
  const exitCompareMode = () => {
    setCompareMode(false)
    setSelectedCards(new Set())
  }

  // Get top 3 cashback categories for a card
  const getTopCategories = (card: CreditCard) => {
    const categories = card.categories || {}
    return Object.entries(categories)
      .filter(([key]) => key !== 'other')
      .sort(([, a], [, b]) => b - a)
      .slice(0, 3)
      .filter(([, rate]) => rate > 1)
  }

  // Format category name
  const formatCategory = (cat: string) => {
    return cat.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  return (
    <div className="explore-page">
      <div className="background-gradient" />
      
      {/* Toast Notification */}
      {toast && (
        <div className="toast">
          <span className="toast-icon">⚠️</span>
          {toast}
        </div>
      )}
      
      <header className="explore-header">
        <Link to="/" className="back-link">
          <span>←</span> Back to Home
        </Link>
        <div className="header-content">
          <div className="logo">
            <span className="logo-icon">🥷</span>
            <h1>CardNinja</h1>
          </div>
          <h2>Explore All Cards</h2>
          <p className="subtitle">Browse credit cards</p>
        </div>
      </header>

      {/* Compare Cards Sidebar Button */}
      <div className="compare-sidebar">
        {!compareMode ? (
          <button 
            className="compare-toggle-btn"
            onClick={() => setCompareMode(true)}
          >
            <span className="compare-icon">⚖️</span>
            <span className="compare-text">Compare Cards</span>
          </button>
        ) : (
          <div className="compare-actions">
            <button 
              className="compare-btn deselect-btn"
              onClick={deselectAll}
            >
              Deselect
            </button>
            <button 
              className="compare-btn compare-now-btn"
              onClick={() => {
                if (selectedCards.size < 2) {
                  showToast('Select at least 2 cards to compare')
                } else {
                  setShowCompareModal(true)
                }
              }}
            >
              Compare
            </button>
            <button 
              className="compare-btn cancel-btn"
              onClick={exitCompareMode}
            >
              Cancel
            </button>
          </div>
        )}
      </div>

      <main className="explore-main">
        {loading ? (
          <div className="loading">
            <div className="loading-spinner" />
            <p>Loading cards...</p>
          </div>
        ) : (
          cardsByIssuer.map(({ issuer, cards }) => (
            <section key={issuer} className="issuer-section">
              <h3 className="issuer-title">
                <span className="issuer-name">{issuer}</span>
                <span className="card-count">{cards.length} cards</span>
              </h3>
              
              <div className="cards-grid">
                {cards.map(card => (
                  <div 
                    key={card.id} 
                    className={`explore-card ${compareMode ? 'compare-mode' : ''} ${selectedCards.has(card.id) ? 'selected' : ''}`}
                    onClick={compareMode ? () => toggleCardSelection(card.id) : undefined}
                  >
                    {/* Checkbox for compare mode */}
                    {compareMode && (
                      <div className="card-checkbox">
                        <input 
                          type="checkbox"
                          checked={selectedCards.has(card.id)}
                          onChange={() => toggleCardSelection(card.id)}
                          onClick={(e) => e.stopPropagation()}
                        />
                        <span className="checkmark">✓</span>
                      </div>
                    )}
                    
                    <div 
                      className="card-header"
                      style={{ backgroundColor: card.color || '#1a1a2e' }}
                    >
                      {card.image ? (
                        <img 
                          src={card.image} 
                          alt={card.name}
                          className="card-image"
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = 'none'
                          }}
                        />
                      ) : (
                        <div className="card-placeholder">
                          <span>{card.issuer.charAt(0)}</span>
                        </div>
                      )}
                    </div>
                    
                    <div className="card-body">
                      <h4 className="card-name">{card.name}</h4>
                      
                      <div className="card-fee">
                        <span className="fee-label">Annual Fee</span>
                        <span className="fee-value">
                          {card.annual_fee === 0 ? 'Free' : `$${card.annual_fee}`}
                        </span>
                      </div>
                      
                      <div className="card-rewards">
                        <span className="rewards-label">Top Rewards</span>
                        <div className="rewards-list">
                          {getTopCategories(card).length > 0 ? (
                            getTopCategories(card).map(([cat, rate]) => (
                              <div key={cat} className="reward-item">
                                <span className="reward-rate">{rate}%</span>
                                <span className="reward-cat">{formatCategory(cat)}</span>
                              </div>
                            ))
                          ) : (
                            <div className="reward-item">
                              <span className="reward-rate">{card.categories?.other || 1}%</span>
                              <span className="reward-cat">All Purchases</span>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {!compareMode && card.source_url && (
                        <button 
                          className="card-link"
                          onClick={(e) => {
                            e.stopPropagation();
                            e.preventDefault();
                            window.open(card.source_url, '_blank', 'noopener,noreferrer');
                          }}
                        >
                          Learn More →
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          ))
        )}
      </main>

      {/* Compare Modal */}
      {showCompareModal && (
        <CompareModal 
          cards={allCards.filter(card => selectedCards.has(card.id))}
          onClose={() => setShowCompareModal(false)}
        />
      )}
    </div>
  )
}

export default ExplorePage
