/**
 * Universal AI Fashion Stylist Intelligence Engine
 * Dynamically evaluates ANY clothing item (present or future) based on:
 * 1. Garment Type & One-Piece Detection (Maxi dress, gown, jumpsuit, etc.)
 * 2. Formality Rating (1-10 Scale)
 * 3. Style Aesthetics (Ethnic, Formal, Casual Streetwear, Athleisure, Smart Casual)
 * 4. Color Theory & Palette Harmony (Neutrals, Tonal, Complementary, Clashing)
 */

export const ONE_PIECE_KEYWORDS = [
  'dress', 'maxi', 'gown', 'jumpsuit', 'romper', 'one-piece', 'one piece', 
  'anarkali', 'saree', 'frock', 'derss', 'dungaree', 'lehenga'
];

export const HEAVY_FESTIVE_PARTY_KEYWORDS = [
  'wedding', 'party', 'anarkali', 'gown', 'lehenga', 'saree', 'festive', 'traditional', 
  'bridal', 'shaadi', 'gala', 'cocktail', 'heavy', 'embroidery', 'tuxedo'
];

export const isOnePieceGarment = (item) => {
  if (!item) return false;
  const title = (item.title || '').toLowerCase();
  const cat = (item.category || '').toLowerCase();
  const style = (item.style || '').toLowerCase();
  return ONE_PIECE_KEYWORDS.some(kw => title.includes(kw) || cat.includes(kw) || style.includes(kw));
};

export const isHeavyFestiveOrPartyGarment = (item) => {
  if (!item) return false;
  const title = (item.title || '').toLowerCase();
  const cat = (item.category || '').toLowerCase();
  const style = (item.style || '').toLowerCase();
  return HEAVY_FESTIVE_PARTY_KEYWORDS.some(kw => title.includes(kw) || cat.includes(kw) || style.includes(kw));
};

/**
 * Calculates Formality Level (1-10 scale) of any garment based on title, category, and style
 */
export const getGarmentFormality = (item) => {
  if (!item) return 5;
  const title = (item.title || '').toLowerCase();
  const cat = (item.category || '').toLowerCase();
  const style = (item.style || '').toLowerCase();

  if (isHeavyFestiveOrPartyGarment(item)) return 9;
  if (ONE_PIECE_KEYWORDS.some(kw => title.includes(kw) || cat.includes(kw))) return 7;
  if (title.includes('blazer') || title.includes('suit') || style.includes('formal')) return 9;
  if (title.includes('blouse') || title.includes('trouser') || title.includes('silk') || style.includes('smart-formal')) return 8;
  if (title.includes('kurti') || title.includes('shirt') || title.includes('chino') || title.includes('pant 1')) return 7;
  if (title.includes('jeans') || title.includes('denim') || style.includes('smart-casual')) return 6;
  if (title.includes('t-shirt') || title.includes('tee') || title.includes('cargo') || style.includes('casual')) return 4;
  if (title.includes('hoodie') || title.includes('sweatshirt') || title.includes('jogger')) return 3;
  if (title.includes('active') || title.includes('trackpant') || title.includes('sport')) return 2;

  return 5;
};

/**
 * Determines primary aesthetic classification (ethnic, formal, casual, streetwear, sporty, party, wedding)
 */
export const getGarmentAesthetic = (item) => {
  if (!item) return 'casual';
  const title = (item.title || '').toLowerCase();
  const cat = (item.category || '').toLowerCase();
  const style = (item.style || '').toLowerCase();

  if (title.includes('wedding') || style.includes('wedding') || title.includes('anarkali') || title.includes('lehenga')) return 'wedding';
  if (title.includes('party') || style.includes('party') || title.includes('gown') || title.includes('cocktail')) return 'party';
  if (title.includes('kurti') || title.includes('saree') || style.includes('ethnic')) return 'ethnic';
  if (title.includes('blazer') || title.includes('blouse') || title.includes('trouser') || style.includes('formal')) return 'formal';
  if (title.includes('hoodie') || title.includes('cargo') || title.includes('graphic') || style.includes('streetwear')) return 'streetwear';
  if (title.includes('jogger') || title.includes('track') || style.includes('sporty')) return 'sporty';
  return 'casual';
};


/**
 * Evaluates Color Theory compatibility between two garment colors
 */
export const getColorHarmonyScore = (topColorRaw, bottomColorRaw) => {
  const topColor = (topColorRaw || 'neutral').toLowerCase();
  const bottomColor = (bottomColorRaw || 'neutral').toLowerCase();

  const neutralColors = ['black', 'white', 'grey', 'gray', 'beige', 'cream', 'navy', 'denim', 'blue', 'neutral', 'pant 1'];
  
  const isTopNeutral = neutralColors.some(c => topColor.includes(c));
  const isBottomNeutral = neutralColors.some(c => bottomColor.includes(c));

  // Neutral bottoms (Black, White, Navy, Beige, Jeans) go with almost all tops!
  if (isBottomNeutral) return 10;
  if (isTopNeutral) return 9;

  // Same color family (Tonal)
  if (topColor === bottomColor) return 9;

  // Unfavorable saturated clash (e.g. Green bottom + Pink/Red top)
  if ((topColor.includes('pink') || topColor.includes('red')) && (bottomColor.includes('green') || bottomColor.includes('olive'))) {
    return 2;
  }

  return 6;
};

/**
 * Universal Stylist Matcher: Calculates total compatibility score between ANY Top and Bottom
 */
export const calculateOutfitCompatibility = (topItem, bottomItem) => {
  if (!topItem || isOnePieceGarment(topItem)) {
    return { score: 100, isOnePiece: true, reason: 'Standalone one-piece look' };
  }
  if (!bottomItem) {
    return { score: 0, isOnePiece: false, reason: 'Missing bottom item' };
  }

  const topFormality = getGarmentFormality(topItem);
  const bottomFormality = getGarmentFormality(bottomItem);
  const formalityDiff = Math.abs(topFormality - bottomFormality);

  const topAesthetic = getGarmentAesthetic(topItem);
  const bottomAesthetic = getGarmentAesthetic(bottomItem);

  let matchScore = 85;

  // 1. Formality Delta Penalty
  matchScore -= (formalityDiff * 4);

  // 2. Aesthetic Category Matching Rules
  if (topAesthetic === 'ethnic') {
    if (bottomAesthetic === 'streetwear' || bottomAesthetic === 'sporty') {
      matchScore -= 25; // High penalty for Cargo/Joggers on Ethnic Kurtis
    } else if (bottomAesthetic === 'formal' || bottomAesthetic === 'ethnic' || bottomAesthetic === 'casual') {
      matchScore += 10; // Bonus for Trousers, Black Pants, Jeans
    }
  } else if (topAesthetic === 'formal') {
    if (bottomAesthetic === 'streetwear' || bottomAesthetic === 'sporty') {
      matchScore -= 20; // Penalty for Cargo/Joggers on Blouses
    } else if (bottomAesthetic === 'formal' || bottomAesthetic === 'casual') {
      matchScore += 10;
    }
  } else if (topAesthetic === 'streetwear') {
    if (bottomAesthetic === 'streetwear' || bottomAesthetic === 'casual' || bottomAesthetic === 'sporty') {
      matchScore += 10; // Cargo pants & Joggers pair naturally with T-shirts/Hoodies
    }
  }

  // 3. Color Theory Score
  const colorScore = getColorHarmonyScore(topItem.color || topItem.title, bottomItem.color || bottomItem.title);
  matchScore += (colorScore - 5);

  const finalScore = Math.min(99, Math.max(50, Math.round(matchScore)));

  return {
    score: finalScore,
    isOnePiece: false,
    reason: `Formality & Aesthetic match (${topAesthetic} top + ${bottomAesthetic} bottom).`
  };
};

/**
 * Evaluates all available bottoms in wardrobe and selects the best matching bottom for any top.
 * Allows repeating top-ranking bottoms (like Black Pants/Jeans) if they offer superior style match.
 */
export const selectBestMatchingBottom = (topItem, availableBottoms, optionIndex = 0) => {
  if (!topItem || isOnePieceGarment(topItem)) {
    return null; // One-piece dress does NOT need bottoms!
  }
  if (!availableBottoms || availableBottoms.length === 0) {
    return null;
  }

  const scoredList = availableBottoms.map(bottomItem => {
    const compat = calculateOutfitCompatibility(topItem, bottomItem);
    return {
      bottomItem,
      score: compat.score
    };
  });

  // Sort descending by style compatibility score
  scoredList.sort((a, b) => b.score - a.score);

  const highestScore = scoredList[0].score;

  // Filter top-performing bottoms (within 3 points of best score)
  const topCandidates = scoredList.filter(s => s.score >= highestScore - 3);

  // Return best matching bottom with optionIndex rotation among top candidates
  return topCandidates[optionIndex % topCandidates.length].bottomItem;
};

/**
 * Ranks and filters garments based on occasion target formality (1-10 scale).
 * Heavily deprioritizes heavy wedding/party dresses and formal suits in casual daily college outfits
 * when casual options are present!
 */
export const filterAndRankGarmentsForOccasion = (garmentList, targetFormality = 5) => {
  if (!garmentList || garmentList.length === 0) return [];

  const scored = garmentList.map(item => {
    const formality = getGarmentFormality(item);
    const style = (item.style || '').toLowerCase();
    const title = (item.title || '').toLowerCase();
    const isHeavy = isHeavyFestiveOrPartyGarment(item);
    
    let scorePenalty = 0;

    if (targetFormality <= 6) {
      // Casual / Daily College Routine (Formality <= 6):
      if (isHeavy || title.includes('wedding') || title.includes('party') || title.includes('anarkali') || title.includes('gown') || title.includes('lehenga') || title.includes('saree')) {
        scorePenalty += 75; // STEEP penalty for heavy wedding/party dresses in daily casual wear
      } else if (style === 'formal' || title.includes('formal') || title.includes('suit') || title.includes('blazer')) {
        scorePenalty += 45; // Deprioritize formal office suits in daily casual college looks
      }
    } else if (targetFormality >= 8) {
      // Formal / Wedding / Party / Professional Routine (Formality >= 8):
      if (style === 'casual' || style === 'sporty' || title.includes('hoodie') || title.includes('cargo') || title.includes('trackpant')) {
        scorePenalty += 55; // Deprioritize casual hoodies/cargos in formal/party settings
      } else if (isHeavy || style === 'formal' || title.includes('wedding') || title.includes('party') || title.includes('trouser')) {
        scorePenalty -= 30; // Bonus for wedding/party/formal clothes in high formality settings
      }
    }

    const formalityDelta = Math.abs(formality - targetFormality);
    const totalScore = 100 - (formalityDelta * 8) - scorePenalty;

    return { item, score: totalScore };
  });

  scored.sort((a, b) => b.score - a.score);
  return scored.map(s => s.item);
};

