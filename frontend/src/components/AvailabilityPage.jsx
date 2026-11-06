import React, { useEffect, useMemo, useState } from 'react';
import { AlertCircle, Check, Clock3, Loader2, Search, Shirt, WashingMachine, Zap, Bell } from 'lucide-react';

const CLOTHING_CATEGORIES = ['tops', 'bottoms', 'outerwear', 'dresses', 'one_piece'];
const NON_CLOTHING_CATEGORIES = ['footwear', 'bags', 'accessories', 'jewelry'];

const AVAILABILITY_OPTIONS = [
  ['ready', 'Ready'],
  ['to_wash', 'To wash'],
  ['in_wash', 'In wash'],
  ['drying', 'Drying'],
  ['damaged', 'Damaged'],
  ['missing', 'Missing'],
  ['borrowed', 'Borrowed'],
  ['unavailable', 'Unavailable'],
];
const IRONING_OPTIONS = [
  ['ready', 'No ironing needed'],
  ['needs_ironing', 'Needs ironing'],
  ['being_ironed', 'Being ironed'],
];
const STATUS_COLORS = {
  ready: '#059669',
  available: '#059669',
  to_wash: '#D97706',
  in_wash: '#2563EB',
  drying: '#7C3AED',
  needs_ironing: '#D97706',
  being_ironed: '#2563EB',
  damaged: '#DC2626',
  missing: '#64748B',
  borrowed: '#7C3AED',
  unavailable: '#64748B',
};

const STATUS_TABS = [
  { id: 'ready', label: 'Ready to Wear', icon: Check, color: '#059669', bg: '#ECFDF5' },
  { id: 'laundry', label: 'In Wash', icon: WashingMachine, color: '#2563EB', bg: '#EFF6FF' },
  { id: 'missing', label: 'Missing/Damaged', icon: AlertCircle, color: '#DC2626', bg: '#FEF2F2' },
];

const toDateTimeInput = value => {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return localDate.toISOString().slice(0, 16);
};

export default function AvailabilityPage({ onItemUpdated }) {
  const [items, setItems] = useState([]);
  const [drafts, setDrafts] = useState({});
  const [search, setSearch] = useState('');
  const [activeTab, setActiveTab] = useState('ready');
  const [loading, setLoading] = useState(true);
  const [savingId, setSavingId] = useState(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [pendingReminders, setPendingReminders] = useState([]);
  const [readyConfirmations, setReadyConfirmations] = useState([]);

  useEffect(() => {
    let cancelled = false;
    fetch('http://localhost:8000/api/availability?user_id=1')
      .then(async response => {
        const data = await response.json();
        if (!response.ok || data.status !== 'success') {
          throw new Error(data.detail || 'Could not load wardrobe availability.');
        }
        if (!cancelled) setItems(data.items || []);
      })
      .catch(loadError => {
        if (!cancelled) setError(loadError.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  // Load pending wear reminders
  useEffect(() => {
    let cancelled = false;
    fetch('http://localhost:8000/api/outfit-wear-events?user_id=1')
      .then(async response => {
        const data = await response.json();
        if (!response.ok || data.status !== 'success') {
          throw new Error(data.detail || 'Could not load wear reminders.');
        }
        if (!cancelled) setPendingReminders(data.events || []);
      })
      .catch(err => {
        if (!cancelled) console.error('Could not load wear reminders:', err);
      });
    return () => { cancelled = true; };
  }, []);

  // Load items needing ready confirmation (2+ days in wash)
  useEffect(() => {
    let cancelled = false;
    fetch('http://localhost:8000/api/laundry/ready-confirmation?user_id=1')
      .then(async response => {
        const data = await response.json();
        if (!response.ok || data.status !== 'success') {
          throw new Error(data.detail || 'Could not load ready confirmations.');
        }
        if (!cancelled) setReadyConfirmations(data.items || []);
      })
      .catch(err => {
        if (!cancelled) console.error('Could not load ready confirmations:', err);
      });
    return () => { cancelled = true; };
  }, []);

  // Filter only clothing items (exclude footwear, bags, accessories)
  const clothingItems = useMemo(
    () => items.filter(item => {
      const category = (item.category || '').toLowerCase();
      return CLOTHING_CATEGORIES.some(cat => category.includes(cat));
    }),
    [items]
  );

  // Non-clothing items (footwear, bags, accessories) - only show missing status
  const nonClothingItems = useMemo(
    () => items.filter(item => {
      const category = (item.category || '').toLowerCase();
      return NON_CLOTHING_CATEGORIES.some(cat => category.includes(cat));
    }),
    [items]
  );

  const counts = useMemo(() => ({
    ready: clothingItems.filter(item => ['ready', 'available'].includes(item.availability_status)).length,
    laundry: clothingItems.filter(item => ['to_wash', 'in_wash', 'drying'].includes(item.availability_status)).length,
    missing: clothingItems.filter(item => ['damaged', 'missing', 'borrowed', 'unavailable'].includes(item.availability_status)).length,
  }), [clothingItems]);

  // Get items for active tab
  const visibleItems = useMemo(() => {
    const filtered = clothingItems.filter(item => {
      const text = `${item.title} ${item.color} ${item.category}`.toLowerCase();
      const matchesSearch = text.includes(search.toLowerCase());

      const currentStatus = drafts[item.id]?.availability_status ?? item.availability_status;

      let matchesTab = false;
      switch (activeTab) {
        case 'ready':
          matchesTab = ['ready', 'available'].includes(currentStatus);
          break;
        case 'laundry':
          matchesTab = ['to_wash', 'in_wash', 'drying'].includes(currentStatus);
          break;
        case 'missing':
          matchesTab = ['damaged', 'missing', 'borrowed', 'unavailable'].includes(currentStatus);
          break;
        default:
          matchesTab = true;
      }

      return matchesSearch && matchesTab;
    });

    return filtered;
  }, [clothingItems, search, activeTab, drafts]);

  const draftFor = item => drafts[item.id] || {
    availability_status: item.availability_status || 'ready',
    ironing_status: item.ironing_status || 'ready',
    expected_available_at: toDateTimeInput(item.expected_available_at),
    notify_when_ready: Boolean(item.notify_when_ready),
    status_note: item.status_note || '',
  };

  const changeDraft = (item, field, value) => {
    setDrafts(current => {
      const nextDraft = { ...draftFor(item), [field]: value };
      if (
        (field === 'expected_available_at' && !value)
        || (field === 'availability_status' && !['to_wash', 'in_wash', 'drying'].includes(value))
      ) {
        nextDraft.notify_when_ready = false;
      }
      return { ...current, [item.id]: nextDraft };
    });
  };

  const saveItem = async item => {
    const draft = draftFor(item);
    setSavingId(item.id);
    setError('');
    setNotice('');
    try {
      const response = await fetch(`http://localhost:8000/api/clothes/${encodeURIComponent(item.id)}/availability`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...draft,
          expected_available_at: draft.expected_available_at
            ? new Date(draft.expected_available_at).toISOString()
            : null,
          notify_when_ready: Boolean(draft.notify_when_ready),
          status_note: draft.status_note || null,
          user_id: 1,
        }),
      });
      const data = await response.json();
      if (!response.ok || data.status !== 'success') {
        throw new Error(data.detail || 'Could not save this garment status.');
      }
      setItems(current => current.map(entry => entry.id === item.id ? data.item : entry));
      setDrafts(current => {
        const next = { ...current };
        delete next[item.id];
        return next;
      });
      onItemUpdated?.(data.item);
      setNotice(`${data.item.title} status saved.`);
    } catch (saveError) {
      setError(saveError.message);
    } finally {
      setSavingId(null);
    }
  };

  // Handle wear reminder answers
  const handleWearReminderSubmit = async (eventId, answers) => {
    try {
      const response = await fetch(`http://localhost:8000/api/outfit-wear-events/${eventId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          answers: answers.map(a => ({
            item_id: a.item_id,
            actually_worn: a.actually_worn,
            in_laundry: a.in_laundry
          })),
          user_id: 1
        })
      });
      const data = await response.json();
      if (!response.ok || data.status !== 'success') {
        throw new Error(data.detail || 'Could not save wear answers.');
      }
      setPendingReminders(data.events || []);
      setNotice('Wear status saved. Items marked as "in laundry" will be tracked.');
      // Refresh items to get updated status
      fetch('http://localhost:8000/api/availability?user_id=1')
        .then(res => res.json())
        .then(data => {
          if (data.status === 'success') setItems(data.items || []);
        });
    } catch (err) {
      setError(err.message);
    }
  };

  const handleWearReminderDismiss = async (eventId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/outfit-wear-events/${eventId}?user_id=1`, {
        method: 'DELETE'
      });
      const data = await response.json();
      if (!response.ok || data.status !== 'success') {
        throw new Error(data.detail || 'Could not dismiss reminder.');
      }
      setPendingReminders(data.events || []);
    } catch (err) {
      setError(err.message);
    }
  };

  // Quick status change helper
  const quickStatusChange = async (item, newStatus) => {
    setSavingId(item.id);
    try {
      const response = await fetch(`http://localhost:8000/api/clothes/${encodeURIComponent(item.id)}/availability`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          availability_status: newStatus,
          ironing_status: item.ironing_status || 'ready',
          expected_available_at: null,
          notify_when_ready: false,
          status_note: null,
          user_id: 1,
        }),
      });
      const data = await response.json();
      if (!response.ok || data.status !== 'success') {
        throw new Error(data.detail || 'Could not update status.');
      }
      setItems(current => current.map(entry => entry.id === item.id ? data.item : entry));
      setDrafts(current => {
        const next = { ...current };
        delete next[item.id];
        return next;
      });
      onItemUpdated?.(data.item);
      setNotice(`${item.title} marked as ${newStatus.replace('_', ' ')}.`);

      // Refresh ready confirmations list
      fetch('http://localhost:8000/api/laundry/ready-confirmation?user_id=1')
        .then(res => res.json())
        .then(data => {
          if (data.status === 'success') setReadyConfirmations(data.items || []);
        });
    } catch (err) {
      setError(err.message);
    } finally {
      setSavingId(null);
    }
  };

  // Missing non-clothing items
  const missingAccessories = useMemo(
    () => nonClothingItems.filter(item => ['damaged', 'missing', 'borrowed', 'unavailable'].includes(item.availability_status)),
    [nonClothingItems]
  );

  return (
    <section style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
        <div>
          <h1 style={{ margin: 0, color: '#0F172A', fontSize: '1.8rem', fontWeight: 850 }}>Smart Laundry & Wear Tracking</h1>
          <p style={{ color: '#64748B', margin: '0.4rem 0 0', fontSize: '0.95rem' }}>
            Clothes automatically move to "In Wash" after wearing. Confirm when ready after 2 days.
          </p>
        </div>
        <WashingMachine size={32} color="#7C4DFF" aria-hidden="true" />
      </header>

      {/* Pending Wear Reminders */}
      {pendingReminders.length > 0 && (
        <div style={{ background: '#FFF7ED', border: '1px solid #FED7AA', borderRadius: 16, padding: '1.2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: '1rem' }}>
            <Bell size={20} color="#EA580C" />
            <div>
              <h3 style={{ margin: 0, color: '#9A3412', fontSize: '1rem' }}>Quick Laundry Check</h3>
              <p style={{ margin: '3px 0 0', color: '#C2410C', fontSize: '0.85rem' }}>
                You wore these items recently. Are they in the wash?
              </p>
            </div>
          </div>
          {pendingReminders.slice(0, 1).map(event => (
            <div key={event.id} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem' }}>
              {event.garments.map(garment => (
                <div key={garment.id} style={{ display: 'flex', alignItems: 'center', gap: 10, background: '#fff', padding: '0.75rem', borderRadius: 12, border: '1px solid #FED7AA' }}>
                  {garment.imageUrl ? (
                    <img src={garment.imageUrl} alt="" style={{ width: 50, height: 50, objectFit: 'contain', borderRadius: 8 }} />
                  ) : (
                    <div style={{ width: 50, height: 50, borderRadius: 8, background: '#FFF7ED', display: 'grid', placeItems: 'center' }}>
                      <Shirt size={20} color="#FDBA74" />
                    </div>
                  )}
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#1E1B2E' }}>{garment.title}</div>
                    <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
                      <button
                        onClick={() => handleWearReminderSubmit(event.id, [{ item_id: garment.id, actually_worn: true, in_laundry: true }])}
                        style={{ padding: '0.35rem 0.6rem', border: '1px solid #FDBA74', borderRadius: 6, background: '#FFF7ED', color: '#C2410C', fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer' }}
                      >
                        In Wash
                      </button>
                      <button
                        onClick={() => handleWearReminderSubmit(event.id, [{ item_id: garment.id, actually_worn: true, in_laundry: false }])}
                        style={{ padding: '0.35rem 0.6rem', border: '1px solid #BBF7D0', borderRadius: 6, background: '#F0FDF4', color: '#15803D', fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer' }}
                      >
                        Ready
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ))}
          <button
            onClick={() => handleWearReminderDismiss(pendingReminders[0].id)}
            style={{ marginTop: '0.75rem', padding: '0.5rem 0.8rem', border: 0, borderRadius: 8, background: 'transparent', color: '#C2410C', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer' }}
          >
            Dismiss reminder
          </button>
        </div>
      )}

      {/* Ready Confirmation (2+ days in wash) */}
      {readyConfirmations.length > 0 && (
        <div style={{ background: '#ECFDF5', border: '1px solid #A7F3D0', borderRadius: 16, padding: '1.2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: '1rem' }}>
            <Clock3 size={20} color="#059669" />
            <div>
              <h3 style={{ margin: 0, color: '#065F46', fontSize: '1rem' }}>Laundry Ready Check</h3>
              <p style={{ margin: '3px 0 0', color: '#047857', fontSize: '0.85rem' }}>
                These items have been in wash for 2+ days. Are they ready to wear?
              </p>
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem' }}>
            {readyConfirmations.map(item => (
              <div key={item.id} style={{ display: 'flex', alignItems: 'center', gap: 10, background: '#fff', padding: '0.75rem', borderRadius: 12, border: '1px solid #A7F3D0' }}>
                {item.imageUrl ? (
                  <img src={item.imageUrl} alt="" style={{ width: 50, height: 50, objectFit: 'contain', borderRadius: 8 }} />
                ) : (
                  <div style={{ width: 50, height: 50, borderRadius: 8, background: '#ECFDF5', display: 'grid', placeItems: 'center' }}>
                    <Shirt size={20} color="#6EE7B7" />
                  </div>
                )}
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#1E1B2E' }}>{item.title}</div>
                  <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: 2, textTransform: 'capitalize' }}>
                    {item.availability_status.replace('_', ' ')}
                  </div>
                  <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
                    <button
                      onClick={() => quickStatusChange(item, 'ready')}
                      disabled={savingId === item.id}
                      style={{ padding: '0.35rem 0.6rem', border: '1px solid #BBF7D0', borderRadius: 6, background: '#F0FDF4', color: '#15803D', fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer' }}
                    >
                      Yes, Ready
                    </button>
                    <button
                      onClick={() => quickStatusChange(item, 'drying')}
                      disabled={savingId === item.id}
                      style={{ padding: '0.35rem 0.6rem', border: '1px solid #DDD6FE', borderRadius: 6, background: '#F5F3FF', color: '#7C3AED', fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer' }}
                    >
                      Still Drying
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Status Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        {STATUS_TABS.map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                flex: '1 1 140px',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '0.9rem 1rem',
                border: `2px solid ${isActive ? tab.color : '#E2E8F0'}`,
                borderRadius: 14,
                background: isActive ? tab.bg : '#fff',
                color: isActive ? tab.color : '#64748B',
                fontSize: '0.9rem',
                fontWeight: isActive ? 800 : 600,
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              <Icon size={18} />
              <span>{tab.label}</span>
              <span style={{
                marginLeft: 'auto',
                padding: '0.2rem 0.5rem',
                borderRadius: 999,
                background: isActive ? tab.color : '#E2E8F0',
                color: isActive ? '#fff' : '#64748B',
                fontSize: '0.75rem',
                fontWeight: 800
              }}>
                {counts[tab.id]}
              </span>
            </button>
          );
        })}
      </div>

      {/* Search */}
      <label style={{ display: 'flex', alignItems: 'center', gap: 10, border: '1px solid #E2E8F0', borderRadius: 12, padding: '0.75rem 1rem', background: '#fff' }}>
        <Search size={18} color="#64748B" />
        <input
          aria-label="Search clothes"
          value={search}
          onChange={event => setSearch(event.target.value)}
          placeholder="Search clothes by name, color, or category…"
          style={{ width: '100%', border: 0, outline: 0, fontSize: '0.9rem' }}
        />
      </label>

      {error && <div role="alert" style={messageStyle('#FEF2F2', '#B91C1C')}><AlertCircle size={17} />{error}</div>}
      {notice && <div role="status" style={messageStyle('#ECFDF5', '#047857')}><Check size={17} />{notice}</div>}

      {loading ? (
        <div style={emptyStyle}><Loader2 size={24} className="availability-spin" /> Loading wardrobe status…</div>
      ) : clothingItems.length === 0 ? (
        <div style={emptyStyle}><Shirt size={24} /> Your wardrobe has no clothes. Add garments to track their laundry status.</div>
      ) : visibleItems.length === 0 ? (
        <div style={emptyStyle}>No clothes in this category.</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1rem' }}>
          {visibleItems.map(item => {
            const draft = draftFor(item);
            const status = draft.availability_status;
            return (
              <article key={item.id} className="availability-item-card">
                <div className="availability-item-image">
                  {item.imageUrl
                    ? <img src={item.imageUrl} alt={item.title} />
                    : <Shirt size={48} color="#CBD5E1" />}
                  <span className="availability-item-badge" style={{ color: STATUS_COLORS[status] || '#475569' }}>
                    {status.replaceAll('_', ' ')}
                  </span>
                </div>
                <div className="availability-item-content">
                  <div className="availability-item-title" title={item.title}>{item.title}</div>
                  {/* Quick Actions based on tab */}
                  {activeTab === 'ready' && (
                    <div className="availability-item-actions">
                      <button
                        onClick={() => quickStatusChange(item, 'in_wash')}
                        disabled={savingId === item.id}
                        className="availability-action-button is-wash"
                      >
                        In Wash
                      </button>
                      <button
                        onClick={() => quickStatusChange(item, 'missing')}
                        disabled={savingId === item.id}
                        className="availability-action-button is-missing"
                      >
                        Missing
                      </button>
                    </div>
                  )}

                  {activeTab === 'laundry' && (
                    <button
                      onClick={() => quickStatusChange(item, 'ready')}
                      disabled={savingId === item.id}
                      className="availability-action-button is-ready"
                    >
                      Mark as Ready
                    </button>
                  )}

                  {activeTab === 'missing' && (
                    <button
                      onClick={() => quickStatusChange(item, 'ready')}
                      disabled={savingId === item.id}
                      className="availability-action-button is-ready"
                    >
                      Found It - Ready
                    </button>
                  )}

                  {/* Advanced options */}
                  <details className="availability-item-advanced">
                    <summary>
                      Advanced options
                    </summary>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.5rem', paddingTop: '0.5rem', borderTop: '1px solid #E2E8F0' }}>
                      <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#475569' }}>
                        Status
                        <select value={draft.availability_status} onChange={event => changeDraft(item, 'availability_status', event.target.value)} style={selectStyle}>
                          {AVAILABILITY_OPTIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                        </select>
                      </label>
                      <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#475569' }}>
                        Ironing
                        <select value={draft.ironing_status} onChange={event => changeDraft(item, 'ironing_status', event.target.value)} style={selectStyle}>
                          {IRONING_OPTIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                        </select>
                      </label>
                      <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#475569' }}>
                        Expected ready
                        <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <Clock3 size={14} color="#64748B" />
                          <input type="datetime-local" value={draft.expected_available_at} onChange={event => changeDraft(item, 'expected_available_at', event.target.value)} style={{ ...selectStyle, minWidth: 0 }} />
                        </span>
                      </label>
                      <button
                        type="button"
                        onClick={() => saveItem(item)}
                        disabled={savingId === item.id}
                        style={{ ...saveButton, opacity: savingId === item.id ? 0.65 : 1 }}
                      >
                        {savingId === item.id ? 'Saving…' : 'Save changes'}
                      </button>
                    </div>
                  </details>
                </div>
              </article>
            );
          })}
        </div>
      )}

      {/* Missing Accessories Section */}
      {missingAccessories.length > 0 && (
        <div style={{ marginTop: '1.5rem', padding: '1.2rem', background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: 16 }}>
          <h3 style={{ margin: '0 0 1rem', color: '#991B1B', fontSize: '1rem', fontWeight: 700 }}>Missing Accessories & Footwear</h3>
          <p style={{ color: '#7F1D1D', fontSize: '0.85rem', marginBottom: '1rem' }}>
            These items don't need washing but are currently unavailable. Mark them as ready when found.
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '0.75rem' }}>
            {missingAccessories.map(item => (
              <div key={item.id} style={{ display: 'flex', alignItems: 'center', gap: 10, background: '#fff', padding: '0.75rem', borderRadius: 12, border: '1px solid #FECACA' }}>
                {item.imageUrl ? (
                  <img src={item.imageUrl} alt="" style={{ width: 45, height: 45, objectFit: 'contain', borderRadius: 8 }} />
                ) : (
                  <div style={{ width: 45, height: 45, borderRadius: 8, background: '#FEF2F2', display: 'grid', placeItems: 'center' }}>
                    <Shirt size={18} color="#FCA5A5" />
                  </div>
                )}
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#1E1B2E' }}>{item.title}</div>
                  <div style={{ fontSize: '0.75rem', color: '#64748B', textTransform: 'capitalize' }}>{item.category}</div>
                </div>
                <button
                  onClick={() => quickStatusChange(item, 'ready')}
                  disabled={savingId === item.id}
                  style={{ padding: '0.4rem 0.7rem', border: '1px solid #BBF7D0', borderRadius: 8, background: '#F0FDF4', color: '#15803D', fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer' }}
                >
                  Ready
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

const selectStyle = { border: '1px solid #E2E8F0', borderRadius: 9, background: '#fff', padding: '0.55rem', color: '#334155', width: '100%' };
const saveButton = { width: '100%', border: 0, borderRadius: 10, padding: '0.65rem', color: '#fff', background: 'linear-gradient(135deg, #7C4DFF, #6366F1)', fontWeight: 800, cursor: 'pointer' };
const emptyStyle = { minHeight: 140, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, color: '#64748B', background: '#F8FAFC', borderRadius: 16, padding: '1.2rem' };
const messageStyle = (background, color) => ({ display: 'flex', alignItems: 'center', gap: 8, padding: '0.75rem 0.9rem', borderRadius: 10, background, color, fontSize: '0.85rem' });
