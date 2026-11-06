import React, { useEffect, useRef, useState } from 'react';
import { Calendar, CheckCircle2, Sparkles, RefreshCw, Shirt, ChevronLeft, ChevronRight, Award, Check, Eye } from 'lucide-react';
import OutfitFlatLayBoard from './OutfitFlatLayBoard';
import OutfitDetailModal from './OutfitDetailModal';
import { isOnePieceGarment, isHeavyFestiveOrPartyGarment, selectBestMatchingBottom, calculateOutfitCompatibility, filterAndRankGarmentsForOccasion } from '../utils/fashionStylistEngine';
import { formatPlanDate, getEntriesForPlanDate, getPlanDateForDay, WEEKDAYS } from './WeekdayOutfitAssignment';

const isGarmentRequiringPreparation = item => {
  if (!item) return false;
  const text = `${item.category || ''} ${item.title || ''}`.toLowerCase();
  if (/\b(footwear|shoe|sneaker|loafer|boot|sandal|heel|bag|purse|handbag|tote|backpack|accessor|jewell|jewel|watch|chain|belt)\b/.test(text)) {
    return false;
  }
  return /\b(top|tops|shirt|tee|t-?shirt|blouse|sweater|hoodie|cardigan|dress|kurti|kurta|saree|lehenga|gown|jumpsuit|one_piece|one-piece|bottom|trouser|pant|jean|skirt|short|legging|chino|outerwear|jacket|coat|blazer)\b/.test(text);
};

const getPreparationGarments = outfit =>
  Object.values(outfit?.slotItems || {}).filter(isGarmentRequiringPreparation);


export default function DailyOutfitPlanner({
  userProfile,
  clothes,
  weeklySchedule,
  onScheduleOutfit,
  onRemoveScheduledOutfit,
  onConfirmOutfitWorn,
  onConfirmGarmentStatuses,
  onEnableOutfitNotifications,
  isWeekdayScheduleLoaded,
  plannerRequest
}) {
  const [weekOffset, setWeekOffset] = useState(0);
  const weekReferenceDate = new Date();
  weekReferenceDate.setDate(weekReferenceDate.getDate() + weekOffset * 7);
  const days = WEEKDAYS.map(day => ({ ...day, date: getPlanDateForDay(day.id, weekReferenceDate) }));
  const [activeDayIndex, setActiveDayIndex] = useState((new Date().getDay() + 6) % 7);
  const [isAnalyzingAgent, setIsAnalyzingAgent] = useState(false);
  const [dynamicOutfitsByDay, setDynamicOutfitsByDay] = useState({});
  const [occasionInput, setOccasionInput] = useState('College');
  const [analysisError, setAnalysisError] = useState('');
  const [pendingSelection, setPendingSelection] = useState(null);
  const [isConfirmingSelection, setIsConfirmingSelection] = useState(false);
  const [readinessAnswers, setReadinessAnswers] = useState({});
  const [modalOutfit, setModalOutfit] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [scheduleError, setScheduleError] = useState('');
  const [planNotice, setPlanNotice] = useState('');
  const [removingScheduleId, setRemovingScheduleId] = useState('');
  const [wearSavingScheduleId, setWearSavingScheduleId] = useState('');
  const [notificationMessage, setNotificationMessage] = useState('');
  const processedPlannerRequest = useRef(null);

  const updateOccasion = value => {
    setOccasionInput(value);
    setDynamicOutfitsByDay({});
    setAnalysisError('');
  };

  useEffect(() => {
    if (!planNotice) return undefined;
    const timeout = window.setTimeout(() => setPlanNotice(''), 4500);
    return () => window.clearTimeout(timeout);
  }, [planNotice]);

  // Categorize stored wardrobe items from SQLite DB
  const getCategorizedWardrobe = () => {
    const items = (clothes || []).filter(item =>
      ['ready', 'available'].includes(item.availability_status || 'ready')
      && (item.ironing_status || 'ready') === 'ready'
    );
    const topsList = [];
    const bottomsList = [];
    const footwearList = [];
    const bagsList = [];
    const accessoriesList = [];
    const outerwearList = [];

    items.forEach(c => {
      const cat = (c.category || '').toLowerCase();
      const title = (c.title || '').toLowerCase();

      if (isOnePieceGarment(c) || ['tops', 'top', 'shirt', 'tee', 'blouse', 'sweater', 'hoodie', 'kurti'].some(kw => cat.includes(kw) || title.includes(kw))) {
        topsList.push(c);
      } else if (['bottoms', 'bottom', 'pants', 'jeans', 'trousers', 'skirt', 'short', 'chino', 'cargo'].some(kw => cat.includes(kw) || title.includes(kw))) {
        bottomsList.push(c);
      } else if (['footwear', 'foot', 'shoes', 'sneakers', 'loafers', 'boots', 'sandals', 'heels'].some(kw => cat.includes(kw) || title.includes(kw))) {
        footwearList.push(c);
      } else if (['bags', 'bag', 'purse', 'handbag', 'tote', 'crossbody', 'backpack'].some(kw => cat.includes(kw) || title.includes(kw))) {
        bagsList.push(c);
      } else if (['outerwear', 'outer', 'jacket', 'coat', 'blazer'].some(kw => cat.includes(kw) || title.includes(kw))) {
        outerwearList.push(c);
      } else {
        accessoriesList.push(c);
      }
    });

    return {
      tops: topsList,
      bottoms: bottomsList,
      footwear: footwearList,
      bags: bagsList,
      accessories: accessoriesList,
      outerwear: outerwearList
    };
  };

  // Generate 4 distinct complete outfit options for each day grounded in stored wardrobe items
  const generateOutfitOptionsForDay = (dayId) => {
    if (dynamicOutfitsByDay[dayId]) {
      return dynamicOutfitsByDay[dayId];
    }

    const catItems = getCategorizedWardrobe();
    const dayOffset = days.findIndex(d => d.id === dayId);
    
    // Target formality based on daily routine (College = 5 casual/smart-casual, Office = 8 formal)
    const routine = userProfile?.defaultRoutine || 'College Student';
    const isOffice = routine.toLowerCase().includes('office') || routine.toLowerCase().includes('professional');
    const targetFormality = isOffice ? 8 : 5;

    const rankedTops = filterAndRankGarmentsForOccasion(catItems.tops, targetFormality);
    const rankedBottoms = filterAndRankGarmentsForOccasion(catItems.bottoms, targetFormality);
    const rankedFootwear = filterAndRankGarmentsForOccasion(catItems.footwear, targetFormality);
    const rankedOuterwear = filterAndRankGarmentsForOccasion(catItems.outerwear, targetFormality);

    // Strictly filter out heavy festive/wedding/party dresses for daily routine
    const dailyTops = rankedTops.filter(item => {
      const isHeavy = isHeavyFestiveOrPartyGarment(item);
      const title = (item.title || '').toLowerCase();
      const style = (item.style || '').toLowerCase();
      return !isHeavy && !title.includes('wedding') && !title.includes('party') && !style.includes('wedding') && !style.includes('party');
    });

    const effectiveTops = dailyTops.length > 0 ? dailyTops : rankedTops;

    const trendThemes = [
      {
        title: 'Smart Oversized Campus & Tailoring Look',
        trendSignal: '🔥 Verified Trend: Oversized Linen & Wide-Leg Tailoring',
        vibe: 'Clean Smart Campus'
      },
      {
        title: 'Streetwear Layered Denim & Loafers Look',
        trendSignal: '🔥 Verified Trend: Vintage Outerwear & Dark Denim',
        vibe: 'Effortless Street Style'
      },
      {
        title: 'Clean Minimalist Monochrome Ensemble',
        trendSignal: '🔥 Verified Trend: Monochrome Dark Neutrals',
        vibe: 'Minimalist Chic'
      },
      {
        title: 'Athleisure Comfort Rotation',
        trendSignal: '🔥 Verified Trend: Relaxed Athleisure & Chunky Sneakers',
        vibe: 'Sporty Campus'
      }
    ];

    const isBagExcluded = Boolean(
      userProfile?.excludeBags || 
      (userProfile?.activeExclusions && userProfile.activeExclusions.some(ex => ex.toLowerCase().includes('bag') || ex.toLowerCase().includes('purse'))) ||
      (userProfile?.userBio && /no bag|no bags|don't want bag|don't want bags|without bag|without bags|no purse|no handbag|didn't give me purse|didn't give me bag/i.test(userProfile.userBio)) ||
      (userProfile?.context_rules && /no bag|no bags|don't want bag|don't want bags|without bag|without bags|no purse|no handbag|didn't give me purse|didn't give me bag/i.test(userProfile.context_rules))
    );

    const isAccExcluded = Boolean(
      userProfile?.excludeAccessories || 
      (userProfile?.activeExclusions && userProfile.activeExclusions.some(ex => ex.toLowerCase().includes('accessori') || ex.toLowerCase().includes('jewell'))) ||
      (userProfile?.userBio && /no accessor|no jewell/i.test(userProfile.userBio)) ||
      (userProfile?.context_rules && /no accessor|no jewell/i.test(userProfile.context_rules))
    );

    const isOuterwearExcluded = Boolean(
      userProfile?.excludeOuterwear || 
      (userProfile?.activeExclusions && userProfile.activeExclusions.some(ex => ex.toLowerCase().includes('outerwear') || ex.toLowerCase().includes('jacket'))) ||
      (userProfile?.userBio && /no jacket|no coat|no outerwear/i.test(userProfile.userBio)) ||
      (userProfile?.context_rules && /no jacket|no coat|no outerwear/i.test(userProfile.context_rules))
    );

    const isFootwearExcluded = Boolean(
      userProfile?.excludeFootwear || 
      (userProfile?.activeExclusions && userProfile.activeExclusions.some(ex => ex.toLowerCase().includes('footwear') || ex.toLowerCase().includes('shoe'))) ||
      (userProfile?.userBio && /no shoe|no footwear/i.test(userProfile.userBio)) ||
      (userProfile?.context_rules && /no shoe|no footwear/i.test(userProfile.context_rules))
    );

    const preferredFootwearName = userProfile?.preferredFootwear || 
      (userProfile?.context_rules && /only want shoe|only use shoe|shoe with all|shoe only|only shoe|prefer shoe|use shoe/i.test(userProfile.context_rules) ? "Shoe" : null) ||
      (userProfile?.userBio && /only want shoe|only use shoe|shoe with all|shoe only|only shoe|prefer shoe|use shoe/i.test(userProfile.userBio) ? "Shoe" : null);

    return trendThemes.map((theme, optIdx) => {
      // Pick top item from daily casual tops only
      const topObj = effectiveTops.length > 0 ? effectiveTops[(dayOffset + optIdx) % effectiveTops.length] : (catItems.tops[0] || null);
      const isOnePiece = isOnePieceGarment(topObj);
      
      // Intelligently select style-matching bottom item from ranked bottoms
      const bottomObj = selectBestMatchingBottom(topObj, rankedBottoms.length > 0 ? rankedBottoms : catItems.bottoms, dayOffset + optIdx);

      // Footwear Selection: If preferred footwear is specified (e.g., "Shoe") and top is not Kurti/Ethnic, strictly pick "Shoe"
      let shoeObj = null;
      if (!isFootwearExcluded) {
        const topTitleStr = (topObj?.title || '').toLowerCase();
        const topStyleStr = (topObj?.style || '').toLowerCase();
        const isEthnicTop = topTitleStr.includes('kurti') || topTitleStr.includes('ethnic') || topStyleStr.includes('ethnic');

        if (preferredFootwearName && !isEthnicTop) {
          const matchedPrefShoe = catItems.footwear.find(f => (f.title || '').toLowerCase().includes(preferredFootwearName.toLowerCase()));
          if (matchedPrefShoe) {
            shoeObj = matchedPrefShoe;
          }
        }

        if (!shoeObj) {
          shoeObj = rankedFootwear.length > 0 ? rankedFootwear[(dayOffset + optIdx) % rankedFootwear.length] : null;
        }
      }

      const bagObj = isBagExcluded ? null : (catItems.bags.length > 0 ? catItems.bags[(dayOffset + optIdx) % catItems.bags.length] : null);
      const accObj = isAccExcluded ? null : (catItems.accessories.length > 0 ? catItems.accessories[(dayOffset + optIdx) % catItems.accessories.length] : null);
      
      // Smart Outerwear Matching: Outerwear is NOT added by default unless top requires layering (crop top, tank top, tube top) or cold weather!
      let outerObj = null;
      if (!isOuterwearExcluded && rankedOuterwear.length > 0) {
        const topTitleStr = (topObj?.title || '').toLowerCase();
        const topTypeStr = (topObj?.attributes?.type || topObj?.category || '').toLowerCase();
        const needsLayering = topTitleStr.includes('crop') || topTitleStr.includes('tank') || topTitleStr.includes('sleeveless') || topTitleStr.includes('tube') || topTypeStr.includes('crop') || topTypeStr.includes('tank');
        if (needsLayering) {
          outerObj = rankedOuterwear[optIdx % rankedOuterwear.length];
        }
      }

      const topTitle = topObj ? topObj.title : 'Oversized White Linen Shirt';
      const bottomTitle = isOnePiece ? 'None Needed (One-Piece Dress)' : (bottomObj ? bottomObj.title : 'Beige Pleated Trousers');
      const shoeTitle = isFootwearExcluded ? null : (shoeObj ? shoeObj.title : 'White Classic Sneakers');
      const bagTitle = isBagExcluded ? null : (bagObj ? bagObj.title : 'Black Canvas Tote Bag / Purse');
      const accTitle = isAccExcluded ? null : (accObj ? accObj.title : 'Gold Analog Watch & Minimal Chain');
      const outerTitle = outerObj ? outerObj.title : 'None Needed';

      const heroImage = (topObj && topObj.imageUrl) || (bottomObj && bottomObj.imageUrl) || (shoeObj && shoeObj.imageUrl) || 'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=600&q=80';


      const compat = calculateOutfitCompatibility(topObj, bottomObj);
      const isHeavy = topObj ? (topObj.title || '').toLowerCase().includes('wedding') || (topObj.title || '').toLowerCase().includes('party') || (topObj.title || '').toLowerCase().includes('anarkali') || (topObj.title || '').toLowerCase().includes('gown') : false;
      
      let computedScore = `${compat.score}%`;
      if (isOnePiece) {
        computedScore = isHeavy ? '72%' : '96%';
      }

      // Dynamic Title Generator based on actual garments selected
      let dynamicTitle = theme.title;
      if (topObj) {
        const topName = topObj.title || 'Top';
        if (isOnePiece) {
          dynamicTitle = isHeavy ? `Festive ${topName} & Footwear Look` : `Breezy Everyday ${topName} Look`;
        } else if (bottomObj) {
          dynamicTitle = `${topName} & ${bottomObj.title} Pair`;
        } else {
          dynamicTitle = `${topName} Ensemble`;
        }
      }

      let reasonStr = isOnePiece 
        ? `AI Stylist matched stored '${topTitle}' as a standalone one-piece silhouette.`
        : `AI Stylist evaluated style & color harmony: paired '${topTitle}' with compatible '${bottomTitle}', matched with '${shoeTitle}'.`;

      if (isHeavy) {
        reasonStr += ` (Notice: Heavy wedding/party dresses are best suited for festive celebrations).`;
      }

      return {
        id: `${dayId}-opt-${optIdx + 1}`,
        title: dynamicTitle,
        matchScore: computedScore,
        trendSignal: theme.trendSignal,
        reason: reasonStr,
        image: heroImage,
        slotItems: {
          topObj,
          bottomObj,
          shoeObj,
          bagObj,
          accObj,
          outerObj,
          isBagExcluded,
          isAccExcluded
        },
        slots: {
          top: topTitle,
          bottom: bottomTitle,
          footwear: shoeTitle,
          bag: bagTitle,
          accessory: accTitle,
          outerwear: outerTitle
        }
      };
    });
  };


  const handleRunBackendAgent = async (requestedOccasion = occasionInput) => {
    if (!requestedOccasion?.trim()) {
      setAnalysisError('Enter or select an occasion before analyzing outfits.');
      return;
    }
    setIsAnalyzingAgent(true);
    setAnalysisError('');
    setPlanNotice('');
    try {
      const res = await fetch('http://localhost:8000/api/stylist-recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 1,
          occasion: requestedOccasion.trim(),
          style_preference: userProfile?.stylePreference || 'stylish-trendy',
          exclude_bags: userProfile?.excludeBags || false,
          exclude_accessories: userProfile?.excludeAccessories || false,
          context_rules: userProfile?.userBio || null,
          clothes: clothes || []
        })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Could not analyze outfits for this occasion.');
      }
      setDynamicOutfitsByDay(previous => {
        const resultsByDay = { ...previous };
        days.forEach(day => {
          resultsByDay[day.id] = data.outfits || [];
        });
        return resultsByDay;
      });
      if (!data.outfits?.length) setAnalysisError(data.message || 'No suitable ready-to-wear outfit matched this occasion.');
    } catch (err) {
      setAnalysisError(err.message || 'Could not analyze outfits for this occasion.');
    } finally {
      setIsAnalyzingAgent(false);
    }
  };

  const currentDay = days[activeDayIndex];
  const todayPlanDate = getPlanDateForDay(days[(new Date().getDay() + 6) % 7].id);
  useEffect(() => {
    if (!plannerRequest?.requestId || processedPlannerRequest.current === plannerRequest.requestId) return;
    processedPlannerRequest.current = plannerRequest.requestId;
    const requestedDayIndex = days.findIndex(day => day.id === plannerRequest.dayId);
    setActiveDayIndex(requestedDayIndex >= 0 ? requestedDayIndex : 0);
    setOccasionInput(plannerRequest.occasion);
    setDynamicOutfitsByDay({});
    handleRunBackendAgent(plannerRequest.occasion);
  }, [plannerRequest]);

  const currentOptions = (dynamicOutfitsByDay[currentDay.id] || []).filter(outfit => {
    const slots = outfit.slotItems || {};
    const top = slots.topObj;
    const bottom = slots.bottomObj;
    const footwear = slots.shoeObj;
    const topIsOnePiece = top && isOnePieceGarment(top);
    if (!top?.id || !footwear?.id || (!topIsOnePiece && !bottom?.id)) return false;
    return Object.values(slots).filter(item => item && typeof item === 'object' && item.id).every(item => {
      const stored = (clothes || []).find(entry => String(entry.id) === String(item.id));
      return stored
        && ['ready', 'available'].includes(stored.availability_status || 'ready')
        && (stored.ironing_status || 'ready') === 'ready';
    });
  });
  const currentScheduledEntries = getEntriesForPlanDate(weeklySchedule, currentDay.id, currentDay.date)
    .filter(entry => entry.confirmation_status === 'awaiting');
  const olderAwaitingEntries = Object.values(weeklySchedule).flat().filter(entry =>
    entry.confirmation_status === 'awaiting' && entry.plan_date < todayPlanDate
  );
  const overdueAwaitingEntries = Object.values(weeklySchedule).flat().filter(entry =>
    entry.confirmation_status === 'awaiting' && entry.plan_date < todayPlanDate
  );

  const enableOutfitNotifications = async () => {
    if (!onEnableOutfitNotifications) return;
    try {
      const permission = await onEnableOutfitNotifications();
      setNotificationMessage(
        permission === 'granted'
          ? 'Outfit reminders are enabled.'
          : permission === 'unsupported'
            ? 'This browser does not support desktop notifications. Past plans will remain listed here.'
            : 'Notifications were not enabled. Past plans will remain listed here.'
      );
    } catch (error) {
      setNotificationMessage(`Could not enable reminders: ${error.message}`);
    }
  };
  const selectedForCurrentDay = currentScheduledEntries.some(entry => entry.outfit?.id === modalOutfit?.id);

  const handleSelectOutfit = async (outfit) => {
    if (!occasionInput.trim() || !isWeekdayScheduleLoaded || currentDay.date < todayPlanDate) return;
    if (currentScheduledEntries.some(entry => entry.outfit?.id === outfit.id)) return;
    const garments = getPreparationGarments(outfit);
    setReadinessAnswers(Object.fromEntries(garments.map(item => [String(item.id), 'ready'])));
    setPendingSelection({ outfit, garments, day: currentDay });
  };

  const confirmSelectedOutfit = async () => {
    if (!pendingSelection || isConfirmingSelection) return;
    const { outfit, garments, day } = pendingSelection;
    const updates = garments
      .filter(item => readinessAnswers[String(item.id)] !== 'ready')
      .map(item => ({
        item_id: String(item.id),
        availability_status: readinessAnswers[String(item.id)] === 'needs_washing' ? 'to_wash' : 'ready',
        ironing_status: readinessAnswers[String(item.id)] === 'needs_ironing' ? 'needs_ironing' : 'ready',
      }));
    setScheduleError('');
    setPlanNotice('');
    setIsConfirmingSelection(true);
    try {
      if (updates.length) {
        await onConfirmGarmentStatuses(updates);
        setDynamicOutfitsByDay(previous => ({
          ...previous,
          [day.id]: (previous[day.id] || []).filter(item => item.id !== outfit.id)
        }));
        setPlanNotice(`${outfit.title} was not scheduled because one or more garments need preparation. Choose another look.`);
      } else {
        await onScheduleOutfit(
          day.id,
          outfit,
          'occasion',
          occasionInput.trim(),
          garments.map(item => String(item.id)),
          day.date
        );
        setPlanNotice(`Added ${occasionInput.trim()} look for ${day.label}.`);
      }
      setPendingSelection(null);
    } catch (error) {
      setScheduleError(error.message || 'Could not verify and schedule this outfit.');
    } finally {
      setIsConfirmingSelection(false);
    }
  };

  const handleRemoveOutfit = async (scheduleId) => {
    setScheduleError('');
    setRemovingScheduleId(scheduleId);
    try {
      await onRemoveScheduledOutfit(scheduleId);
    } catch (error) {
      setScheduleError(error.message || 'Could not remove the planned outfit.');
    } finally {
      setRemovingScheduleId('');
    }
  };

  const handleWearConfirmation = async (dayId, planDate, scheduleId, outfit, worn) => {
    setScheduleError('');
    setWearSavingScheduleId(scheduleId);
    try {
      const result = await onConfirmOutfitWorn(outfit, planDate, dayId, scheduleId, worn);
      setScheduleError(worn
        ? (result?.duplicate ? 'This outfit already has a wear check for today.' : 'Worn outfit confirmed. Complete the laundry check above.')
        : 'Noted — this outfit was not worn, and its clothes remain unchanged. You can reschedule it below.');
    } catch (error) {
      setScheduleError(error.message || 'Could not record this outfit confirmation.');
    } finally {
      setWearSavingScheduleId('');
    }
  };

  const handleOpenModal = (outfit) => {
    setModalOutfit(outfit);
    setIsModalOpen(true);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', maxWidth: '1100px', margin: '0 auto', width: '100%' }}>
      
      {/* Clean Interactive Top Header & Action Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0F172A', fontFamily: 'var(--font-heading)', lineHeight: 1.1 }}>
            Outfit Planner
          </h1>
          <p style={{ color: '#64748B', fontSize: '0.88rem', marginTop: '0.25rem' }}>
            Get wardrobe-based recommendations for any occasion, then plan multiple ready-to-wear looks on the same day.
          </p>
        </div>

        {/* Action Buttons & Weekly Progress */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', background: '#FFFFFF', padding: '0.6rem 1.1rem', borderRadius: '14px', border: '1px solid #ECEBF5', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' }}>
            <Calendar size={18} color="#7C4DFF" />
            <div style={{ fontSize: '0.82rem' }}>
              <span style={{ fontWeight: 800, color: '#0F172A' }}>
                {Object.values(weeklySchedule).flat().filter(entry => entry.confirmation_status === 'awaiting').length} active looks · {days.length} dates
              </span>
            </div>
          </div>
        </div>
      </div>

      <section className="card-widget" style={{ borderRadius: 22, padding: '1.35rem', background: '#fff', border: '1px solid #ECE7FE' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 5 }}>
          <Sparkles size={20} color="#7C4DFF" />
          <h2 style={{ margin: 0, color: '#1C1D21', fontSize: '1.08rem', fontWeight: 850 }}>Find a look for your occasion</h2>
        </div>
        <p style={{ margin: '0 0 1rem 29px', color: '#64748B', fontSize: '0.8rem' }}>
          Recommendations use your wardrobe, style preferences, occasion rules, and live availability checks.
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(180px, 1fr) minmax(180px, 1fr) auto', gap: 10, alignItems: 'end' }}>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 5, color: '#475569', fontSize: '0.75rem', fontWeight: 750 }}>
            Occasion
            <select
              value={['College', 'Wedding', 'Dinner date', 'Party', 'Interview'].includes(occasionInput) ? occasionInput : 'Custom'}
              onChange={event => {
                updateOccasion(event.target.value === 'Custom' ? '' : event.target.value);
              }}
              style={{ border: '1px solid #E2E8F0', borderRadius: 10, padding: '0.68rem 0.75rem', background: '#fff', color: '#334155' }}
            >
              <option>College</option>
              <option>Wedding</option>
              <option>Dinner date</option>
              <option>Party</option>
              <option>Interview</option>
              <option value="Custom">Custom occasion</option>
            </select>
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 5, color: '#475569', fontSize: '0.75rem', fontWeight: 750 }}>
            {['College', 'Wedding', 'Dinner date', 'Party', 'Interview'].includes(occasionInput) ? 'Custom occasion or details' : 'Enter an occasion'}
            <input
              aria-label="Enter a custom occasion"
              value={occasionInput}
              onChange={event => updateOccasion(event.target.value)}
              onKeyDown={event => event.key === 'Enter' && handleRunBackendAgent()}
              maxLength={100}
              placeholder="e.g. College, wedding, dinner date..."
              style={{ border: '1px solid #E2E8F0', borderRadius: 10, padding: '0.68rem 0.75rem' }}
            />
          </label>
          <button
            type="button"
            onClick={() => handleRunBackendAgent()}
            disabled={isAnalyzingAgent || !isWeekdayScheduleLoaded}
            className="btn-primary"
            style={{ minHeight: 42, padding: '0.65rem 1.1rem', borderRadius: 11, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 7 }}
          >
            <RefreshCw size={15} className={isAnalyzingAgent ? 'spin-animation' : ''} />
            {isAnalyzingAgent ? 'Analyzing…' : 'Analyze Outfits'}
          </button>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7, marginTop: 11 }}>
          {['College', 'Wedding', 'Dinner date', 'Party', 'Interview'].map(preset => (
            <button
              type="button"
              key={preset}
              onClick={() => updateOccasion(preset)}
              aria-pressed={occasionInput === preset}
              style={{ border: `1px solid ${occasionInput === preset ? '#7C4DFF' : '#E9E5F5'}`, borderRadius: 999, padding: '0.38rem 0.72rem', background: occasionInput === preset ? '#F0EBFF' : '#FAFAFC', color: occasionInput === preset ? '#7C4DFF' : '#64748B', fontSize: '0.72rem', fontWeight: 750, cursor: 'pointer' }}
            >
              {preset}
            </button>
          ))}
        </div>
        <p style={{ margin: '0.7rem 0 0', color: '#54727D', fontSize: '0.74rem' }}>
          These recommendations are available across all seven days. Choose a day below to add a look to that day's plan.
        </p>
      </section>

      {/* Clean Day Navigation Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10 }}>
        <button type="button" onClick={() => setWeekOffset(value => value - 1)} style={{ display: 'inline-flex', alignItems: 'center', gap: 5, border: '1px solid #E2E8F0', borderRadius: 9, padding: '0.45rem 0.65rem', background: '#fff', color: '#475569', fontWeight: 700, cursor: 'pointer' }}>
          <ChevronLeft size={15} /> Previous week
        </button>
        <strong style={{ color: '#475569', fontSize: '0.85rem' }}>
          {formatPlanDate(days[0].date).split(', ').slice(1).join(', ')} – {formatPlanDate(days[6].date).split(', ').slice(1).join(', ')}
        </strong>
        <button type="button" onClick={() => setWeekOffset(value => value + 1)} style={{ display: 'inline-flex', alignItems: 'center', gap: 5, border: '1px solid #E2E8F0', borderRadius: 9, padding: '0.45rem 0.65rem', background: '#fff', color: '#475569', fontWeight: 700, cursor: 'pointer' }}>
          Next week <ChevronRight size={15} />
        </button>
      </div>
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '0.75rem',
        background: '#FFFFFF',
        padding: '0.6rem',
        borderRadius: '20px',
        border: '1px solid #ECEBF5',
        boxShadow: '0 4px 16px rgba(0,0,0,0.02)'
      }}>
        {days.map((day, idx) => {
          const isActive = activeDayIndex === idx;
          const plannedCount = getEntriesForPlanDate(weeklySchedule, day.id, day.date)
            .filter(entry => entry.confirmation_status === 'awaiting').length;
          const isPlanned = plannedCount > 0;
          const isPastDate = day.date < todayPlanDate;
          const isToday = day.date === todayPlanDate;

          return (
            <button
              key={day.id}
              onClick={() => setActiveDayIndex(idx)}
              style={{
                flex: '1 0 105px',
                padding: '0.75rem 1rem',
                borderRadius: '14px',
                border: 'none',
                background: isActive 
                  ? 'linear-gradient(135deg, #7C4DFF 0%, #6366F1 100%)' 
                  : isPlanned ? '#F0EBFF' : 'transparent',
                color: isActive ? '#FFFFFF' : isPlanned ? '#7C4DFF' : '#606470',
                fontWeight: isActive || isPlanned ? 700 : 500,
                fontSize: '0.9rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                transition: 'all 0.2s ease',
                boxShadow: isActive ? '0 4px 14px rgba(124, 77, 255, 0.3)' : 'none'
              }}
            >
              {isPlanned && <CheckCircle2 size={16} color={isActive ? '#FFFFFF' : '#7C4DFF'} />}
              <span>{day.label} · {new Date(`${day.date}T12:00:00`).toLocaleDateString([], { month: 'short', day: 'numeric' })}{isToday ? ' · Today' : isPastDate ? ' · Past' : plannedCount > 0 ? ` · ${plannedCount}` : ''}</span>
            </button>
          );
        })}
      </div>

      {/* Active Day Section Title */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#1C1D21' }}>
          {currentOptions.length} recommendation{currentOptions.length === 1 ? '' : 's'} for {occasionInput} · {formatPlanDate(currentDay.date)}
        </h2>
        <span style={{ fontSize: '0.82rem', color: '#7C4DFF', background: '#F0EBFF', padding: '0.3rem 0.75rem', borderRadius: '999px', fontWeight: 700 }}>
          ✨ Matched from {clothes?.length || 0} stored wardrobe items
        </span>
      </div>
      {analysisError && (
        <div role="status" style={{ color: '#64748B', background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: 12, padding: '0.9rem 1rem', fontSize: '0.85rem' }}>
          {analysisError}
        </div>
      )}
      {planNotice && <p role="status" style={{ color: '#047857', background: '#ECFDF5', borderRadius: 10, padding: '0.65rem 0.8rem', margin: 0 }}>{planNotice}</p>}
      {/* Outfit recommendation cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.25rem' }}>
        {scheduleError && <p role="alert" style={{ color: '#DC2626' }}>{scheduleError}</p>}
        {currentScheduledEntries.length > 0 && (
          <p style={{ color: '#606470', margin: 0, gridColumn: '1 / -1' }}>
            {currentScheduledEntries.length} look{currentScheduledEntries.length === 1 ? '' : 's'} already planned for {currentDay.label}; a new occasion can be added alongside them.
          </p>
        )}
        {!currentOptions.length && !analysisError && !isAnalyzingAgent && (
          <p style={{ color: '#64748B', gridColumn: '1 / -1', margin: 0 }}>
            Choose an occasion and click <strong>Analyze Outfits</strong> to get wardrobe-matched recommendations.
          </p>
        )}
        {currentOptions.map((option, idx) => {
          const isSelected = currentScheduledEntries.some(entry => entry.outfit?.id === option.id);

          return (
            <div
              key={option.id}
              className="card-widget"
              onClick={() => handleOpenModal(option)}
              style={{
                borderRadius: '20px',
                padding: 0,
                overflow: 'hidden',
                display: 'flex',
                flexDirection: 'column',
                border: isSelected ? '2px solid #7C4DFF' : '1px solid #ECEBF5',
                boxShadow: isSelected ? '0 8px 25px rgba(124, 77, 255, 0.2)' : 'var(--shadow-card)',
                transition: 'all 0.25s ease',
                transform: isSelected ? 'translateY(-4px)' : 'none',
                cursor: 'pointer'
              }}
            >
              {/* Pinterest Outfit Flat-Lay Collage Header */}
              <div style={{ position: 'relative' }}>
                <OutfitFlatLayBoard 
                  slotItems={option.slotItems} 
                  title={option.title} 
                  height={320} 
                />
                
                {/* Match Score Badge */}
                <div style={{
                  position: 'absolute',
                  top: '12px',
                  left: '12px',
                  background: 'rgba(255, 255, 255, 0.95)',
                  color: '#7C4DFF',
                  padding: '0.25rem 0.65rem',
                  borderRadius: '999px',
                  fontSize: '0.75rem',
                  fontWeight: 800,
                  backdropFilter: 'blur(6px)',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                  zIndex: 2
                }}>
                  Option #{idx + 1} • {option.matchScore} Match
                </div>

                {isSelected && (
                  <div style={{
                    position: 'absolute',
                    top: '12px',
                    right: '12px',
                    background: '#7C4DFF',
                    color: '#FFFFFF',
                    padding: '0.3rem 0.7rem',
                    borderRadius: '999px',
                    fontSize: '0.75rem',
                    fontWeight: 800,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.3rem',
                    boxShadow: '0 4px 12px rgba(124, 77, 255, 0.3)',
                    zIndex: 2
                  }}>
                    <Check size={14} /> Selected for {currentDay.label}
                  </div>
                )}
              </div>

              {/* Card Content */}
              <div style={{ padding: '1.25rem', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  {option.trendSignal && (
                    <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#7C4DFF', background: '#F0EBFF', padding: '0.2rem 0.55rem', borderRadius: '6px', marginBottom: '0.4rem', display: 'inline-block' }}>
                      {option.trendSignal}
                    </div>
                  )}
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#1C1D21', marginBottom: '0.4rem', lineHeight: 1.25 }}>
                    {option.title}
                  </h3>
                  <p style={{ fontSize: '0.8rem', color: '#606470', lineHeight: 1.4, marginBottom: '1rem' }}>
                    {option.reason}
                  </p>

                  {/* Clean Complete Look Slot Tags (Top, Bottom, Footwear, Purse/Bag, Jewellery/Accessory) */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem', marginBottom: '1.25rem', background: '#FAF9FE', padding: '0.75rem', borderRadius: '14px', border: '1px solid #ECE7FE' }}>
                    <div style={{ fontSize: '0.78rem', color: '#1C1D21' }}>
                      <strong style={{ color: '#7C4DFF' }}>{isOnePieceGarment(option?.slotItems?.topObj) ? '👗 One-Piece Dress:' : '👔 Top:'}</strong> {option?.slots?.top || 'Top Garment'}
                    </div>
                    {!isOnePieceGarment(option?.slotItems?.topObj) && option?.slots?.bottom && !option.slots.bottom.includes('None Needed') && (
                      <div style={{ fontSize: '0.78rem', color: '#1C1D21' }}>
                        <strong style={{ color: '#7C4DFF' }}>👖 Bottom:</strong> {option.slots.bottom}
                      </div>
                    )}
                    {option?.slots?.footwear && (
                      <div style={{ fontSize: '0.78rem', color: '#1C1D21' }}>
                        <strong style={{ color: '#7C4DFF' }}>👟 Footwear:</strong> {option.slots.footwear}
                      </div>
                    )}
                    {option?.slots?.bag && !option.slots.bag.includes('None Needed') && (
                      <div style={{ fontSize: '0.78rem', color: '#1C1D21' }}>
                        <strong style={{ color: '#7C4DFF' }}>👜 Purse / Bag:</strong> {option.slots.bag}
                      </div>
                    )}
                    {option?.slots?.accessory && !option.slots.accessory.includes('None Needed') && (
                      <div style={{ fontSize: '0.78rem', color: '#1C1D21' }}>
                        <strong style={{ color: '#7C4DFF' }}>💎 Jewellery:</strong> {option.slots.accessory}
                      </div>
                    )}
                    {option?.slots?.outerwear && option.slots.outerwear !== 'None Needed' && (
                      <div style={{ fontSize: '0.78rem', color: '#1C1D21' }}>
                        <strong style={{ color: '#7C4DFF' }}>🧥 Outerwear:</strong> {option.slots.outerwear}
                      </div>
                    )}
                  </div>

                </div>

                {/* Card Action Buttons */}
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSelectOutfit(option);
                    }}
                    disabled={isSelected || !occasionInput.trim() || !isWeekdayScheduleLoaded}
                    className={isSelected ? 'btn-secondary' : 'btn-primary'}
                    style={{
                      flex: 1,
                      justifyContent: 'center',
                      padding: '0.7rem 0.85rem',
                      fontSize: '0.82rem',
                      borderRadius: '14px',
                      background: isSelected ? '#F0EBFF' : 'var(--primary-gradient)',
                      color: isSelected ? '#7C4DFF' : '#FFFFFF'
                    }}
                  >
                    {isSelected ? (
                      <>
                        <CheckCircle2 size={16} /> Already planned
                      </>
                    ) : (
                      <>
                        Verify & add look <ChevronRight size={15} />
                      </>
                    )}
                  </button>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleOpenModal(option);
                    }}
                    style={{
                      background: '#F4F4F6',
                      border: '1px solid #ECEBF5',
                      borderRadius: '14px',
                      padding: '0.7rem 0.85rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      cursor: 'pointer',
                      color: '#606470',
                      transition: 'all 0.15s ease'
                    }}
                    title="Inspect outfit details"
                  >
                    <Eye size={16} />
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Weekly Schedule Summary Card */}
      <div className="card-widget" style={{ borderRadius: '24px', padding: '1.5rem', background: '#FFFFFF' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#1C1D21', marginBottom: '1rem' }}>
          🗓️ Your Dated Occasion Plan
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
            {days.map(d => {
              const scheduledEntries = getEntriesForPlanDate(weeklySchedule, d.id, d.date)
                .filter(entry => entry.confirmation_status === 'awaiting');
              return (
                <div 
                  key={d.date} 
                  style={{
                    background: scheduledEntries.length ? '#FAF9FE' : '#F9FAFB',
                    border: scheduledEntries.length ? '1px solid #ECE7FE' : '1px dashed #E5E7EB',
                    borderRadius: '16px',
                    padding: '0.9rem 1rem',
                  }}
                >
                  <div style={{ fontSize: '0.75rem', fontWeight: 800, color: scheduledEntries.length ? '#7C4DFF' : '#9CA3AF', textTransform: 'uppercase', marginBottom: '0.6rem' }}>
                    {formatPlanDate(d.date)}
                  </div>
                  {scheduledEntries.length ? scheduledEntries.map(scheduledEntry => {
                    const outfit = scheduledEntry.outfit;
                    const unavailableGarments = Object.values(outfit?.slotItems || {})
                      .filter(item => {
                        if (!item?.id) return false;
                        const wardrobeItem = (clothes || []).find(
                          entry => String(entry.id) === String(item.id)
                        );
                        return !wardrobeItem
                          || !['ready', 'available'].includes(wardrobeItem.availability_status || 'ready')
                          || (wardrobeItem?.ironing_status || 'ready') !== 'ready';
                      })
                      .map(item => item.title);
                    return (
                      <div key={scheduledEntry.schedule_id} style={{ background: '#fff', border: '1px solid #ECE7FE', borderRadius: 12, padding: '0.7rem', marginTop: '0.55rem' }}>
                        <button type="button" onClick={() => handleOpenModal(outfit)} style={{ display: 'block', width: '100%', textAlign: 'left', padding: 0, border: 0, background: 'transparent', cursor: 'pointer' }}>
                          <strong style={{ display: 'block', color: '#7C4DFF', fontSize: '0.72rem' }}>{scheduledEntry.occasion || 'Outfit'}</strong>
                          <span style={{ display: 'block', color: '#1C1D21', fontSize: '0.83rem', fontWeight: 800, marginTop: 3 }}>{outfit?.title || 'Planned look'}</span>
                          <span style={{ display: 'block', color: '#606470', fontSize: '0.72rem', marginTop: 3 }}>{outfit?.slots?.top || 'Top'} + {outfit?.slots?.bottom || 'Bottom'}</span>
                        </button>
                        {unavailableGarments.length > 0 && (
                          <div role="alert" style={{ marginTop: '0.45rem', color: '#B91C1C', background: '#FEF2F2', borderRadius: 8, padding: '0.4rem 0.5rem', fontSize: '0.7rem', fontWeight: 750 }}>
                            Not ready: {unavailableGarments.join(', ')}
                          </div>
                        )}
                        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: '0.6rem' }}>
                          {d.date <= todayPlanDate && (
                            <>
                              <span style={{ alignSelf: 'center', color: '#64748B', fontSize: '0.68rem', fontWeight: 700 }}>
                                {d.date < todayPlanDate ? 'Awaiting confirmation' : 'Did you wear this?'}
                              </span>
                              <button
                                type="button"
                                onClick={() => handleWearConfirmation(d.id, d.date, scheduledEntry.schedule_id, outfit, true)}
                                disabled={wearSavingScheduleId === scheduledEntry.schedule_id}
                                style={{ border: 0, borderRadius: 8, padding: '0.4rem 0.5rem', background: '#ECFDF5', color: '#047857', fontSize: '0.7rem', fontWeight: 800, cursor: 'pointer' }}
                              >
                                {wearSavingScheduleId === scheduledEntry.schedule_id ? 'Saving…' : 'Yes, I wore it'}
                              </button>
                              <button
                                type="button"
                                onClick={() => handleWearConfirmation(d.id, d.date, scheduledEntry.schedule_id, outfit, false)}
                                disabled={wearSavingScheduleId === scheduledEntry.schedule_id}
                                style={{ border: '1px solid #E2E8F0', borderRadius: 8, padding: '0.4rem 0.5rem', background: '#fff', color: '#64748B', fontSize: '0.7rem', fontWeight: 700, cursor: 'pointer' }}
                              >
                                No, I didn’t
                              </button>
                            </>
                          )}
                          <button
                            type="button"
                            onClick={() => handleRemoveOutfit(scheduledEntry.schedule_id)}
                            disabled={removingScheduleId === scheduledEntry.schedule_id}
                            style={{ border: 0, background: 'transparent', color: '#DC2626', fontSize: '0.7rem', fontWeight: 700, cursor: 'pointer' }}
                          >
                            {removingScheduleId === scheduledEntry.schedule_id ? 'Removing…' : 'Remove'}
                          </button>
                        </div>
                      </div>
                    );
                  }) : (
                    <span style={{ fontSize: '0.78rem', color: '#9CA3AF', italic: true }}>No outfit picked yet</span>
                  )}
                </div>
              );
            })}
          </div>
          {(olderAwaitingEntries.length > 0 || (
            overdueAwaitingEntries.length > 0 && 'Notification' in window && Notification.permission !== 'granted'
          )) && (
            <section aria-label="Past outfits awaiting confirmation" style={{ marginTop: '1rem', padding: '0.9rem', borderRadius: 12, background: '#FFFBEB', border: '1px solid #FDE68A' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                {olderAwaitingEntries.length > 0 && <h4 style={{ margin: 0, color: '#92400E', fontSize: '0.82rem' }}>Past outfits awaiting confirmation</h4>}
                {overdueAwaitingEntries.length > 0 && 'Notification' in window && Notification.permission !== 'granted' && (
                  <button type="button" onClick={enableOutfitNotifications} style={{ border: '1px solid #FDE68A', borderRadius: 7, padding: '0.35rem 0.5rem', background: '#fff', color: '#92400E', fontSize: '0.68rem', fontWeight: 750, cursor: 'pointer' }}>
                    Turn on reminders
                  </button>
                )}
              </div>
              {notificationMessage && <p role="status" style={{ margin: '0.4rem 0', color: '#92400E', fontSize: '0.72rem' }}>{notificationMessage}</p>}
              {olderAwaitingEntries.map(entry => (
                <div key={entry.schedule_id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap', padding: '0.45rem 0', borderTop: '1px solid #FDE68A' }}>
                  <span style={{ color: '#78350F', fontSize: '0.75rem' }}>
                    Did you wear your planned outfit on {formatPlanDate(entry.plan_date)}? {entry.outfit?.title || ''}
                  </span>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button type="button" onClick={() => handleWearConfirmation(entry.day_id, entry.plan_date, entry.schedule_id, entry.outfit, true)} disabled={wearSavingScheduleId === entry.schedule_id} style={{ border: 0, borderRadius: 7, padding: '0.35rem 0.5rem', background: '#ECFDF5', color: '#047857', fontSize: '0.68rem', fontWeight: 800, cursor: 'pointer' }}>
                      Yes, I wore it
                    </button>
                    <button type="button" onClick={() => handleWearConfirmation(entry.day_id, entry.plan_date, entry.schedule_id, entry.outfit, false)} disabled={wearSavingScheduleId === entry.schedule_id} style={{ border: '1px solid #E2E8F0', borderRadius: 7, padding: '0.35rem 0.5rem', background: '#fff', color: '#64748B', fontSize: '0.68rem', fontWeight: 700, cursor: 'pointer' }}>
                      No, I didn’t
                    </button>
                  </div>
                </div>
              ))}
            </section>
          )}
          {Object.values(weeklySchedule).flat().some(entry =>
            entry.confirmation_status === 'not_worn'
          ) && (
            <div style={{ marginTop: '1rem', borderTop: '1px solid #ECEBF5', paddingTop: '0.8rem' }}>
              <strong style={{ color: '#475569', fontSize: '0.8rem' }}>Not worn · reschedule if you like</strong>
              {Object.values(weeklySchedule).flat()
                .filter(entry => entry.confirmation_status === 'not_worn')
                .map(entry => {
                  const nextDate = new Date(`${todayPlanDate}T12:00:00`);
                  nextDate.setDate(nextDate.getDate() + 1);
                  const planDate = `${nextDate.getFullYear()}-${String(nextDate.getMonth() + 1).padStart(2, '0')}-${String(nextDate.getDate()).padStart(2, '0')}`;
                  const dayId = WEEKDAYS[nextDate.getDay() === 0 ? 6 : nextDate.getDay() - 1].id;
                  return (
                    <div key={entry.schedule_id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginTop: 6 }}>
                      <span style={{ color: '#64748B', fontSize: '0.75rem' }}>{entry.outfit?.title || 'Planned look'} · {formatPlanDate(entry.plan_date)}</span>
                      <button type="button" onClick={() => onScheduleOutfit(dayId, entry.outfit, entry.source || 'occasion', entry.occasion, [], planDate)} style={{ border: 0, borderRadius: 8, padding: '0.4rem 0.6rem', background: '#F0EBFF', color: '#7C4DFF', fontSize: '0.7rem', fontWeight: 800, cursor: 'pointer' }}>
                        Reschedule for {formatPlanDate(planDate)}
                      </button>
                    </div>
                  );
                })}
            </div>
          )}
      </div>

      {pendingSelection && (
        <div
          role="presentation"
          onMouseDown={event => {
            if (!isConfirmingSelection && event.target === event.currentTarget) setPendingSelection(null);
          }}
          style={{ position: 'fixed', inset: 0, zIndex: 1300, display: 'grid', placeItems: 'center', padding: 16, background: 'rgba(15, 23, 42, 0.48)' }}
        >
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="outfit-readiness-title"
            style={{ width: 'min(100%, 520px)', maxHeight: '85vh', overflowY: 'auto', background: '#fff', borderRadius: 20, padding: '1.25rem', boxShadow: '0 20px 60px rgba(15, 23, 42, 0.24)' }}
          >
            <h2 id="outfit-readiness-title" style={{ margin: 0, color: '#0F172A', fontSize: '1.1rem' }}>Check this look before scheduling</h2>
            <p style={{ color: '#64748B', fontSize: '0.82rem', lineHeight: 1.5 }}>
              Confirm each clothing item is clean, available, and ironed for {pendingSelection.day.label}. Bags, jewellery, and footwear are not included in this check.
            </p>
            <div style={{ display: 'grid', gap: 9 }}>
              {pendingSelection.garments.map(item => (
                <label key={item.id} style={{ display: 'grid', gridTemplateColumns: '1fr minmax(155px, 0.8fr)', gap: 10, alignItems: 'center', border: '1px solid #E2E8F0', borderRadius: 12, padding: '0.65rem 0.75rem', color: '#334155', fontSize: '0.8rem', fontWeight: 750 }}>
                  <span>{item.title}</span>
                  <select
                    aria-label={`${item.title} washing and ironing readiness`}
                    value={readinessAnswers[String(item.id)] || 'ready'}
                    disabled={isConfirmingSelection}
                    onChange={event => setReadinessAnswers(previous => ({
                      ...previous,
                      [String(item.id)]: event.target.value
                    }))}
                    style={{ border: '1px solid #E2E8F0', borderRadius: 8, padding: '0.5rem', background: '#fff', color: '#334155' }}
                  >
                    <option value="ready">Clean, ironed & ready</option>
                    <option value="needs_washing">Needs washing</option>
                    <option value="needs_ironing">Needs ironing</option>
                  </select>
                </label>
              ))}
              {!pendingSelection.garments.length && (
                <p style={{ margin: 0, color: '#64748B', fontSize: '0.8rem' }}>No garments need a laundry or ironing check for this look.</p>
              )}
            </div>
            {scheduleError && <p role="alert" style={{ color: '#B91C1C', fontSize: '0.8rem' }}>{scheduleError}</p>}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 16, flexWrap: 'wrap' }}>
              <button type="button" onClick={() => setPendingSelection(null)} disabled={isConfirmingSelection} style={{ border: '1px solid #E2E8F0', borderRadius: 10, background: '#fff', padding: '0.6rem 0.85rem', color: '#475569', fontWeight: 750, cursor: isConfirmingSelection ? 'not-allowed' : 'pointer' }}>
                Cancel
              </button>
              <button type="button" onClick={confirmSelectedOutfit} disabled={isConfirmingSelection} style={{ border: 0, borderRadius: 10, background: '#7C4DFF', padding: '0.6rem 0.9rem', color: '#fff', fontWeight: 800, cursor: isConfirmingSelection ? 'wait' : 'pointer' }}>
                {isConfirmingSelection ? 'Saving…' : Object.values(readinessAnswers).some(value => value !== 'ready') ? 'Save status & choose another' : 'Confirm ready & schedule'}
              </button>
            </div>
          </section>
        </div>
      )}

      {/* Interactive Outfit Inspector Modal */}
      <OutfitDetailModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        outfit={modalOutfit}
        dayLabel={currentDay.fullLabel}
        onSelectOutfit={handleSelectOutfit}
        isSelected={selectedForCurrentDay}
      />

    </div>
  );
}
