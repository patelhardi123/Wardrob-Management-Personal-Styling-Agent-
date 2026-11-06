import React, { useState } from 'react';
import { Sparkles, CloudRain, Sun, Compass, Play, RotateCcw } from 'lucide-react';
import AgentTrace from './AgentTrace';

export default function OutfitGenerator({ userProfile, onGenerateOutfit, outfitResult, isGenerating }) {
  const [requestText, setRequestText] = useState('Job interview tomorrow, expecting rainy weather');
  const [selectedOccasion, setSelectedOccasion] = useState('interview');
  const [selectedWeather, setSelectedWeather] = useState('rainy');

  const occasionPresets = [
    { id: 'interview', label: 'Job Interview' },
    { id: 'college', label: 'Daily College' },
    { id: 'office', label: 'Office Formal' },
    { id: 'party', label: 'Night Party' },
    { id: 'date', label: 'Dinner Date' },
    { id: 'festival', label: 'Festival / Traditional' },
    { id: 'casual', label: 'Casual Outing' }
  ];

  const weatherPresets = [
    { id: 'sunny', label: 'Sunny / Warm (28°C)', icon: Sun },
    { id: 'rainy', label: 'Rainy & Breezy (20°C)', icon: CloudRain },
    { id: 'chilly', label: 'Chilly / Winter (12°C)', icon: Compass }
  ];

  const handleTrigger = (e) => {
    e.preventDefault();
    onGenerateOutfit({ requestText, occasion: selectedOccasion, weather: selectedWeather });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      
      {/* Top Banner */}
      <div className="card-widget" style={{
        backgroundColor: '#FAF9FE',
        borderColor: '#ECE7FE',
        borderRadius: '24px',
        padding: '2rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.6rem' }}>
          <span style={{
            padding: '0.35rem 0.75rem',
            borderRadius: '20px',
            backgroundColor: '#F0EBFF',
            color: '#7C4DFF',
            fontWeight: 700,
            fontSize: '0.78rem'
          }}>
            LangGraph Stylist Studio
          </span>
        </div>
        <h2 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#1C1D21', marginBottom: '0.5rem' }}>
          Multi-Agent Outfit Orchestration
        </h2>
        <p style={{ color: '#606470', fontSize: '0.92rem', maxWidth: '800px', lineHeight: 1.5 }}>
          Enter your occasion or daily routine. Specialized agents collaborate to verify weather, trends, style fit, and wardrobe inventory — completing EVERY slot (Tops, Bottoms, Outerwear, Footwear, Bag & Accessories).
        </p>
      </div>

      {/* Input Controls Panel */}
      <div className="card-widget" style={{ borderRadius: '24px' }}>
        <form onSubmit={handleTrigger}>
          
          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ fontSize: '0.9rem', fontWeight: 700, color: '#1C1D21', display: 'block', marginBottom: '0.5rem' }}>
              Free-Text Request / Prompt
            </label>
            <input 
              type="text" 
              value={requestText} 
              onChange={(e) => setRequestText(e.target.value)}
              placeholder="e.g. Need an outfit for a tech job interview tomorrow, it might rain..."
              style={{
                width: '100%',
                padding: '0.85rem 1.1rem',
                borderRadius: '14px',
                border: '1px solid #ECEBF5',
                backgroundColor: '#FAF9FE',
                fontSize: '0.95rem',
                outline: 'none',
                color: '#1C1D21'
              }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
            
            {/* Occasion Quick Presets */}
            <div>
              <label style={{ fontSize: '0.85rem', fontWeight: 700, color: '#1C1D21', display: 'block', marginBottom: '0.5rem' }}>
                Occasion Presets
              </label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {occasionPresets.map(occ => (
                  <button
                    key={occ.id}
                    type="button"
                    onClick={() => setSelectedOccasion(occ.id)}
                    style={{
                      background: selectedOccasion === occ.id ? '#7C4DFF' : '#FAF9FE',
                      border: selectedOccasion === occ.id ? 'none' : '1px solid #ECEBF5',
                      color: selectedOccasion === occ.id ? '#FFFFFF' : '#606470',
                      borderRadius: '10px',
                      padding: '0.45rem 0.85rem',
                      fontSize: '0.82rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    {occ.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Weather Presets */}
            <div>
              <label style={{ fontSize: '0.85rem', fontWeight: 700, color: '#1C1D21', display: 'block', marginBottom: '0.5rem' }}>
                Weather Context
              </label>
              <div style={{ display: 'flex', gap: '0.6rem' }}>
                {weatherPresets.map(w => {
                  const Icon = w.icon;
                  const isSelected = selectedWeather === w.id;
                  return (
                    <button
                      key={w.id}
                      type="button"
                      onClick={() => setSelectedWeather(w.id)}
                      style={{
                        flex: 1,
                        background: isSelected ? '#F0EBFF' : '#FAF9FE',
                        border: isSelected ? '1px solid #7C4DFF' : '1px solid #ECEBF5',
                        color: isSelected ? '#7C4DFF' : '#606470',
                        borderRadius: '10px',
                        padding: '0.55rem 0.5rem',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.4rem'
                      }}
                    >
                      <Icon size={15} /> {w.label}
                    </button>
                  );
                })}
              </div>
            </div>

          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button 
              type="submit" 
              disabled={isGenerating}
              className="btn-primary"
              style={{ fontSize: '0.95rem', padding: '0.85rem 1.8rem' }}
            >
              {isGenerating ? (
                <>
                  <RotateCcw size={18} className="pulse-active" /> Executing Multi-Agent Pipeline...
                </>
              ) : (
                <>
                  <Play size={18} /> Run LangGraph Agent Pipeline
                </>
              )}
            </button>
          </div>

        </form>
      </div>

      {/* Outfit Results & Complete Slot Breakdown */}
      {outfitResult && (outfitResult.status === 'no_match' || outfitResult.count === 0 || !outfitResult.slots) ? (
        <div className="card-widget" style={{
          borderRadius: '24px',
          padding: '3rem 2rem',
          textAlign: 'center',
          background: '#FFFFFF',
          border: '1px solid #ECEBF5'
        }}>
          <div style={{
            width: '60px',
            height: '60px',
            borderRadius: '50%',
            backgroundColor: '#F3F0FF',
            color: '#7C4DFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1.25rem'
          }}>
            <Sparkles size={26} />
          </div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#1C1D21', marginBottom: '0.5rem' }}>
            No Matching Outfits Found
          </h3>
          <p style={{ color: '#606470', fontSize: '0.95rem', maxWidth: '520px', margin: '0 auto 1rem', lineHeight: 1.5 }}>
            {outfitResult.message || "We couldn't find a suitable outfit in your current wardrobe for this occasion."}
          </p>
        </div>
      ) : outfitResult && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: '1.75rem' }}>
          
          {/* Left Column: Recommendation & Slots */}
          <div className="card-widget" style={{ borderRadius: '24px' }}>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem' }}>
              <div>
                <span style={{
                  padding: '0.25rem 0.65rem',
                  borderRadius: '8px',
                  backgroundColor: '#F0EBFF',
                  color: '#7C4DFF',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  display: 'inline-block',
                  marginBottom: '0.4rem'
                }}>
                  Top Pick — Outfit #1
                </span>
                <h3 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#1C1D21' }}>
                  {outfitResult.occasion}
                </h3>
              </div>
              <span style={{
                padding: '0.35rem 0.75rem',
                borderRadius: '20px',
                backgroundColor: '#E6F9F0',
                color: '#00B86B',
                fontWeight: 700,
                fontSize: '0.82rem'
              }}>
                Match Score: {outfitResult.confidence}
              </span>
            </div>

            {/* Justification Box */}
            <div style={{
              backgroundColor: '#FAF9FE',
              borderLeft: '4px solid #7C4DFF',
              padding: '1rem 1.25rem',
              borderRadius: '12px',
              fontSize: '0.88rem',
              lineHeight: 1.5,
              marginBottom: '1.5rem',
              color: '#4A4D5A'
            }}>
              <strong style={{ color: '#1C1D21' }}>Stylist Reason:</strong> {outfitResult.reasoning}
            </div>

            {/* Complete Slots Breakdown */}
            <h4 style={{ fontSize: '0.88rem', fontWeight: 800, marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#8E92A0' }}>
              Complete Outfit Slots (All 6 Categories Filled)
            </h4>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.9rem' }}>
              
              <div style={{ backgroundColor: '#FAF9FE', padding: '0.85rem 1rem', borderRadius: '14px', border: '1px solid #ECEBF5' }}>
                <span style={{ fontSize: '0.7rem', color: '#8E92A0', textTransform: 'uppercase', fontWeight: 700 }}>Top Slot</span>
                <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#1C1D21' }}>{outfitResult.slots.top.name}</div>
                <span style={{ fontSize: '0.75rem', color: '#7C4DFF', fontWeight: 600 }}>{outfitResult.slots.top.color} • {outfitResult.slots.top.style}</span>
              </div>

              <div style={{ backgroundColor: '#FAF9FE', padding: '0.85rem 1rem', borderRadius: '14px', border: '1px solid #ECEBF5' }}>
                <span style={{ fontSize: '0.7rem', color: '#8E92A0', textTransform: 'uppercase', fontWeight: 700 }}>Bottom Slot</span>
                <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#1C1D21' }}>{outfitResult.slots.bottom.name}</div>
                <span style={{ fontSize: '0.75rem', color: '#7C4DFF', fontWeight: 600 }}>{outfitResult.slots.bottom.color} • {outfitResult.slots.bottom.style}</span>
              </div>

              <div style={{ backgroundColor: '#FAF9FE', padding: '0.85rem 1rem', borderRadius: '14px', border: '1px solid #ECEBF5' }}>
                <span style={{ fontSize: '0.7rem', color: '#8E92A0', textTransform: 'uppercase', fontWeight: 700 }}>Outerwear Slot</span>
                <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#1C1D21' }}>{outfitResult.slots.outerwear.name}</div>
                <span style={{ fontSize: '0.75rem', color: '#00B86B', fontWeight: 600 }}>{outfitResult.slots.outerwear.color} • Rain resistant</span>
              </div>

              <div style={{ backgroundColor: '#FAF9FE', padding: '0.85rem 1rem', borderRadius: '14px', border: '1px solid #ECEBF5' }}>
                <span style={{ fontSize: '0.7rem', color: '#8E92A0', textTransform: 'uppercase', fontWeight: 700 }}>Footwear Slot</span>
                <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#1C1D21' }}>{outfitResult.slots.footwear.name}</div>
                <span style={{ fontSize: '0.75rem', color: '#7C4DFF', fontWeight: 600 }}>{outfitResult.slots.footwear.color} • {outfitResult.slots.footwear.style}</span>
              </div>

              <div style={{ backgroundColor: '#FAF9FE', padding: '0.85rem 1rem', borderRadius: '14px', border: '1px solid #ECEBF5' }}>
                <span style={{ fontSize: '0.7rem', color: '#8E92A0', textTransform: 'uppercase', fontWeight: 700 }}>Bag / Purse Slot</span>
                <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#1C1D21' }}>{outfitResult.slots.bag.name}</div>
                <span style={{ fontSize: '0.75rem', color: '#7C4DFF', fontWeight: 600 }}>{outfitResult.slots.bag.color}</span>
              </div>

              <div style={{ backgroundColor: '#FAF9FE', padding: '0.85rem 1rem', borderRadius: '14px', border: '1px solid #ECEBF5' }}>
                <span style={{ fontSize: '0.7rem', color: '#8E92A0', textTransform: 'uppercase', fontWeight: 700 }}>Accessory Slot</span>
                <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#1C1D21' }}>{outfitResult.slots.accessories[0].name}</div>
                <span style={{ fontSize: '0.75rem', color: '#E91E63', fontWeight: 600 }}>{outfitResult.slots.accessories[0].color}</span>
              </div>

            </div>

          </div>

          {/* Right Column: AI Model Photo Visualization */}
          <div className="card-widget" style={{ borderRadius: '24px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <span style={{
                padding: '0.25rem 0.65rem',
                borderRadius: '8px',
                backgroundColor: '#FFF0F5',
                color: '#E91E63',
                fontSize: '0.72rem',
                fontWeight: 700
              }}>
                Visualization Agent
              </span>
              <Sparkles size={16} color="#E91E63" />
            </div>

            <div style={{ position: 'relative', width: '100%', flex: 1, minHeight: '380px', borderRadius: '16px', overflow: 'hidden', background: '#F0EBFF' }}>
              <img 
                src={outfitResult.visualizationImage} 
                alt="AI Generated Model Wearing Outfit" 
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
              <div style={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                right: 0,
                background: 'linear-gradient(to top, rgba(0,0,0,0.8), transparent)',
                padding: '1.25rem 1rem 0.85rem',
                fontSize: '0.78rem',
                color: '#D6C7FF'
              }}>
                <strong style={{ color: 'white', display: 'block', marginBottom: '0.1rem' }}>Generic Model AI Render</strong>
                Generated from outfit attributes
              </div>
            </div>
          </div>

        </div>
      )}

      {/* Embedded Agent Trace Section */}
      <AgentTrace traceData={outfitResult?.agentTrace} />

    </div>
  );
}

