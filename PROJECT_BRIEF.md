PROJECT: AI Smart Wardrobe & Personal Stylist — Agentic AI Project

## NORTH STAR
Given a user's digital wardrobe, an agentic AI system recommends a COMPLETE outfit — top,
bottom (or one-piece), outerwear when needed, footwear, bag/purse, and accessories — for a
given day, occasion, and season/weather. Before generating outfits, the system establishes the
user's personal style (via a quick preference picker or an optional photo-based analysis) and
factors in current fashion trends. It always grounds recommendations in what the user already
owns before ever suggesting a purchase. For the top-ranked outfit, the system also generates an
AI photo of a generic fashion model wearing that exact outfit, so the user can actually see the
look rather than just reading a list of items. The multi-agent reasoning — several specialized
agents collaborating and handing off to each other, with that handoff visible — is the graded
deliverable. UI polish is secondary to that.

## PROBLEM THIS SOLVES
People own plenty of clothes but still: don't know what to combine, waste time choosing outfits
for different occasions, buy duplicates of things they already own, forget about unused items,
and don't know what category is actually missing from their wardrobe. This system fixes all
five using computer vision (to digitize the wardrobe) + a multi-agent recommendation system (to
reason about what to wear and what to buy).

## USER JOURNEY
```
Sign up
  ↓
Style Profile step: pick a style (Minimal/Classic/Medium/Stylish-Trendy/Bold + tags)
  OR upload a selfie for AI-proposed style profile (user confirms/edits before saving)
  ↓
Build wardrobe: manually enter items, OR (later phase) upload photos of owned clothes
  ↓
Open app to see Daily Routine Outfit (auto-generated based on user's default routine like "college", ensuring day-to-day rotation)
  OR Ask for an outfit for a special occasion: free text ("job interview tomorrow") or quick-select occasion buttons
  ↓
Orchestrator routes the request through: Style Profile Agent → Occasion Agent →
  Context Agent (weather/season) → Trend Agent → Wardrobe Agent → Outfit Agent
  ↓
2-3 ranked, COMPLETE outfits returned, each with every slot filled (or explicitly marked
  "none available") and a plain-language reason for the pick
```

## ONBOARDING / STYLE PROFILE
At signup (editable later in settings), the user establishes a default routine (e.g., college, office, casual), selects their body shape (e.g., hourglass, pear, rectangle, inverted triangle), and sets a style profile via ONE of:
  (a) **Picker** — style intensity/aesthetic: Minimal, Classic, Medium/Balanced,
      Stylish/Trendy, Bold — plus optional free tags (streetwear, ethnic, formal-office,
      athleisure, etc.).
  (b) **Photo** — upload a selfie; the system infers style-relevant signals only (general
      skin-tone category for color matching, general silhouette for fit guidance) and
      proposes a style profile back to the user as an editable suggestion — never silently
      saved, and never commenting on anything beyond clothing-relevant signals (no remarks
      on weight, age, or attractiveness).
This profile is stored once and reused on every future outfit request — it is not
re-derived per request.

## TREND AWARENESS
The system checks current fashion trends (trending colors, silhouettes, accessory styles) and
factors them into which OWNED items get prioritized — it never invents items the user doesn't
have. To keep this fast, cheap, and demo-reliable: trend signals are fetched by a separate
scheduled/manual job into a `trend_notes` table, and the Trend Agent just reads from that table
at request time rather than hitting a live search API on every single outfit request. A
manually-curated, weekly-refreshed trend list is a completely legitimate version of this for a
student project — it's still genuinely current, just not live-scraped.

## AI OUTFIT VISUALIZATION
Once the Outfit Agent returns its top-ranked outfit, generate an AI photo of a generic fashion
model wearing that exact combination — no user photo, no body-type parameter, just the outfit
itself. This is a plain text-to-image call, not a research project:
- Build the image prompt directly from the outfit's structured attributes already produced by
  the Outfit Agent (category, color, pattern, style per slot) — e.g. *"full-body photo of a
  fashion model on a plain studio background, wearing a white checked shirt, blue jeans, and
  white sneakers, natural pose, fashion photography."*
- Call any hosted text-to-image API (Stability AI, a Replicate-hosted model, or similar —
  swappable via env var, same pattern as the LLM provider).
- Only generate the image for the TOP-ranked outfit by default, not all 2-3 options, to keep
  image-gen API costs and latency down. Add a "visualize this one instead" button for the
  alternates that generates on demand rather than eagerly.
- Cache the generated image URL against the outfit record so re-viewing the same
  recommendation doesn't re-call the image API.
- This is independent of Method A/D — it works purely off text descriptions, so it doesn't
  need any garment photos to exist first, and can be built well before the CV phases.

## TECH STACK
- Frontend: React (Vite)
- Backend: Python + FastAPI
- Database: MySQL
- Agent orchestration: LangGraph
- LLM: pluggable via env var — start with a local Ollama model for dev, swappable to
  Gemini/OpenAI later
- Computer vision (later phase): OpenCV + a pretrained clothing classifier (mock/placeholder
  acceptable until that phase)
- Image generation (outfit visualization): any hosted text-to-image API (Stability AI,
  Replicate-hosted model, or similar), swappable via env var like the LLM provider
- Weather: Open-Meteo (free, no API key) added mid-project

## DATA MODEL (MySQL — starting schema, add indexes/constraints as needed)
```sql
CREATE TABLE users (
  user_id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100),
  email VARCHAR(150) UNIQUE,
  password_hash VARCHAR(255),
  style_preference VARCHAR(50),   -- minimal, classic, medium, stylish-trendy, bold
  style_tags VARCHAR(255),        -- comma-separated, e.g. "streetwear,formal-office"
  default_routine VARCHAR(50),    -- e.g. college, office, casual - used for daily recommendations
  style_photo_url VARCHAR(255),   -- optional
  body_shape VARCHAR(50),         -- e.g. pear, apple, rectangle, hourglass, inverted triangle
  skin_tone_note VARCHAR(50),     -- optional, derived from photo, color-matching only
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE trend_notes (
  trend_id INT PRIMARY KEY AUTO_INCREMENT,
  season VARCHAR(50),             -- e.g. summer-2026
  category VARCHAR(50),           -- footwear, outerwear, color, accessory, silhouette...
  trend_tag VARCHAR(100),         -- e.g. "sage green", "chunky loafers"
  source VARCHAR(255),
  fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE clothes (
  clothing_id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT,
  category VARCHAR(50),        -- shirt, t-shirt, jeans, trousers, dress, jacket, shoes,
                                -- bag, accessory...
  color VARCHAR(50),
  pattern VARCHAR(50),
  style VARCHAR(50),           -- casual, formal, ethnic, sporty...
  season VARCHAR(50),          -- summer, winter, monsoon, all-season
  image_url VARCHAR(255),
  usage_count INT DEFAULT 0,
  last_used DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE outfits (
  outfit_id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT,
  occasion VARCHAR(50),
  weather VARCHAR(50),
  rating INT,
  visualization_image_url VARCHAR(255),  -- cached AI-generated model photo, nullable
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE outfit_items (
  outfit_id INT,
  clothing_id INT,
  FOREIGN KEY (outfit_id) REFERENCES outfits(outfit_id),
  FOREIGN KEY (clothing_id) REFERENCES clothes(clothing_id)
);

```

## AGENT ARCHITECTURE (LangGraph — 6 agent nodes + 1 orchestrator)

Shared state passed between nodes:
```
{
  user_id: int,
  raw_request: str | None,      # None for the daily routine generation
  style_profile: dict | None,   # {preference, tags, default_routine, body_shape, skin_tone_note} — cached, loaded once
  occasion: str | None,
  weather: dict | None,         # {condition, temp_c}
  trend_notes: list | None,
  candidate_clothes: list | None,   # grouped by category incl. bags/accessories
  outfits: list | None,         # each: {top, bottom, outerwear, footwear, bag, accessories}
  visualization_image_url: str | None,   # generated only for the top-ranked outfit
  messages: list                # full agent trace, for demo/debugging
}
```

1. **Orchestrator** — routes the request through the pipeline below; can skip agents whose
   output is already known/cached (e.g. skip Style Profile Agent once cached).
2. **Style Profile Agent** — loads the cached profile (picker or photo-derived). Only
   re-runs the photo analysis if the user explicitly updates their profile.
3. **Occasion Agent** — parses free text into a structured occasion (interview, wedding,
   college, office, party, date, festival, casual-outing...) + formality level. If no request
   is provided (daily rotation mode) or if unstated, it falls back to the user's `default_routine`
   (e.g., college).
4. **Context Agent** — resolves weather/season into concrete constraints (fabric weight,
   layering, footwear/material to avoid in rain, etc.).
5. **Trend Agent** — reads `trend_notes`, returns only tags relevant to this request's
   category/occasion. Never invents a trend not in the table.
6. **Wardrobe Agent** — filters the user's inventory by style/season/occasion formality,
   grouped by category (tops, bottoms, outerwear, footwear, bags, accessories). Empty
   categories are returned as empty lists, not omitted. Wedding looks must be an ethnic or
   explicitly festive/formal one-piece garment, or coordinated ethnic separates (a generic
   one-piece category alone does not imply ethnic wear); interview looks require a formal
   shirt/blouse, formal trousers, and formal footwear. Incomplete or dress-code-mismatched
   combinations are not returned as outfit recommendations. Occasion-specific candidates
   must be ranked before any candidate limit is applied, so random sampling cannot skip
   suitable garments already in the wardrobe.
7. **Outfit Agent (the Stylist)** — takes candidates + occasion + context + style_profile +
   trend tags, returns 2-3 ranked, COMPLETE outfits. Every applicable slot (top, bottom,
   outerwear if needed, footwear, bag, accessories) must be filled or explicitly marked "none
   available" — never silently dropped, never an invented item. Justification per outfit
   covers occasion/weather fit, style-profile fit, and trend alignment (only when genuinely
   relevant). Heavily prioritizes rotation: checks `last_used` dates and underused items
   (low usage_count) to ensure the user gets a visibly different outfit each day for their
   daily routine.
8. **Visualization Agent** — takes only the TOP-ranked outfit's structured attributes
   (category/color/pattern/style per slot, no user photo, no body-type parameter) and builds
   a text-to-image prompt describing a generic fashion model wearing that exact combination,
   then calls the image-generation API. This node is deterministic prompt-building, not
   reasoning — its job is to translate structured data into a good image prompt, then cache
   the result.

**Trend Agent implementation note:** populate `trend_notes` via a scheduled/manual job, not a
live search call per request — keeps the demo fast, deterministic, and not network-dependent.

## MVP SCOPE (must work for the demo, in priority order)
1. Manual wardrobe entry, including bag/purse and accessory as their own categories.
2. Style preference picker at onboarding (photo-based version is stretch).
3. Full 6-agent LangGraph pipeline producing a ranked, explained, COMPLETE outfit for a
   free-text request like "I have an interview tomorrow, it's raining."
4. A curated `trend_notes` table (manually refreshed is fine) feeding the Trend Agent.
5. Occasion + weather visibly changing the recommendation.
6. An AI-generated photo of a generic model wearing the top-ranked outfit (no body-type
   parameter, no user photo — just the outfit itself).
7. A visible per-agent trace in the UI — this is the single most important grading criterion.

## STRETCH SCOPE (only after MVP is solid)
8. Photo-based style profiling as an alternative to the picker.
9. Method A: photo upload of owned clothes → CV attribute detection → editable confirmation.
10. Analytics dashboard: category breakdown, most/least used items, utilization score.
11. Real weather API (Open-Meteo).
12. Live trend fetching replacing the manual seed list.
13. "Visualize this one instead" for the 2nd/3rd ranked outfits, on demand.

## PHASE PLAN (build in this order — CV is pushed later on purpose; it's the highest-risk,
lowest-priority part relative to the agentic reasoning that's actually being graded)

**Phase 0 — Scaffold:** monorepo with `/frontend` (React+Vite), `/backend` (`/agents`,
`/vision`, `/db`, `/api`), `/docs`, `docker-compose.yml` (MySQL+backend+frontend). Hello-world
health check end to end. No features yet.

**Phase 1 — Auth + DB + manual wardrobe CRUD + style onboarding:** JWT auth, the full schema
above, a manual add/edit/delete wardrobe form including bag/accessory categories, and the
style-picker onboarding step (with a "skip, I'll do a photo later" option). Seed ~20 items
(incl. a bag and 2-3 accessories) and a handful of manual `trend_notes` rows.

**Phase 2 — Single-agent outfit baseline:** one LLM call (no LangGraph yet, no trends yet)
that takes a free-text request + wardrobe + style_preference and returns 2-3 ranked COMPLETE
outfits. Validates prompt quality and the full-slot output shape before formalizing agents.

**Phase 3 — Formalize the full LangGraph pipeline:** all 6 agents as real, separate nodes with
their own system prompts (see below). Style Profile Agent loads the cached picker profile;
Trend Agent reads the seeded `trend_notes`. Expose the per-agent trace in the API response.

**Phase 4 — Weather + occasion presets:** wire Context Agent to Open-Meteo; add quick-select
occasion buttons alongside free text. Confirm recommendations visibly change with weather/
occasion.

**Phase 5 — AI outfit visualization:** add the Visualization Agent. Once the Outfit Agent
returns its ranked outfits, build a text-to-image prompt from the top-ranked outfit's
structured attributes (category/color/pattern/style per slot — no user photo, no body-type
parameter) and call a hosted text-to-image API to render a generic model wearing that
combination. Cache the resulting URL on the outfit record. Display it prominently next to the
top recommendation in the UI. This phase does not depend on any garment photos existing, so it
can be built entirely with the manually-entered wardrobe from Phase 1.

**Phase 6 — Method A + photo-based style profiling:** photo upload of owned clothes → CV
classifier (mock acceptable) → editable confirmation before save. Also add the photo-based
style-profile path from onboarding, same edit-before-save principle, storing only the derived
fields, never re-analyzing per request.

**Phase 7 — Analytics dashboard:** total items, category breakdown chart, most/least used
items and colors, wardrobe utilization score — keep it consistent with the usage_count logic
already used by the Outfit Agent.

**Phase 8 — Demo polish:** seed the clean demo dataset (white shirt, blue jeans, black
trousers, black t-shirt, white sneakers, plus a bag/accessory), write a short demo script,
and clean up the agent-trace UI so a non-technical viewer can follow which agent did what.

## Agent system prompts (for `backend/agents/`, reference once Phase 3 starts)

**Style Profile Agent**
```
You are the Style Profile Agent. Two modes:
(1) Picker mode: given a selected style_preference and optional tags, simply structure and
return them — {style_preference, style_tags}.
(2) Photo mode: given a description of style-relevant visual signals from a user's photo
(general skin-tone category, general silhouette), propose a style_preference, style_tags, and
skin_tone_note. Always frame this as a PROPOSAL for the user to confirm or edit, never as a
final judgment — include a "confidence: low/medium/high" field and never comment on the
person's appearance beyond what's needed for color/fit matching (no comments on weight, age,
attractiveness, or anything outside clothing-relevant signals). Respond in structured JSON only.
On every outfit-generation request after the profile exists, simply load and return the cached
profile — do not re-analyze anything.
```

**Trend Agent**
```
You are the Trend Agent. Given a list of trend_notes rows (season, category, trend_tag,
source) and the current occasion/category context, return the subset of trend tags actually
relevant to this request. Never invent a trend not present in the provided rows. Respond in
structured JSON only: {relevant_trends: [...]}.
```

**Occasion Agent**
```
You are the Occasion Agent. Given a free-text user request (if any) and the user's default_routine
(e.g., "college"), extract: (1) the occasion category from [interview, wedding, college, office,
party, date, festival, casual-outing, other], (2) an implied formality level. If the request is
empty or unstated, fall back to the user's default_routine. Respond in structured JSON only.
```

**Context Agent**
```
You are the Context Agent. Given weather data (condition, temperature) and optionally a
season, translate it into concrete clothing constraints: fabric weight, layering needs, and
any footwear/material to avoid (e.g. avoid suede or canvas in rain). Respond in structured
JSON only: {constraints: [...], reasoning: "..."}.
```

**Wardrobe Agent**
```
You are the Wardrobe Agent. Given a user's full clothing inventory and a set of constraints
(occasion formality, weather constraints), filter and return the subset of items that are
plausible candidates, grouped by category: tops, bottoms, outerwear, footwear, bags,
accessories. Do not invent items not present in the inventory. Empty categories return as
empty lists, not omitted keys.
```

**Outfit Agent (Stylist)**
```
You are the Outfit Agent, the creative stylist. Given candidate clothes grouped by category,
the occasion, weather constraints, the user's style_profile, and relevant trend tags, propose
2-3 COMPLETE outfits. Each outfit must address every applicable slot: top, bottom (or
one-piece), outerwear (if weather requires), footwear, bag, and accessories — if a slot has no
candidates, say so explicitly ("no bag suggested — none in your wardrobe suit this occasion")
rather than silently dropping it. Justification per outfit covers: occasion/weather fit,
style_preference fit, and trend alignment only when genuinely relevant. 

Crucially, for daily wear, you must ensure variety. Strictly avoid combining items that were
recently worn together, and heavily penalize items with recent `last_used` dates to give the
user a fresh look every day. Prefer lower usage_count items. Never suggest an item outside
the candidate list; never invent a purchase suggestion.
```


**Visualization Agent (prompt-builder, not an LLM reasoning call)**
```
Given the top-ranked outfit's structured attributes (top: {color, pattern, category}, bottom:
{...}, outerwear: {...} or null, footwear: {...}, bag: {...} or null, accessories: [...]),
build a single text-to-image prompt describing a generic fashion model wearing exactly this
combination. Template:
"Full-body photo of a fashion model on a plain neutral studio background, standing in a
natural pose, wearing [top color] [top pattern] [top category], [bottom color] [bottom
category], [outerwear description if present], [footwear color] [footwear category], carrying
a [bag description if present], with [accessory descriptions if present]. Fashion photography,
soft studio lighting, photorealistic."
Omit any slot marked "none available" entirely from the prompt rather than describing an
absence. Do not reference the user's appearance, body type, or any personal photo — this
prompt describes ONLY the clothing items.
```

## 4-person team split (unchanged from original plan)
- **Student 1 (Frontend):** login, style onboarding UI, wardrobe UI, outfit/agent-trace UI,
  dashboard.
- **Student 2 (Computer Vision):** starts prototyping in a notebook during Phases 1-4 against
  demo photos, then implements Phase 5/6's classifier and photo-based style profiling — don't
  let this person sit idle waiting for Phase 5 to formally start.
- **Student 3 (Agentic AI):** LangGraph, all 6 agent nodes + orchestrator, this is the core
  graded component.
- **Student 4 (Backend & DB):** FastAPI, MySQL, auth, all API routes, weather/trend job
  scheduling.
