import React, { useEffect, useState } from 'react';
import { Check, Clock3, WashingMachine, X } from 'lucide-react';

export default function WearLaundryReminder({ events, onSubmit, onDismiss }) {
  const [answers, setAnswers] = useState({});
  const [savingId, setSavingId] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    setAnswers(current => {
      const next = { ...current };
      for (const event of events) {
        if (!next[event.id]) {
          next[event.id] = Object.fromEntries(event.garments.map(garment => [
            garment.id,
            { actually_worn: true, in_laundry: null }
          ]));
        }
      }
      return next;
    });
  }, [events]);

  useEffect(() => {
    if (!notice) return undefined;
    const timeout = window.setTimeout(() => setNotice(''), 4500);
    return () => window.clearTimeout(timeout);
  }, [notice]);

  if (!events.length) {
    return notice
      ? <div role="status" style={{ marginBottom: '1rem', padding: '0.7rem 0.9rem', borderRadius: 10, background: '#ECFDF5', color: '#047857', fontSize: '0.82rem' }}>{notice}</div>
      : null;
  }
  const event = events[0];
  const eventAnswers = answers[event.id] || {};
  const updateAnswer = (itemId, key, value) => {
    setAnswers(current => ({
      ...current,
      [event.id]: {
        ...(current[event.id] || {}),
        [itemId]: { ...(current[event.id]?.[itemId] || {}), [key]: value }
      }
    }));
  };

  const submit = async () => {
    setSavingId(event.id);
    setError('');
    setNotice('');
    try {
      const submitted = Object.entries(eventAnswers)
        .filter(([, answer]) => answer.actually_worn !== null)
        .map(([item_id, answer]) => ({ item_id, ...answer }));
      await onSubmit(event.id, submitted);
      setNotice('Your answers were saved. Estimated dates never automatically mark clothes ready.');
      setAnswers(current => {
        const next = { ...current };
        delete next[event.id];
        return next;
      });
    } catch (submitError) {
      setError(submitError.message || 'Could not save your laundry answers. Please retry.');
    } finally {
      setSavingId('');
    }
  };

  const dismiss = async () => {
    setError('');
    try {
      await onDismiss(event.id);
    } catch (dismissError) {
      setError(dismissError.message || 'Could not dismiss this reminder.');
    }
  };

  return (
    <aside aria-labelledby="wear-reminder-title" style={{ margin: '0 0 1.25rem', padding: '1rem', background: '#FBFAFF', border: '1px solid #E7DFFF', borderRadius: 18, boxShadow: '0 6px 20px rgba(80, 50, 150, 0.06)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start' }}>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <span style={{ display: 'grid', placeItems: 'center', width: 38, height: 38, borderRadius: 12, background: '#F0EBFF', color: '#7C4DFF' }}><WashingMachine size={20} /></span>
          <div>
            <h2 id="wear-reminder-title" style={{ margin: 0, fontSize: '1rem', color: '#1E1B2E' }}>Quick wardrobe check</h2>
            <p style={{ margin: '3px 0 0', color: '#64748B', fontSize: '0.8rem' }}>Did you put any of these worn clothes in the laundry?</p>
          </div>
        </div>
        <button type="button" onClick={dismiss} aria-label="Dismiss laundry reminder" title="Dismiss reminder" style={iconButton}><X size={17} /></button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: '0.65rem', marginTop: '0.9rem' }}>
        {event.garments.map(garment => {
          const answer = eventAnswers[garment.id] || { actually_worn: true, in_laundry: null };
          return (
            <div key={garment.id} style={{ display: 'flex', alignItems: 'center', gap: 9, background: '#fff', border: '1px solid #E8EAF2', borderRadius: 12, padding: '0.55rem' }}>
              {garment.imageUrl
                ? <img src={garment.imageUrl} alt="" style={{ width: 48, height: 48, objectFit: 'contain', borderRadius: 8, background: '#F8FAFC' }} />
                : <span style={{ width: 48, height: 48, borderRadius: 8, background: '#F8FAFC', display: 'grid', placeItems: 'center', color: '#8E92A0' }}><WashingMachine size={20} /></span>}
              <div style={{ flex: 1, minWidth: 0 }}>
                <strong style={{ display: 'block', color: '#334155', fontSize: '0.78rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{garment.title}</strong>
                <button
                  type="button"
                  aria-pressed={answer.actually_worn}
                  onClick={() => updateAnswer(garment.id, 'actually_worn', !answer.actually_worn)}
                  style={{ border: 0, padding: 0, marginTop: 4, background: 'transparent', color: answer.actually_worn ? '#64748B' : '#7C4DFF', fontSize: '0.7rem', fontWeight: 700, cursor: 'pointer' }}
                >
                  {answer.actually_worn ? 'Worn in this look' : 'Not worn — skip'}
                </button>
              </div>
              <div role="group" aria-label={`${garment.title}: put in laundry?`} style={{ display: 'flex', gap: 4 }}>
                {[['yes', true], ['no', false]].map(([label, value]) => (
                  <button
                    key={label}
                    type="button"
                    disabled={!answer.actually_worn}
                    aria-pressed={answer.in_laundry === value}
                    onClick={() => updateAnswer(garment.id, 'in_laundry', value)}
                    style={{
                      ...choiceButton,
                      background: answer.in_laundry === value ? (value ? '#FEF3C7' : '#ECFDF5') : '#F8FAFC',
                      color: answer.in_laundry === value ? (value ? '#B45309' : '#047857') : '#64748B',
                      borderColor: answer.in_laundry === value ? (value ? '#FCD34D' : '#A7F3D0') : '#E2E8F0',
                      opacity: answer.actually_worn ? 1 : 0.45,
                    }}
                  >
                    {label.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginTop: '0.8rem' }}>
        <span style={{ color: '#64748B', fontSize: '0.73rem', display: 'flex', alignItems: 'center', gap: 5 }}><Clock3 size={14} /> Unanswered items stay unchanged.</span>
        <button type="button" onClick={submit} disabled={savingId === event.id} style={submitButton}>
          {savingId === event.id ? 'Saving…' : <><Check size={15} /> Save answers</>}
        </button>
      </div>
      {error && <p role="alert" style={{ color: '#B91C1C', margin: '0.65rem 0 0', fontSize: '0.8rem' }}>{error}</p>}
      {notice && <p role="status" style={{ color: '#047857', margin: '0.65rem 0 0', fontSize: '0.8rem' }}>{notice}</p>}
    </aside>
  );
}

const iconButton = { border: 0, borderRadius: 8, padding: 6, color: '#64748B', background: 'transparent', cursor: 'pointer' };
const choiceButton = { border: '1px solid', borderRadius: 7, padding: '0.35rem 0.45rem', fontSize: '0.65rem', fontWeight: 850, cursor: 'pointer' };
const submitButton = { display: 'inline-flex', alignItems: 'center', gap: 6, border: 0, borderRadius: 9, padding: '0.58rem 0.8rem', background: '#7C4DFF', color: '#fff', fontWeight: 800, cursor: 'pointer' };
