import { CreditCard, Category } from '../api'
import './CardRecommendation.css'

interface CardRecommendationProps {
  card: CreditCard
  category: Category
  rank: number
}

function CardRecommendation({ card, category, rank }: CardRecommendationProps) {
  const cashback = card.categories[category.id] || 1
  const annualFee = card.annual_fee ?? 0
  const specialOffers = card.special_offers || []

  return (
    <div 
      className={`card-recommendation ${rank === 1 ? 'top-pick' : ''}`}
      style={{ animationDelay: `${(rank - 1) * 0.1}s` }}
    >
      {rank === 1 && <div className="top-badge">Best Pick</div>}
      
      <div className="card-header">
        <div className="rank">#{rank}</div>
        {card.image ? (
          <div className="card-visual card-visual-image">
            <img 
              src={card.image} 
              alt={`${card.issuer} ${card.name}`}
              className="card-image"
              onError={(e) => {
                // Fallback to CSS design if image fails to load
                const target = e.currentTarget;
                target.style.display = 'none';
                const fallback = target.nextElementSibling as HTMLElement;
                if (fallback) fallback.style.display = 'flex';
              }}
            />
            <div 
              className="card-visual-fallback"
              style={{ 
                background: `linear-gradient(135deg, ${card.color}, ${card.color}cc)`,
                display: 'none'
              }}
            >
              <div className="card-chip" />
              <div className="card-issuer">{card.issuer}</div>
            </div>
          </div>
        ) : (
          <div 
            className="card-visual"
            style={{ background: `linear-gradient(135deg, ${card.color}, ${card.color}cc)` }}
          >
            <div className="card-chip" />
            <div className="card-issuer">{card.issuer}</div>
          </div>
        )}
      </div>

      <div className="card-info">
        <h3 className="card-name">
          {card.source_url ? (
            <a href={card.source_url} target="_blank" rel="noopener noreferrer">
              {card.name}
            </a>
          ) : (
            card.name
          )}
        </h3>
        <p className="card-issuer-name">{card.issuer}</p>
        
        <div className="cashback-display">
          <span className="cashback-value">{cashback}%</span>
          <span className="cashback-label">cash back</span>
        </div>

        <div className="card-details">
          <div className="detail">
            <span className="detail-label">Annual Fee</span>
            <span className="detail-value">
              {annualFee === 0 ? 'Free' : `$${annualFee}`}
            </span>
          </div>
        </div>

        {specialOffers.length > 0 && (
          <div className="special-offers">
            <span className="offers-label">Highlights</span>
            <ul className="offers-list">
              {specialOffers.slice(0, 2).map((offer, i) => (
                <li key={i}>{offer}</li>
              ))}
            </ul>
          </div>
        )}

        {card.source_url && (
          <a 
            href={card.source_url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="card-link-btn"
            title="Visit card page"
          >
            <span>Learn More</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </a>
        )}
      </div>
    </div>
  )
}

export default CardRecommendation
