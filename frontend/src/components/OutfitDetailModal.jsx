import React from 'react';
import { X, CheckCircle2, Sparkles, Check, ChevronRight, Tag, ShieldCheck, Heart, Award } from 'lucide-react';
import OutfitFlatLayBoard from './OutfitFlatLayBoard';
import { isOnePieceGarment } from '../utils/fashionStylistEngine';

export default function OutfitDetailModal({ isOpen, onClose, outfit, dayLabel, onSelectOutfit, isSelected }) {
  if (!isOpen || !outfit) return null;

  const slotItems = outfit.slotItems || {};
  const isOnePiece = isOnePieceGarment(slotItems.topObj);

  const isBagExcluded = slotItems.bagObj === null || slotItems.isBagExcluded;
  const isAccExcluded = slotItems.accObj === null || slotItems.isAccExcluded;

  const rawItemsList = [
    { label: isOnePiece ? 'One-Piece Dress' : 'Top Garment', icon: isOnePiece ? '👗' : '👔', obj: slotItems.topObj, fallbackTitle: outfit.slots?.top },
    ...(!isOnePiece ? [{ label: 'Bottom Pants', icon: '👖', obj: slotItems.bottomObj, fallbackTitle: outfit.slots?.bottom }] : []),
    { label: 'Footwear', icon: '👟', obj: slotItems.shoeObj, fallbackTitle: outfit.slots?.footwear },
    ...(!isBagExcluded && outfit.slots?.bag ? [{ label: 'Purse / Bag', icon: '👜', obj: slotItems.bagObj, fallbackTitle: outfit.slots?.bag }] : []),
    ...(!isAccExcluded && outfit.slots?.accessory ? [{ label: 'Jewellery & Accessories', icon: '💎', obj: slotItems.accObj, fallbackTitle: outfit.slots?.accessory }] : []),
    ...(slotItems.outerObj ? [{ label: 'Outerwear', icon: '🧥', obj: slotItems.outerObj, fallbackTitle: outfit.slots?.outerwear }] : [])
  ];

  const itemsList = rawItemsList.filter(item => item.fallbackTitle && !item.fallbackTitle.includes('None Needed'));

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 1000,
      backgroundColor: 'rgba(15, 17, 26, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1.5rem',
      animation: 'fadeIn 0.2s ease-out'
    }}>
      <div style={{
        backgroundColor: '#FFFFFF',
        borderRadius: '28px',
        maxWidth: '960px',
        width: '100%',
        maxHeight: '90vh',
        overflowY: 'auto',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.3)',
        display: 'flex',
        flexDirection: 'column',
        border: '1px solid #ECEBF5'
      }}>
        
        {/* Modal Header */}
        <div style={{
          padding: '1.5rem 2rem',
          borderBottom: '1px solid #ECEBF5',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          sticky: 'top',
          top: 0,
          background: '#FFFFFF',
          zIndex: 10
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#7C4DFF', fontSize: '0.8rem', fontWeight: 800, textTransform: 'uppercase' }}>
              <Sparkles size={16} /> Interactive Outfit Inspector • {dayLabel || 'Daily Planner'}
            </div>
            <h2 style={{ fontSize: '1.45rem', fontWeight: 800, color: '#1C1D21', fontFamily: 'var(--font-heading)', marginTop: '0.2rem' }}>
              {outfit.title}
            </h2>
          </div>

          <button
            onClick={onClose}
            style={{
              background: '#F4F4F6',
              border: 'none',
              borderRadius: '50%',
              width: '38px',
              height: '38px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              color: '#606470',
              transition: 'all 0.15s ease'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          
          {/* Top Section: Pinterest Studio Canvas & AI Trend Summary */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.75rem', alignItems: 'start' }}>
            
            {/* Left: High-Res Interactive Flat-Lay Board */}
            <div>
              <div style={{ fontSize: '0.82rem', fontWeight: 800, color: '#8E92A0', textTransform: 'uppercase', marginBottom: '0.6rem' }}>
                📸 Flat-Lay Studio Board
              </div>
              <OutfitFlatLayBoard slotItems={slotItems} title={outfit.title} height={360} />
            </div>

            {/* Right: AI Stylist Analysis & Match Info */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {/* Match Badge & Trend */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                <span style={{
                  background: 'linear-gradient(135deg, #7C4DFF 0%, #6366F1 100%)',
                  color: '#FFFFFF',
                  padding: '0.4rem 1rem',
                  borderRadius: '999px',
                  fontWeight: 800,
                  fontSize: '0.88rem',
                  boxShadow: '0 4px 14px rgba(124, 77, 255, 0.3)'
                }}>
                  {outfit.matchScore} Compatibility Score
                </span>
                
                {outfit.unavailabilityNotice && (
                  <span style={{ fontSize: '0.8rem', fontWeight: 800, color: '#DC2626', background: '#FEE2E2', padding: '0.4rem 0.85rem', borderRadius: '999px', border: '1px solid #FCA5A5' }}>
                    {outfit.unavailabilityNotice}
                  </span>
                )}

                {outfit.trendSignal && (
                  <span style={{ fontSize: '0.8rem', fontWeight: 800, color: '#7C4DFF', background: '#F0EBFF', padding: '0.4rem 0.85rem', borderRadius: '999px' }}>
                    {outfit.trendSignal}
                  </span>
                )}
              </div>

              {/* Unavailability Notice Warning Card */}
              {outfit.unavailabilityNotice && (
                <div style={{ background: '#FFF5F5', padding: '1rem', borderRadius: '16px', border: '1px solid #FECDD3', color: '#991B1B', fontSize: '0.85rem', lineHeight: '1.45', fontWeight: 600 }}>
                  🚨 <strong>Wardrobe Item Missing Notice:</strong> Your owned wardrobe currently lacks dedicated items that fully match this occasion. The system has selected the closest candidate combination above.
                </div>
              )}

              {/* AI Reasoning Box */}
              <div style={{ background: '#FAF9FE', padding: '1.25rem', borderRadius: '18px', border: '1px solid #ECE7FE' }}>
                <div style={{ fontSize: '0.82rem', fontWeight: 800, color: '#7C4DFF', textTransform: 'uppercase', marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <ShieldCheck size={16} /> AI Stylist Reasoning
                </div>
                <p style={{ fontSize: '0.92rem', color: '#1C1D21', lineHeight: 1.55 }}>
                  {outfit.reason}
                </p>
              </div>

              {/* Phase 5 AI Outfit Visualization Section */}
              {outfit.visualization_image_url && (
                <div style={{ background: '#F8F5FF', padding: '1.25rem', borderRadius: '20px', border: '1px solid #D8C4FF', display: 'flex', gap: '1rem', alignItems: 'center' }}>
                  <img 
                    src={outfit.visualization_image_url} 
                    alt="AI Fashion Model" 
                    style={{ width: '95px', height: '120px', borderRadius: '14px', objectFit: 'cover', boxShadow: '0 4px 12px rgba(124, 77, 255, 0.2)' }}
                  />
                  <div>
                    <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#7C4DFF', textTransform: 'uppercase', background: '#EAE0FF', padding: '0.2rem 0.6rem', borderRadius: '6px' }}>
                      ✨ AI Fashion Model Render
                    </span>
                    <h4 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#1C1D21', margin: '0.3rem 0 0.2rem 0' }}>
                      Rendered Model Outfit View
                    </h4>
                    <p style={{ fontSize: '0.78rem', color: '#6A6E7D', margin: 0 }}>
                      AI photo of a fashion model wearing this exact combination.
                    </p>
                  </div>
                </div>
              )}


              {/* Action Button */}
              <button
                onClick={() => {
                  onSelectOutfit(outfit);
                  onClose();
                }}
                className={isSelected ? 'btn-secondary' : 'btn-primary'}
                style={{
                  width: '100%',
                  padding: '0.95rem 1.25rem',
                  borderRadius: '16px',
                  fontSize: '0.95rem',
                  justifyContent: 'center',
                  background: isSelected ? '#F0EBFF' : 'var(--primary-gradient)',
                  color: isSelected ? '#7C4DFF' : '#FFFFFF',
                  boxShadow: isSelected ? 'none' : '0 6px 20px rgba(124, 77, 255, 0.35)'
                }}
              >
                {isSelected ? (
                  <>
                    <CheckCircle2 size={18} /> Selected Choice for {dayLabel}
                  </>
                ) : (
                  <>
                    Wear This Outfit on {dayLabel} <ChevronRight size={18} />
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Bottom Section: Item-by-Item Interactive Breakdown */}
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#1C1D21', marginBottom: '1rem' }}>
              🛍️ Matched Wardrobe Items ({itemsList.length} Items)
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '1rem' }}>
              {itemsList.map((item, idx) => {
                const itemObj = item.obj;
                const titleText = itemObj?.title || item.fallbackTitle || 'Wardrobe Item';
                const imageSrc = itemObj?.imageUrl || 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=400&q=80';

                return (
                  <div
                    key={idx}
                    style={{
                      background: '#FFFFFF',
                      borderRadius: '18px',
                      border: '1px solid #ECEBF5',
                      padding: '0.85rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.75rem',
                      boxShadow: '0 2px 10px rgba(0,0,0,0.02)',
                      transition: 'transform 0.2s ease',
                    }}
                  >
                    {/* Item Image */}
                    <div style={{ height: '140px', background: '#FAF9FE', borderRadius: '12px', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '6px' }}>
                      <img 
                        src={imageSrc} 
                        alt={titleText} 
                        style={{ maxHeight: '100%', maxWidth: '100%', objectFit: 'contain', filter: 'drop-shadow(0 4px 8px rgba(0,0,0,0.1))' }}
                      />
                    </div>

                    {/* Item Details */}
                    <div>
                      <div style={{ fontSize: '0.68rem', color: '#7C4DFF', fontWeight: 800, textTransform: 'uppercase', marginBottom: '0.25rem' }}>
                        {item.icon} {item.label}
                      </div>
                      <div style={{ fontSize: '0.88rem', fontWeight: 800, color: '#1C1D21', lineHeight: 1.25, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {titleText}
                      </div>
                      {itemObj?.color && (
                        <div style={{ fontSize: '0.75rem', color: '#8E92A0', marginTop: '0.2rem' }}>
                          Color: <span style={{ color: '#606470', fontWeight: 700 }}>{itemObj.color}</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Developer / Debug Mode Inspector Section (Part 19 Requirement) */}
          <div style={{ borderTop: '1px dashed #ECEBF5', paddingTop: '1.5rem', marginTop: '0.5rem' }}>
            <details style={{ background: '#181924', color: '#F1F5F9', borderRadius: '16px', padding: '1rem 1.25rem', fontSize: '0.85rem' }}>
              <summary style={{ cursor: 'pointer', fontWeight: 800, color: '#A78BFA', userSelect: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                🛠️ Developer Debug View — 12-Dimensional Compatibility Analysis & Rule Trace
              </summary>
              <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.75rem', background: '#0F1117', padding: '0.85rem', borderRadius: '12px' }}>
                  <div><span style={{ color: '#94A3B8' }}>Rule Score:</span> <strong style={{ color: '#38BDF8' }}>{outfit.ruleScore ?? 'N/A'}/10</strong></div>
                  <div><span style={{ color: '#94A3B8' }}>ML Score:</span> <strong style={{ color: '#34D399' }}>{outfit.mlScore ?? 'N/A'}/10</strong></div>
                  <div><span style={{ color: '#94A3B8' }}>Combined:</span> <strong style={{ color: '#F472B6' }}>{outfit.combinedScore ?? outfit.matchScore}</strong></div>
                  <div><span style={{ color: '#94A3B8' }}>Critic Verdict:</span> <strong style={{ color: '#FBBF24' }}>{outfit.criticVerdict || 'PASS'}</strong></div>
                </div>

                {outfit.subScores && (
                  <div>
                    <div style={{ fontSize: '0.78rem', fontWeight: 800, color: '#CBD5E1', marginBottom: '0.4rem', textTransform: 'uppercase' }}>12-Dimension Sub-Scores:</div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))', gap: '0.5rem' }}>
                      {Object.entries(outfit.subScores).map(([dim, val]) => (
                        <div key={dim} style={{ background: '#27293D', padding: '0.4rem 0.6rem', borderRadius: '8px', fontSize: '0.75rem', display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ color: '#94A3B8' }}>{dim}:</span>
                          <strong style={{ color: '#A78BFA' }}>{val}/10</strong>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {outfit.appliedRules && outfit.appliedRules.length > 0 && (
                  <div>
                    <div style={{ fontSize: '0.78rem', fontWeight: 800, color: '#34D399', marginBottom: '0.3rem', textTransform: 'uppercase' }}>Applied Styling Rules:</div>
                    <ul style={{ margin: 0, paddingLeft: '1.2rem', color: '#E2E8F0', fontSize: '0.78rem', lineHeight: '1.5' }}>
                      {outfit.appliedRules.map((rule, rIdx) => (
                        <li key={rIdx}>{rule}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {outfit.issues && outfit.issues.length > 0 && (
                  <div>
                    <div style={{ fontSize: '0.78rem', fontWeight: 800, color: '#F87171', marginBottom: '0.3rem', textTransform: 'uppercase' }}>Detected Tradeoffs / Warnings:</div>
                    <ul style={{ margin: 0, paddingLeft: '1.2rem', color: '#FCA5A5', fontSize: '0.78rem', lineHeight: '1.5' }}>
                      {outfit.issues.map((iss, iIdx) => (
                        <li key={iIdx}>{iss}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </details>
          </div>

        </div>

      </div>
    </div>
  );
}
