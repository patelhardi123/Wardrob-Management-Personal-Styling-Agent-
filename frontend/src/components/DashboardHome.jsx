import React from 'react';
import { 
  Sparkles, 
  ArrowRight, 
  Calendar, 
  Shirt, 
  Flame, 
  GraduationCap, 
  Briefcase, 
  UserCheck, 
  Heart, 
  PartyPopper, 
  Grid
} from 'lucide-react';

export default function DashboardHome({ 
  userProfile, 
  clothes, 
  onAskForOutfit, 
  outfitResult, 
  onSelectOccasion 
}) {
  // Category counts calculated from inventory or fallback defaults
  const getCategoryCount = (catName, defaultCount) => {
    if (!clothes || clothes.length === 0) return defaultCount;
    const count = clothes.filter(c => c.category?.toLowerCase() === catName.toLowerCase()).length;
    return count > 0 ? count : defaultCount;
  };

  const categories = [
    { name: 'Tops', count: getCategoryCount('Top', 128), icon: '👕' },
    { name: 'Bottoms', count: getCategoryCount('Bottom', 96), icon: '👖' },
    { name: 'Outerwear', count: getCategoryCount('Outerwear', 42), icon: '🧥' },
    { name: 'Footwear', count: getCategoryCount('Footwear', 58), icon: '👟' },
    { name: 'Bags', count: getCategoryCount('Bag', 34), icon: '👜' },
    { name: 'Accessories', count: getCategoryCount('Accessory', 56), icon: '💍' },
  ];

  const occasionChips = [
    { id: 'college', label: 'College', icon: GraduationCap },
    { id: 'office', label: 'Office', icon: Briefcase },
    { id: 'interview', label: 'Interview', icon: UserCheck },
    { id: 'date-night', label: 'Date Night', icon: Heart },
    { id: 'party', label: 'Party', icon: PartyPopper },
    { id: 'more', label: 'More', icon: Grid },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      
      {/* Top Main Grid Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.8fr) minmax(0, 1fr)', gap: '1.75rem' }}>
        
        {/* Left Column Stack */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
          
          {/* Hero Banner Card */}
          <div style={{
            backgroundColor: '#FAF9FE',
            borderRadius: '24px',
            border: '1px solid #ECE7FE',
            padding: '2.25rem 2.5rem',
            position: 'relative',
            overflow: 'hidden',
            display: 'flex',
            alignItems: 'center',
            minHeight: '230px',
            boxShadow: '0 4px 20px rgba(124, 77, 255, 0.04)'
          }}>
            <div style={{ maxWidth: '52%', zIndex: 2 }}>
              <h2 style={{ fontSize: '1.85rem', fontWeight: 800, color: '#1C1D21', lineHeight: 1.25, marginBottom: '0.6rem' }}>
                Ready to get dressed?
              </h2>
              <p style={{ color: '#6A6E7D', fontSize: '0.92rem', lineHeight: 1.45, marginBottom: '1.5rem' }}>
                Tell us the occasion or let AI suggest the perfect outfit for you.
              </p>
              <button 
                onClick={onAskForOutfit}
                className="btn-primary"
                style={{
                  padding: '0.85rem 1.6rem',
                  borderRadius: '14px',
                  fontSize: '0.95rem',
                  boxShadow: '0 6px 20px rgba(124, 77, 255, 0.35)'
                }}
              >
                <Sparkles size={18} />
                Ask for an Outfit
              </button>
            </div>

            {/* Banner Right Image Artwork */}
            <div style={{
              position: 'absolute',
              right: '-10px',
              top: '50%',
              transform: 'translateY(-50%)',
              width: '46%',
              height: '115%',
              zIndex: 1,
              pointerEvents: 'none'
            }}>
              <img 
                src="/hero_banner.png" 
                alt="Outfit Flat Lay"
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'contain',
                  objectPosition: 'center right',
                  filter: 'drop-shadow(0 10px 15px rgba(0,0,0,0.06))'
                }}
              />
            </div>
          </div>

          {/* Daily Outfit Widget */}
          <div className="card-widget" style={{ borderRadius: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.2rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <Calendar size={20} color="#7C4DFF" />
                <div>
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#1C1D21' }}>Daily Outfit</h3>
                  <span style={{ fontSize: '0.78rem', color: '#8E92A0' }}>
                    Your AI-generated daily outfit based on your routine.
                  </span>
                </div>
              </div>
              <button 
                onClick={onAskForOutfit}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#7C4DFF',
                  fontWeight: 700,
                  fontSize: '0.85rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.3rem',
                  cursor: 'pointer'
                }}
              >
                View <ArrowRight size={15} />
              </button>
            </div>

            {/* Outfit Preview Display */}
            {outfitResult ? (
              <div style={{
                backgroundColor: '#FAF9FE',
                borderRadius: '16px',
                padding: '1.25rem',
                border: '1px solid #ECE7FE',
                display: 'flex',
                alignItems: 'center',
                gap: '1.5rem'
              }}>
                {outfitResult.aiModelImage && (
                  <img 
                    src={outfitResult.aiModelImage} 
                    alt="AI Outfit Visualization" 
                    style={{ width: '90px', height: '110px', borderRadius: '12px', objectFit: 'cover' }}
                  />
                )}
                <div>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#7C4DFF', textTransform: 'uppercase' }}>
                    {outfitResult.occasion}
                  </span>
                  <h4 style={{ fontSize: '1rem', fontWeight: 800, color: '#1C1D21', margin: '0.2rem 0 0.4rem 0' }}>
                    {outfitResult.outfitName}
                  </h4>
                  <p style={{ fontSize: '0.82rem', color: '#6A6E7D', lineHeight: 1.4 }}>
                    {outfitResult.reasoning}
                  </p>
                </div>
              </div>
            ) : (
              <div style={{
                backgroundColor: '#FAF9FE',
                borderRadius: '18px',
                border: '1px border-dashed #E4E0FA',
                padding: '2.5rem 1.5rem',
                textAlign: 'center',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem'
              }}>
                <Shirt size={32} color="#CBD0E1" />
                <p style={{ fontWeight: 700, fontSize: '0.9rem', color: '#1C1D21' }}>Your daily outfit will appear here</p>
                <span style={{ fontSize: '0.78rem', color: '#8E92A0' }}>Come back tomorrow for a fresh look!</span>
              </div>
            )}
          </div>

          {/* Need Inspiration Section */}
          <div className="card-widget" style={{ borderRadius: '24px' }}>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#1C1D21', marginBottom: '0.3rem' }}>
              Need inspiration?
            </h3>
            <p style={{ color: '#8E92A0', fontSize: '0.82rem', marginBottom: '1.1rem' }}>
              Explore outfit ideas for different occasions.
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
              {occasionChips.map((chip) => {
                const Icon = chip.icon;
                return (
                  <button
                    key={chip.id}
                    onClick={() => onSelectOccasion(chip.label)}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.6rem 1.1rem',
                      borderRadius: '14px',
                      backgroundColor: '#FFFFFF',
                      border: '1px solid #ECEBF5',
                      color: '#4A4D5A',
                      fontWeight: 600,
                      fontSize: '0.85rem',
                      cursor: 'pointer',
                      boxShadow: '0 2px 6px rgba(0, 0, 0, 0.02)',
                      transition: 'all 0.15s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = '#F0EBFF';
                      e.currentTarget.style.borderColor = '#D6C7FF';
                      e.currentTarget.style.color = '#7C4DFF';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = '#FFFFFF';
                      e.currentTarget.style.borderColor = '#ECEBF5';
                      e.currentTarget.style.color = '#4A4D5A';
                    }}
                  >
                    <Icon size={16} color="#7C4DFF" />
                    <span>{chip.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

        </div>

        {/* Right Column Stack */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
          
          {/* Style Profile Card */}
          <div className="card-widget" style={{ borderRadius: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#1C1D21' }}>Style Profile</h3>
              <button 
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#7C4DFF',
                  fontWeight: 700,
                  fontSize: '0.82rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.2rem',
                  cursor: 'pointer'
                }}
              >
                View Profile <ArrowRight size={14} />
              </button>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
              <img 
                src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=250" 
                alt="Profile Avatar" 
                style={{ width: '80px', height: '80px', borderRadius: '50%', objectFit: 'cover' }}
              />
              <div>
                <h4 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#1C1D21', marginBottom: '0.5rem' }}>
                  {userProfile?.stylePreference || 'Minimal • Classic'}
                </h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.6rem' }}>
                  {(userProfile?.tags || ['Neutral', 'Clean', 'Comfort']).map((tag, idx) => (
                    <span 
                      key={idx} 
                      style={{
                        padding: '0.25rem 0.65rem',
                        borderRadius: '8px',
                        backgroundColor: '#F3F1FD',
                        color: '#606470',
                        fontSize: '0.75rem',
                        fontWeight: 600
                      }}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
                <div style={{ fontSize: '0.78rem', color: '#8E92A0', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                  <span>⏳ Body Shape:</span>
                  <span style={{ fontWeight: 700, color: '#4A4D5A' }}>{userProfile?.bodyShape || 'Hourglass'}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Wardrobe Overview Card */}
          <div className="card-widget" style={{ borderRadius: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#1C1D21' }}>Wardrobe Overview</h3>
              <button 
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#7C4DFF',
                  fontWeight: 700,
                  fontSize: '0.82rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.2rem',
                  cursor: 'pointer'
                }}
              >
                View All <ArrowRight size={14} />
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', textAlign: 'center' }}>
              {categories.map((cat, idx) => (
                <div 
                  key={idx} 
                  style={{
                    backgroundColor: '#FAF9FE',
                    borderRadius: '16px',
                    padding: '0.9rem 0.5rem',
                    border: '1px solid #F0EEF8'
                  }}
                >
                  <div style={{ fontSize: '1.5rem', marginBottom: '0.3rem' }}>{cat.icon}</div>
                  <div style={{ fontWeight: 800, fontSize: '1.15rem', color: '#1C1D21' }}>{cat.count}</div>
                  <div style={{ fontSize: '0.75rem', color: '#8E92A0', fontWeight: 500 }}>{cat.name}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Outfit Streak Card */}
          <div className="card-widget" style={{ borderRadius: '24px' }}>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#1C1D21', marginBottom: '1.25rem' }}>
              Outfit Streak
            </h3>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
              {/* Circular Progress Ring */}
              <div style={{ position: 'relative', width: '90px', height: '90px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg width="90" height="90" viewBox="0 0 90 90">
                  <circle cx="45" cy="45" r="38" stroke="#F0EBFF" strokeWidth="8" fill="none" />
                  <circle 
                    cx="45" 
                    cy="45" 
                    r="38" 
                    stroke="#7C4DFF" 
                    strokeWidth="8" 
                    fill="none" 
                    strokeDasharray="238" 
                    strokeDashoffset="60"
                    strokeLinecap="round" 
                    transform="rotate(-90 45 45)"
                  />
                </svg>
                <Shirt size={24} color="#7C4DFF" style={{ position: 'absolute' }} />
              </div>

              <div>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem' }}>
                  <span style={{ fontSize: '1.75rem', fontWeight: 800, color: '#1C1D21' }}>12</span>
                  <span style={{ fontSize: '0.95rem', fontWeight: 600, color: '#7E8292' }}>days</span>
                </div>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#1C1D21', margin: '0.2rem 0 0.3rem 0', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                  Keep it going! <Flame size={16} color="#FF5252" fill="#FF5252" />
                </div>
                <div style={{ fontSize: '0.74rem', color: '#8E92A0' }}>
                  Wear • Track • Repeat
                </div>
              </div>
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}
