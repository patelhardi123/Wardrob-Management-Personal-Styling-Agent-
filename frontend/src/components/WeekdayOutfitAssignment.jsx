import React, { useState } from 'react';
import { Calendar } from 'lucide-react';

export const WEEKDAYS = [
  { id: 'mon', label: 'Monday', fullLabel: 'Monday Routine' },
  { id: 'tue', label: 'Tuesday', fullLabel: 'Tuesday Routine' },
  { id: 'wed', label: 'Wednesday', fullLabel: 'Wednesday Routine' },
  { id: 'thu', label: 'Thursday', fullLabel: 'Thursday Routine' },
  { id: 'fri', label: 'Friday', fullLabel: 'Friday Routine' },
  { id: 'sat', label: 'Saturday', fullLabel: 'Saturday Routine' },
  { id: 'sun', label: 'Sunday', fullLabel: 'Sunday Routine' }
];

export const getPlanDateForDay = (dayId, referenceDate = new Date()) => {
  const weekdayIndex = WEEKDAYS.findIndex(day => day.id === dayId);
  if (weekdayIndex < 0) return '';
  const date = new Date(referenceDate.getFullYear(), referenceDate.getMonth(), referenceDate.getDate());
  date.setDate(date.getDate() - ((date.getDay() + 6) % 7) + weekdayIndex);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
};

export const getNextPlanDateForDay = (dayId, referenceDate = new Date()) => {
  const planDate = getPlanDateForDay(dayId, referenceDate);
  if (!planDate) return '';
  const [year, month, day] = planDate.split('-').map(Number);
  const date = new Date(year, month - 1, day);
  const today = new Date(referenceDate.getFullYear(), referenceDate.getMonth(), referenceDate.getDate());
  if (date < today) date.setDate(date.getDate() + 7);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
};

export const formatPlanDate = value => {
  if (!value) return '';
  const [year, month, day] = value.split('-').map(Number);
  return new Date(year, month - 1, day).toLocaleDateString([], {
    weekday: 'long',
    month: 'long',
    day: 'numeric'
  });
};

export const getEntriesForPlanDate = (schedule, dayId, planDate) =>
  (schedule[dayId] || []).filter(entry => entry.plan_date === planDate);

export default function WeekdayOutfitAssignment({ outfit, schedule, onAssign, source, disabled = false }) {
  const [selectedDay, setSelectedDay] = useState('');
  const [occasion, setOccasion] = useState(outfit?.occasion || '');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');

  const assignedDays = WEEKDAYS.filter(day =>
    (schedule[day.id] || []).some(entry => entry.outfit?.id === outfit.id)
  );

  const handleAssign = async () => {
    if (!selectedDay || !occasion.trim() || isSaving || disabled) return;
    setError('');
    setIsSaving(true);
    try {
      await onAssign(selectedDay, outfit, source, occasion.trim(), [], getPlanDateForDay(selectedDay));
      setSelectedDay('');
    } catch (assignmentError) {
      setError(assignmentError.message || 'Could not add this outfit to your weekday plan.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginTop: '0.5rem' }}>
      <span style={{ color: '#606470', fontSize: '0.75rem', fontWeight: 700 }}>
      Plan this look for a day
      </span>
      {assignedDays.length > 0 && (
        <span style={{ color: '#059669', fontSize: '0.75rem', fontWeight: 700 }}>
          Already planned for {assignedDays.map(day => day.label).join(', ')}.
        </span>
      )}
      <label style={{ color: '#606470', fontSize: '0.72rem', fontWeight: 700 }}>
        Occasion or time of day
        <input
          aria-label="Occasion or time of day for this outfit"
          value={occasion}
          onChange={event => setOccasion(event.target.value)}
          maxLength={80}
          placeholder="e.g. College, dinner date, wedding"
          style={{ display: 'block', width: '100%', boxSizing: 'border-box', marginTop: 4, padding: '0.55rem', border: '1px solid #ECE7FE', borderRadius: 10 }}
        />
      </label>
      <div style={{ display: 'flex', gap: '0.45rem' }}>
        <select
          aria-label="Choose a day for this outfit"
          value={selectedDay}
          onChange={event => setSelectedDay(event.target.value)}
          disabled={disabled || isSaving}
          style={{ minWidth: 0, flex: 1, padding: '0.55rem', border: '1px solid #ECE7FE', borderRadius: '10px', background: '#FFFFFF', color: '#606470' }}
        >
          <option value="">Choose a day</option>
          {WEEKDAYS.map(day => (
            <option key={day.id} value={day.id} disabled={getPlanDateForDay(day.id) < getPlanDateForDay(WEEKDAYS[(new Date().getDay() + 6) % 7].id)}>
              {day.label}, {new Date(`${getPlanDateForDay(day.id)}T12:00:00`).toLocaleDateString([], { month: 'short', day: 'numeric' })}{(schedule[day.id] || []).filter(entry => entry.plan_date === getPlanDateForDay(day.id) && entry.confirmation_status === 'awaiting').length ? ` — ${(schedule[day.id] || []).filter(entry => entry.plan_date === getPlanDateForDay(day.id) && entry.confirmation_status === 'awaiting').length} planned` : ''}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={handleAssign}
          disabled={!selectedDay || !occasion.trim() || disabled || isSaving}
          style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.35rem',
            padding: '0.55rem 0.7rem', border: '1px solid #ECE7FE', borderRadius: '10px',
            background: selectedDay && occasion.trim() && !disabled ? '#F0EBFF' : '#F3F4F6',
            color: selectedDay && occasion.trim() && !disabled ? '#7C4DFF' : '#9CA3AF',
            fontWeight: 700, cursor: selectedDay && occasion.trim() && !disabled ? 'pointer' : 'not-allowed'
          }}
        >
          <Calendar size={15} /> {isSaving ? 'Adding…' : 'Add to plan'}
        </button>
      </div>
      {disabled && <span style={{ color: '#8E92A0', fontSize: '0.75rem' }}>Loading your weekly plan…</span>}
      {error && <span role="alert" style={{ color: '#DC2626', fontSize: '0.75rem' }}>{error}</span>}
    </div>
  );
}
