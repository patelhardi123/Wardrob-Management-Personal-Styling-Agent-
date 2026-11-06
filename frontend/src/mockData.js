// Mock Seed Data for Wardrobe, Style Profile, and Trends
export const INITIAL_USER_PROFILE = {
  name: "Sarah Jenkins",
  email: "sarah@example.com",
  stylePreference: "stylish-trendy", // minimal, classic, medium, stylish-trendy, bold
  styleTags: ["streetwear", "smart-casual", "minimal-chic"],
  defaultRoutine: "Daily Look", // Daily Look, Work & Office, Smart Casual
  bodyShape: "hourglass", // hourglass, pear, rectangle, inverted triangle, apple
  skinToneNote: "Warm undertone (derived via photo)",
  avatarUrl: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80"
};

export const INITIAL_CLOTHES = [
  {
    id: 101,
    category: "tops",
    title: "Oversized White Linen Shirt",
    color: "White",
    pattern: "Solid",
    style: "smart-casual",
    season: "summer",
    usageCount: 4,
    lastUsed: "2026-08-25",
    imageUrl: "https://images.unsplash.com/photo-1598033129183-c4f50c736f10?auto=format&fit=crop&w=400&q=80"
  },
  {
    id: 102,
    category: "tops",
    title: "Classic Black Fitted Tee",
    color: "Black",
    pattern: "Solid",
    style: "casual",
    season: "all-season",
    usageCount: 12,
    lastUsed: "2026-08-29",
    imageUrl: "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=400&q=80"
  },
  {
    id: 103,
    category: "bottoms",
    title: "High-Waisted Straight Blue Jeans",
    color: "Blue",
    pattern: "Denim",
    style: "casual",
    season: "all-season",
    usageCount: 18,
    lastUsed: "2026-08-28",
    imageUrl: "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=400&q=80"
  },
  {
    id: 104,
    category: "bottoms",
    title: "Tailored Beige Pleated Trousers",
    color: "Beige",
    pattern: "Solid",
    style: "formal",
    season: "all-season",
    usageCount: 3,
    lastUsed: "2026-08-15",
    imageUrl: "https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?auto=format&fit=crop&w=400&q=80"
  },
  {
    id: 105,
    category: "outerwear",
    title: "Vintage Dark Leather Jacket",
    color: "Black",
    pattern: "Solid",
    style: "streetwear",
    season: "winter",
    usageCount: 6,
    lastUsed: "2026-08-20",
    imageUrl: "https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&w=400&q=80"
  },
  {
    id: 106,
    category: "footwear",
    title: "Retro White Chunky Sneakers",
    color: "White",
    pattern: "Solid",
    style: "sporty",
    season: "all-season",
    usageCount: 15,
    lastUsed: "2026-08-29",
    imageUrl: "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?auto=format&fit=crop&w=400&q=80"
  },
  {
    id: 107,
    category: "footwear",
    title: "Black Leather Loafers",
    color: "Black",
    pattern: "Solid",
    style: "formal",
    season: "all-season",
    usageCount: 2,
    lastUsed: "2026-08-10",
    imageUrl: "https://images.unsplash.com/photo-1614252235316-8c857d38b5f4?auto=format&fit=crop&w=400&q=80"
  },
  {
    id: 108,
    category: "bags",
    title: "Minimalist Black Crossbody Bag",
    color: "Black",
    pattern: "Solid",
    style: "casual",
    season: "all-season",
    usageCount: 9,
    lastUsed: "2026-08-27",
    imageUrl: "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?auto=format&fit=crop&w=400&q=80"
  },
  {
    id: 109,
    category: "accessories",
    title: "Gold Minimalist Chain & Analog Watch",
    color: "Gold",
    pattern: "Metallic",
    style: "smart-casual",
    season: "all-season",
    usageCount: 22,
    lastUsed: "2026-08-29",
    imageUrl: "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=400&q=80"
  }
];

export const MOCK_TRENDS = [
  { id: 1, season: "summer-2026", category: "color", tag: "Sage Green & Warm Earth Tones" },
  { id: 2, season: "summer-2026", category: "footwear", tag: "Chunky Loafers & Retro Runners" },
  { id: 3, season: "summer-2026", category: "silhouette", tag: "Relaxed Wide-Leg Tailoring" },
  { id: 4, season: "summer-2026", category: "accessory", tag: "Layered Delicate Gold Jewelry" }
];

export const MOCK_OUTFIT_RESULT = {
  outfitId: "outfit-99",
  occasion: "Job Interview & College Tech Presentation",
  weather: { condition: "Rainy & Breezy", tempC: 22 },
  rank: 1,
  confidence: "96%",
  reasoning: "Combines high-formality tailoring (beige trousers + black loafers) with a crisp oversized white linen shirt. The dark leather jacket handles rainy weather while keeping a trendy edge. Gold accessories align with current summer trends.",
  slots: {
    top: { name: "Oversized White Linen Shirt", color: "White", style: "smart-casual", id: 101 },
    bottom: { name: "Tailored Beige Pleated Trousers", color: "Beige", style: "formal", id: 104 },
    outerwear: { name: "Vintage Dark Leather Jacket", color: "Black", style: "streetwear", id: 105 },
    footwear: { name: "Black Leather Loafers", color: "Black", style: "formal", id: 107 },
    bag: { name: "Minimalist Black Crossbody Bag", color: "Black", style: "casual", id: 108 },
    accessories: [{ name: "Gold Minimalist Chain & Analog Watch", color: "Gold", id: 109 }]
  },
  visualizationImage: "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=800&q=80",
  agentTrace: [
    {
      agent: "Orchestrator",
      status: "completed",
      time: "10ms",
      summary: "Initiated multi-agent graph pipeline. Input: 'Job interview tomorrow, raining outside'."
    },
    {
      agent: "Style Profile Agent",
      status: "completed",
      time: "45ms",
      summary: "Loaded cached profile: 'stylish-trendy', tags: ['streetwear', 'smart-casual'], body: 'hourglass'."
    },
    {
      agent: "Occasion Agent",
      status: "completed",
      time: "80ms",
      summary: "Extracted formality level High (8/10). Occasion classified as 'interview'."
    },
    {
      agent: "Context Agent",
      status: "completed",
      time: "110ms",
      summary: "Resolved weather constraints: Rain detected -> avoid canvas/suede footwear; include water-resistant outerwear."
    },
    {
      agent: "Trend Agent",
      status: "completed",
      time: "60ms",
      summary: "Matched trends: 'Relaxed Wide-Leg Tailoring' & 'Chunky Loafers'."
    },
    {
      agent: "Wardrobe Agent",
      status: "completed",
      time: "95ms",
      summary: "Filtered 9 wardrobe items down to 6 eligible candidates. Excluded canvas sneakers due to rain."
    },
    {
      agent: "Outfit Agent (Stylist)",
      status: "completed",
      time: "320ms",
      summary: "Generated 3 candidate complete outfits. Ranked Outfit #1 as top pick based on usage rotation & formality score."
    },
    {
      agent: "Visualization Agent",
      status: "completed",
      time: "450ms",
      summary: "Constructed studio prompt: 'Full-body photo of model in white linen shirt, beige trousers, leather jacket, black loafers'. Rendered model image."
    }
  ]
};
