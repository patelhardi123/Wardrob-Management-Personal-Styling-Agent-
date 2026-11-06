import React, { useState } from 'react';
import { Sparkles, Search, CheckCircle2, ChevronDown, ChevronUp, Activity, Image as ImageIcon, Check } from 'lucide-react';
import AgentTrace from './AgentTrace';
import OutfitFlatLayBoard from './OutfitFlatLayBoard';
import WeekdayOutfitAssignment from './WeekdayOutfitAssignment';
import { isOnePieceGarment, selectBestMatchingBottom, calculateOutfitCompatibility, filterAndRankGarmentsForOccasion } from '../utils/fashionStylistEngine';

export default function OccasionAgentView({ userProfile, clothes, weekdaySchedule, onScheduleOutfit, isWeekdayScheduleLoaded }) {
  const [occasionInput, setOccasionInput] = useState('Job Interview');
  const [selectedWeather, setSelectedWeather] = useState('sunny');
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedOutfitId, setSelectedOutfitId] = useState(null);
  const [showTraceDrawer, setShowTraceDrawer] = useState(false);
  const [dynamicOutfits, setDynamicOutfits] = useState(null);
  const [liveTrace, setLiveTrace] = useState(null);

  const presets = [
    { label: '💼 Job Interview', text: 'Job Interview', weather: 'sunny' },
    { label: '💍 Wedding / Reception', text: 'Wedding Event', weather: 'sunny' },
    { label: '🍷 Dinner Date', text: 'Romantic Dinner Date', weather: 'chilly' },
    { label: '🎉 Night Out / Party', text: 'Night Party', weather: 'sunny' },
    { label: '🌧️ Casual Outing', text: 'Casual Outing', weather: 'rainy' },
  ];

  // Helper to dynamically build preference outfits based on available stored wardrobe items
  const getOccasionOutfitOptions = (query) => {
    const q = (query || occasionInput || '').toLowerCase();
    let targetFormality = 5; // default casual
    if (q.includes('interview') || q.includes('formal') || q.includes('wedding') || q.includes('office') || q.includes('corporate')) {
      targetFormality = 9;
    } else if (q.includes('date') || q.includes('dinner') || q.includes('party') || q.includes('reception')) {
      targetFormality = 7;
    }

    const items = (clothes || []).filter(item =>
      ['ready', 'available'].includes(item.availability_status || 'ready')
      && (item.ironing_status || 'ready') === 'ready'
    );
    const catItems = {
      tops: items.filter(c => isOnePieceGarment(c) || ['tops', 'top', 'shirt', 'tee', 'blouse', 'sweater', 'hoodie', 'kurti'].some(kw => (c.category || '').toLowerCase().includes(kw) || (c.title || '').toLowerCase().includes(kw))),
      bottoms: items.filter(c => ['bottoms', 'bottom', 'pants', 'jeans', 'trousers', 'skirt', 'short', 'chino', 'cargo'].some(kw => (c.category || '').toLowerCase().includes(kw) || (c.title || '').toLowerCase().includes(kw))),
      footwear: items.filter(c => ['footwear', 'foot', 'shoes', 'sneakers', 'loafers', 'boots', 'sandals', 'heels'].some(kw => (c.category || '').toLowerCase().includes(kw) || (c.title || '').toLowerCase().includes(kw))),
      bags: items.filter(c => ['bags', 'bag', 'purse', 'handbag', 'tote', 'crossbody', 'backpack'].some(kw => (c.category || '').toLowerCase().includes(kw) || (c.title || '').toLowerCase().includes(kw))),
      accessories: items.filter(c => ['accessories', 'accessory', 'jewellery', 'jewelry', 'watch', 'belt', 'chain'].some(kw => (c.category || '').toLowerCase().includes(kw) || (c.title || '').toLowerCase().includes(kw))),
      outerwear: items.filter(c => ['outerwear', 'outer', 'jacket', 'coat', 'blazer'].some(kw => (c.category || '').toLowerCase().includes(kw) || (c.title || '').toLowerCase().includes(kw)))
    };

    const rankedTops = filterAndRankGarmentsForOccasion(catItems.tops, targetFormality);
    const rankedBottoms = filterAndRankGarmentsForOccasion(catItems.bottoms, targetFormality);
    const rankedFootwear = filterAndRankGarmentsForOccasion(catItems.footwear, targetFormality);
    const rankedOuterwear = filterAndRankGarmentsForOccasion(catItems.outerwear, targetFormality);

    const themes = [
      {
        id: 'occ-pref-1',
        title: 'Preference #1: Executive Smart Formal',
        trendSignal: '🔥 Verified Trend: Relaxed Wide-Leg Tailoring + Leather Contrast',
        reason: 'Trend Agent evaluated fashion signals and paired your tailored dark trousers with a crisp shirt & leather jacket for formal events.'
      },
      {
        id: 'occ-pref-2',
        title: 'Preference #2: Modern Elegant Casual',
        trendSignal: '🔥 Verified Trend: Minimalist Monochrome & Neutral Tones',
        reason: 'Trend Agent cross-referenced your neutral tops with dark trousers for long events offering comfort and modern elegance.'
      },
      {
        id: 'occ-pref-3',
        title: 'Preference #3: Contemporary Creative Formal',
        trendSignal: '🔥 Verified Trend: Clean Footwear with Tailored Trousers',
        reason: 'Trend Agent verified high-street runway trends combining subtle top with monochrome contrast for a creative formal outfit.'
      }
    ];

    const isBagExcluded = Boolean(
      userProfile?.excludeBags || 
      (userProfile?.activeExclusions && userProfile.activeExclusions.some(ex => ex.toLowerCase().includes('bag') || ex.toLowerCase().includes('purse'))) ||
      (userProfile?.userBio && /no bag|no bags|don't want bag|don't want bags|without bag|without bags|no purse|no handbag|didn't give me purse|didn't give me bag/i.test(userProfile.userBio)) ||
      (userProfile?.context_rules && /no bag|no bags|don't want bag|don't want bags|without bag|without bags|no purse|no handbag|didn't give me purse|didn't give me bag/i.test(userProfile.context_rules))
    );

    const isAccExcluded = Boolean(
      userProfile?.excludeAccessories || 
      (userProfile?.activeExclusions && userProfile.activeExclusions.some(ex => ex.toLowerCase().includes('accessori') || ex.toLowerCase().includes('jewell'))) ||
      (userProfile?.userBio && /no accessor|no jewell/i.test(userProfile.userBio)) ||
      (userProfile?.context_rules && /no accessor|no jewell/i.test(userProfile.context_rules))
    );

    return themes.map((t, idx) => {
      const topObj = (rankedTops.length > 0 ? rankedTops[idx % rankedTops.length] : catItems.tops[0]) || null;
      const isOnePiece = isOnePieceGarment(topObj);

      // Select style matching bottom item using Universal Fashion Stylist Engine
      const bottomObj = selectBestMatchingBottom(topObj, rankedBottoms.length > 0 ? rankedBottoms : catItems.bottoms, idx);

      const preferredFootwearName = userProfile?.preferredFootwear || 
        (userProfile?.context_rules && /only want shoe|only use shoe|shoe with all|shoe only|only shoe|prefer shoe|use shoe/i.test(userProfile.context_rules) ? "Shoe" : null) ||
        (userProfile?.userBio && /only want shoe|only use shoe|shoe with all|shoe only|only shoe|prefer shoe|use shoe/i.test(userProfile.userBio) ? "Shoe" : null);

      let shoeObj = null;
      const topTitleStr = (topObj?.title || '').toLowerCase();
      const topStyleStr = (topObj?.style || '').toLowerCase();
      const isEthnicTop = topTitleStr.includes('kurti') || topTitleStr.includes('ethnic') || topStyleStr.includes('ethnic');

      if (preferredFootwearName && !isEthnicTop) {
        const matchedPrefShoe = catItems.footwear.find(f => (f.title || '').toLowerCase().includes(preferredFootwearName.toLowerCase()));
        if (matchedPrefShoe) {
          shoeObj = matchedPrefShoe;
        }
      }

      if (!shoeObj) {
        shoeObj = (rankedFootwear.length > 0 ? rankedFootwear[idx % rankedFootwear.length] : catItems.footwear[0]) || null;
      }
      const bagObj = isBagExcluded ? null : (catItems.bags[idx % Math.max(1, catItems.bags.length)] || null);
      const accObj = isAccExcluded ? null : (catItems.accessories[idx % Math.max(1, catItems.accessories.length)] || null);
      const outerObj = catItems.outerwear[idx % Math.max(1, catItems.outerwear.length)] || null;

      const topTitle = topObj ? topObj.title : 'Oversized White Linen Shirt';
      const bottomTitle = isOnePiece ? 'None Needed (One-Piece Dress)' : (bottomObj ? bottomObj.title : 'Tailored Beige Pleated Trousers');
      const shoeTitle = shoeObj ? shoeObj.title : 'Black Leather Loafers';
      const bagTitle = isBagExcluded ? null : (bagObj ? bagObj.title : 'Minimalist Black Crossbody Bag');
      const accTitle = isAccExcluded ? null : (accObj ? accObj.title : 'Gold Analog Watch & Jewellery');
      const outerTitle = outerObj ? outerObj.title : 'Vintage Dark Leather Jacket';

      const compat = calculateOutfitCompatibility(topObj, bottomObj);
      const computedScore = isOnePiece ? '97%' : `${compat.score}%`;

      return {
        id: t.id,
        rank: idx + 1,
        title: t.title,
        matchScore: computedScore,
        trendSignal: t.trendSignal,
        reason: t.reason,
        slotItems: {
          topObj,
          bottomObj,
          shoeObj,
          bagObj,
          accObj,
          outerObj,
          isBagExcluded,
          isAccExcluded
        },
        slots: {
          top: topTitle,
          bottom: bottomTitle,
          footwear: shoeTitle,
          bag: bagTitle,
          accessory: accTitle,
          outerwear: outerTitle
        }
      };
    });
  };

  const currentOptions = (dynamicOutfits || getOccasionOutfitOptions(occasionInput)).filter(outfit => {
    const slots = outfit.slotItems || {};
    const top = slots.topObj;
    const bottom = slots.bottomObj;
    const footwear = slots.shoeObj;
    if (!top?.id || !footwear?.id || (!isOnePieceGarment(top) && !bottom?.id)) return false;
    return [top, bottom, footwear].filter(Boolean).every(item => {
      const stored = (clothes || []).find(entry => String(entry.id) === String(item.id));
      return stored
        && ['ready', 'available'].includes(stored.availability_status || 'ready')
        && (stored.ironing_status || 'ready') === 'ready';
    });
  });

  const handleGenerate = async (queryText, weatherVal) => {
    setIsGenerating(true);
    setSelectedOutfitId(null);
    const targetOccasion = queryText || occasionInput;
    if (queryText) setOccasionInput(queryText);
    if (weatherVal) setSelectedWeather(weatherVal);

    try {
      const res = await fetch('http://localhost:8000/api/stylist-recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 1,
          occasion: targetOccasion,
          style_preference: userProfile?.stylePreference || 'stylish-trendy',
          exclude_bags: userProfile?.excludeBags || false,
          exclude_accessories: userProfile?.excludeAccessories || false,
          context_rules: userProfile?.userBio || null,
          clothes: clothes || []
        })
      });
      const data = await res.json();
      if (data.outfits) {
        setDynamicOutfits(data.outfits);
      }
      if (data.agentTrace) {
        setLiveTrace(data.agentTrace);
      }
    } catch (err) {
      console.warn("Backend server call error, showing fallback mock options", err);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', maxWidth: '1100px', margin: '0 auto', width: '100%' }}>
      
      {/* Clean Interactive Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0F172A', fontFamily: 'var(--font-heading)', lineHeight: 1.1 }}>
            Occasion Outfit Curator
          </h1>
          <p style={{ color: '#64748B', fontSize: '0.88rem', marginTop: '0.25rem' }}>
            Instant AI styling for events, dates, interviews, and special outings.
          </p>
        </div>
      </div>

      {/* Clean Interactive Occasion Input Card */}
      <div className="card-widget" style={{ borderRadius: '24px', padding: '1.75rem', background: '#FFFFFF' }}>
        
        <div style={{ marginBottom: '1.25rem' }}>
          <label style={{ fontSize: '0.85rem', fontWeight: 800, color: '#1C1D21', display: 'block', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Enter Occasion or Event Request:
          </label>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <div style={{ flex: 1, position: 'relative' }}>
              <input 
                type="text" 
                value={occasionInput}
                onChange={(e) => setOccasionInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleGenerate(occasionInput)}
                placeholder="e.g. Job interview tomorrow, evening dinner date, or rainy day..."
                style={{
                  width: '100%',
                  padding: '0.9rem 1.25rem 0.9rem 2.75rem',
                  borderRadius: '16px',
                  border: '1px solid #ECEBF5',
                  backgroundColor: '#FAF9FE',
                  fontSize: '0.95rem',
                  outline: 'none',
                  color: '#1C1D21',
                  fontFamily: 'var(--font-body)'
                }}
              />
              <Search size={18} color="#8E92A0" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
            </div>

            <button 
              onClick={() => handleGenerate(occasionInput)}
              disabled={isGenerating}
              className="btn-primary"
              style={{ padding: '0.9rem 1.6rem', borderRadius: '16px' }}
            >
              {isGenerating ? 'Styling...' : 'Get Outfits'}
            </button>
          </div>
        </div>

        {/* Quick Occasion Preset Pills */}
        <div>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#8E92A0', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '0.5rem' }}>
            Quick Occasion Shortcuts:
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {presets.map((preset, idx) => (
              <button
                key={idx}
                onClick={() => handleGenerate(preset.text, preset.weather)}
                style={{
                  background: occasionInput.toLowerCase().includes(preset.text.toLowerCase()) ? '#F0EBFF' : '#FAF9FE',
                  border: occasionInput.toLowerCase().includes(preset.text.toLowerCase()) ? '1px solid #7C4DFF' : '1px solid #ECE7FE',
                  color: occasionInput.toLowerCase().includes(preset.text.toLowerCase()) ? '#7C4DFF' : '#606470',
                  padding: '0.45rem 0.85rem',
                  borderRadius: '999px',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

      </div>

      {/* Occasion Results Title */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#1C1D21' }}>
          {currentOptions.length} Outfit Preferences for "{occasionInput}"
        </h2>

        {clothes && clothes.length <= 5 && (
          <span style={{ fontSize: '0.8rem', color: '#F59E0B', background: '#FEF3C7', padding: '0.3rem 0.75rem', borderRadius: '999px', fontWeight: 700 }}>
            ⚠️ Limited wardrobe count ({clothes.length} items) — showing best available preferences
          </span>
        )}
      </div>

      {/* 2-3 Preference Outfit Cards or 0 Match Message */}
      {currentOptions.length === 0 ? (
        <div className="card-widget" style={{
          borderRadius: '24px',
          padding: '3.5rem 2rem',
          textAlign: 'center',
          background: '#FFFFFF',
          border: '1px solid #ECEBF5',
          boxShadow: 'var(--shadow-card)'
        }}>
          <div style={{
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            backgroundColor: '#F3F0FF',
            color: '#7C4DFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1.25rem'
          }}>
            <Sparkles size={28} />
          </div>
          <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#1C1D21', marginBottom: '0.6rem' }}>
            No Matching Outfits Found
          </h3>
          <p style={{ color: '#606470', fontSize: '0.95rem', maxWidth: '520px', margin: '0 auto 1.25rem', lineHeight: 1.55 }}>
            We couldn't find a suitable outfit in your current wardrobe for this occasion.
          </p>
          <p style={{ color: '#8E92A0', fontSize: '0.82rem', maxWidth: '480px', margin: '0 auto' }}>
            Tip: Try uploading ethnic/festive items for weddings, formal wear for interviews, or add new clothing pieces to your wardrobe.
          </p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
          {currentOptions.map((pref) => {
            const isSelected = selectedOutfitId === pref.id;

            return (
              <div
                key={pref.id}
                className="card-widget"
                style={{
                  borderRadius: '24px',
                  padding: 0,
                  overflow: 'hidden',
                  display: 'flex',
                  flexDirection: 'column',
                  border: isSelected ? '2px solid #7C4DFF' : '1px solid #ECEBF5',
                  boxShadow: isSelected ? '0 10px 30px rgba(124, 77, 255, 0.2)' : 'var(--shadow-card)',
                  transition: 'all 0.25s ease',
                  transform: isSelected ? 'translateY(-4px)' : 'none'
                }}
              >
                {/* Pinterest Outfit Flat-Lay Collage Header */}
                <div style={{ position: 'relative' }}>
                  <OutfitFlatLayBoard 
                    slotItems={pref.slotItems} 
                    title={pref.title} 
                    height={320} 
                  />

                  <div style={{
                    position: 'absolute',
                    top: '14px',
                    left: '14px',
                    background: 'rgba(255, 255, 255, 0.95)',
                    color: '#7C4DFF',
                    padding: '0.3rem 0.75rem',
                    borderRadius: '999px',
                    fontSize: '0.78rem',
                    fontWeight: 800,
                    backdropFilter: 'blur(6px)',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                    zIndex: 2
                  }}>
                    {pref.matchScore} Match Score
                  </div>

                  {isSelected && (
                    <div style={{
                      position: 'absolute',
                      top: '14px',
                      right: '14px',
                      background: '#10B981',
                      color: '#FFFFFF',
                      padding: '0.35rem 0.75rem',
                      borderRadius: '999px',
                      fontSize: '0.78rem',
                      fontWeight: 800,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.35rem',
                      boxShadow: '0 4px 12px rgba(16, 185, 129, 0.4)',
                      zIndex: 2
                    }}>
                      <Check size={15} /> Selected Outfit
                    </div>
                  )}
                </div>

                {/* Content Body */}
                <div style={{ padding: '1.35rem', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    {pref.trendSignal && (
                      <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#7C4DFF', background: '#F0EBFF', padding: '0.25rem 0.65rem', borderRadius: '8px', marginBottom: '0.5rem', display: 'inline-block' }}>
                        {pref.trendSignal}
                      </div>
                    )}
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#1C1D21', marginBottom: '0.45rem', lineHeight: 1.25 }}>
                      {pref.title}
                    </h3>
                    <p style={{ fontSize: '0.82rem', color: '#606470', lineHeight: 1.45, marginBottom: '1.1rem' }}>
                      {pref.reason}
                    </p>

                    {/* Clean Slot Breakdown */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.6rem', marginBottom: '1.25rem', background: '#FAF9FE', padding: '0.85rem', borderRadius: '14px', border: '1px solid #ECE7FE' }}>
                      <div>
                        <span style={{ fontSize: '0.68rem', color: '#7C4DFF', textTransform: 'uppercase', fontWeight: 700, display: 'block' }}>👔 Top</span>
                        <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#1C1D21' }}>{pref.slots.top}</span>
                      </div>
                      {pref.slots.bottom && !pref.slots.bottom.includes('None Needed') && (
                        <div>
                          <span style={{ fontSize: '0.68rem', color: '#7C4DFF', textTransform: 'uppercase', fontWeight: 700, display: 'block' }}>👖 Bottom</span>
                          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#1C1D21' }}>{pref.slots.bottom}</span>
                        </div>
                      )}
                      <div>
                        <span style={{ fontSize: '0.68rem', color: '#7C4DFF', textTransform: 'uppercase', fontWeight: 700, display: 'block' }}>👟 Footwear</span>
                        <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#1C1D21' }}>{pref.slots.footwear}</span>
                      </div>
                      {pref.slots.bag && (
                        <div>
                          <span style={{ fontSize: '0.68rem', color: '#7C4DFF', textTransform: 'uppercase', fontWeight: 700, display: 'block' }}>👜 Purse / Bag</span>
                          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#1C1D21' }}>{pref.slots.bag}</span>
                        </div>
                      )}
                      {pref.slots.accessory && (
                        <div>
                          <span style={{ fontSize: '0.68rem', color: '#7C4DFF', textTransform: 'uppercase', fontWeight: 700, display: 'block' }}>💎 Jewellery</span>
                          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#1C1D21' }}>{pref.slots.accessory}</span>
                        </div>
                      )}
                      {pref.slots.outerwear && pref.slots.outerwear !== 'None Needed' && (
                        <div>
                          <span style={{ fontSize: '0.68rem', color: '#7C4DFF', textTransform: 'uppercase', fontWeight: 700, display: 'block' }}>🧥 Outerwear</span>
                          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#1C1D21' }}>{pref.slots.outerwear}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Select Button */}
                  <button
                    onClick={() => setSelectedOutfitId(pref.id)}
                    className={isSelected ? 'btn-secondary' : 'btn-primary'}
                    style={{
                      width: '100%',
                      justifyContent: 'center',
                      padding: '0.75rem 1rem',
                      borderRadius: '14px',
                      fontSize: '0.88rem',
                      background: isSelected ? '#E6F9F0' : 'var(--primary-gradient)',
                      color: isSelected ? '#10B981' : '#FFFFFF',
                      boxShadow: isSelected ? 'none' : '0 4px 14px rgba(124, 77, 255, 0.3)'
                    }}
                  >
                    {isSelected ? (
                      <>
                        <CheckCircle2 size={18} /> Selected for {occasionInput}
                      </>
                    ) : (
                      'Select & Wear This Outfit'
                    )}
                  </button>
                  <WeekdayOutfitAssignment
                    outfit={pref}
                    schedule={weekdaySchedule}
                    onAssign={onScheduleOutfit}
                    source="occasion"
                    disabled={!isWeekdayScheduleLoaded}
                  />
                </div>

              </div>
            );
          })}
        </div>
      )}

    </div>
  );
}
