import React, { useState } from 'react';
import { X, Sparkles, Camera, Check, Tag, UserCheck } from 'lucide-react';

export default function OnboardingModal({ isOpen, onClose, userProfile, onSave }) {
  const [stylePreference, setStylePreference] = useState(userProfile.stylePreference);
  const [bodyShape, setBodyShape] = useState(userProfile.bodyShape);
  const [defaultRoutine, setDefaultRoutine] = useState(userProfile.defaultRoutine);
  const [selectedTags, setSelectedTags] = useState(userProfile.styleTags || []);
  const [activeMode, setActiveMode] = useState('picker'); // 'picker' or 'photo'
  const [photoUploaded, setPhotoUploaded] = useState(false);

  if (!isOpen) return null;

  const styleOptions = [
    { id: 'minimal', label: 'Minimal', desc: 'Clean lines, neutral palette, effortless simplicity.' },
    { id: 'classic', label: 'Classic', desc: 'Timeless cuts, elegant structures, refined looks.' },
    { id: 'medium', label: 'Medium / Balanced', desc: 'Versatile mix of casual comfort and tailored aesthetics.' },
    { id: 'stylish-trendy', label: 'Stylish / Trendy', desc: 'Modern silhouettes, current fashion-forward details.' },
    { id: 'bold', label: 'Bold & Expressive', desc: 'Vibrant colors, eye-catching patterns, distinct statements.' }
  ];

  const availableTags = ['streetwear', 'formal-office', 'ethnic', 'athleisure', 'minimal-chic', 'vintage', 'preppy', 'smart-casual'];
  const bodyShapes = ['hourglass', 'pear', 'rectangle', 'inverted triangle', 'apple'];

  const toggleTag = (tag) => {
    if (selectedTags.includes(tag)) {
      setSelectedTags(selectedTags.filter(t => t !== tag));
    } else {
      setSelectedTags([...selectedTags, tag]);
    }
  };

  const handlePhotoSimulate = () => {
    setPhotoUploaded(true);
    // Simulate AI proposal
    setTimeout(() => {
      setStylePreference('stylish-trendy');
      setBodyShape('hourglass');
      if (!selectedTags.includes('smart-casual')) {
        setSelectedTags([...selectedTags, 'smart-casual']);
      }
    }, 600);
  };

  const handleSave = () => {
    onSave({
      ...userProfile,
      stylePreference,
      bodyShape,
      defaultRoutine,
      styleTags: selectedTags
    });
    onClose();
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(10px)',
      zIndex: 100,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1.5rem'
    }}>
      <div className="glass-panel-accent" style={{ maxWidth: '680px', width: '100%', maxHeight: '90vh', overflowY: 'auto', padding: '2rem' }}>
        
        {/* Modal Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <div>
            <span className="chip chip-purple" style={{ marginBottom: '0.4rem' }}>Phase 1 Onboarding</span>
            <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.5rem', fontWeight: 700 }}>
              Establish Your Personal Style Profile
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Stored once and used across all multi-agent outfit recommendations.
            </p>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={24} />
          </button>
        </div>

        {/* Mode Selector (Picker vs Photo proposal) */}
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', background: 'rgba(0,0,0,0.3)', padding: '0.35rem', borderRadius: '12px' }}>
          <button 
            onClick={() => setActiveMode('picker')}
            style={{
              flex: 1,
              padding: '0.65rem',
              borderRadius: '8px',
              border: 'none',
              background: activeMode === 'picker' ? 'var(--gradient-main)' : 'transparent',
              color: 'white',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              fontSize: '0.88rem'
            }}
          >
            <Sparkles size={16} /> Method A: Quick Preference Picker
          </button>

          <button 
            onClick={() => setActiveMode('photo')}
            style={{
              flex: 1,
              padding: '0.65rem',
              borderRadius: '8px',
              border: 'none',
              background: activeMode === 'photo' ? 'var(--gradient-main)' : 'transparent',
              color: 'white',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              fontSize: '0.88rem'
            }}
          >
            <Camera size={16} /> Method B: Photo AI Proposal
          </button>
        </div>

        {activeMode === 'photo' && (
          <div style={{
            background: 'rgba(139, 92, 246, 0.1)',
            border: '1px dashed var(--primary-purple)',
            borderRadius: '12px',
            padding: '1.5rem',
            textAlign: 'center',
            marginBottom: '1.5rem'
          }}>
            <Camera size={36} color="var(--primary-purple)" style={{ marginBottom: '0.5rem' }} />
            <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.25rem' }}>Upload Selfie for Style Signal Extraction</h4>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
              Infers clothing-relevant signals (skin-tone category & silhouette) to propose editable defaults. Never stored silently!
            </p>
            {!photoUploaded ? (
              <button onClick={handlePhotoSimulate} className="btn-primary" style={{ margin: '0 auto', fontSize: '0.85rem' }}>
                Simulate Photo Analysis
              </button>
            ) : (
              <div style={{ color: 'var(--accent-emerald)', fontSize: '0.85rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem' }}>
                <Check size={18} /> Analysis Complete: Warm Undertone & Hourglass Silhouette derived! (Review options below)
              </div>
            )}
          </div>
        )}

        {/* Style Intensity Picker */}
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-main)', display: 'block', marginBottom: '0.75rem' }}>
            1. Select Aesthetic Intensity
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(1, 1fr)', gap: '0.65rem' }}>
            {styleOptions.map((opt) => (
              <div 
                key={opt.id}
                onClick={() => setStylePreference(opt.id)}
                style={{
                  background: stylePreference === opt.id ? 'rgba(139, 92, 246, 0.2)' : 'rgba(255,255,255,0.03)',
                  border: stylePreference === opt.id ? '1px solid var(--primary-purple)' : '1px solid var(--border-glass)',
                  borderRadius: '10px',
                  padding: '0.85rem 1rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  transition: 'all 0.2s ease'
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.92rem', color: stylePreference === opt.id ? '#c084fc' : 'var(--text-main)' }}>
                    {opt.label}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{opt.desc}</div>
                </div>
                {stylePreference === opt.id && <Check size={18} color="#c084fc" />}
              </div>
            ))}
          </div>
        </div>

        {/* Default Routine & Body Shape Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
          <div>
            <label style={{ fontSize: '0.85rem', fontWeight: 600, display: 'block', marginBottom: '0.5rem' }}>
              Default Daily Routine
            </label>
            <select 
              value={defaultRoutine} 
              onChange={(e) => setDefaultRoutine(e.target.value)}
              className="input-field"
            >
              <option value="college">College / University</option>
              <option value="office">Corporate / Office</option>
              <option value="casual">Work From Home / Casual</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.85rem', fontWeight: 600, display: 'block', marginBottom: '0.5rem' }}>
              Body Silhouette (Fit Guidance)
            </label>
            <select 
              value={bodyShape} 
              onChange={(e) => setBodyShape(e.target.value)}
              className="input-field"
              style={{ textTransform: 'capitalize' }}
            >
              {bodyShapes.map(shape => (
                <option key={shape} value={shape}>{shape.charAt(0).toUpperCase() + shape.slice(1)}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Style Tags */}
        <div style={{ marginBottom: '2rem' }}>
          <label style={{ fontSize: '0.85rem', fontWeight: 600, display: 'block', marginBottom: '0.5rem' }}>
            Style Tags & Micro-Aesthetics
          </label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {availableTags.map(tag => {
              const isSelected = selectedTags.includes(tag);
              return (
                <button
                  key={tag}
                  onClick={() => toggleTag(tag)}
                  style={{
                    background: isSelected ? 'rgba(236, 72, 153, 0.2)' : 'rgba(255, 255, 255, 0.04)',
                    border: isSelected ? '1px solid var(--primary-pink)' : '1px solid var(--border-glass)',
                    color: isSelected ? '#f472b6' : 'var(--text-muted)',
                    borderRadius: '20px',
                    padding: '0.4rem 0.85rem',
                    fontSize: '0.8rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.35rem'
                  }}
                >
                  <Tag size={12} /> #{tag}
                </button>
              );
            })}
          </div>
        </div>

        {/* Footer Actions */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
          <button onClick={onClose} className="btn-secondary">Cancel</button>
          <button onClick={handleSave} className="btn-primary">
            <UserCheck size={16} /> Save Profile & Continue
          </button>
        </div>

      </div>
    </div>
  );
}
