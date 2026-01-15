export interface CreditCard {
  id: string;
  name: string;
  issuer: string;
  color: string;
  image?: string; // URL to card image
  annualFee: number;
  categories: {
    [key: string]: number; // cashback percentage
  };
  specialOffers?: string[];
  source_url?: string; // URL to card details page
}

export interface Category {
  id: string;
  name: string;
  icon: string;
  keywords: string[];
}

export const categories: Category[] = [
  {
    id: 'dining',
    name: 'Dining',
    icon: '🍽️',
    keywords: ['restaurant', 'food', 'eat', 'dining', 'cafe', 'coffee', 'doordash', 'ubereats', 'grubhub', 'chipotle', 'starbucks', 'mcdonald']
  },
  {
    id: 'groceries',
    name: 'Groceries',
    icon: '🛒',
    keywords: ['grocery', 'groceries', 'supermarket', 'whole foods', 'trader joe', 'safeway', 'kroger', 'costco', 'walmart grocery', 'target grocery', 'food store']
  },
  {
    id: 'travel',
    name: 'Travel',
    icon: '✈️',
    keywords: ['flight', 'airline', 'hotel', 'airbnb', 'travel', 'vacation', 'delta', 'united', 'american airlines', 'southwest', 'marriott', 'hilton', 'expedia', 'booking']
  },
  {
    id: 'gas',
    name: 'Gas',
    icon: '⛽',
    keywords: ['gas', 'fuel', 'gas station', 'shell', 'chevron', 'exxon', 'mobil', 'bp', 'costco gas']
  },
  {
    id: 'streaming',
    name: 'Streaming',
    icon: '📺',
    keywords: ['netflix', 'hulu', 'disney', 'hbo', 'spotify', 'apple music', 'youtube', 'streaming', 'subscription', 'amazon prime video']
  },
  {
    id: 'online_shopping',
    name: 'Online Shopping',
    icon: '🛍️',
    keywords: ['amazon', 'online', 'ebay', 'etsy', 'wayfair', 'target', 'walmart', 'best buy', 'macy', 'nordstrom', 'zappos', 'shopping', 'ecommerce']
  },
  {
    id: 'transit',
    name: 'Transit',
    icon: '🚇',
    keywords: ['uber', 'lyft', 'taxi', 'transit', 'subway', 'metro', 'bus', 'train', 'commute', 'rideshare']
  },
  {
    id: 'entertainment',
    name: 'Entertainment',
    icon: '🎬',
    keywords: ['movie', 'theater', 'concert', 'entertainment', 'event', 'ticket', 'ticketmaster', 'stubhub', 'amc', 'regal']
  },
  {
    id: 'drugstore',
    name: 'Drugstore',
    icon: '💊',
    keywords: ['cvs', 'walgreens', 'pharmacy', 'drugstore', 'rite aid', 'medicine', 'health']
  },
  {
    id: 'other',
    name: 'Other',
    icon: '💳',
    keywords: []
  }
];

export const creditCards: CreditCard[] = [
  {
    id: 'chase-sapphire-preferred',
    name: 'Sapphire Preferred',
    issuer: 'Chase',
    color: '#1a365d',
    annualFee: 95,
    categories: {
      travel: 5,
      dining: 3,
      streaming: 3,
      online_shopping: 1,
      groceries: 1,
      gas: 1,
      transit: 1,
      entertainment: 1,
      drugstore: 1,
      other: 1
    },
    specialOffers: ['5x on travel through Chase portal', '3x on dining worldwide']
  },
  {
    id: 'amex-gold',
    name: 'Gold Card',
    issuer: 'American Express',
    color: '#c9a227',
    annualFee: 250,
    categories: {
      dining: 4,
      groceries: 4,
      travel: 3,
      streaming: 1,
      online_shopping: 1,
      gas: 1,
      transit: 1,
      entertainment: 1,
      drugstore: 1,
      other: 1
    },
    specialOffers: ['4x at restaurants', '4x at US supermarkets', '$120 dining credit', '$120 Uber credit']
  },
  {
    id: 'citi-custom-cash',
    name: 'Custom Cash',
    issuer: 'Citi',
    color: '#00558c',
    annualFee: 0,
    categories: {
      dining: 5,
      groceries: 5,
      gas: 5,
      transit: 5,
      streaming: 5,
      drugstore: 5,
      entertainment: 5,
      travel: 1,
      online_shopping: 1,
      other: 1
    },
    specialOffers: ['5% on top spending category (up to $500/month)', 'No annual fee']
  },
  {
    id: 'discover-it',
    name: 'Discover it',
    issuer: 'Discover',
    color: '#ff6600',
    annualFee: 0,
    categories: {
      dining: 5,
      groceries: 5,
      gas: 5,
      online_shopping: 5,
      streaming: 1,
      travel: 1,
      transit: 1,
      entertainment: 1,
      drugstore: 1,
      other: 1
    },
    specialOffers: ['5% rotating categories (up to $1,500/quarter)', 'Cashback match first year', 'No annual fee']
  },
  {
    id: 'amex-blue-cash-preferred',
    name: 'Blue Cash Preferred',
    issuer: 'American Express',
    color: '#006fcf',
    annualFee: 95,
    categories: {
      groceries: 6,
      streaming: 6,
      transit: 3,
      gas: 3,
      dining: 1,
      travel: 1,
      online_shopping: 1,
      entertainment: 1,
      drugstore: 1,
      other: 1
    },
    specialOffers: ['6% at US supermarkets (up to $6k/year)', '6% on streaming', '3% on transit & gas']
  },
  {
    id: 'capital-one-savor',
    name: 'Savor Rewards',
    issuer: 'Capital One',
    color: '#d03027',
    annualFee: 95,
    categories: {
      dining: 4,
      entertainment: 4,
      streaming: 4,
      groceries: 3,
      travel: 1,
      gas: 1,
      transit: 1,
      online_shopping: 1,
      drugstore: 1,
      other: 1
    },
    specialOffers: ['4% on dining & entertainment', '3% at grocery stores', '8% on Capital One Entertainment']
  },
  {
    id: 'amazon-prime-visa',
    name: 'Prime Visa',
    issuer: 'Chase',
    color: '#232f3e',
    annualFee: 0,
    categories: {
      online_shopping: 5,
      groceries: 2,
      dining: 2,
      gas: 2,
      drugstore: 2,
      travel: 1,
      streaming: 1,
      transit: 1,
      entertainment: 1,
      other: 1
    },
    specialOffers: ['5% at Amazon & Whole Foods', '2% at restaurants, gas & drugstores', 'Requires Prime membership']
  },
  {
    id: 'chase-freedom-unlimited',
    name: 'Freedom Unlimited',
    issuer: 'Chase',
    color: '#0066b2',
    annualFee: 0,
    categories: {
      dining: 3,
      drugstore: 3,
      travel: 5,
      groceries: 1.5,
      gas: 1.5,
      streaming: 1.5,
      online_shopping: 1.5,
      transit: 1.5,
      entertainment: 1.5,
      other: 1.5
    },
    specialOffers: ['5% on travel through Chase', '3% on dining & drugstores', '1.5% on everything else']
  },
  {
    id: 'wells-fargo-autograph',
    name: 'Autograph',
    issuer: 'Wells Fargo',
    color: '#cd1409',
    annualFee: 0,
    categories: {
      dining: 3,
      travel: 3,
      gas: 3,
      transit: 3,
      streaming: 3,
      entertainment: 3,
      groceries: 1,
      online_shopping: 1,
      drugstore: 1,
      other: 1
    },
    specialOffers: ['3x on restaurants, travel, gas, transit, streaming', 'No annual fee', 'Cell phone protection']
  },
  {
    id: 'us-bank-altitude-go',
    name: 'Altitude Go',
    issuer: 'U.S. Bank',
    color: '#002855',
    annualFee: 0,
    categories: {
      dining: 4,
      groceries: 2,
      gas: 2,
      streaming: 2,
      travel: 1,
      online_shopping: 1,
      transit: 1,
      entertainment: 1,
      drugstore: 1,
      other: 1
    },
    specialOffers: ['4x on dining', '2x on grocery, gas & streaming', 'No annual fee', '$15 streaming credit']
  }
];

export function detectCategory(query: string): Category {
  const lowerQuery = query.toLowerCase();
  
  for (const category of categories) {
    for (const keyword of category.keywords) {
      if (lowerQuery.includes(keyword.toLowerCase())) {
        return category;
      }
    }
  }
  
  return categories.find(c => c.id === 'other')!;
}

export function getTopCardsForCategory(categoryId: string, limit: number = 3): CreditCard[] {
  return [...creditCards]
    .sort((a, b) => (b.categories[categoryId] || 0) - (a.categories[categoryId] || 0))
    .slice(0, limit);
}

export function getBestCardForQuery(query: string): { card: CreditCard; category: Category; cashback: number } {
  const category = detectCategory(query);
  const topCards = getTopCardsForCategory(category.id, 1);
  const card = topCards[0];
  
  return {
    card,
    category,
    cashback: card.categories[category.id] || 1
  };
}
