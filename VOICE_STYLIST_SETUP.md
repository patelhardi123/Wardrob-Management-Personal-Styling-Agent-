# Voice Stylist Agent - Setup and Documentation

## Overview

The Voice Stylist Agent is a new feature that allows users to interact naturally with their AI Smart Wardrobe using voice commands. Users can speak to request outfits, check clothing availability, update washing/ironing status, and receive spoken responses with outfit recommendations.

## Architecture

### Voice Pipeline Components

1. **Speech-to-Text (STT)**: Browser-native Web Speech API (free, no API keys required)
2. **Intent Understanding**: LangGraph node that classifies user intent and extracts parameters
3. **LangGraph Orchestration**: Routes requests to appropriate tools or existing workflows
4. **Tool Execution**: Retrieves wardrobe data, updates status, generates outfits
5. **Validation**: Verifies actions and ensures outfits satisfy constraints
6. **Text-to-Speech (TTS)**: Browser Web Speech API (free) or optional OpenAI TTS API
7. **Frontend Update**: Displays outfit cards, status updates, and plays spoken response

### Key Features

- **Natural Language Commands**: Speak naturally to request outfits or update status
- **Clothing Availability Management**: Track washing and ironing status
- **Automatic Outfit Replanning**: Excludes unavailable items from recommendations
- **Conversation Context**: Supports follow-up commands without repeating context
- **Persistent Stylist Chat**: Typed messages and voice transcripts share a saved conversation; requests and selections persist, while saved looks can be reopened from the chat page
- **Constraint-Aware Changes**: A color request attached to a garment (for example, “yellow top”) filters that slot only, so other colors remain available to complete the outfit; color/item exclusions and category restrictions are applied before recommendations, preferred colors rank matching owned items higher, and partial replacements keep unchanged pieces where possible
- **Garment Alternatives**: When a request names multiple garment types as choices (for example, a one-piece or a lehenga), any matching requested type may satisfy that requirement
- **Occasion-Specific Validation**: Wedding recommendations prioritize festive/ethnic looks, interviews require formal attire and suitable formal footwear, and invalid combinations are not returned
- **Honest No-Match Responses**: If the wardrobe cannot satisfy the active requirements, the assistant explains that no valid outfit is available instead of treating it as a service error
- **Voice Status Updates**: Update clothing status via voice commands
- **Ready-to-Wear Filtering**: Request outfits using only ready-to-wear items

The stylist is currently configured for one local profile (`user_id=1`). This is not
authentication or multi-user isolation. Conversation turns and saved outfits are stored in the
existing SQLite database.

## Database Schema Changes

### New Fields in `clothes` table

- `availability_status`: TEXT (values: 'available', 'in_wash', 'drying', 'unavailable')
- `ironing_status`: TEXT (values: 'ready', 'needs_ironing', 'being_ironed')
- `expected_available_at`: TEXT (ISO datetime string, optional)
- `last_status_updated`: TIMESTAMP (auto-updated on status change)

The database migration is automatic - the new columns are added when the application starts.

## Environment Variables

### Required Variables

```bash
# OpenAI API Key (for LLM and optional TTS)
OPENAI_API_KEY=your_openai_api_key_here

# Optional: OpenRouter API Key (alternative LLM provider)
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=google/gemini-2.0-flash-001

# Optional: Use OpenAI TTS instead of browser TTS
USE_OPENAI_TTS=true  # Set to 'true' to use OpenAI TTS, 'false' for browser TTS
```

### Optional Variables

```bash
# Weather API (for weather-aware outfit planning)
# The application uses Open-Meteo free API by default, no key required

# Shopping APIs (for shopping suggestions)
SERPAPI_KEY=your_serpapi_key
RAPIDAPI_KEY=your_rapidapi_key
```

## Installation Instructions

### Backend Setup

1. **Navigate to backend directory**
```bash
cd backend
```

2. **Create or activate virtual environment**
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
# Create or edit .env file
# Add your OPENAI_API_KEY
```

5. **Initialize database**
The database is automatically initialized on first run. New columns for availability and ironing status are added automatically.

6. **Start the backend server**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Start the development server**
```bash
npm run dev
```

4. **Open in browser**
Navigate to `http://localhost:5173`

## Running the Application

### Start Backend
```bash
cd backend
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Mac/Linux
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend
```bash
cd frontend
npm run dev
```

### Access Voice Stylist
- Open browser to `http://localhost:5173`
- Click "Voice Stylist" in the navigation bar
- Click the microphone button to start recording
- Speak your command
- View the response and outfit recommendations

## Voice Commands

### Outfit Requests
- "Suggest an outfit for college today."
- "What should I wear for a wedding?"
- "Plan an outfit for tomorrow based on the weather."
- "Suggest an outfit for a date night."

### Status Updates
- "My blue jeans are in the wash."
- "My white shirt needs ironing."
- "I have ironed my white shirt; mark it as ready."
- "My black dress is unavailable."

### Availability Queries
- "What clothes in my wardrobe are currently unavailable?"
- "Which items are ready to wear?"

### Constraints and Modifications
- "Don't suggest jeans today."
- "Suggest an outfit using only clothes that are ready to wear."
- "Show me another outfit."
- "Replace the trousers in this outfit."

### Follow-up Commands
After receiving an outfit suggestion:
- "Show me another option."
- "Don't use those jeans."
- "What about something more formal?"
- "Keep these trousers and find something to wear with them."
- "Change the top but keep the trousers."
- "No bag."
- "Only white clothes."
- "Save this look."
- "Choose the second option."

Voice and typed input use the same request parser and conversation ID. Outfit restrictions stay
active during follow-ups until the user changes them or starts a new conversation. A request
that has no valid outfit returns `response_type: "no_match"` and no outfit cards; actual
processing failures use `response_type: "error"`.

## API Endpoints

### Voice Command Endpoint
```
POST /api/voice/command
Content-Type: application/json

{
  "user_message": "Suggest an outfit for college today",
  "conversation_id": "optional-existing-conversation-id",
  "selected_outfit_id": "optional-outfit-id",
  "request_id": "optional-idempotency-key",
  "user_id": 1
}

Response:
{
  "status": "success",
  "agent_response": "I've found 3 outfit recommendations for college...",
  "response_type": "outfit",
  "intent": "outfit_request",
  "occasion": "college",
  "conversation_id": "...",
  "outfits": [...],
  "conversation_state": {...},
  "execution_trace": [...]
}
```

Use `GET /api/voice/conversations/{conversation_id}?user_id=1` to reload a conversation and
`GET /api/voice/saved-outfits?user_id=1` to list looks saved from the stylist chat.

### Text-to-Speech Endpoint
```
POST /api/voice/tts
Content-Type: multipart/form-data

text: "Your outfit is ready"
voice: "alloy"

Response:
{
  "status": "success",
  "audio_data": "data:audio/mp3;base64,...",
  "provider": "openai" or "browser"
}
```

## Testing

### Run Voice Agent Tests
```bash
cd backend
python -m pytest test_voice_agent.py test_fashion_engine.py -q
```

### Test Coverage
The test suite covers:
- Intent classification (outfit requests, status updates, availability queries)
- Parameter extraction (occasion, constraints, exclusions)
- Status update handling (single match, ambiguous match, not found)
- Availability filtering and checking
- Outfit request routing to existing pipeline
- End-to-end pipeline integration
- Persistent conversation, selected-option, no-match, and modification constraints
- Edge cases and error handling

## Browser Compatibility

### Speech Recognition (STT)
- Chrome/Edge: Full support via Web Speech API
- Safari: Partial support (may require HTTPS)
- Firefox: Limited support

### Speech Synthesis (TTS)
- All modern browsers support Web Speech API for TTS
- No additional plugins required

## Troubleshooting

### Microphone Permission Denied
- Ensure browser has microphone permissions
- Check system privacy settings
- Try a different browser (Chrome/Edge recommended)

### Speech Recognition Not Working
- Ensure you're using a supported browser (Chrome/Edge)
- Check that you're not in incognito/private mode
- Verify microphone is not muted
- Try using the text input field instead

### Voice Commands Not Recognized
- Speak clearly and at a normal pace
- Minimize background noise
- Use the editable text field to correct recognition before sending
- Try simpler phrasing

### Status Updates Not Saving
- Check backend server is running
- Verify database permissions
- Check browser console for errors
- Ensure item exists in wardrobe

### Outfit Recommendations Empty
- Verify wardrobe has items
- Check availability status of items
- Try relaxing constraints
- Check backend logs for errors

## Security Considerations

- **API Keys**: Never commit API keys to version control
- **Single-user configuration**: This installation uses the configured profile only; it does
  not implement authentication or multi-user access control
- **Validation**: All status updates are validated on the backend
- **No Arbitrary Execution**: Voice commands cannot execute arbitrary code
- **Ambiguity Handling**: Ambiguous item selections require user confirmation

## Known Limitations

1. **Speech Recognition Accuracy**: Browser STT may have accuracy issues with accents or background noise
2. **Browser Support**: Some browsers have limited speech API support
3. **Offline Mode**: Requires internet connection for LLM calls (unless using local models)
4. **Language Support**: Currently optimized for English
5. **LLM Availability**: Structured intent extraction uses the configured LLM when available,
   with a deterministic parser fallback; no LLM is required for the core constraints

## Future Enhancements

- Multi-language support
- Voice biometrics for user identification
- Local LLM integration for offline mode
- Voice customization (speed, pitch, voice selection)
- Account authentication and true multi-user data isolation

## Files Created/Modified

### New Files
- `backend/fashion/voice_service.py` - Voice service adapter for STT/TTS
- `backend/voice_agent_graph.py` - Voice agent LangGraph workflow
- `backend/test_voice_agent.py` - Comprehensive test suite
- `frontend/src/components/VoiceStylist.jsx` - Voice UI component
- `VOICE_STYLIST_SETUP.md` - This documentation

### Modified Files
- `backend/database.py` - Added availability/ironing status fields
- `backend/main.py` - Added voice API endpoints
- `backend/agent_graph.py` - Added availability filtering to wardrobe agent
- `backend/requirements.txt` - Added pytest dependency
- `frontend/src/App.jsx` - Added Voice Stylist tab
- `frontend/src/components/Header.jsx` - Added Voice Stylist navigation
- `frontend/src/components/ItemDetailModal.jsx` - Added status management UI
- `frontend/src/index.css` - Added Voice Stylist styles

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review browser console for errors
3. Check backend server logs
4. Verify environment variables are set correctly
5. Ensure all dependencies are installed

## License

This Voice Stylist Agent is part of the AI Smart Wardrobe project.
