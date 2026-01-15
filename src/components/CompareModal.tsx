import { CreditCard } from '../api'
import './CompareModal.css'

interface CompareModalProps {
  cards: CreditCard[]
  onClose: () => void
}

function CompareModal({ cards, onClose }: CompareModalProps) {
  // Get all unique categories across all cards
  const allCategories = new Set<string>()
  cards.forEach(card => {
    Object.keys(card.categories || {}).forEach(cat => allCategories.add(cat))
  })
  const categoryList = Array.from(allCategories).filter(c => c !== 'other')
  categoryList.push('other') // Add other at the end

  // Format category name
  const formatCategory = (cat: string) => {
    return cat.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  // Get best rate for a category across all cards
  const getBestRate = (category: string) => {
    return Math.max(...cards.map(c => c.categories?.[category] || 1))
  }

  return (
    <div className="compare-modal-overlay" onClick={onClose}>
      <div className="compare-modal" onClick={e => e.stopPropagation()}>
        <div className="compare-header">
          <h2>⚖️ Card Comparison</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="compare-content">
          <table className="compare-table">
            <thead>
              <tr>
                <th className="feature-col">Feature</th>
                {cards.map(card => (
                  <th key={card.id} className="card-col">
                    <div 
                      className="card-header-cell"
                      style={{ borderTopColor: card.color || '#00d4ff' }}
                    >
                      {card.image && (
                        <img 
                          src={card.image} 
                          alt={card.name}
                          className="card-thumb"
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = 'none'
                          }}
                        />
                      )}
                      <div className="card-info">
                        <span className="card-issuer">{card.issuer}</span>
                        <span className="card-name">{card.name}</span>
                      </div>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {/* Annual Fee */}
              <tr>
                <td className="feature-label">Annual Fee</td>
                {cards.map(card => (
                  <td key={card.id} className="feature-value">
                    <span className={card.annual_fee === 0 ? 'highlight-green' : ''}>
                      {card.annual_fee === 0 ? 'Free' : `$${card.annual_fee}`}
                    </span>
                  </td>
                ))}
              </tr>

              {/* Reward Type */}
              <tr>
                <td className="feature-label">Reward Type</td>
                {cards.map(card => (
                  <td key={card.id} className="feature-value">
                    {card.reward_type || 'Cashback'}
                  </td>
                ))}
              </tr>

              {/* Point Value */}
              <tr>
                <td className="feature-label">Point Value</td>
                {cards.map(card => (
                  <td key={card.id} className="feature-value">
                    {card.point_value ? (
                      <>
                        <span className="point-value">{card.point_value.best_value}¢</span>
                        <span className="point-note">{card.point_value.best_redemption}</span>
                      </>
                    ) : (
                      '1¢ per point'
                    )}
                  </td>
                ))}
              </tr>

              {/* Divider */}
              <tr className="section-divider">
                <td colSpan={cards.length + 1}>Reward Categories</td>
              </tr>

              {/* Categories */}
              {categoryList.map(category => {
                const bestRate = getBestRate(category)
                return (
                  <tr key={category}>
                    <td className="feature-label">{formatCategory(category)}</td>
                    {cards.map(card => {
                      const rate = card.categories?.[category] || 1
                      const isBest = rate === bestRate && rate > 1
                      return (
                        <td key={card.id} className="feature-value">
                          <span className={`rate ${isBest ? 'best-rate' : ''} ${rate > 1 ? 'bonus-rate' : ''}`}>
                            {rate}%
                          </span>
                        </td>
                      )
                    })}
                  </tr>
                )
              })}

              {/* Divider */}
              <tr className="section-divider">
                <td colSpan={cards.length + 1}>Benefits & Offers</td>
              </tr>

              {/* Special Offers */}
              <tr>
                <td className="feature-label">Sign-up Bonus</td>
                {cards.map(card => (
                  <td key={card.id} className="feature-value offers-cell">
                    {card.special_offers && card.special_offers.length > 0 ? (
                      <ul className="offers-list">
                        {card.special_offers.slice(0, 2).map((offer, i) => (
                          <li key={i}>{offer}</li>
                        ))}
                      </ul>
                    ) : (
                      <span className="no-data">—</span>
                    )}
                  </td>
                ))}
              </tr>

              {/* Card Link */}
              <tr>
                <td className="feature-label">Learn More</td>
                {cards.map(card => (
                  <td key={card.id} className="feature-value">
                    {card.source_url ? (
                      <a 
                        href={card.source_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="card-link-btn"
                      >
                        View Card →
                      </a>
                    ) : (
                      <span className="no-data">—</span>
                    )}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default CompareModal
