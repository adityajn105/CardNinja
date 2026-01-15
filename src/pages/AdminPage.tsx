import { useState, useEffect, useRef } from 'react'
import './AdminPage.css'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface CardSource {
  id: string
  name: string
  issuer: string
  color: string
  url: string
  image?: string
}

interface CardSourcesData {
  cards: CardSource[]
}

function AdminPage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState('')
  const [loading, setLoading] = useState<string | null>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)
  const [activeTab, setActiveTab] = useState<'logs' | 'sources'>('logs')
  const [cardSources, setCardSources] = useState<CardSourcesData | null>(null)
  const [editingCard, setEditingCard] = useState<CardSource | null>(null)
  const [isAddingCard, setIsAddingCard] = useState(false)
  const [selectedImage, setSelectedImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text })
    setTimeout(() => setMessage(null), 5000)
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoginError('')
    setLoading('login')
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/admin/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
      })
      
      const data = await response.json()
      
      if (data.success) {
        setIsAuthenticated(true)
        sessionStorage.setItem('adminAuth', password)
      } else {
        setLoginError('Invalid password')
      }
    } catch {
      setLoginError('Connection failed')
    } finally {
      setLoading(null)
    }
  }

  useEffect(() => {
    const savedPassword = sessionStorage.getItem('adminAuth')
    if (savedPassword) {
      setPassword(savedPassword)
      fetch(`${API_BASE_URL}/api/admin/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: savedPassword })
      })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            setIsAuthenticated(true)
          } else {
            sessionStorage.removeItem('adminAuth')
          }
        })
        .catch(() => sessionStorage.removeItem('adminAuth'))
    }
  }, [])

  const handleLogout = () => {
    setIsAuthenticated(false)
    setPassword('')
    sessionStorage.removeItem('adminAuth')
  }

  const apiCall = async (endpoint: string, method: string = 'POST', body?: object) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password, ...body })
    })
    return response.json()
  }

  const downloadFile = async (endpoint: string, filename: string) => {
    setLoading(endpoint)
    try {
      const data = await apiCall(endpoint)
      
      if (data.success) {
        const content = typeof data.content === 'string' 
          ? data.content 
          : JSON.stringify(data.content, null, 2)
        
        const blob = new Blob([content], { type: 'text/plain' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        
        showMessage('success', `Downloaded ${filename}`)
      } else {
        throw new Error(data.error || 'Download failed')
      }
    } catch (error) {
      showMessage('error', error instanceof Error ? error.message : 'Download failed')
    } finally {
      setLoading(null)
    }
  }

  const clearFile = async (endpoint: string, label: string) => {
    if (!confirm(`Are you sure you want to clear ${label}? This cannot be undone.`)) {
      return
    }
    
    setLoading(endpoint)
    try {
      const data = await apiCall(endpoint)
      
      if (data.success) {
        showMessage('success', data.message)
      } else {
        throw new Error(data.error || 'Clear failed')
      }
    } catch (error) {
      showMessage('error', error instanceof Error ? error.message : 'Clear failed')
    } finally {
      setLoading(null)
    }
  }

  const loadCardSources = async () => {
    setLoading('loadSources')
    try {
      const data = await apiCall('/api/admin/card-sources')
      if (data.success) {
        setCardSources(data.content)
      } else {
        throw new Error(data.error)
      }
    } catch (error) {
      showMessage('error', error instanceof Error ? error.message : 'Failed to load card sources')
    } finally {
      setLoading(null)
    }
  }

  const saveCardSources = async () => {
    if (!cardSources) return
    
    setLoading('saveSources')
    try {
      const data = await apiCall('/api/admin/card-sources/update', 'POST', { content: cardSources })
      if (data.success) {
        showMessage('success', data.message)
      } else {
        throw new Error(data.error)
      }
    } catch (error) {
      showMessage('error', error instanceof Error ? error.message : 'Failed to save card sources')
    } finally {
      setLoading(null)
    }
  }

  useEffect(() => {
    if (isAuthenticated && activeTab === 'sources' && !cardSources) {
      loadCardSources()
    }
  }, [isAuthenticated, activeTab])

  const handleCardEdit = (card: CardSource) => {
    setEditingCard({ ...card })
    setIsAddingCard(false)
    setSelectedImage(null)
    setImagePreview(null)
  }

  const handleCardAdd = () => {
    setEditingCard({
      id: '',
      name: '',
      issuer: '',
      color: '#1a365d',
      url: '',
      image: ''
    })
    setIsAddingCard(true)
    setSelectedImage(null)
    setImagePreview(null)
  }

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedImage(file)
      const reader = new FileReader()
      reader.onloadend = () => {
        setImagePreview(reader.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const uploadImage = async (filename: string): Promise<string | null> => {
    if (!selectedImage) return null
    
    const formData = new FormData()
    formData.append('password', password)
    formData.append('image', selectedImage)
    formData.append('filename', filename)
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/admin/upload-card-image`, {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      
      if (data.success) {
        return data.image_path
      } else {
        throw new Error(data.error)
      }
    } catch (error) {
      showMessage('error', error instanceof Error ? error.message : 'Failed to upload image')
      return null
    }
  }

  const handleCardSave = async () => {
    if (!editingCard || !cardSources) return
    
    setLoading('saveCard')
    
    // Generate ID from issuer and name if new
    let cardId = editingCard.id
    if (isAddingCard) {
      cardId = `${editingCard.issuer.toLowerCase().replace(/\s+/g, '-')}-${editingCard.name.toLowerCase().replace(/\s+/g, '-')}`
    }
    
    // Upload image if selected
    let imagePath = editingCard.image
    if (selectedImage) {
      const filename = `${editingCard.issuer.toLowerCase().replace(/\s+/g, '-')}-${editingCard.name.toLowerCase().replace(/\s+/g, '-')}`
      const uploadedPath = await uploadImage(filename)
      if (uploadedPath) {
        imagePath = uploadedPath
      }
    }
    
    const updatedCard = {
      ...editingCard,
      id: cardId,
      image: imagePath
    }
    
    if (isAddingCard) {
      setCardSources({
        cards: [...cardSources.cards, updatedCard]
      })
    } else {
      setCardSources({
        cards: cardSources.cards.map(c => c.id === editingCard.id ? updatedCard : c)
      })
    }
    
    setEditingCard(null)
    setIsAddingCard(false)
    setSelectedImage(null)
    setImagePreview(null)
    setLoading(null)
    
    showMessage('success', isAddingCard ? 'Card added (remember to Save Changes)' : 'Card updated (remember to Save Changes)')
  }

  const handleCardDelete = (cardId: string) => {
    if (!cardSources) return
    if (!confirm('Delete this card source?')) return
    
    setCardSources({
      cards: cardSources.cards.filter(c => c.id !== cardId)
    })
  }

  const closeEditModal = () => {
    setEditingCard(null)
    setIsAddingCard(false)
    setSelectedImage(null)
    setImagePreview(null)
  }

  // Login screen
  if (!isAuthenticated) {
    return (
      <div className="admin-page">
        <div className="login-container">
          <div className="login-header">
            <span className="admin-icon">🔐</span>
            <h1>Admin Access</h1>
          </div>
          
          <form onSubmit={handleLogin} className="login-form">
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter admin password"
              className="login-input"
              autoFocus
            />
            {loginError && <div className="login-error">{loginError}</div>}
            <button 
              type="submit" 
              className="login-btn"
              disabled={loading === 'login'}
            >
              {loading === 'login' ? <span className="spinner" /> : 'Access Admin Panel'}
            </button>
          </form>
          
          <a href="/" className="back-link">← Back to Home</a>
        </div>
      </div>
    )
  }

  return (
    <div className="admin-page">
      <div className="admin-container wide">
        <div className="admin-header">
          <span className="admin-icon">🔧</span>
          <h1>Admin Panel</h1>
          <button className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>

        {message && (
          <div className={`admin-message ${message.type}`}>
            {message.type === 'success' ? '✅' : '❌'} {message.text}
          </div>
        )}

        {/* Tabs */}
        <div className="admin-tabs">
          <button 
            className={`tab-btn ${activeTab === 'logs' ? 'active' : ''}`}
            onClick={() => setActiveTab('logs')}
          >
            📄 Logs & Data
          </button>
          <button 
            className={`tab-btn ${activeTab === 'sources' ? 'active' : ''}`}
            onClick={() => setActiveTab('sources')}
          >
            💳 Card Sources
          </button>
        </div>

        {/* Logs Tab */}
        {activeTab === 'logs' && (
          <div className="admin-sections">
            <section className="admin-section">
              <h2>📥 Download Files</h2>
              <div className="admin-buttons">
                <button
                  className="admin-btn download-btn"
                  onClick={() => downloadFile('/api/admin/logs/update', 'update_log.txt')}
                  disabled={loading !== null}
                >
                  {loading === '/api/admin/logs/update' ? <span className="spinner" /> : <span className="btn-icon">📄</span>}
                  <span className="btn-text">Download Update Log</span>
                  <span className="btn-hint">update_log.txt</span>
                </button>

                <button
                  className="admin-btn download-btn"
                  onClick={() => downloadFile('/api/admin/logs/chat', 'chat_sessions.json')}
                  disabled={loading !== null}
                >
                  {loading === '/api/admin/logs/chat' ? <span className="spinner" /> : <span className="btn-icon">💬</span>}
                  <span className="btn-text">Download Chat Sessions</span>
                  <span className="btn-hint">chat_sessions.json</span>
                </button>
              </div>
            </section>

            <section className="admin-section danger-section">
              <h2>🗑️ Clear Data</h2>
              <p className="danger-warning">⚠️ These actions cannot be undone!</p>
              <div className="admin-buttons">
                <button
                  className="admin-btn danger-btn"
                  onClick={() => clearFile('/api/admin/clear/update', 'Update Log')}
                  disabled={loading !== null}
                >
                  {loading === '/api/admin/clear/update' ? <span className="spinner" /> : <span className="btn-icon">🧹</span>}
                  <span className="btn-text">Clear Update Log</span>
                </button>

                <button
                  className="admin-btn danger-btn"
                  onClick={() => clearFile('/api/admin/clear/chat', 'Chat Sessions')}
                  disabled={loading !== null}
                >
                  {loading === '/api/admin/clear/chat' ? <span className="spinner" /> : <span className="btn-icon">🧹</span>}
                  <span className="btn-text">Clear Chat Sessions</span>
                </button>
              </div>
            </section>
          </div>
        )}

        {/* Card Sources Tab */}
        {activeTab === 'sources' && (
          <div className="sources-section">
            <div className="sources-header">
              <h2>💳 Card Sources ({cardSources?.cards.length || 0} cards)</h2>
              <div className="sources-actions">
                <button 
                  className="action-btn add-btn"
                  onClick={handleCardAdd}
                >
                  ➕ Add Card
                </button>
                <button 
                  className="action-btn refresh-btn"
                  onClick={loadCardSources}
                  disabled={loading === 'loadSources'}
                >
                  {loading === 'loadSources' ? <span className="spinner" /> : '🔄'} Reload
                </button>
                <button 
                  className="action-btn save-btn"
                  onClick={saveCardSources}
                  disabled={loading === 'saveSources'}
                >
                  {loading === 'saveSources' ? <span className="spinner" /> : '💾'} Save Changes
                </button>
              </div>
            </div>

            {/* Edit Modal */}
            {editingCard && (
              <div className="edit-modal-overlay" onClick={closeEditModal}>
                <div className="edit-modal" onClick={e => e.stopPropagation()}>
                  <h3>{isAddingCard ? 'Add New Card' : 'Edit Card'}</h3>
                  <div className="edit-form">
                    <label>
                      <span>Issuer</span>
                      <input
                        type="text"
                        value={editingCard.issuer}
                        onChange={e => setEditingCard({...editingCard, issuer: e.target.value})}
                        placeholder="e.g., Chase"
                      />
                    </label>
                    <label>
                      <span>Card Name</span>
                      <input
                        type="text"
                        value={editingCard.name}
                        onChange={e => setEditingCard({...editingCard, name: e.target.value})}
                        placeholder="e.g., Sapphire Preferred"
                      />
                    </label>
                    <label>
                      <span>URL</span>
                      <input
                        type="url"
                        value={editingCard.url}
                        onChange={e => setEditingCard({...editingCard, url: e.target.value})}
                        placeholder="https://..."
                      />
                    </label>
                    <label>
                      <span>Color</span>
                      <div className="color-input">
                        <input
                          type="color"
                          value={editingCard.color}
                          onChange={e => setEditingCard({...editingCard, color: e.target.value})}
                        />
                        <input
                          type="text"
                          value={editingCard.color}
                          onChange={e => setEditingCard({...editingCard, color: e.target.value})}
                        />
                      </div>
                    </label>
                    
                    {/* Image Section */}
                    <div className="image-section">
                      <span className="image-label">Card Image</span>
                      
                      {/* Show current image path only when editing */}
                      {!isAddingCard && editingCard.image && (
                        <div className="current-image">
                          <img 
                            src={editingCard.image} 
                            alt="Current card" 
                            onError={(e) => (e.target as HTMLImageElement).style.display = 'none'}
                          />
                          <span className="image-path">{editingCard.image}</span>
                        </div>
                      )}
                      
                      {/* Image preview for new upload */}
                      {imagePreview && (
                        <div className="image-preview">
                          <img src={imagePreview} alt="Preview" />
                          <span className="preview-label">New image to upload</span>
                        </div>
                      )}
                      
                      {/* Upload button */}
                      <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleImageSelect}
                        accept="image/*"
                        style={{ display: 'none' }}
                      />
                      <button 
                        type="button"
                        className="upload-btn"
                        onClick={() => fileInputRef.current?.click()}
                      >
                        📤 {isAddingCard ? 'Upload Image' : 'Upload New Image'}
                      </button>
                      {isAddingCard && (
                        <span className="upload-hint">
                          Image will be saved as: {editingCard.issuer && editingCard.name 
                            ? `${editingCard.issuer.toLowerCase().replace(/\s+/g, '-')}-${editingCard.name.toLowerCase().replace(/\s+/g, '-')}.png`
                            : 'issuer-card-name.png'}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="edit-actions">
                    <button className="cancel-btn" onClick={closeEditModal}>Cancel</button>
                    <button 
                      className="save-btn" 
                      onClick={handleCardSave}
                      disabled={loading === 'saveCard'}
                    >
                      {loading === 'saveCard' ? <span className="spinner" /> : (isAddingCard ? 'Add Card' : 'Save Changes')}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Cards List */}
            <div className="sources-list">
              {cardSources?.cards.map(card => (
                <div key={card.id} className="source-card">
                  {/* Card Image */}
                  <div className="card-image-thumb">
                    {card.image ? (
                      <img 
                        src={card.image} 
                        alt={card.name}
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = 'none'
                          const parent = (e.target as HTMLImageElement).parentElement
                          if (parent) {
                            parent.innerHTML = `<div class="card-image-fallback" style="background:${card.color}">${card.issuer.charAt(0)}</div>`
                          }
                        }}
                      />
                    ) : (
                      <div 
                        className="card-image-fallback"
                        style={{ backgroundColor: card.color }}
                      >
                        {card.issuer.charAt(0)}
                      </div>
                    )}
                  </div>
                  <div 
                    className="card-color-bar"
                    style={{ backgroundColor: card.color }}
                  />
                  <div className="card-info">
                    <div className="card-issuer">{card.issuer}</div>
                    <div className="card-name">{card.name}</div>
                    <a href={card.url} target="_blank" rel="noopener noreferrer" className="card-url">
                      {card.url.substring(0, 40)}...
                    </a>
                  </div>
                  <div className="card-actions">
                    <button className="edit-btn" onClick={() => handleCardEdit(card)}>✏️</button>
                    <button className="delete-btn" onClick={() => handleCardDelete(card.id)}>🗑️</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="admin-footer">
          <a href="/" className="back-link">← Back to Home</a>
        </div>
      </div>
    </div>
  )
}

export default AdminPage
