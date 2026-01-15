import { Category } from '../api'
import './CategorySelector.css'

interface CategorySelectorProps {
  categories: Category[]
  selectedCategory: Category | null
  onSelect: (category: Category) => void
}

function CategorySelector({ categories, selectedCategory, onSelect }: CategorySelectorProps) {
  // Filter out 'other' category from display
  const displayCategories = categories.filter(c => c.id !== 'other')

  return (
    <div className="category-selector">
      {displayCategories.map((category, index) => (
        <button
          key={category.id}
          className={`category-btn ${selectedCategory?.id === category.id ? 'selected' : ''}`}
          onClick={() => onSelect(category)}
          style={{ animationDelay: `${index * 0.05}s` }}
        >
          <span className="category-icon">{category.icon}</span>
          <span className="category-name">{category.name}</span>
        </button>
      ))}
    </div>
  )
}

export default CategorySelector
