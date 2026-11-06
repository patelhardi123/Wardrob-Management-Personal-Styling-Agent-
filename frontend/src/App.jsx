import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import HomeDashboard from './components/HomeDashboard';
import DailyOutfitPlanner from './components/DailyOutfitPlanner';
import WardrobeGrid from './components/WardrobeGrid';
import AgentTrace from './components/AgentTrace';
import AgentHubPage from './components/AgentHubPage';
import OnboardingModal from './components/OnboardingModal';
import AddItemModal from './components/AddItemModal';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import VoiceStylist from './components/VoiceStylist';
import AvailabilityPage from './components/AvailabilityPage';
import WearLaundryReminder from './components/WearLaundryReminder';
import AuthPage from './components/AuthPage';
import { getPlanDateForDay } from './components/WeekdayOutfitAssignment';
import { INITIAL_USER_PROFILE, INITIAL_CLOTHES, MOCK_OUTFIT_RESULT } from './mockData';


export default function App() {
  const [activeTab, setActiveTab] = useState('home'); // 'home', 'daily-outfit', 'wardrobe', 'occasions', 'trace'
  const [weekdaySchedule, setWeekdaySchedule] = useState({});
  const [plannerRequest, setPlannerRequest] = useState(null);
  const [isWeekdayScheduleLoaded, setIsWeekdayScheduleLoaded] = useState(false);
  const [weekdayScheduleError, setWeekdayScheduleError] = useState('');
  const [pendingWearEvents, setPendingWearEvents] = useState([]);
  const [outfitNotificationRefresh, setOutfitNotificationRefresh] = useState(0);
  const [authUser, setAuthUser] = useState(() => {
    try {
      const savedUser = JSON.parse(localStorage.getItem('wardrobe_auth_user'));
      return savedUser?.name && savedUser?.email ? savedUser : null;
    } catch {
      return null;
    }
  });
  const [userProfile, setUserProfile] = useState(() => {
    try {
      const saved = localStorage.getItem('wardrobe_user_profile');
      return saved ? JSON.parse(saved) : INITIAL_USER_PROFILE;
    } catch {
      return INITIAL_USER_PROFILE;
    }
  });
  const [clothes, setClothes] = useState(INITIAL_CLOTHES);
  const [outfitResult, setOutfitResult] = useState(MOCK_OUTFIT_RESULT);

  const [isOnboardingOpen, setIsOnboardingOpen] = useState(false);
  const [isAddItemOpen, setIsAddItemOpen] = useState(false);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [activeTab]);

  // Fetch persistent wardrobe items & user profile from SQLite backend on load
  useEffect(() => {
    if (!authUser) return;
    fetch('http://localhost:8000/api/clothes')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success' && data.clothes && data.clothes.length > 0) {
          setClothes(data.clothes);
        }
      })
      .catch(err => console.warn('Could not fetch persistent wardrobe, using fallback', err));

    fetch('http://localhost:8000/api/profile')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success' && data.profile && Object.keys(data.profile).length > 0) {
          setUserProfile(prev => {
            const merged = {
              ...prev,
              ...data.profile,
              name: authUser.name,
              email: authUser.email
            };
            localStorage.setItem('wardrobe_user_profile', JSON.stringify(merged));
            return merged;
          });
        }
      })
      .catch(err => console.warn('Could not fetch persistent profile, using local state', err));
  }, [authUser]);

  useEffect(() => {
    if (!authUser) return;
    fetch('http://localhost:8000/api/weekday-outfits?user_id=1')
      .then(async response => {
        const data = await response.json();
        if (!response.ok || data.status !== 'success') {
          throw new Error(data.detail || 'Could not load the weekday outfit plan.');
        }
        setWeekdaySchedule(data.schedule || {});
      })
      .catch(err => setWeekdayScheduleError(err.message))
      .finally(() => setIsWeekdayScheduleLoaded(true));
  }, [authUser]);

  useEffect(() => {
    if (!authUser) return;
    fetch('http://localhost:8000/api/outfit-wear-events?user_id=1')
      .then(async response => {
        const data = await response.json();
        if (!response.ok || data.status !== 'success') {
          throw new Error(data.detail || 'Could not load laundry reminders.');
        }
        setPendingWearEvents(data.events || []);
      })
      .catch(err => console.warn('Could not load pending wear reminders:', err));
  }, [authUser]);

  useEffect(() => {
    if (!('Notification' in window) || Notification.permission !== 'granted') return;
    const today = getPlanDateForDay(new Date().toLocaleDateString('en-US', { weekday: 'short' }).slice(0, 3).toLowerCase());
    Object.values(weekdaySchedule).flat().forEach(entry => {
      if (
        entry.confirmation_status !== 'awaiting'
        || !entry.plan_date
        || entry.plan_date >= today
      ) return;
      const notificationKey = `wardrobe_outfit_confirmation_${entry.schedule_id}`;
      if (localStorage.getItem(notificationKey)) return;
      const notification = new Notification('Outfit confirmation needed', {
        body: `Did you wear your planned outfit on ${new Date(`${entry.plan_date}T12:00:00`).toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric' })}?`,
        tag: notificationKey
      });
      notification.onclick = () => {
        window.focus();
        setActiveTab('daily-outfit');
        notification.close();
      };
      localStorage.setItem(notificationKey, 'true');
    });
  }, [weekdaySchedule, outfitNotificationRefresh]);

  useEffect(() => {
    if (!('Notification' in window) || Notification.permission !== 'granted') return undefined;
    const notifyWhenDue = () => {
      const now = Date.now();
      clothes
        .filter(item =>
          item.notify_when_ready
          && ['to_wash', 'in_wash', 'drying'].includes(item.availability_status)
          && item.expected_available_at
        )
        .forEach(item => {
          const readyAt = new Date(item.expected_available_at).getTime();
          if (Number.isNaN(readyAt) || readyAt > now) return;
          const notificationKey = `wardrobe_laundry_notified_${item.id}_${readyAt}`;
          if (localStorage.getItem(notificationKey)) return;
          const notification = new Notification('Laundry readiness check', {
            body: `${item.title} was estimated ready. Confirm its status before wearing it.`,
            tag: notificationKey
          });
          notification.onclick = () => {
            window.focus();
            setActiveTab('availability');
            notification.close();
          };
          localStorage.setItem(notificationKey, 'true');
        });
    };
    notifyWhenDue();
    const timer = window.setInterval(notifyWhenDue, 60_000);
    return () => window.clearInterval(timer);
  }, [clothes]);

  const handleConfirmOutfitWorn = async (outfit, planDate, plannedDay, scheduleId, worn = true) => {
    const itemIds = Object.values(outfit?.slotItems || {})
      .filter(item => item && item.id !== undefined && item.id !== null)
      .map(item => String(item.id));
    const response = await fetch('http://localhost:8000/api/outfit-wear-events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        outfit,
        item_ids: itemIds,
        wear_date: planDate,
        planned_day: plannedDay,
        schedule_id: scheduleId,
        worn,
        user_id: 1
      })
    });
    const data = await response.json();
    if (!response.ok || data.status !== 'success') {
      throw new Error(data.detail || 'Could not record the outfit confirmation.');
    }
    setPendingWearEvents(data.pending_events || []);
    setWeekdaySchedule(previous => ({
      ...previous,
      [plannedDay]: (previous[plannedDay] || []).map(entry =>
        entry.schedule_id === scheduleId
          ? { ...entry, confirmation_status: worn ? 'worn' : 'not_worn' }
          : entry
      )
    }));
    if (worn) {
      await handleRefreshWardrobe();
    }
    return data.event;
  };

  const handleAuthenticated = user => {
    setAuthUser(user);
    setUserProfile(previous => {
      const updatedProfile = { ...previous, name: user.name, email: user.email };
      localStorage.setItem('wardrobe_user_profile', JSON.stringify(updatedProfile));
      return updatedProfile;
    });
    localStorage.setItem('wardrobe_auth_user', JSON.stringify(user));
  };

  const handleLogout = () => {
    localStorage.removeItem('wardrobe_auth_user');
    setAuthUser(null);
  };

  const handleSubmitWearEvent = async (eventId, answers) => {
    const response = await fetch(`http://localhost:8000/api/outfit-wear-events/${encodeURIComponent(eventId)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answers, user_id: 1 })
    });
    const data = await response.json();
    if (!response.ok || data.status !== 'success') {
      throw new Error(data.detail || 'Could not save laundry answers.');
    }
    setPendingWearEvents(data.events || []);
    setClothes(previous => previous.map(item => {
      const answer = answers.find(entry => String(entry.item_id) === String(item.id));
      return answer?.actually_worn && answer.in_laundry === true
        ? { ...item, availability_status: 'to_wash', expected_available_at: null }
        : item;
    }));
    try {
      const clothesResponse = await fetch('http://localhost:8000/api/clothes?user_id=1');
      const clothesData = await clothesResponse.json();
      if (!clothesResponse.ok || clothesData.status !== 'success') {
        throw new Error(clothesData.detail || 'Could not refresh wardrobe statuses.');
      }
      setClothes(clothesData.clothes || []);
    } catch (refreshError) {
      console.warn('Laundry answers were saved, but wardrobe status refresh failed:', refreshError);
    }
  };

  const handleDismissWearEvent = async eventId => {
    const response = await fetch(`http://localhost:8000/api/outfit-wear-events/${encodeURIComponent(eventId)}?user_id=1`, {
      method: 'DELETE'
    });
    const data = await response.json();
    if (!response.ok || data.status !== 'success') {
      throw new Error(data.detail || 'Could not dismiss this reminder.');
    }
    setPendingWearEvents(data.events || []);
  };

  const handleRefreshWearEvents = async () => {
    const response = await fetch('http://localhost:8000/api/outfit-wear-events?user_id=1');
    const data = await response.json();
    if (!response.ok || data.status !== 'success') {
      throw new Error(data.detail || 'Could not refresh the laundry reminder.');
    }
    setPendingWearEvents(data.events || []);
  };

  const handleEnableOutfitNotifications = async () => {
    if (!('Notification' in window)) return 'unsupported';
    const permission = await Notification.requestPermission();
    setOutfitNotificationRefresh(value => value + 1);
    return permission;
  };

  const handleAvailabilityItemUpdated = updatedItem => {
    setClothes(previous => previous.map(item => item.id === updatedItem.id ? updatedItem : item));
    if (
      !['ready', 'available'].includes(updatedItem.availability_status || 'ready')
      || (updatedItem.ironing_status || 'ready') !== 'ready'
    ) {
      removeUpcomingPlansUsingItem(updatedItem.id);
    }
  };

  const removeUpcomingPlansUsingItem = itemId => {
    const today = new Date();
    const todayDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
    setWeekdaySchedule(previous => Object.fromEntries(
      Object.entries(previous).map(([dayId, entries]) => [
        dayId,
        entries.filter(entry => !(
          entry.confirmation_status === 'awaiting'
          && entry.plan_date >= todayDate
          && Object.values(entry.outfit?.slotItems || {}).some(item => String(item?.id) === String(itemId))
        ))
      ]).filter(([, entries]) => entries.length)
    ));
  };

  const handleRefreshWardrobe = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/clothes?user_id=1');
      const data = await response.json();
      if (!response.ok || data.status !== 'success') {
        throw new Error(data.detail || 'Could not refresh wardrobe status.');
      }
      setClothes(data.clothes || []);
    } catch (refreshError) {
      console.warn('Could not refresh wardrobe after a Voice Stylist status update:', refreshError);
    }
  };

  const handleScheduleOutfit = async (dayId, outfit, source, occasion = 'Outfit', readyConfirmedItemIds = [], planDate = getPlanDateForDay(dayId)) => {
    const response = await fetch('http://localhost:8000/api/weekday-outfits', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        day_id: dayId,
        plan_date: planDate,
        outfit,
        source,
        occasion,
        ready_confirmed_item_ids: readyConfirmedItemIds,
        user_id: 1
      })
    });
    const data = await response.json();
    if (!response.ok || data.status !== 'success') {
      throw new Error(data.detail || 'Could not add this outfit to the weekday plan.');
    }
    setWeekdayScheduleError('');
    setWeekdaySchedule(previous => ({
      ...previous,
      [dayId]: [...(previous[dayId] || []), data.scheduled_outfit]
    }));
    setClothes(previous => previous.map(item =>
      readyConfirmedItemIds.includes(String(item.id))
        ? {
            ...item,
            availability_status: 'ready',
            ironing_status: 'ready',
            expected_available_at: null,
          }
        : item
    ));
    return data.scheduled_outfit;
  };

  const handleConfirmGarmentStatuses = async updates => {
    for (const update of updates) {
      const response = await fetch(`http://localhost:8000/api/clothes/${encodeURIComponent(update.item_id)}/availability`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          availability_status: update.availability_status,
          ironing_status: update.ironing_status,
          expected_available_at: null,
          user_id: 1
        })
      });
      const data = await response.json();
      if (!response.ok || data.status !== 'success') {
        throw new Error(data.detail || `Could not save readiness for ${update.item_id}.`);
      }
      setClothes(previous => previous.map(item =>
        String(item.id) === String(data.item.id) ? data.item : item
      ));
      if (
        data.item.availability_status !== 'ready'
        && data.item.availability_status !== 'available'
        || (data.item.ironing_status || 'ready') !== 'ready'
      ) {
        removeUpcomingPlansUsingItem(data.item.id);
      }
    }
  };

  const handleReplaceScheduledOutfit = async (scheduleId, dayId, outfit, source, expectedOutfitId, planDate) => {
    const response = await fetch('http://localhost:8000/api/weekday-outfits', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        day_id: dayId,
        plan_date: planDate,
        schedule_id: scheduleId,
        outfit,
        source,
        expected_outfit_id: expectedOutfitId,
        user_id: 1
      })
    });
    const data = await response.json();
    if (!response.ok || data.status !== 'success') {
      throw new Error(data.detail || 'Could not update the planned outfit.');
    }
    setWeekdayScheduleError('');
    setWeekdaySchedule(previous => ({
      ...previous,
      [dayId]: (previous[dayId] || []).map(entry =>
        entry.schedule_id === scheduleId ? data.scheduled_outfit : entry
      )
    }));
    return data.scheduled_outfit;
  };

  const handleRemoveScheduledOutfit = async (scheduleId) => {
    const response = await fetch(`http://localhost:8000/api/weekday-outfits/${encodeURIComponent(scheduleId)}?user_id=1`, {
      method: 'DELETE'
    });
    const data = await response.json();
    if (!response.ok || data.status !== 'success') {
      throw new Error(data.detail || 'Could not remove the outfit from the weekday plan.');
    }
    setWeekdayScheduleError('');
    setWeekdaySchedule(previous => {
      const next = Object.fromEntries(
        Object.entries(previous)
          .map(([dayId, entries]) => [dayId, entries.filter(entry => entry.schedule_id !== scheduleId)])
          .filter(([, entries]) => entries.length > 0)
      );
      return next;
    });
  };

  const handleSaveProfile = async (updatedProfile) => {
    setUserProfile(updatedProfile);
    try {
      localStorage.setItem('wardrobe_user_profile', JSON.stringify(updatedProfile));
      await fetch('http://localhost:8000/api/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedProfile)
      });
    } catch (err) {
      console.warn('Could not persist profile to database:', err);
    }
  };

  const handleOpenPlanner = (occasion, dayId) => {
    setPlannerRequest({ occasion, dayId, requestId: Date.now() });
    setActiveTab('daily-outfit');
  };

  const handleAddItem = async (newItem) => {
    // Save to React state immediately
    setClothes(prev => [newItem, ...prev]);

    // Save to SQLite Database permanently
    try {
      const response = await fetch('http://localhost:8000/api/clothes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newItem)
      });
      const data = await response.json();
      if (data.status === 'success' && data.item) {
        setClothes(prev => prev.map(item => item.id === newItem.id ? data.item : item));
      }
    } catch (err) {
      console.warn('Failed to persist item to SQLite DB:', err);
    }
  };

  const handleDeleteItem = async (itemId) => {
    // Remove from React state immediately
    setClothes(prev => prev.filter(item => item.id !== itemId));

    // Remove from SQLite Database permanently
    try {
      await fetch(`http://localhost:8000/api/clothes/${itemId}`, {
        method: 'DELETE'
      });
    } catch (err) {
      console.warn('Failed to delete item from SQLite DB:', err);
    }
  };

  const handleUpdateItem = async (updatedItem) => {
    // Update React state immediately
    setClothes(prev => prev.map(item => item.id === updatedItem.id ? updatedItem : item));

    // Update SQLite Database permanently
    try {
      await fetch(`http://localhost:8000/api/clothes/${updatedItem.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedItem)
      });
    } catch (err) {
      console.warn('Failed to update item in SQLite DB:', err);
    }
  };

  if (!authUser) {
    return <AuthPage onAuthenticated={handleAuthenticated} />;
  }

  return (
    <div className="app-container">
      
      {/* Top Navigation Bar with Page Tabs & User Controls */}
      <Header 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        userProfile={userProfile} 
        onSaveProfile={handleSaveProfile} 
        clothes={clothes}
        onLogout={handleLogout}
      />

      {/* Main Page Content */}
      <div className="main-content">
        {weekdayScheduleError && (
          <div role="alert" className="status-message error">
            Could not load your weekday outfit plan: {weekdayScheduleError}
          </div>
        )}
        <WearLaundryReminder
          events={pendingWearEvents}
          onSubmit={handleSubmitWearEvent}
          onDismiss={handleDismissWearEvent}
        />

        {/* Home dashboard with real wardrobe and weekly-plan data */}
        {activeTab === 'home' && (
          <HomeDashboard
            userProfile={userProfile}
            clothes={clothes}
            weeklySchedule={weekdaySchedule}
            pendingWearEvents={pendingWearEvents}
            onOpenPlanner={handleOpenPlanner}
            onNavigate={setActiveTab}
          />
        )}

        {/* Clean Interactive Daily Outfit Planner Page */}
        {(activeTab === 'daily-outfit' || activeTab === 'occasions' || activeTab === 'college' || activeTab === 'college-planner' || activeTab === 'daily') && (
          <DailyOutfitPlanner 
            userProfile={userProfile}
            clothes={clothes}
            weeklySchedule={weekdaySchedule}
            onScheduleOutfit={handleScheduleOutfit}
            onRemoveScheduledOutfit={handleRemoveScheduledOutfit}
            onConfirmOutfitWorn={handleConfirmOutfitWorn}
            onConfirmGarmentStatuses={handleConfirmGarmentStatuses}
            onEnableOutfitNotifications={handleEnableOutfitNotifications}
            isWeekdayScheduleLoaded={isWeekdayScheduleLoaded}
            plannerRequest={plannerRequest}
          />
        )}

        {/* Wardrobe Page */}
        {activeTab === 'wardrobe' && (
          <WardrobeGrid 
            clothes={clothes}
            onAddItem={() => setIsAddItemOpen(true)}
            onDeleteItem={handleDeleteItem}
            onUpdateItem={handleUpdateItem}
          />
        )}

        {activeTab === 'availability' && (
          <AvailabilityPage onItemUpdated={handleAvailabilityItemUpdated} />
        )}

        {/* Phase 7 Wardrobe Analytics Dashboard Page */}
        {activeTab === 'analytics' && (
          <AnalyticsDashboard 
            clothes={clothes}
          />
        )}

        {/* 🤖 AI Agent Hub Page — live multi-agent pipeline trace */}
        {activeTab === 'agents' && (
          <AgentHubPage
            clothes={clothes}
            userProfile={userProfile}
          />
        )}

        {/* 🎤 Voice Stylist Agent */}
        {activeTab === 'voice' && (
          <VoiceStylist
            clothes={clothes}
            userProfile={userProfile}
            weekdaySchedule={weekdaySchedule}
            onScheduleOutfit={handleScheduleOutfit}
            onReplaceScheduledOutfit={handleReplaceScheduledOutfit}
            onRemoveScheduledOutfit={handleRemoveScheduledOutfit}
            onRefreshWardrobe={handleRefreshWardrobe}
            onRefreshWearEvents={handleRefreshWearEvents}
            isWeekdayScheduleLoaded={isWeekdayScheduleLoaded}
          />
        )}

      </div>


      {/* Modals */}
      <OnboardingModal 
        isOpen={isOnboardingOpen}
        onClose={() => setIsOnboardingOpen(false)}
        userProfile={userProfile}
        onSave={handleSaveProfile}
      />

      <AddItemModal 
        isOpen={isAddItemOpen}
        onClose={() => setIsAddItemOpen(false)}
        onSave={handleAddItem}
      />

    </div>
  );
}
