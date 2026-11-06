import React, { useState } from 'react';
import { Sun, Calendar as CalendarIcon, Bell, ChevronDown, Check, Edit2, Search, Shirt, Home, Calendar, UserCheck, BarChart2, Bot, Mic, WashingMachine, LogOut } from 'lucide-react';

export default function Header({ activeTab, setActiveTab, userProfile, onSaveProfile, clothes = [], onLogout }) {
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [isEditingName, setIsEditingName] = useState(false);
  const [tempName, setTempName] = useState(userProfile?.name || 'Sarah Jenkins');

  const notifications = clothes.filter(item =>
    item.notify_when_ready
    && item.expected_available_at
    && ['to_wash', 'in_wash', 'drying'].includes(item.availability_status)
  );

  const navItems = [
    { id: 'home', label: 'Home', icon: Home },
    { id: 'daily-outfit', label: 'Outfit Planner', icon: Calendar },
    { id: 'wardrobe', label: 'My Wardrobe', icon: Shirt },
    { id: 'availability', label: 'Laundry Tracking', icon: WashingMachine },
    { id: 'voice', label: 'Voice Assistant', icon: Mic, badge: 'New' },
    { id: 'agents', label: 'AI Agents', icon: Bot, badge: 'Live' },
    { id: 'analytics', label: 'Analytics', icon: BarChart2 },
  ];


  const handleNameSave = () => {
    if (tempName.trim() && onSaveProfile) {
      onSaveProfile({
        ...userProfile,
        name: tempName.trim()
      });
    }
    setIsEditingName(false);
  };

  return (
    <header style={{
      backgroundColor: '#FFFFFF',
      borderBottom: '1px solid rgba(86, 124, 141, 0.15)',
      boxShadow: '0 4px 16px rgba(47, 65, 86, 0.04)',
      position: 'sticky',
      top: 0,
      zIndex: 100,
      padding: '0.85rem 2rem'
    }}>
      <div style={{
        maxWidth: '1300px',
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        
        {/* Brand Logo */}
        <div 
          onClick={() => setActiveTab('home')}
          style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}
        >
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #2F4156 0%, #567C8D 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#FFFFFF',
            boxShadow: '0 4px 12px rgba(47, 65, 86, 0.25)'
          }}>
            <Shirt size={22} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#2F4156', fontFamily: 'var(--font-heading)', lineHeight: 1 }}>
              Smart Wardrobe
            </h1>
            <span style={{ fontSize: '0.72rem', color: '#567C8D', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Personal AI Stylist
            </span>
          </div>
        </div>

        {/* Top Navigation Options Panel */}
        <nav className="header-navigation" style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem',
          backgroundColor: '#F5EFEB',
          padding: '0.35rem 0.5rem',
          borderRadius: '16px',
          border: '1px solid rgba(86, 124, 141, 0.12)'
        }}>
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
                  gap: '0.5rem',
                  padding: '0.55rem 1rem',
                  borderRadius: '12px',
                  border: 'none',
                  backgroundColor: isActive ? '#2F4156' : 'transparent',
                  color: isActive ? '#FFFFFF' : '#567C8D',
                  fontWeight: isActive ? 700 : 600,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  boxShadow: isActive ? '0 4px 12px rgba(47, 65, 86, 0.25)' : 'none',
                  position: 'relative',
                  whiteSpace: 'nowrap'
                }}
              >
                <Icon size={15} color={isActive ? '#FFFFFF' : '#567C8D'} />
                <span>{item.label}</span>
                {item.badge && (
                  <span style={{
                    fontSize: '0.6rem',
                    fontWeight: 800,
                    backgroundColor: item.badge === 'Live' ? '#10B981' : '#F59E0B',
                    color: '#FFFFFF',
                    padding: '0.1rem 0.35rem',
                    borderRadius: '999px',
                    lineHeight: 1.4,
                    animation: item.badge === 'Live' ? 'pulse 2s infinite' : 'none'
                  }}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Right Controls Widget Cluster */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          
          {/* Weather Widget */}
          <div style={{
            backgroundColor: '#F5EFEB',
            borderRadius: '12px',
            padding: '0.45rem 0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.55rem',
            border: '1px solid rgba(86, 124, 141, 0.12)'
          }}>
            <Sun size={17} color="#567C8D" />
            <div>
              <div style={{ fontWeight: 800, fontSize: '0.85rem', color: '#2F4156', lineHeight: 1 }}>28°C</div>
              <div style={{ fontSize: '0.68rem', color: '#78909C' }}>Sunny</div>
            </div>
          </div>

          {/* Notifications Button */}
          <div style={{ position: 'relative' }}>
            <button 
              aria-label={`Laundry notifications${notifications.length ? `, ${notifications.length} items` : ''}`}
              onClick={() => setIsNotificationsOpen(!isNotificationsOpen)}
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '12px',
                backgroundColor: isNotificationsOpen ? '#567C8D' : '#F5EFEB',
                border: '1px solid rgba(86, 124, 141, 0.12)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                color: isNotificationsOpen ? '#FFFFFF' : '#2F4156',
                transition: 'all 0.18s ease'
              }}
            >
              <Bell size={17} />
              {notifications.length > 0 && (
                <span style={{ position: 'absolute', top: -4, right: -4, minWidth: 16, height: 16, display: 'grid', placeItems: 'center', borderRadius: '999px', background: '#DC2626', color: '#fff', fontSize: 10, fontWeight: 800, border: '2px solid #fff' }}>
                  {notifications.length}
                </span>
              )}
            </button>

            {/* Notifications Dropdown */}
            {isNotificationsOpen && (
              <div style={{
                position: 'absolute',
                top: '48px',
                right: 0,
                width: '290px',
                backgroundColor: '#FFFFFF',
                border: '1px solid #E2E8F0',
                borderRadius: '18px',
                padding: '1rem',
                boxShadow: '0 12px 35px rgba(47, 65, 86, 0.12)',
                zIndex: 110
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <span style={{ fontSize: '0.82rem', fontWeight: 800, color: '#2F4156' }}>Laundry reminders</span>
                  <span style={{ fontSize: '0.7rem', color: '#2F4156', fontWeight: 700, background: '#C8D9E6', padding: '0.15rem 0.5rem', borderRadius: '999px' }}>{notifications.length}</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem' }}>
                  {notifications.length ? notifications.map(item => (
                    <button
                      type="button"
                      key={item.id}
                      onClick={() => {
                        setActiveTab('availability');
                        setIsNotificationsOpen(false);
                      }}
                      style={{ textAlign: 'left', background: '#F5EFEB', padding: '0.65rem 0.8rem', borderRadius: '10px', border: '1px solid rgba(86,124,141,0.1)', cursor: 'pointer' }}
                    >
                      <div style={{ fontSize: '0.78rem', color: '#2F4156', lineHeight: 1.35 }}>{item.title} · {item.availability_status.replaceAll('_', ' ')}</div>
                      <div style={{ fontSize: '0.66rem', color: '#78909C', marginTop: '0.2rem' }}>
                        Estimated ready {new Date(item.expected_available_at).toLocaleString()}
                      </div>
                    </button>
                  )) : (
                    <div style={{ background: '#F8FAFC', color: '#64748B', padding: '0.75rem', borderRadius: 10, fontSize: '0.76rem' }}>
                      No laundry reminders yet. Set an expected-ready time and enable notifications from Availability.
                    </div>
                  )}
                </div>
                <p style={{ margin: '0.65rem 0 0', color: '#78909C', fontSize: '0.65rem' }}>Browser reminders only fire while this app is open. Estimated times never change garment status.</p>
              </div>
            )}
          </div>

          {/* Profile Dropdown */}
          <div style={{ position: 'relative' }}>
            <div 
              onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.55rem',
                backgroundColor: '#F5EFEB',
                border: isProfileMenuOpen ? '1.5px solid #2F4156' : '1px solid rgba(86, 124, 141, 0.12)',
                borderRadius: '24px',
                padding: '0.3rem 0.75rem 0.3rem 0.35rem',
                cursor: 'pointer',
                transition: 'all 0.18s ease'
              }}
            >
              <img 
                src={userProfile?.avatarUrl || "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=250"} 
                alt="Avatar"
                style={{ width: '32px', height: '32px', borderRadius: '50%', objectFit: 'cover', border: '2px solid #567C8D' }}
              />
              <span style={{ fontWeight: 700, fontSize: '0.85rem', color: '#2F4156' }}>
                {userProfile?.name || 'Sarah Jenkins'}
              </span>
              <ChevronDown size={15} color="#567C8D" />
            </div>

            {/* Profile Dropdown Drawer */}
            {isProfileMenuOpen && (
              <div style={{
                position: 'absolute',
                top: '48px',
                right: 0,
                width: '270px',
                backgroundColor: '#FFFFFF',
                border: '1px solid #E2E8F0',
                borderRadius: '18px',
                padding: '1.1rem',
                boxShadow: '0 12px 35px rgba(47, 65, 86, 0.12)',
                zIndex: 110,
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem'
              }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#567C8D', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Profile Settings
                </div>

                <div>
                  <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#2F4156', display: 'block', marginBottom: '0.25rem' }}>
                    Your Name:
                  </label>
                  {isEditingName ? (
                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                      <input 
                        type="text"
                        value={tempName}
                        onChange={(e) => setTempName(e.target.value)}
                        style={{
                          flex: 1,
                          padding: '0.4rem 0.65rem',
                          borderRadius: '8px',
                          border: '1px solid #2F4156',
                          fontSize: '0.85rem',
                          outline: 'none'
                        }}
                        onKeyDown={(e) => e.key === 'Enter' && handleNameSave()}
                      />
                      <button 
                        onClick={handleNameSave}
                        style={{
                          background: '#2F4156',
                          color: '#FFF',
                          border: 'none',
                          borderRadius: '8px',
                          padding: '0.4rem 0.6rem',
                          cursor: 'pointer'
                        }}
                      >
                        <Check size={15} />
                      </button>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#F5EFEB', padding: '0.45rem 0.65rem', borderRadius: '10px' }}>
                      <span style={{ fontSize: '0.88rem', fontWeight: 700, color: '#2F4156' }}>{userProfile?.name || 'Sarah Jenkins'}</span>
                      <button 
                        onClick={() => setIsEditingName(true)}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#567C8D' }}
                      >
                        <Edit2 size={13} />
                      </button>
                    </div>
                  )}
                </div>

                <div>
                  <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#2F4156', display: 'block', marginBottom: '0.25rem' }}>
                    Style Vibe:
                  </label>
                  <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#2F4156', background: '#C8D9E6', padding: '0.35rem 0.65rem', borderRadius: '8px' }}>
                    ✨ {userProfile?.stylePreference || 'stylish-trendy'}
                  </div>
                </div>

                <button 
                  onClick={() => setIsProfileMenuOpen(false)}
                  className="btn-secondary"
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '10px', fontSize: '0.8rem', justifyContent: 'center' }}
                >
                  Close Settings
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsProfileMenuOpen(false);
                    onLogout?.();
                  }}
                  style={{
                    display: 'flex',
                    width: '100%',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.45rem',
                    border: '1px solid #E5D6D2',
                    borderRadius: '10px',
                    padding: '0.55rem',
                    background: '#FFF8F6',
                    color: '#A65345',
                    fontSize: '0.8rem',
                    fontWeight: 700,
                    cursor: 'pointer'
                  }}
                >
                  <LogOut size={15} /> Sign out
                </button>
              </div>
            )}
          </div>

        </div>

      </div>
    </header>
  );
}
