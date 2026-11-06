import React from 'react';
import { Sparkles, Shirt, Sliders, User, RefreshCw, Zap } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, onOpenOnboarding, userProfile }) {
  return (
    <header className="glass-panel" style={{ borderRadius: 0, borderTop: 'none', borderLeft: 'none', borderRight: 'none', sticky: 'top', zIndex: 50, padding: '0.85rem 2rem' }}>
      <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        
        {/* Brand Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ 
            width: '42px', 
            height: '42px', 
            borderRadius: '12px', 
            background: 'var(--gradient-main)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: 'var(--shadow-glow)'
          }}>
            <Sparkles size={24} color="white" />
          </div>
          <div>
            <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.35rem', fontWeight: 800, letterSpacing: '-0.02em', background: 'var(--gradient-main)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              WARDROBE.AI
            </h1>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
              Multi-Agent Stylist
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', gap: '0.5rem', background: 'rgba(0,0,0,0.3)', padding: '0.3rem', borderRadius: '12px', border: '1px solid var(--border-glass)' }}>
          <button 
            onClick={() => setActiveTab('stylist')}
            className={`btn-secondary ${activeTab === 'stylist' ? 'chip-purple' : ''}`}
            style={{ border: 'none', padding: '0.5rem 1.25rem', fontSize: '0.88rem' }}
          >
            <Zap size={16} /> Stylist Studio
          </button>
          
          <button 
            onClick={() => setActiveTab('wardrobe')}
            className={`btn-secondary ${activeTab === 'wardrobe' ? 'chip-purple' : ''}`}
            style={{ border: 'none', padding: '0.5rem 1.25rem', fontSize: '0.88rem' }}
          >
            <Shirt size={16} /> Digital Wardrobe
          </button>

          <button 
            onClick={() => setActiveTab('trace')}
            className={`btn-secondary ${activeTab === 'trace' ? 'chip-pink' : ''}`}
            style={{ border: 'none', padding: '0.5rem 1.25rem', fontSize: '0.88rem' }}
          >
            <RefreshCw size={16} /> Agent Trace
          </button>
        </nav>

        {/* User Style Profile Badge & Trigger */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button 
            onClick={onOpenOnboarding}
            style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid var(--border-glass-accent)',
              borderRadius: '12px',
              padding: '0.4rem 0.85rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              cursor: 'pointer',
              color: 'var(--text-main)',
              transition: 'all 0.2s ease'
            }}
            title="Edit Style Profile Onboarding"
          >
            <img 
              src={userProfile.avatarUrl} 
              alt={userProfile.name} 
              style={{ width: '32px', height: '32px', borderRadius: '50%', objectFit: 'cover' }} 
            />
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontSize: '0.82rem', fontWeight: 600 }}>{userProfile.name}</div>
              <div style={{ fontSize: '0.7rem', color: '#c084fc', textTransform: 'capitalize' }}>
                {userProfile.stylePreference.replace('-', ' ')} • {userProfile.bodyShape}
              </div>
            </div>
            <Sliders size={16} color="var(--text-muted)" />
          </button>
        </div>

      </div>
    </header>
  );
}
