import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Loader2, Volume2, AlertCircle, CheckCircle, Edit2, Send, X, Maximize2, Calendar, BookmarkPlus, Plus, ImagePlus, StopCircle, Image as ImageIcon } from 'lucide-react';
import OutfitFlatLayBoard from './OutfitFlatLayBoard';
import OutfitDetailModal from './OutfitDetailModal';
import WeekdayOutfitAssignment, { getEntriesForPlanDate, getNextPlanDateForDay, getPlanDateForDay, WEEKDAYS } from './WeekdayOutfitAssignment';

const WEEKDAY_ALIASES = {
  mon: ['monday', 'mon'],
  tue: ['tuesday', 'tue', 'tues'],
  wed: ['wednesday', 'wed'],
  thu: ['thursday', 'thu', 'thur', 'thurs'],
  fri: ['friday', 'fri'],
  sat: ['saturday', 'sat'],
  sun: ['sunday', 'sun']
};

const getScheduleRequest = (message) => {
  const day = WEEKDAYS.find(({ id }) =>
    WEEKDAY_ALIASES[id].some(alias => new RegExp(`\\b${alias}\\b`, 'i').test(message))
  );
  if (!day || !/\b(save|add|plan|schedule|put|reserve|book|assign)\b/i.test(message)) {
    return null;
  }

  const preference = message.match(/\b(first|1st|second|2nd|third|3rd)\s+(?:outfit|look|option|preference|choice)\b/i);
  const preferenceIndex = {
    first: 0,
    '1st': 0,
    second: 1,
    '2nd': 1,
    third: 2,
    '3rd': 2
  };
  const occasion = [
    ['Dinner date', /\b(dinner|date|romantic)\b/i],
    ['Wedding', /\b(wedding|reception|sangeet|mehndi)\b/i],
    ['College', /\b(college|class|campus)\b/i],
    ['Work', /\b(office|work|interview|meeting)\b/i],
    ['Party', /\b(party|night out|club)\b/i]
  ].find(([, pattern]) => pattern.test(message))?.[0];

  return {
    day,
    planDate: getNextPlanDateForDay(day.id),
    outfitIndex: preference ? preferenceIndex[preference[1].toLowerCase()] : 0,
    occasion
  };
};

const getPlanCommand = (message) => {
  const day = WEEKDAYS.find(({ id }) =>
    WEEKDAY_ALIASES[id].some(alias => new RegExp(`\\b${alias}\\b`, 'i').test(message))
  );
  if (!day || !/\b(plan|planned|schedule|scheduled)\b/i.test(message)) return null;

  const removesOutfit = /\b(remove|delete|clear)\b/i.test(message);
  const replacesOutfit = /\b(add|updated|update|replace|change|refresh|new)\b/i.test(message);
  const occasion = [
    ['Dinner date', /\b(dinner|date|romantic)\b/i],
    ['Wedding', /\b(wedding|reception|sangeet|mehndi)\b/i],
    ['College', /\b(college|class|campus)\b/i],
    ['Work', /\b(office|work|interview|meeting)\b/i],
    ['Party', /\b(party|night out|club)\b/i]
  ].find(([, pattern]) => pattern.test(message))?.[0];
  if (removesOutfit && !replacesOutfit) return { day, action: 'remove', occasion };
  if (replacesOutfit || /\b(exclude|without|omit|skip)\b/i.test(message)) {
    return { day, action: 'update', occasion };
  }
  return null;
};

const selectScheduledEntry = (entries = [], command) => {
  if (command.occasion) {
    const occasion = command.occasion.toLowerCase();
    return entries.find(entry => (entry.occasion || '').toLowerCase().includes(occasion)) || null;
  }
  return entries.length === 1 ? entries[0] : null;
};

const getStylingPreferences = (request = '') => {
  const text = request.toLowerCase();
  const preferences = [];
  const occasion = [
    ['dinner date', /\b(dinner|date|romantic)\b/],
    ['Wedding', /\b(wedding|reception|sangeet)\b/],
    ['College', /\b(college|class|campus)\b/],
    ['Work', /\b(office|work|interview|meeting)\b/],
    ['Party', /\b(party|night out|club)\b/]
  ].find(([, pattern]) => pattern.test(text));
  if (occasion) preferences.push(occasion[0]);

  const color = text.match(/\b(white|black|blue|red|green|pink|beige|brown|grey|gray|yellow)\s+(?:clothes|outfit|look|only)\b|\bonly\s+(white|black|blue|red|green|pink|beige|brown|grey|gray|yellow)\b/);
  if (color) preferences.push(`${color[1] || color[2]} only`);
  if (/\b(no|without|skip|exclude)\s+(?:a\s+)?bag\b/.test(text)) preferences.push('No bag');
  if (/\b(ready to wear|ready-to-wear|ready clothes)\b/.test(text)) preferences.push('Ready-to-wear only');
  if (/\b(formal|elegant|casual|trendy|comfortable)\b/.test(text)) {
    const style = text.match(/\b(formal|elegant|casual|trendy|comfortable)\b/);
    preferences.push(`${style[1][0].toUpperCase()}${style[1].slice(1)} style`);
  }
  return preferences.length ? preferences : ['Wardrobe-matched', 'Your style'];
};

const VoiceStylist = ({
  clothes,
  userProfile,
  weekdaySchedule,
  onScheduleOutfit,
  onReplaceScheduledOutfit,
  onRemoveScheduledOutfit,
  onRefreshWardrobe,
  onRefreshWearEvents,
  isWeekdayScheduleLoaded
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [recognizedText, setRecognizedText] = useState('');
  const [editableText, setEditableText] = useState('');
  const [agentResponse, setAgentResponse] = useState('');
  const [outfits, setOutfits] = useState([]);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [messages, setMessages] = useState([]);
  const [savedLooks, setSavedLooks] = useState([]);
  const [isLoadingSavedLooks, setIsLoadingSavedLooks] = useState(false);
  const [showSavedLooks, setShowSavedLooks] = useState(false);
  const [conversationId, setConversationId] = useState(() => {
    const savedId = localStorage.getItem('wardrobe_stylist_conversation_id');
    if (savedId) return savedId;
    const newId = crypto.randomUUID();
    localStorage.setItem('wardrobe_stylist_conversation_id', newId);
    return newId;
  });
  const [selectedOutfitId, setSelectedOutfitId] = useState(null);
  const [selectedOutfit, setSelectedOutfit] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Image upload state
  const [uploadedImage, setUploadedImage] = useState(null);      // File object
  const [imagePreviewUrl, setImagePreviewUrl] = useState(null);  // Object URL for preview
  const [isImageProcessing, setIsImageProcessing] = useState(false);
  const imageInputRef = useRef(null);
  const abortControllerRef = useRef(null); // For cancelling in-flight requests

  const recognitionRef = useRef(null);
  const recognitionTranscriptRef = useRef('');
  const submitVoiceCommandRef = useRef(null);
  const synthesisRef = useRef(window.speechSynthesis);
  const chatEndRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`http://localhost:8000/api/voice/conversations/${conversationId}?user_id=1`)
      .then(response => {
        if (response.status === 404) return null;
        if (!response.ok) throw new Error(`Conversation load failed (${response.status})`);
        return response.json();
      })
      .then(data => {
        if (!cancelled && data?.status === 'success') {
          setMessages(data.messages || []);
          setSelectedOutfitId(data.state?.current_outfit_id || null);
        }
      })
      .catch(err => {
        if (!cancelled) console.error('Could not load stylist conversation:', err);
      });
    return () => { cancelled = true; };
  }, [conversationId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, isProcessing]);

  useEffect(() => {
    if (!success) return undefined;
    const timeout = window.setTimeout(() => setSuccess(null), 4500);
    return () => window.clearTimeout(timeout);
  }, [success]);

  // Keep the recognition instance alive while transcript state changes.
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = 0; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += `${transcript} `;
          } else {
            interimTranscript += `${transcript} `;
          }
        }

        recognitionTranscriptRef.current = finalTranscript.trim();
        setRecognizedText(`${finalTranscript}${interimTranscript}`.trim());
      };

      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (event.error !== 'aborted') setError(`Speech recognition error: ${event.error}`);
        setIsRecording(false);
      };

      recognitionRef.current.onend = () => {
        setIsRecording(false);
        if (recognitionTranscriptRef.current && !isProcessing) {
          submitVoiceCommandRef.current?.(recognitionTranscriptRef.current);
        }
      };
    } else {
      setError('Speech recognition is not supported in your browser');
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (synthesisRef.current) {
        synthesisRef.current.cancel();
      }
    };
  }, []);

  const startRecording = () => {
    setError(null);
    recognitionTranscriptRef.current = '';
    setRecognizedText('');
    setEditableText('');
    setSuccess(null);

    if (recognitionRef.current) {
      try {
        recognitionRef.current.start();
        setIsRecording(true);
      } catch (err) {
        setError('Could not start speech recognition');
        console.error(err);
      }
    }
  };

  const stopRecording = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsRecording(false);
    }
  };

  /** Stop everything: recording, speech synthesis, and any in-flight API request */
  const handleStop = () => {
    // Stop microphone
    if (recognitionRef.current && isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
    }
    // Stop speech synthesis
    if (synthesisRef.current) {
      synthesisRef.current.cancel();
      setIsSpeaking(false);
    }
    // Abort in-flight API request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsProcessing(false);
    setIsImageProcessing(false);
  };

  const speakResponse = (text) => {
    if (!synthesisRef.current) return;

    synthesisRef.current.cancel(); // Stop any ongoing speech

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    synthesisRef.current.speak(utterance);
  };

  /** Handle image file selection */
  const handleImageSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setError('Please select an image file (JPG, PNG, WEBP, etc.)');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('Image must be smaller than 10 MB.');
      return;
    }
    // Revoke previous object URL to free memory
    if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl);
    setUploadedImage(file);
    setImagePreviewUrl(URL.createObjectURL(file));
    setError(null);
    // Reset the input so the same file can be re-selected
    e.target.value = '';
  };

  /** Clear the attached image */
  const handleClearImage = () => {
    if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl);
    setUploadedImage(null);
    setImagePreviewUrl(null);
  };

  /** Submit image + text to the vision-stylist endpoint */
  const handleImageSubmit = async () => {
    if (abortControllerRef.current) return;
    const question = editableText.trim() || recognizedText.trim();
    if (!uploadedImage) {
      setError('Please attach an image first.');
      return;
    }
    if (!question) {
      setError('Please describe what you want to know about the image.');
      return;
    }

    setIsImageProcessing(true);
    setError(null);
    setSuccess(null);

    const reqId = crypto.randomUUID();
    const optimisticUser = {
      id: reqId,
      role: 'user',
      content: `[Image uploaded] ${question}`,
      has_image: true,
      image_preview: imagePreviewUrl,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, optimisticUser]);

    const controller = new AbortController();
    abortControllerRef.current = controller;
    let timedOut = false;
    const requestTimeout = window.setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, 45000);

    try {
      const formData = new FormData();
      formData.append('file', uploadedImage);
      formData.append('user_message', question);
      formData.append('conversation_id', conversationId);
      formData.append('request_id', reqId);
      formData.append('user_id', '1');

      const response = await fetch('http://localhost:8000/api/voice/image-stylist', {
        method: 'POST',
        body: formData,
        signal: controller.signal
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Request failed (${response.status})`);
      }

      const data = await response.json();
      if (controller.signal.aborted || abortControllerRef.current !== controller) return;
      if (data.status === 'success') {
        setMessages(data.messages || []);
        if (data.conversation_id) {
          setConversationId(data.conversation_id);
          localStorage.setItem('wardrobe_stylist_conversation_id', data.conversation_id);
        }
        // When the image endpoint returns a full outfit look, update outfit state
        if (data.response_type === 'outfit' && data.outfits?.length) {
          setOutfits(data.outfits);
          setSelectedOutfitId(data.conversation_state?.current_outfit_id || null);
          setSuccess('Here are outfit looks from your wardrobe that match your image!');
        } else {
          setSuccess('Image analyzed — stylist answered your question!');
        }
        speakResponse(data.agent_response);
        // Clear the image and text after successful submission
        handleClearImage();
        setEditableText('');
        setRecognizedText('');
      } else {
        throw new Error(data.detail || 'Image analysis failed.');
      }
    } catch (err) {
      if (abortControllerRef.current !== controller) return;
      if (timedOut) {
        setError('The stylist took too long to respond. Please try sending your message again.');
      } else if (err.name === 'AbortError') {
        setMessages(prev => prev.filter(m => m.id !== reqId));
      } else {
        setError(err.message);
        setMessages(prev => [
          ...prev.filter(m => m.id !== reqId),
          {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: `Couldn't analyze the image: ${err.message}`,
            response_type: 'error',
            outfits: []
          }
        ]);
      }
    } finally {
      window.clearTimeout(requestTimeout);
      if (abortControllerRef.current !== controller) return;
      setIsImageProcessing(false);
      abortControllerRef.current = null;
    }
  };

  const handleSubmit = async (command, outfitIdOverride) => {
    if (abortControllerRef.current) return;
    const textToSend = command || editableText || recognizedText;

    if (!textToSend.trim()) {
      setError('Please speak or type a command');
      return;
    }

    const planCommand = getPlanCommand(textToSend);
    if (planCommand?.action === 'remove') {
      if (!isWeekdayScheduleLoaded) {
        setError('Your weekly plan is still loading. Please try again in a moment.');
        return;
      }
      const entries = getEntriesForPlanDate(
        weekdaySchedule, planCommand.day.id, getPlanDateForDay(planCommand.day.id)
      ).filter(entry => entry.confirmation_status === 'awaiting');
      if (!entries.length) {
        setError(`There is no outfit planned for ${planCommand.day.label} to remove.`);
        return;
      }
      const entryToRemove = selectScheduledEntry(entries, planCommand);
      if (!entryToRemove) {
        setError(`More than one look is planned for ${planCommand.day.label}. Specify an occasion, for example “remove the dinner date look”.`);
        return;
      }
      setIsProcessing(true);
      setError(null);
      setSuccess(null);
      const userTurn = {
        id: crypto.randomUUID(),
        role: 'user',
        content: textToSend,
        created_at: new Date().toISOString()
      };
      try {
        await onRemoveScheduledOutfit(entryToRemove.schedule_id);
        setMessages(previous => [
          ...previous,
          userTurn,
          {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: `Removed the ${entryToRemove.occasion || 'outfit'} look from your ${planCommand.day.label} plan.`,
            created_at: new Date().toISOString()
          }
        ]);
        setSuccess(`Removed the ${entryToRemove.occasion || 'outfit'} look from your ${planCommand.day.label} plan.`);
      } catch (removeError) {
        setError(removeError.message || `Could not remove the ${planCommand.day.label} outfit.`);
      } finally {
        setIsProcessing(false);
        setEditableText('');
        setRecognizedText('');
      }
      return;
    }

    const planEntry = planCommand?.action === 'update'
      ? selectScheduledEntry(
          getEntriesForPlanDate(weekdaySchedule, planCommand.day.id, getPlanDateForDay(planCommand.day.id))
            .filter(entry => entry.confirmation_status === 'awaiting'),
          planCommand
        )
      : null;
    if (planCommand?.action === 'update' && !planEntry) {
      const entries = getEntriesForPlanDate(
        weekdaySchedule, planCommand.day.id, getPlanDateForDay(planCommand.day.id)
      ).filter(entry => entry.confirmation_status === 'awaiting');
      setError(entries.length
        ? `More than one look may be planned for ${planCommand.day.label}. Specify which occasion to update.`
        : `There is no outfit planned for ${planCommand.day.label} to update.`);
      return;
    }

    setIsProcessing(true);
    setError(null);
    setSuccess(null);
    const messageId = crypto.randomUUID();
    setMessages(prev => [...prev, {
      id: messageId,
      role: 'user',
      content: textToSend,
      created_at: new Date().toISOString()
    }]);

    const controller = new AbortController();
    abortControllerRef.current = controller;
    let timedOut = false;
    const requestTimeout = window.setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, 45000);

    try {
      const response = await fetch('http://localhost:8000/api/voice/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_message: textToSend,
          conversation_id: conversationId,
          selected_outfit_id: outfitIdOverride || selectedOutfitId,
          context_outfit: planEntry?.outfit,
          request_id: messageId,
          user_id: 1
        }),
        signal: controller.signal
      });

      const data = await response.json();
      if (controller.signal.aborted || abortControllerRef.current !== controller) return;

      if (!response.ok) {
        throw new Error(data.detail || data.agent_response || `Request failed (${response.status})`);
      }

      if (data.status === 'success') {
        setAgentResponse(data.agent_response);
        setMessages(data.messages || []);
        setSelectedOutfitId(data.conversation_state?.current_outfit_id || null);
        if (data.conversation_id) {
          setConversationId(data.conversation_id);
          localStorage.setItem('wardrobe_stylist_conversation_id', data.conversation_id);
        }

        const scheduleRequest = getScheduleRequest(textToSend);
        let scheduleSuccess = null;
        let scheduleError = null;
        const isOutfitResponse = data.response_type === 'outfit' || data.response_type === 'saved';
        const previousSelectedOutfitId = planEntry?.outfit?.id || outfitIdOverride || selectedOutfitId;

        if (data.response_type === 'outfit') {
          setOutfits(data.outfits || []);
        }

        if (data.response_type === 'outfit' && data.outfits?.length) {
          const updatedOutfit = data.outfits[0];
          const plannedEntriesToUpdate = planEntry
            ? [{ day: planCommand.day, entry: planEntry }]
            : planCommand
              ? []
              : WEEKDAYS
                .flatMap(day => getEntriesForPlanDate(
                  weekdaySchedule, day.id, getPlanDateForDay(day.id)
                )
                  .filter(entry => entry.confirmation_status === 'awaiting')
                  .filter(entry => entry.outfit?.id === previousSelectedOutfitId)
                  .map(entry => ({ day, entry })));

          if (plannedEntriesToUpdate.length) {
            try {
              for (const { day, entry } of plannedEntriesToUpdate) {
                await onReplaceScheduledOutfit(
                  entry.schedule_id, day.id, updatedOutfit, 'voice', entry.outfit.id, entry.plan_date
                );
              }
              scheduleSuccess = `Updated the planned outfit${plannedEntriesToUpdate.length > 1 ? 's' : ''} for ${plannedEntriesToUpdate.map(({ day }) => day.label).join(', ')}.`;
            } catch (replacementError) {
              scheduleError = replacementError.message;
            }
          }
        }

        if (!scheduleSuccess && !scheduleError && scheduleRequest && isOutfitResponse) {
          const previousRecommendedOutfits = [...(data.messages || []), ...messages]
            .reverse()
            .find(message => message.role === 'assistant' && message.outfits?.length)?.outfits || [];
          const returnedSelection = data.intent === 'selection' ? data.outfits?.[0] : null;
          const availableOutfits = data.outfits?.length
            ? data.outfits
            : returnedSelection
              ? [returnedSelection]
              : data.saved_outfit?.outfit
                ? [data.saved_outfit.outfit]
                : data.conversation_state?.current_outfits?.length
                  ? data.conversation_state.current_outfits
                  : previousRecommendedOutfits.length
                    ? previousRecommendedOutfits
                    : outfits;
          const isAlreadySelectedResponse = data.intent === 'selection' || Boolean(data.saved_outfit?.outfit);
          const outfitToSchedule = isAlreadySelectedResponse
            ? availableOutfits[0]
            : availableOutfits[scheduleRequest.outfitIndex];

          if (!isWeekdayScheduleLoaded) {
            scheduleError = 'Your weekly plan is still loading. Please try that request again in a moment.';
          } else if (!outfitToSchedule) {
            scheduleError = `I couldn't find that outfit option, so nothing was added to ${scheduleRequest.day.label}'s plan.`;
          } else {
            try {
              const occasion = scheduleRequest.occasion || data.conversation_state?.occasion || 'Outfit';
              await onScheduleOutfit(scheduleRequest.day.id, outfitToSchedule, 'voice', occasion, [], scheduleRequest.planDate);
              scheduleSuccess = `“${outfitToSchedule.title}” added to your ${scheduleRequest.day.label} plan for ${occasion}.`;
            } catch (assignmentError) {
              scheduleError = `I couldn't add the outfit to ${scheduleRequest.day.label}'s plan: ${assignmentError.message}`;
            }
          }
        }

        if (scheduleError) {
          setSuccess(null);
          setError(scheduleError);
        } else if (scheduleSuccess) {
          setSuccess(scheduleSuccess);
          setError(null);
        }

        if (data.response_type === 'outfit') {
          if (!scheduleSuccess && !scheduleError) {
            setSuccess('Outfit recommendations generated');
          }
        } else if (data.response_type === 'no_match' || data.response_type === 'clarification') {
          setOutfits([]);
          setSuccess(null);
        } else if (data.response_type === 'status_update') {
          await onRefreshWardrobe?.();
          setSuccess('Clothing status updated successfully');
        } else if (data.response_type === 'wear_reminder') {
          await onRefreshWearEvents?.();
          setSuccess('Wear confirmation recorded. Your laundry check is ready.');
        } else if (data.response_type === 'saved') {
          if (!scheduleSuccess && !scheduleError) {
            setSuccess('Look saved to your wardrobe');
          }
        } else {
          setSuccess('Command processed successfully');
        }

        // Speak the response
        speakResponse(data.agent_response);
      } else {
        setError(data.agent_response || 'Failed to process command');
        setMessages(prev => [...prev, {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.agent_response || 'I could not process that request.',
          response_type: 'error',
          outfits: []
        }]);
      }
    } catch (err) {
      if (abortControllerRef.current !== controller) return;
      if (timedOut) {
        setError('The stylist took too long to respond. Please try sending your message again.');
      } else if (err.name === 'AbortError') {
        // User pressed Stop — just clear processing state silently
      } else {
        const isNetworkError = err instanceof TypeError;
        const errorMessage = isNetworkError
          ? `Network error: ${err.message}`
          : err.message;
        setError(errorMessage);
        console.error(err);
        setMessages(prev => [...prev, {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: isNetworkError
            ? `I couldn't connect to the stylist service. You can try again or continue by typing. (${err.message})`
            : `The stylist couldn't process that request: ${err.message}`,
          response_type: 'error',
          outfits: []
        }]);
      }
    } finally {
      window.clearTimeout(requestTimeout);
      if (abortControllerRef.current !== controller) return;
      setIsProcessing(false);
      setRecognizedText('');
      setEditableText('');
      abortControllerRef.current = null;
    }
  };
  submitVoiceCommandRef.current = command => {
    if (!isProcessing) handleSubmit(command);
  };

  const startNewConversation = () => {
    const newId = crypto.randomUUID();
    localStorage.setItem('wardrobe_stylist_conversation_id', newId);
    setConversationId(newId);
    setMessages([]);
    setOutfits([]);
    setSelectedOutfitId(null);
    setSelectedOutfit(null);
    setAgentResponse('');
    setError(null);
    setSuccess(null);
  };

  const toggleSavedLooks = async () => {
    if (showSavedLooks) {
      setShowSavedLooks(false);
      return;
    }
    setShowSavedLooks(true);
    setIsLoadingSavedLooks(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/voice/saved-outfits?user_id=1');
      const data = await response.json();
      if (!response.ok || data.status !== 'success') {
        throw new Error(data.detail || 'Could not load saved looks');
      }
      setSavedLooks(data.outfits || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoadingSavedLooks(false);
    }
  };

  const saveOutfit = (outfitId) => {
    setSelectedOutfitId(outfitId);
    handleSaveOutfit(outfitId);
  };

  const handleSaveOutfit = async (outfitId) => {
    const messageId = crypto.randomUUID();
    setIsProcessing(true);
    setError(null);
    setMessages(prev => [...prev, {
      id: messageId,
      role: 'user',
      content: 'Save this look',
      created_at: new Date().toISOString()
    }]);
    try {
      const response = await fetch('http://localhost:8000/api/voice/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_message: 'Save this look',
          conversation_id: conversationId,
          selected_outfit_id: outfitId,
          request_id: messageId,
          user_id: 1
        })
      });
      const data = await response.json();
      if (!response.ok || data.status !== 'success') {
        throw new Error(data.detail || data.agent_response || 'Could not save this outfit');
      }
      setMessages(data.messages || []);
      setSelectedOutfitId(data.conversation_state?.current_outfit_id || outfitId);
      if (data.saved_outfit) {
        setSavedLooks(previous => [
          data.saved_outfit,
          ...previous.filter(look => look.id !== data.saved_outfit.id)
        ]);
      }
      setSuccess(data.agent_response);
      speakResponse(data.agent_response);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
      setEditableText('');
    }
  };

  const handleTextSubmit = () => {
    handleSubmit();
  };

  return (
    <div className="voice-stylist-container">
      <div className="voice-header">
        <div>
          <span className="voice-eyebrow">YOUR PERSONAL STYLIST</span>
          <h2><Mic size={24} aria-hidden="true" /> Your personal stylist</h2>
          <p className="voice-subtitle">Chat naturally. Discover outfits from your own wardrobe.</p>
        </div>
        <div className="voice-header-actions">
          <span className="wardrobe-sync-badge"><span /> Wardrobe synced</span>
          <button type="button" className={`new-conversation-button ${showSavedLooks ? 'active' : ''}`} onClick={toggleSavedLooks}>
            <BookmarkPlus size={16} /> {showSavedLooks ? 'Hide saved looks' : 'Saved looks'}
          </button>
          <button type="button" className="new-conversation-button" onClick={startNewConversation} disabled={isProcessing}>
            <Plus size={16} /> New chat
          </button>
        </div>
      </div>

      {showSavedLooks && (
        <section className="saved-looks-panel" aria-label="Saved outfits">
          <div className="saved-looks-heading">
            <div>
              <span className="voice-eyebrow">YOUR COLLECTION</span>
              <h3>Saved looks</h3>
            </div>
            <button type="button" className="saved-looks-close" onClick={() => setShowSavedLooks(false)} aria-label="Close saved looks">
              <X size={18} />
            </button>
          </div>
          {isLoadingSavedLooks ? (
            <p className="saved-looks-empty">Loading saved looks…</p>
          ) : savedLooks.length ? (
            <ul className="saved-looks-list">
              {savedLooks.map(saved => (
                <li key={saved.id}>
                  <span>{saved.title}</span>
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedOutfit(saved.outfit);
                      setSelectedOutfitId(saved.id);
                      setIsModalOpen(true);
                    }}
                  >
                    View
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="saved-looks-empty">No saved looks yet. Save an outfit card and it will appear here.</p>
          )}
        </section>
      )}

      {/* Status Messages */}
      {error && (
        <div className="status-message error">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="status-message success">
          <CheckCircle size={20} />
          <span>{success}</span>
        </div>
      )}

      <div className="chat-history-heading">
        <div>
          <span className="voice-eyebrow">YOUR STYLING SESSION</span>
          <h3>Conversation</h3>
        </div>
        <span>{messages.length} {messages.length === 1 ? 'message' : 'messages'}</span>
      </div>
      <div className="stylist-chat-history" aria-live="polite">
        {messages.length === 0 && !isProcessing && (
          <div className="voice-chat-empty">
            <div className="voice-chat-empty-icon"><Mic size={21} /></div>
            <div>
              <strong>Your stylist is ready</strong>
              <p>Start with a suggested prompt or tell me what you need in your own words.</p>
            </div>
          </div>
        )}
        {messages.map((message, messageIndex) => (
          <div
            key={message.id || `${message.role}-${messageIndex}`}
            className={`stylist-chat-message ${message.role === 'user' ? 'user-message' : 'assistant-message'}`}
          >
            {message.role === 'assistant' && <Volume2 size={16} aria-hidden="true" />}
            {message.role === 'user' && message.has_image && (
              <span className="chat-image-badge" aria-label="Image attached">
                <ImageIcon size={13} /> Image
              </span>
            )}
            <div className="stylist-message-content">
              {message.image_preview && (
                <img
                  src={message.image_preview}
                  alt="Uploaded garment"
                  className="chat-uploaded-image-thumb"
                />
              )}
              <p>{message.has_image ? message.content.replace('[Image uploaded] ', '') : message.content}</p>
              {message.role === 'assistant' && message.readiness_confirmation && (
                <div role="group" aria-label={`Confirm whether ${message.readiness_confirmation.title} is ready`} style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 10 }}>
                  <button
                    type="button"
                    onClick={() => handleSubmit('yes')}
                    disabled={isProcessing}
                    style={{ border: 0, borderRadius: 9, padding: '0.55rem 0.75rem', background: '#ECFDF5', color: '#047857', fontWeight: 800, cursor: 'pointer' }}
                  >
                    Yes, ready
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSubmit('no')}
                    disabled={isProcessing}
                    style={{ border: '1px solid #E2E8F0', borderRadius: 9, padding: '0.55rem 0.75rem', background: '#fff', color: '#475569', fontWeight: 800, cursor: 'pointer' }}
                  >
                    No, not yet
                  </button>
                </div>
              )}
              {message.role === 'assistant' && message.outfits?.length > 0 && (
                <div className="outfit-results-section">
                  <h3>Wardrobe-checked options</h3>
                  <div className="outfit-cards-grid">
                    {message.outfits.map((outfit, index) => {
                      const unavailableOutfitItems = Object.values(outfit.slotItems || {})
                        .filter(item => item?.id)
                        .filter(item => {
                          const wardrobeItem = clothes.find(
                            entry => String(entry.id) === String(item.id)
                          );
                          return !wardrobeItem
                            || !['ready', 'available'].includes(wardrobeItem.availability_status || 'ready')
                            || (wardrobeItem.ironing_status || 'ready') !== 'ready';
                        })
                        .map(item => item.title);
                      const currentAvailabilityWarning = outfit.availabilityWarning || (
                        unavailableOutfitItems.length
                          ? `Unavailable now: ${unavailableOutfitItems.join(', ')}.`
                          : ''
                      );
                      const precedingRequests = messages.slice(0, messageIndex).reverse()
                        .filter(previous => previous.role === 'user');
                      const request = precedingRequests[0]?.content || '';
                      const preferenceRequest = precedingRequests.find(previous =>
                        getStylingPreferences(previous.content).some(preference =>
                          !['Wardrobe-matched', 'Your style'].includes(preference)
                        )
                      )?.content || request;
                      const preferences = getStylingPreferences(preferenceRequest);
                      const topItem = outfit?.slotItems?.topObj;
                      const category = (topItem?.category || '').toLowerCase();
                      const garmentText = [
                        topItem?.title,
                        category,
                        topItem?.style,
                        topItem?.attributes?.category,
                        topItem?.attributes?.type
                      ].filter(Boolean).join(' ').toLowerCase();
                      const isOnePiece = ['one_piece', 'one-piece', 'dress', 'dresses'].includes(category) ||
                        /dress|maxi|gown|jumpsuit|romper|one[-_ ]piece|anarkali|saree|frock|bodycon|lehenga|sharara/.test(garmentText);

                      return (
                        <article key={outfit.id || index} className="voice-outfit-card">
                          <button
                            type="button"
                            className="voice-outfit-preview"
                            onClick={() => { setSelectedOutfit(outfit); setSelectedOutfitId(outfit.id); setIsModalOpen(true); }}
                            aria-label={`View ${outfit.title}`}
                          >
                            <OutfitFlatLayBoard slotItems={outfit.slotItems} title={outfit.title} height={250} />
                            <span className="voice-outfit-index">Option {index + 1} · {outfit.matchScore} match</span>
                            <span className="voice-outfit-expand"><Maximize2 size={15} /></span>
                          </button>

                          <div className="voice-outfit-main">
                            <div className="voice-outfit-meta">
                              <span className="voice-outfit-tag"><Calendar size={13} /> {outfit.occasion || request.match(/\b(college|dinner date|date|wedding|interview|office|party)\b/i)?.[0] || 'Wardrobe match'}</span>
                              {outfit.trendSignal && <span className="voice-outfit-tag">{outfit.trendSignal}</span>}
                            </div>
                            <h4>{outfit.title}</h4>
                            {currentAvailabilityWarning && (
                              <p role="alert" style={{ margin: '0.35rem 0', padding: '0.5rem 0.6rem', borderRadius: 8, background: '#FEF2F2', color: '#B91C1C', fontSize: '0.75rem', fontWeight: 700 }}>
                                {currentAvailabilityWarning} This look is not confirmed ready to wear.
                              </p>
                            )}
                            <p className="voice-outfit-reason">{outfit.reason}</p>

                            <div className="voice-outfit-items">
                              <div><strong>{isOnePiece ? 'One-piece' : 'Top'}</strong><span>{outfit?.slots?.top || 'Not specified'}</span></div>
                              {!isOnePiece && outfit?.slots?.bottom && !outfit.slots.bottom.includes('None Needed') && (
                                <div><strong>Bottom</strong><span>{outfit.slots.bottom}</span></div>
                              )}
                              {outfit?.slots?.footwear && <div><strong>Footwear</strong><span>{outfit.slots.footwear}</span></div>}
                              {outfit?.slots?.bag && !outfit.slots.bag.includes('None Needed') && <div><strong>Bag</strong><span>{outfit.slots.bag}</span></div>}
                              {outfit?.slots?.accessory && !outfit.slots.accessory.includes('None Needed') && <div><strong>Accessories</strong><span>{outfit.slots.accessory}</span></div>}
                              {outfit?.slots?.outerwear && !outfit.slots.outerwear.includes('None Needed') && <div><strong>Outerwear</strong><span>{outfit.slots.outerwear}</span></div>}
                            </div>

                            <div className="voice-outfit-actions">
                              <button type="button" onClick={() => handleSubmit('Try different footwear for this look', outfit.id)} disabled={isProcessing}>Try different footwear</button>
                              <button type="button" onClick={() => handleSubmit('Change the top for this look', outfit.id)} disabled={isProcessing}>Change top</button>
                              <button type="button" onClick={() => handleSubmit('Make this look more elegant', outfit.id)} disabled={isProcessing}>Make it more elegant</button>
                              <button type="button" className="voice-save-look" onClick={() => saveOutfit(outfit.id)} disabled={isProcessing}>
                                <BookmarkPlus size={15} /> Save look
                              </button>
                            </div>
                            <WeekdayOutfitAssignment
                              outfit={outfit}
                              schedule={weekdaySchedule}
                              onAssign={onScheduleOutfit}
                              source="voice"
                              disabled={!isWeekdayScheduleLoaded}
                            />
                          </div>

                          <aside className="voice-outfit-preferences">
                            <h5><Maximize2 size={14} /> Styling preferences</h5>
                            {preferences.map(preference => (
                              <span key={preference}>{preference}</span>
                            ))}
                          </aside>
                        </article>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        {(isProcessing || isImageProcessing) && (
          <div className="stylist-chat-message assistant-message">
            <Loader2 size={16} className="spinner" />
            <div className="stylist-message-content">
              <p>{isImageProcessing ? 'Analyzing your image and cross-referencing your wardrobe…' : 'Checking your wardrobe and active requirements…'}</p>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Voice Input Section */}
      <div className="voice-input-section">
        <div className="voice-input-intro">
          <div>
            <h3>What are you looking for?</h3>
            <p>Speak naturally, type, or upload a garment image to get AI styling advice.</p>
          </div>
          <span className="voice-status-badge">
            <span className={`voice-status-dot ${isRecording ? 'is-recording' : (isProcessing || isImageProcessing) ? 'is-processing' : ''}`} />
            {isRecording ? 'Listening' : isImageProcessing ? 'Analyzing image…' : isProcessing ? 'Styling your request' : 'Ready when you are'}
          </span>
        </div>

        {/* Image preview strip */}
        {imagePreviewUrl && (
          <div className="image-upload-preview-strip">
            <div className="image-preview-card">
              <img src={imagePreviewUrl} alt="Garment to analyze" className="image-preview-thumb" />
              <div className="image-preview-info">
                <span className="image-preview-name">{uploadedImage?.name || 'image.jpg'}</span>
                <span className="image-preview-hint">Ask anything about this item ↓</span>
              </div>
              <button
                type="button"
                className="image-preview-remove"
                onClick={handleClearImage}
                aria-label="Remove image"
              >
                <X size={14} />
              </button>
            </div>
          </div>
        )}

        <div className="voice-composer">
          <div className="microphone-controls">
            {!isRecording ? (
              <button
                onClick={startRecording}
                className="mic-button"
                disabled={isProcessing || isImageProcessing}
                title="Click to start recording"
              >
                <Mic size={32} />
              </button>
            ) : (
              <button
                onClick={stopRecording}
                className="mic-button recording"
                title="Click to stop recording"
              >
                <MicOff size={32} />
              </button>
            )}
            <span className="mic-helper">{isRecording ? 'Tap to finish' : 'Tap to speak'}</span>
          </div>

          <div className="text-preview-section">
            <label className="preview-label" htmlFor="voice-command-input">
              {isRecording ? 'Recognized speech' : uploadedImage ? 'Your question about the image' : 'Your request'}
            </label>
            <textarea
              id="voice-command-input"
              value={editableText || recognizedText}
              onChange={(e) => setEditableText(e.target.value)}
              placeholder={uploadedImage
                ? 'e.g. "Which tops from my wardrobe match this pant?" or "What colors suit this?"'
                : 'Tell your stylist what you want or ask for a change…'}
              className="text-preview"
              disabled={isProcessing || isImageProcessing}
              rows={1}
            />
            <div className="voice-composer-footer">
              <span>Voice, text, and image share the same conversation.</span>
              <div className="voice-composer-actions">
                {/* Hidden file input */}
                <input
                  ref={imageInputRef}
                  type="file"
                  accept="image/*"
                  style={{ display: 'none' }}
                  onChange={handleImageSelect}
                  id="image-upload-input"
                />
                {/* Image upload button */}
                <button
                  type="button"
                  onClick={() => imageInputRef.current?.click()}
                  className={`image-upload-button ${uploadedImage ? 'has-image' : ''}`}
                  disabled={isProcessing || isImageProcessing}
                  title="Upload a garment image for styling advice"
                  aria-label="Upload outfit image"
                >
                  <ImagePlus size={17} />
                  <span>{uploadedImage ? 'Change image' : 'Add image'}</span>
                </button>

                {/* Stop button — shown when processing or speaking */}
                {(isProcessing || isImageProcessing || isSpeaking || isRecording) && (
                  <button
                    type="button"
                    onClick={handleStop}
                    className="stop-button"
                    aria-label="Stop current action"
                    title="Stop recording / analysis / speech"
                  >
                    <StopCircle size={17} />
                    <span>Stop</span>
                  </button>
                )}

                {/* Submit: image mode vs text mode */}
                {uploadedImage ? (
                  <button
                    onClick={handleImageSubmit}
                    className="submit-button image-submit"
                    disabled={isImageProcessing || isProcessing || !(editableText || recognizedText).trim()}
                    aria-label={isImageProcessing ? 'Analyzing image' : 'Analyze image with AI'}
                  >
                    {isImageProcessing ? <Loader2 size={17} className="spinner" /> : <ImagePlus size={17} />}
                    <span>{isImageProcessing ? 'Analyzing…' : 'Ask about image'}</span>
                  </button>
                ) : (
                  <button
                    onClick={handleTextSubmit}
                    className="submit-button"
                    disabled={isProcessing || !(editableText || recognizedText).trim()}
                    aria-label={isProcessing ? 'Stylist is processing your request' : 'Send request'}
                  >
                    {isProcessing ? <Loader2 size={17} className="spinner" /> : <Send size={17} />}
                    <span>{isProcessing ? 'Thinking…' : 'Ask stylist'}</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Outfit Detail Modal */}
      {isModalOpen && selectedOutfit && (
        <OutfitDetailModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          outfit={selectedOutfit}
        />
      )}

    </div>
  );
};

export default VoiceStylist;
