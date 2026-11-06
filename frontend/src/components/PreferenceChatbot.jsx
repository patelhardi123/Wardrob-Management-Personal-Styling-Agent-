import React, { useState, useEffect } from 'react';
import { Sparkles, Send, User, Bot, CheckCircle2, ArrowRight, RefreshCw, Sliders, Check, ChevronDown } from 'lucide-react';
import { parseContextRules } from '../utils/contextParser';

export default function PreferenceChatbot({ userProfile, onUpdateProfile, onNavigateToTab }) {
  const defaultInitialMessages = [
    {
      sender: 'bot',
      text: `Hello ${userProfile?.name || 'there'}! 👋 I am your AI Stylist Assistant. Customize your styling preferences or click quick filters below!`,
      timestamp: 'Just now'
    }
  ];

  const [messages, setMessages] = useState(() => {
    if (userProfile?.chatMessages && userProfile.chatMessages.length > 0) {
      return userProfile.chatMessages;
    }
    return defaultInitialMessages;
  });

  useEffect(() => {
    if (userProfile?.chatMessages && userProfile.chatMessages.length > 0) {
      setMessages(userProfile.chatMessages);
    }
  }, [userProfile?.chatMessages]);

  const [inputText, setInputText] = useState('');

  const quickPresets = [
    {
      label: '🎒 No Bags / Purses',
      prompt: "I want my daily outfits without carrying bags or purses.",
      ruleKey: 'excludeBags'
    },
    {
      label: '💎 Minimal Accessories',
      prompt: 'I prefer minimal clean outfits without extra accessories or jewellery.',
      ruleKey: 'excludeAccessories'
    },
    {
      label: '👔 Smart Casual Vibe',
      prompt: 'My main requirement is daily smart-casual outfit rotation for regular outings.'
    },
    {
      label: '💼 Formal Office Vibe',
      prompt: 'I need office-appropriate smart casual daily outfits.'
    }
  ];

  const handleSendMessage = (customPrompt) => {
    const textToSend = customPrompt || inputText;
    if (!textToSend.trim()) return;

    const userMsg = { 
      sender: 'user', 
      text: textToSend, 
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
    };
    const updatedMessages = [...messages, userMsg];

    const updatedContext = parseContextRules(textToSend, userProfile);

    setTimeout(() => {
      let botText = `Saved preference: "${textToSend}".`;
      if (updatedContext.activeExclusions && updatedContext.activeExclusions.length > 0) {
        botText += ` Active rules applied across all outfit looks: ${updatedContext.activeExclusions.join(', ')}.`;
      } else {
        botText += ` Updated daily outfit matching algorithm!`;
      }

      const botReply = {
        sender: 'bot',
        text: botText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isSuccessCard: true,
        contextData: updatedContext
      };

      const finalMessages = [...updatedMessages, botReply];
      setMessages(finalMessages);
      
      onUpdateProfile({
        ...updatedContext,
        chatMessages: finalMessages
      });
    }, 350);

    setInputText('');
  };

  const handleToggleRule = (ruleKey, promptText) => {
    const isCurrentlyActive = Boolean(userProfile?.[ruleKey]);
    if (isCurrentlyActive) {
      const newContext = {
        ...userProfile,
        [ruleKey]: false,
        activeExclusions: (userProfile?.activeExclusions || []).filter(ex => !ex.toLowerCase().includes(ruleKey.replace('exclude', '').toLowerCase()))
      };
      onUpdateProfile(newContext);
    } else {
      handleSendMessage(promptText);
    }
  };

  const handleResetRules = () => {
    const resetMsg = {
      sender: 'bot',
      text: '🔄 All custom context constraints have been cleared. Complete outfit matching is restored!',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    const resetMessagesList = [
      ...defaultInitialMessages,
      resetMsg
    ];

    const resetContext = {
      ...userProfile,
      excludeBags: false,
      excludeAccessories: false,
      excludeOuterwear: false,
      excludeFootwear: false,
      dynamicExclusions: [],
      activeExclusions: [],
      userBio: '',
      context_rules: null,
      lastUpdatedRule: null,
      chatMessages: resetMessagesList
    };

    setMessages(resetMessagesList);
    onUpdateProfile(resetContext);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', width: '100%', maxWidth: '1100px', margin: '0 auto' }}>
      
      {/* 1. TOP HERO BANNER (Image 2 Aesthetic Look) */}
      <div style={{
        position: 'relative',
        borderRadius: '28px',
        overflow: 'hidden',
        minHeight: '380px',
        backgroundColor: '#F5EFEB',
        display: 'flex',
        alignItems: 'center',
        boxShadow: '0 12px 35px rgba(47, 65, 86, 0.1)',
        border: '1px solid rgba(86, 124, 141, 0.2)'
      }}>
        {/* Background Wardrobe Rack Image */}
        <div style={{
          position: 'absolute',
          top: 0,
          right: 0,
          bottom: 0,
          width: '58%',
          backgroundImage: 'url("/hero_banner.png")',
          backgroundSize: 'cover',
          backgroundPosition: 'center right',
          maskImage: 'linear-gradient(to right, transparent 0%, black 35%)',
          WebkitMaskImage: 'linear-gradient(to right, transparent 0%, black 35%)',
          opacity: 0.95
        }} />

        {/* Content Box */}
        <div style={{
          position: 'relative',
          zIndex: 2,
          padding: '3rem 3.5rem',
          maxWidth: '560px'
        }}>
          <h1 style={{
            fontSize: '3.1rem',
            fontWeight: 800,
            color: '#2F4156',
            fontFamily: 'var(--font-heading)',
            lineHeight: 1.1,
            letterSpacing: '1px',
            marginBottom: '0.8rem'
          }}>
            TRENDY.<br />
            AESTHETIC.<br />
            <span style={{ color: '#567C8D' }}>YOU.</span>
          </h1>

          <p style={{
            fontSize: '1rem',
            fontWeight: 600,
            color: '#567C8D',
            letterSpacing: '1.5px',
            textTransform: 'uppercase',
            marginBottom: '1rem'
          }}>
            FASHION THAT SPEAKS YOUR STYLE
          </p>

          <div style={{
            fontSize: '0.85rem',
            color: '#78909C',
            fontWeight: 600,
            marginBottom: '1.75rem',
            letterSpacing: '0.5px'
          }}>
            Trendy Looks &nbsp;|&nbsp; Premium Quality &nbsp;|&nbsp; Everyday Slay
          </div>

          <button
            onClick={() => onNavigateToTab('daily-outfit')}
            style={{
              backgroundColor: '#2F4156',
              color: '#FFFFFF',
              border: 'none',
              padding: '0.85rem 1.8rem',
              borderRadius: '12px',
              fontWeight: 800,
              fontSize: '0.88rem',
              letterSpacing: '1.2px',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.6rem',
              boxShadow: '0 6px 20px rgba(47, 65, 86, 0.3)',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#567C8D'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#2F4156'; e.currentTarget.style.transform = 'none'; }}
          >
            NEW STYLES. NEW YOU. <ArrowRight size={17} />
          </button>
        </div>
      </div>

      {/* 2. QUICK PREFERENCE FILTER CONTROLS */}
      <div className="card-widget" style={{ borderRadius: '20px', padding: '1.25rem 1.5rem', background: '#FFFFFF' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <div style={{ width: '34px', height: '34px', borderRadius: '10px', background: '#C8D9E6', color: '#2F4156', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Sliders size={18} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#2F4156', lineHeight: 1.2 }}>
                Quick Preference Controls
              </h3>
              <span style={{ fontSize: '0.78rem', color: '#567C8D' }}>
                Toggle rules instantly or type custom instructions into the chatbot below
              </span>
            </div>
          </div>

          {userProfile?.activeExclusions && userProfile.activeExclusions.length > 0 && (
            <button
              onClick={handleResetRules}
              style={{
                background: '#F5EFEB',
                border: '1px solid rgba(86,124,141,0.2)',
                color: '#2F4156',
                padding: '0.4rem 0.85rem',
                borderRadius: '12px',
                fontSize: '0.78rem',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
                transition: 'all 0.15s ease'
              }}
            >
              <RefreshCw size={13} /> Clear Active Rules ({userProfile.activeExclusions.length})
            </button>
          )}
        </div>

        {/* Quick Rule Interactive Pills */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.65rem' }}>
          {quickPresets.map((preset, idx) => {
            const isActive = preset.ruleKey ? Boolean(userProfile?.[preset.ruleKey]) : false;
            return (
              <button
                key={idx}
                onClick={() => {
                  if (preset.ruleKey) {
                    handleToggleRule(preset.ruleKey, preset.prompt);
                  } else {
                    handleSendMessage(preset.prompt);
                  }
                }}
                style={{
                  background: isActive ? '#2F4156' : '#F5EFEB',
                  border: isActive ? 'none' : '1px solid rgba(86, 124, 141, 0.15)',
                  padding: '0.55rem 1rem',
                  borderRadius: '14px',
                  fontSize: '0.82rem',
                  fontWeight: 700,
                  color: isActive ? '#FFFFFF' : '#2F4156',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.45rem',
                  boxShadow: isActive ? '0 4px 14px rgba(47, 65, 86, 0.25)' : 'none'
                }}
              >
                {isActive && <Check size={14} />}
                <span>{preset.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. INTERACTIVE CHATBOT ASSISTANT (Under the Hero Banner) */}
      <div className="card-widget" style={{ borderRadius: '24px', padding: '1.5rem', display: 'flex', flexDirection: 'column', height: '520px', background: '#FFFFFF' }}>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1rem', borderBottom: '1px solid #E2E8F0', paddingBottom: '0.75rem' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '10px', background: '#2F4156', color: '#FFF', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Bot size={18} />
          </div>
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#2F4156' }}>AI Stylist Assistant</h3>
            <span style={{ fontSize: '0.72rem', color: '#567C8D', fontWeight: 600 }}>Ask styling advice or specify outfit exclusions</span>
          </div>
        </div>

        {/* Chat Messages */}
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.1rem', paddingRight: '0.4rem', marginBottom: '1.25rem' }}>
          {messages.map((msg, idx) => (
            <div key={idx} style={{
              display: 'flex',
              flexDirection: msg.sender === 'user' ? 'row-reverse' : 'row',
              alignItems: 'flex-start',
              gap: '0.75rem'
            }}>
              <div style={{
                width: '36px',
                height: '36px',
                borderRadius: '12px',
                background: msg.sender === 'user' ? '#2F4156' : '#567C8D',
                color: '#FFF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                boxShadow: '0 4px 12px rgba(47, 65, 86, 0.15)'
              }}>
                {msg.sender === 'user' ? <User size={18} /> : <Bot size={18} />}
              </div>

              <div style={{ maxWidth: '82%' }}>
                <div style={{
                  padding: '0.95rem 1.25rem',
                  borderRadius: msg.sender === 'user' ? '20px 20px 4px 20px' : '20px 20px 20px 4px',
                  background: msg.sender === 'user' ? '#2F4156' : '#F5EFEB',
                  color: msg.sender === 'user' ? '#FFFFFF' : '#2F4156',
                  fontSize: '0.92rem',
                  lineHeight: 1.5,
                  fontWeight: 500,
                  boxShadow: '0 2px 8px rgba(0,0,0,0.03)'
                }}>
                  {msg.text}

                  {msg.isSuccessCard && (
                    <div style={{ marginTop: '0.85rem', background: '#FFFFFF', borderRadius: '14px', padding: '0.85rem 1.1rem', border: '1px solid #C8D9E6' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', color: '#567C8D', fontWeight: 700, fontSize: '0.88rem', marginBottom: '0.4rem' }}>
                        <CheckCircle2 size={17} /> Rule Updated
                      </div>
                      <button 
                        onClick={() => onNavigateToTab('daily-outfit')}
                        className="btn-primary" 
                        style={{ width: '100%', justifyContent: 'center', padding: '0.55rem 0.9rem', fontSize: '0.82rem', borderRadius: '10px' }}
                      >
                        View Daily Outfits <ArrowRight size={15} />
                      </button>
                    </div>
                  )}
                </div>
                <div style={{ fontSize: '0.7rem', color: '#78909C', marginTop: '0.3rem', textAlign: msg.sender === 'user' ? 'right' : 'left' }}>
                  {msg.timestamp}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Input Bar */}
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <input
            type="text"
            placeholder="Type your styling preference (e.g. 'I don't want bags on daily outfits')..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            style={{
              flex: 1,
              padding: '0.85rem 1.2rem',
              borderRadius: '14px',
              border: '1px solid rgba(86, 124, 141, 0.2)',
              backgroundColor: '#F5EFEB',
              fontSize: '0.92rem',
              outline: 'none',
              fontFamily: 'var(--font-body)',
              color: '#2F4156'
            }}
          />
          <button
            onClick={() => handleSendMessage()}
            className="btn-primary"
            style={{ padding: '0.85rem 1.4rem', borderRadius: '14px' }}
          >
            <Send size={17} /> Save
          </button>
        </div>

      </div>

    </div>
  );
}



