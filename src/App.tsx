import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import './App.css'
import { fetchCategories, fetchCardsForCategory, Category, CreditCard } from './api'
import CategorySelector from './components/CategorySelector'
import CardRecommendation from './components/CardRecommendation'
import ChatAssistant from './components/ChatAssistant'
import ExplorePage from './pages/ExplorePage'
import AdminPage from './pages/AdminPage'

function HomePage() {
  const [categories, setCategories] = useState<Category[]>([])
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null)
  const [topCards, setTopCards] = useState<CreditCard[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingCards, setLoadingCards] = useState(false)

  // Fetch categories on mount
  useEffect(() => {
    const loadCategories = async () => {
      try {
        const data = await fetchCategories()
        setCategories(data)
      } catch (error) {
        console.error('Failed to load categories:', error)
      } finally {
        setLoading(false)
      }
    }
    loadCategories()
  }, [])

  // Fetch cards when category changes
  useEffect(() => {
    if (!selectedCategory) {
      setTopCards([])
      return
    }

    const loadCards = async () => {
      setLoadingCards(true)
      try {
        const data = await fetchCardsForCategory(selectedCategory.id, 3)
        setTopCards(data.cards)
      } catch (error) {
        console.error('Failed to load cards:', error)
        setTopCards([])
      } finally {
        setLoadingCards(false)
      }
    }
    loadCards()
  }, [selectedCategory])

  return (
    <div className="app">
      <div className="background-gradient" />
      
      <header className="header">
        <div className="logo">
          <span className="logo-icon">🥷</span>
          <h1>CardNinja</h1>
        </div>
        <p className="tagline">Maximize your rewards like a ninja</p>
        
        <Link to="/explore" className="explore-button">
          <span className="explore-icon">🎴</span>
          Explore All Cards
        </Link>
      </header>

      <main className="main-content">
        <section className="category-section">
          <h2>What are you buying?</h2>
          <p className="section-subtitle">Select a category to see the best cards</p>
          
          {loading ? (
            <div className="loading">Loading categories...</div>
          ) : (
            <CategorySelector 
              categories={categories}
              selectedCategory={selectedCategory}
              onSelect={setSelectedCategory}
            />
          )}
        </section>

        {selectedCategory && (
          <section className="recommendations-section animate-slide-up">
            <h2>
              Best cards for <span className="highlight">{selectedCategory.name}</span>
            </h2>
            <p className="section-subtitle">
              Ranked by cashback percentage for this category
            </p>
            
            {loadingCards ? (
              <div className="loading">Finding best cards...</div>
            ) : (
              <div className="cards-grid">
                {topCards.map((card, index) => (
                  <CardRecommendation 
                    key={card.id}
                    card={card}
                    category={selectedCategory}
                    rank={index + 1}
                  />
                ))}
              </div>
            )}
          </section>
        )}
      </main>

      <ChatAssistant />
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/explore" element={<ExplorePage />} />
        <Route path="/admin" element={<AdminPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
