import React from 'react';
import { 
  Home, 
  Calendar, 
  Shirt, 
  UserCheck,
  Zap,
  Bot,
  BarChart2,
  Droplets,
  Mic
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, userProfile }) {
  const routineLabel = userProfile?.defaultRoutine && userProfile.defaultRoutine !== 'college' 
    ? userProfile.defaultRoutine 
    : 'Outfit Planner';

  const navItems = [
    { id: 'home', label: 'Home', icon: Home, desc: 'Your wardrobe dashboard' },
    { id: 'daily-outfit', label: 'Outfit Planner', icon: Calendar, desc: 'Recommendations & weekly plan' },
    { id: 'wardrobe', label: 'My Wardrobe', icon: Shirt, desc: 'Digital closet & uploads' },
    { id: 'voice', label: 'Voice Assistant', icon: Mic, desc: 'Chat with your AI stylist', badge: 'New' },
    { id: 'availability', label: 'Availability', icon: Droplets, desc: 'Laundry, ironing & wear status' },
    { id: 'agents', label: 'AI Agent Hub', icon: Bot, desc: 'Live multi-agent pipeline trace', badge: 'Live' },
    { id: 'analytics', label: 'Analytics', icon: BarChart2, desc: 'Wardrobe usage & insights' },
  ];

  return (
    <aside style={{
      width: '270px',
      backgroundColor: '#FFFFFF',
      borderRight: '1px solid #ECEBF5',
      display: 'flex',
      flexDirection: 'column',
      padding: '1.75rem 1.25rem',
      height: '100vh',
      position: 'sticky',
      top: 0,
      flexShrink: 0,
      boxShadow: '2px 0 12px rgba(0, 0, 0, 0.02)'
    }}>
      {/* Brand Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', paddingLeft: '0.25rem', marginBottom: '2rem' }}>
        <div style={{
          width: '42px',
          height: '42px',
          borderRadius: '14px',
          background: 'linear-gradient(135deg, #7C4DFF 0%, #6366F1 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#FFFFFF',
          boxShadow: '0 6px 16px rgba(124, 77, 255, 0.35)'
        }}>
          <Shirt size={22} />
        </div>
        <div>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#1C1D21', lineHeight: 1.1, fontFamily: 'var(--font-heading)' }}>
            Smart Wardrobe
          </h2>
          <span style={{ fontSize: '0.75rem', color: '#8E92A0', fontWeight: 600 }}>Personal AI Stylist</span>
        </div>
      </div>

      {/* Active Style Profile Card */}
      <div style={{
        background: 'linear-gradient(135deg, #FAF9FE 0%, #F0EBFF 100%)',
        borderRadius: '16px',
        padding: '0.9rem 1rem',
        marginBottom: '1.5rem',
        border: '1px solid #EAE5FE'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.75rem', color: '#7C4DFF', fontWeight: 700, marginBottom: '0.3rem' }}>
          <UserCheck size={14} /> Active Style Profile
        </div>
        <div style={{ fontSize: '0.88rem', fontWeight: 800, color: '#1C1D21', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {routineLabel}
        </div>
        <div style={{ fontSize: '0.75rem', color: '#606470', fontWeight: 500, marginTop: '0.15rem' }}>
          Vibe: <span style={{ textTransform: 'capitalize', fontWeight: 700, color: '#6366F1' }}>{userProfile?.stylePreference || 'stylish-trendy'}</span>
        </div>
      </div>

      {/* Navigation Menu */}
      <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#A0A4B0', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '0.6rem', paddingLeft: '0.5rem' }}>
        Navigation
      </div>

      <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.4rem', overflowY: 'auto' }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id || (item.id === 'daily-outfit' && activeTab === 'occasions');
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.85rem 1rem',
                borderRadius: '14px',
                border: 'none',
                backgroundColor: isActive ? '#F0EBFF' : 'transparent',
                color: isActive ? '#7C4DFF' : '#4E5260',
                fontWeight: isActive ? 700 : 500,
                fontSize: '0.9rem',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.18s ease',
                boxShadow: isActive ? '0 4px 12px rgba(124, 77, 255, 0.12)' : 'none'
              }}
              onMouseEnter={(e) => {
                if (!isActive) e.currentTarget.style.backgroundColor = '#FAF9FE';
              }}
              onMouseLeave={(e) => {
                if (!isActive) e.currentTarget.style.backgroundColor = 'transparent';
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                <Icon size={20} color={isActive ? '#7C4DFF' : '#8E92A0'} />
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{ fontSize: '0.88rem', lineHeight: 1.2 }}>{item.label}</span>
                  <span style={{ fontSize: '0.72rem', color: isActive ? '#9472FF' : '#9AA0B0', fontWeight: 400 }}>{item.desc}</span>
                </div>
              </div>

              {item.badge && (
                <span style={{
                  fontSize: '0.65rem',
                  fontWeight: 800,
                  backgroundColor: item.badge === 'Live' ? '#10B981' : item.badge === 'New' ? '#F59E0B' : '#7C4DFF',
                  color: '#FFFFFF',
                  padding: '0.15rem 0.45rem',
                  borderRadius: '999px',
                  animation: item.badge === 'Live' ? 'pulse 2s infinite' : 'none'
                }}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer System Status */}
      <div style={{
        backgroundColor: '#FAF9FE',
        borderRadius: '16px',
        padding: '0.9rem 1rem',
        marginTop: '1rem',
        border: '1px solid #ECE7FE',
        display: 'flex',
        alignItems: 'center',
        gap: '0.6rem'
      }}>
        <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#10B981' }} />
        <div style={{ fontSize: '0.76rem', color: '#606470', fontWeight: 600 }}>
          AI Fashion Engine Connected
        </div>
      </div>
    </aside>
  );
}
