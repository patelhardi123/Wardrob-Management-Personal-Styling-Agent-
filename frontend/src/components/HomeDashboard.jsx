import React, { useMemo, useState } from 'react';
import {
  AlertTriangle,
  ArrowRight,
  BellRing,
  Briefcase,
  Calendar,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Droplets,
  GraduationCap,
  Heart,
  Plane,
  Plus,
  Shirt,
  Sparkles,
  WashingMachine
} from 'lucide-react';
import { getEntriesForPlanDate, getPlanDateForDay, WEEKDAYS } from './WeekdayOutfitAssignment';

const occasionOptions = [
  { id: 'College', label: 'College', icon: GraduationCap, background: '#EAF5FC', color: '#2C7196' },
  { id: 'Wedding', label: 'Wedding', icon: Heart, background: '#FFF0EE', color: '#C9655D' },
  { id: 'Party', label: 'Party', icon: Sparkles, background: '#F2ECFF', color: '#8061C5' },
  { id: 'Office', label: 'Office', icon: Briefcase, background: '#E9F6F1', color: '#37866E' },
  { id: 'Dinner date', label: 'Dinner Date', icon: Heart, background: '#FFF0EB', color: '#C96E52' },
  { id: 'Casual outing', label: 'Casual Outing', icon: Shirt, background: '#EAF2FD', color: '#527AB4' },
  { id: 'Travel', label: 'Travel', icon: Plane, background: '#F0EDFF', color: '#7567B3' },
  { id: 'Custom', label: 'Custom', icon: Plus, background: '#F1F3F4', color: '#61717A' }
];

const formatActivityTime = value => {
  if (!value) return '';
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? ''
    : date.toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
};

const getDay = date => {
  const jsDay = date.getDay();
  return WEEKDAYS[jsDay === 0 ? 6 : jsDay - 1];
};

export default function HomeDashboard({
  userProfile,
  clothes = [],
  weeklySchedule = {},
  pendingWearEvents = [],
  onOpenPlanner,
  onNavigate
}) {
  const [customOccasion, setCustomOccasion] = useState('');
  const [selectedOccasion, setSelectedOccasion] = useState('College');
  const now = new Date();
  const today = getDay(now);

  const wardrobeStats = useMemo(() => {
    const ready = clothes.filter(item =>
      ['ready', 'available'].includes(item.availability_status || 'ready')
      && (item.ironing_status || 'ready') === 'ready'
    ).length;
    const laundry = clothes.filter(item =>
      ['to_wash', 'in_wash', 'drying'].includes(item.availability_status)
    ).length;
    const ironing = clothes.filter(item =>
      ['needs_ironing', 'being_ironed'].includes(item.ironing_status)
    ).length;
    const unavailable = clothes.filter(item =>
      ['damaged', 'missing', 'borrowed', 'unavailable'].includes(item.availability_status)
    ).length;
    return { total: clothes.length, ready, laundry, ironing, unavailable };
  }, [clothes, now]);

  const todayDate = getPlanDateForDay(today.id, now);
  const todayEntries = getEntriesForPlanDate(weeklySchedule, today.id, todayDate)
    .filter(entry => entry.confirmation_status === 'awaiting');
  const plannedCount = Object.values(weeklySchedule).flat()
    .filter(entry => entry.confirmation_status === 'awaiting').length;
  const recentActivity = useMemo(() => {
    const scheduled = Object.entries(weeklySchedule).flatMap(([dayId, entries]) =>
      entries.map(entry => ({
        id: entry.schedule_id,
        label: `Planned a ${entry.occasion || 'new'} outfit for ${WEEKDAYS.find(day => day.id === dayId)?.label || dayId}`,
        time: entry.updated_at,
        icon: Calendar,
        color: '#37866E',
        background: '#E9F6F1'
      }))
    );
    const reminders = pendingWearEvents.map(event => ({
      id: event.id,
      label: `Laundry check for ${event.outfit_title || 'your worn outfit'}`,
      time: event.wear_date,
      icon: BellRing,
      color: '#C9655D',
      background: '#FFF0EE'
    }));
    const statusChanges = clothes
      .filter(item => item.last_status_updated && item.availability_status && item.availability_status !== 'ready')
      .map(item => ({
        id: `status-${item.id}`,
        label: `${item.title} is ${item.availability_status.replaceAll('_', ' ')}`,
        time: item.last_status_updated,
        icon: Droplets,
        color: '#7567B3',
        background: '#F2ECFF'
      }));
    return [...scheduled, ...reminders, ...statusChanges]
      .sort((a, b) => new Date(b.time || 0) - new Date(a.time || 0))
      .slice(0, 5);
  }, [clothes, pendingWearEvents, weeklySchedule]);

  const openOccasion = occasion => {
    const value = occasion === 'Custom' ? customOccasion.trim() : occasion;
    if (!value) {
      setSelectedOccasion('Custom');
      return;
    }
    onOpenPlanner(value, today.id);
  };

  const getOutfitItems = outfit => Object.values(outfit?.slotItems || {})
    .filter(item => item && typeof item === 'object' && item.id)
    .map(item => clothes.find(wardrobeItem => String(wardrobeItem.id) === String(item.id)) || item)
    .slice(0, 3);

  const isOutfitAvailable = outfit => Object.values(outfit?.slotItems || {})
    .filter(item => item && typeof item === 'object' && item.id)
    .every(item => {
      const wardrobeItem = clothes.find(entry => String(entry.id) === String(item.id));
      return wardrobeItem
        && ['ready', 'available'].includes(wardrobeItem.availability_status || 'ready')
        && (wardrobeItem.ironing_status || 'ready') === 'ready';
    });

  const statRows = [
    { label: 'Total items', count: wardrobeStats.total, icon: Shirt, color: '#2C7196', background: '#EAF5FC' },
    { label: 'Ready to wear', count: wardrobeStats.ready, icon: CheckCircle2, color: '#168A6D', background: '#E7F6EF' },
    { label: 'In laundry', count: wardrobeStats.laundry, icon: WashingMachine, color: '#7567B3', background: '#F2ECFF' },
    { label: 'Needs ironing', count: wardrobeStats.ironing, icon: Sparkles, color: '#C67B24', background: '#FFF4E5' },
    { label: 'Unavailable', count: wardrobeStats.unavailable, icon: AlertTriangle, color: '#C9655D', background: '#FFF0EE' }
  ];

  return (
    <main className="home-dashboard">
      <header className="home-greeting">
        <div>
          <h1>Good {now.getHours() < 12 ? 'morning' : now.getHours() < 18 ? 'afternoon' : 'evening'}, {userProfile?.name?.split(' ')[0] || 'there'}! <span aria-hidden="true">☀️</span></h1>
          <p>Your AI stylist is here to help you look your best, every day.</p>
        </div>
        <button type="button" className="home-date-chip" onClick={() => onNavigate('daily-outfit')}>
          <Calendar size={16} />
          {now.toLocaleDateString([], { weekday: 'long', month: 'short', day: 'numeric' })}
        </button>
      </header>

      <section className="home-hero">
        <div className="home-hero-art" aria-hidden="true" />
        <div className="home-hero-content">
          <span className="home-eyebrow"><Sparkles size={13} /> Style planner</span>
          <h2>What are you wearing today?</h2>
          <p>Choose an occasion and get outfit ideas made from your own wardrobe.</p>
          <div className="home-hero-action">
            <input
              aria-label="Occasion or outfit details"
              value={selectedOccasion === 'Custom' ? customOccasion : ''}
              onChange={event => {
                setSelectedOccasion('Custom');
                setCustomOccasion(event.target.value);
              }}
              onKeyDown={event => event.key === 'Enter' && openOccasion('Custom')}
              placeholder="e.g. College, wedding, dinner date, white outfit..."
              maxLength={100}
            />
            <button type="button" onClick={() => openOccasion(selectedOccasion)}>
              Get Outfit Ideas <ArrowRight size={16} />
            </button>
          </div>
        </div>
      </section>

      <section className="home-quick-start">
        <div className="home-section-heading">
          <div>
            <h2>Quick Start</h2>
            <p>Choose an occasion to see wardrobe-matched outfit ideas.</p>
          </div>
          <button type="button" onClick={() => onNavigate('daily-outfit')}>View outfit planner <ArrowRight size={14} /></button>
        </div>
        <div className="home-occasion-grid">
          {occasionOptions.map(option => {
            const Icon = option.icon;
            const active = selectedOccasion.toLowerCase() === option.id.toLowerCase();
            return (
              <button
                type="button"
                key={option.id}
                className={`home-occasion-card${active ? ' is-selected' : ''}`}
                style={{ '--occasion-bg': option.background, '--occasion-color': option.color }}
                onClick={() => {
                  setSelectedOccasion(option.id);
                  if (option.id !== 'Custom') openOccasion(option.id);
                }}
                aria-pressed={active}
              >
                <span><Icon size={22} /></span>
                <strong>{option.label}</strong>
              </button>
            );
          })}
        </div>
        {selectedOccasion === 'Custom' && (
          <div className="home-custom-occasion">
            <input
              aria-label="Custom occasion"
              value={customOccasion}
              onChange={event => setCustomOccasion(event.target.value)}
              onKeyDown={event => event.key === 'Enter' && openOccasion('Custom')}
              placeholder="Type your occasion"
              maxLength={100}
            />
            <button type="button" onClick={() => openOccasion('Custom')} disabled={!customOccasion.trim()}>
              Analyze occasion <ArrowRight size={15} />
            </button>
          </div>
        )}
      </section>

      <section className="home-dashboard-grid">
        <div className="home-main-column">
          <section className="home-panel home-today-panel">
            <div className="home-section-heading">
              <div>
                <h2>Today's Plan</h2>
                <p>Your upcoming looks for the week · {today.label}</p>
              </div>
              <button type="button" onClick={() => onNavigate('daily-outfit')}>View full planner <ArrowRight size={14} /></button>
            </div>
            <div className="home-week-strip">
              {WEEKDAYS.map(day => (
                <button
                  type="button"
                  key={day.id}
                  className={today.id === day.id ? 'is-today' : ''}
                  onClick={() => onOpenPlanner('College', day.id)}
                >
                  <strong>{day.label.slice(0, 3)}</strong>
                  <span>{getEntriesForPlanDate(weeklySchedule, day.id, getPlanDateForDay(day.id, now)).filter(entry => entry.confirmation_status === 'awaiting').length} looks</span>
                </button>
              ))}
            </div>
            <div className="home-today-looks">
              {todayEntries.length ? todayEntries.slice(0, 2).map(entry => {
                const garments = getOutfitItems(entry.outfit);
                const ready = isOutfitAvailable(entry.outfit);
                return (
                  <article className="home-planned-look" key={entry.schedule_id}>
                    <div className="home-look-heading">
                      <span className="home-occasion-tag"><Sparkles size={12} /> {entry.occasion || 'Outfit'}</span>
                      <span className={ready ? 'home-ready-label' : 'home-not-ready-label'}>
                        {ready ? 'Ready to wear' : 'Check availability'}
                      </span>
                    </div>
                    <div className="home-garment-thumbnails">
                      {garments.length ? garments.map((item, index) => (
                        <div key={`${entry.schedule_id}-${item.id || index}`} title={item.title || 'Wardrobe item'}>
                          {item.imageUrl
                            ? <img src={item.imageUrl} alt={item.title || 'Planned outfit garment'} />
                            : <Shirt size={24} />}
                        </div>
                      )) : <div className="home-empty-garment"><Shirt size={26} /></div>}
                    </div>
                    <strong className="home-look-title">{entry.outfit?.title || 'Planned outfit'}</strong>
                    <button type="button" onClick={() => onNavigate('daily-outfit')}>View details <ChevronRight size={13} /></button>
                  </article>
                );
              }) : (
                <div className="home-empty-plan">
                  <Calendar size={23} />
                  <strong>No looks planned for today yet</strong>
                  <span>Explore outfit ideas, then add a look to any day.</span>
                  <button type="button" onClick={() => onOpenPlanner('College', today.id)}>Plan today's outfit <ArrowRight size={14} /></button>
                </div>
              )}
              <button type="button" className="home-add-look" onClick={() => onOpenPlanner('College', today.id)}>
                <span><Plus size={18} /></span>
                <strong>Add another outfit</strong>
                <small>Plan multiple looks for the same day</small>
              </button>
            </div>
            {plannedCount > 2 && <span className="home-plan-count">{plannedCount} looks planned this week</span>}
          </section>

          <section className="home-panel home-activity-panel">
            <div className="home-section-heading">
              <div>
                <h2>Recent Activity</h2>
                <p>Updates from your wardrobe and outfit plan.</p>
              </div>
              <button type="button" onClick={() => onNavigate('availability')}>View availability <ArrowRight size={14} /></button>
            </div>
            {recentActivity.length ? (
              <ul className="home-activity-list">
                {recentActivity.map(activity => {
                  const Icon = activity.icon;
                  return (
                    <li key={activity.id}>
                      <span className="home-activity-icon" style={{ color: activity.color, background: activity.background }}><Icon size={16} /></span>
                      <span className="home-activity-copy">
                        <strong>{activity.label}</strong>
                        <small>{formatActivityTime(activity.time) || 'Recently updated'}</small>
                      </span>
                    </li>
                  );
                })}
              </ul>
            ) : (
              <div className="home-activity-empty">
                <Clock3 size={22} />
                <span>New outfit and wardrobe updates will show here.</span>
              </div>
            )}
          </section>
        </div>

        <aside className="home-side-column">
          <section className="home-panel home-overview-panel">
            <div className="home-section-heading">
              <div><h2>Wardrobe Overview</h2></div>
              <button type="button" onClick={() => onNavigate('wardrobe')}>View wardrobe <ArrowRight size={13} /></button>
            </div>
            <ul className="home-stat-list">
              {statRows.map(row => {
                const Icon = row.icon;
                return (
                  <li key={row.label}>
                    <span className="home-stat-icon" style={{ color: row.color, background: row.background }}><Icon size={18} /></span>
                    <strong>{row.count}</strong>
                    <span>{row.label}</span>
                  </li>
                );
              })}
            </ul>
            <button type="button" className="home-laundry-card" onClick={() => onNavigate('availability')}>
              <span><Droplets size={17} /></span>
              <span><strong>Smart Laundry & Wear Tracking</strong><small>Keep your wardrobe availability up to date before planning a look.</small></span>
              <ChevronRight size={15} />
            </button>
          </section>

          <section className="home-panel home-tip-panel">
            <div className="home-tip-art" aria-hidden="true" />
            <span className="home-tip-icon"><Sparkles size={16} /></span>
            <h2>Style Tip of the Day</h2>
            <p>“A great outfit isn't just about clothes, it's about how you feel in them.”</p>
            <button type="button" onClick={() => onNavigate('voice')}>Ask your Voice Stylist <ArrowRight size={13} /></button>
          </section>

          <button type="button" className="home-voice-card" onClick={() => onNavigate('voice')}>
            <span><Sparkles size={17} /></span>
            <span><strong>Want a more personal suggestion?</strong><small>Chat with your Voice Stylist about preferences and outfit edits.</small></span>
            <ArrowRight size={16} />
          </button>
        </aside>
      </section>
    </main>
  );
}
