# Voice Stylist Agent - Demonstration Script

## Professor Presentation Demo Script

### Introduction (2 minutes)

**Speaker**: "Today I'll demonstrate the Voice Stylist Agent, a new feature for the AI Smart Wardrobe that enables natural voice interactions for outfit recommendations and clothing management."

**Key Points to Cover**:
- Voice-powered interface for digital wardrobe
- Natural language commands for outfit requests
- Clothing availability and ironing status tracking
- Integration with existing multi-agent LangGraph workflow
- Automatic outfit replanning when items are unavailable

---

### Demo Scenario 1: Basic Outfit Request (1 minute)

**Action**: Click microphone button, speak clearly
**Command**: "Suggest an outfit for college today."

**Expected Result**:
- Voice recognition displays text
- Agent processes request
- Outfit cards appear with recommendations
- Spoken response: "I've found 3 outfit recommendations for college..."

**Explain**: "The agent uses the existing LangGraph workflow with 7 nodes including Style Profile, Trend Research, Occasion Assessment, Wardrobe Retrieval, Outfit Stylist, Compatibility Engine, and Outfit Critic to generate personalized recommendations."

---

### Demo Scenario 2: Status Update via Voice (1 minute)

**Action**: Click microphone, speak command
**Command**: "My blue jeans are in the wash."

**Expected Result**:
- Agent identifies the blue jeans item
- Updates availability status to "in_wash"
- Confirmation message: "Your blue jeans are now marked as in the wash."
- Status is immediately reflected in the database

**Explain**: "Users can update clothing status through natural voice commands. The agent intelligently matches the description to the correct item in the wardrobe and updates the database with the new status."

---

### Demo Scenario 3: Ironing Status Update (1 minute)

**Action**: Click microphone, speak command
**Command**: "My white shirt needs ironing."

**Expected Result**:
- Agent identifies the white shirt
- Updates ironing status to "needs_ironing"
- Confirmation message displayed

**Explain**: "Separate tracking for washing and ironing status allows precise management. An item can be clean but still need ironing, which the system accounts for in outfit recommendations."

---

### Demo Scenario 4: Availability Query (1 minute)

**Action**: Click microphone, speak command
**Command**: "What clothes in my wardrobe are currently unavailable?"

**Expected Result**:
- Agent retrieves all items with non-available status
- Lists items with their current status (in wash, drying, needs ironing, etc.)
- Clear, organized response

**Explain**: "Users can quickly check which items are unavailable without browsing through the entire wardrobe. This is especially useful for planning outfits in advance."

---

### Demo Scenario 5: Ready-to-Wear Filtering (1 minute)

**Action**: Click microphone, speak command
**Command**: "Suggest an outfit using only clothes that are ready to wear."

**Expected Result**:
- Agent filters wardrobe to only available + ready items
- Generates outfit recommendations from ready-to-wear items only
- Outfit cards displayed

**Explain**: "The availability checking logic ensures that only items marked as 'available' and 'ready' are included in recommendations. Items in wash, drying, or needing ironing are automatically excluded."

---

### Demo Scenario 6: Constraint-based Request (1 minute)

**Action**: Click microphone, speak command
**Command**: "Suggest an outfit for college, but don't use jeans."

**Expected Result**:
- Agent processes exclusion constraint
- Generates outfits without jeans
- All recommendations respect the constraint

**Explain**: "Natural language constraints are extracted and applied to the outfit generation pipeline. The agent understands exclusions like 'no jeans' and filters accordingly."

---

### Demo Scenario 7: Follow-up Conversation (1 minute)

**Action**: After seeing outfit recommendations, speak follow-up
**Command**: "Show me another option."

**Expected Result**:
- Agent preserves conversation context
- Generates alternative outfit
- Maintains occasion and constraints from previous request

**Explain**: "The agent maintains conversation context, allowing follow-up commands without repeating the entire request. This makes natural, iterative outfit exploration possible."

---

### Demo Scenario 8: Manual Status Management (1 minute)

**Action**: Navigate to Wardrobe page, click on an item
**Steps**:
1. Click on any clothing item
2. In the detail modal, change availability status to "In Wash"
3. Change ironing status to "Needs Ironing"
4. Save changes

**Expected Result**:
- Status changes are immediately saved to database
- Changes persist across page refreshes
- Status is reflected in Voice Stylist queries

**Explain**: "Users can also manage status manually through the UI. All status changes—whether via voice or UI—are persisted in the database and immediately affect outfit recommendations."

---

### Demo Scenario 9: Automatic Replanning (1 minute)

**Action**:
1. Mark a frequently-used item as "in wash"
2. Request an outfit for an occasion that would typically use that item
**Command**: "Suggest an outfit for college."

**Expected Result**:
- Agent excludes the unavailable item
- Automatically selects alternative items
- Outfit recommendations are still valid and complete

**Explain**: "When items become unavailable, the agent automatically replans outfits using other owned garments. This ensures users always receive valid, wearable outfit suggestions."

---

### Technical Architecture Summary (2 minutes)

**Key Technical Points**:

1. **Voice Pipeline**:
   - Speech-to-Text: Browser Web Speech API (free, no API keys)
   - Intent Understanding: Rule-based + LLM-enhanced classification
   - Orchestration: LangGraph workflow with conditional routing
   - Text-to-Speech: Browser Web Speech API or optional OpenAI TTS

2. **Database Schema**:
   - Added `availability_status`, `ironing_status`, `expected_available_at`, `last_status_updated` fields
   - Automatic migration on application startup
   - Persistent status tracking

3. **Integration**:
   - Reuses existing 7-node LangGraph pipeline
   - Reuses 12-dimensional compatibility engine
   - Reuses ML compatibility model
   - No separate recommendation system created

4. **Security**:
   - User isolation (wardrobe and conversations)
   - Backend validation of all status updates
   - No arbitrary code execution
   - Ambiguity handling with user confirmation

5. **Testing**:
   - Comprehensive test suite covering all scenarios
   - Intent classification tests
   - Status update tests
   - End-to-end integration tests

---

### Conclusion (1 minute)

**Speaker**: "The Voice Stylist Agent successfully integrates natural voice interactions with the existing AI Smart Wardrobe architecture. It enables users to:

- Request outfits through natural voice commands
- Update clothing availability and ironing status
- Query which items are unavailable
- Apply constraints and receive filtered recommendations
- Maintain conversation context for follow-up requests

The implementation reuses all existing components—LangGraph workflow, compatibility engine, ML model, and database—while adding a clean, intuitive voice interface. This makes the smart wardrobe more accessible and user-friendly."

---

### Backup Demo Commands (if time permits)

1. **Wedding outfit**: "What should I wear for a wedding?"
2. **Date night**: "Suggest an outfit for a dinner date."
3. **Office attire**: "Plan an outfit for a business meeting."
4. **Weather-based**: "Suggest an outfit for tomorrow based on the weather."
5. **Status recovery**: "I have ironed my white shirt; mark it as ready."

---

### Common Issues & Workarounds

**If speech recognition fails**:
- Use the editable text field to type the command
- Try speaking more slowly and clearly
- Ensure microphone permissions are granted

**If no outfits are returned**:
- Check that wardrobe has sufficient items
- Verify items are marked as available
- Try relaxing constraints

**If status update fails**:
- Ensure the item exists in the wardrobe
- Use the UI to manually update status
- Check backend server is running

---

### Q&A Preparation

**Potential Questions**:

1. **Q: Does this work offline?**
   A: Currently requires internet for LLM calls. Future enhancement could add local LLM support.

2. **Q: What languages are supported?**
   A: Currently optimized for English. Multi-language support is a planned enhancement.

3. **Q: How accurate is the speech recognition?**
   A: Uses browser Web Speech API which is generally accurate in quiet environments. Users can edit recognized text before sending.

4. **Q: Can it handle multiple users?**
   A: Yes, each user's wardrobe and conversation state is isolated. User authentication can be added for production.

5. **Q: What happens if there are multiple similar items?**
   A: The agent asks for clarification before updating status, preventing accidental updates to wrong items.

6. **Q: Is the voice data stored?**
   A: No, voice data is processed in real-time and not stored. Only text transcripts are used temporarily.

---

### Demo Checklist

Before presentation:
- [ ] Backend server running on port 8000
- [ ] Frontend server running on port 5173
- [ ] Microphone permissions granted in browser
- [ ] Test voice recognition works
- [ ] Verify database has sample items
- [ ] Test status updates work
- [ ] Test outfit generation works
- [ ] Have backup commands ready
- [ ] Prepare for potential technical issues

---

### Presentation Tips

1. **Speak clearly and at a moderate pace** when demonstrating voice commands
2. **Minimize background noise** for better speech recognition
3. **Use the text input field** as a backup if voice recognition fails
4. **Explain the "why"** behind each feature, not just the "what"
5. **Show the integration** with existing components (compatibility scores, traces)
6. **Keep the flow natural** - don't rush through scenarios
7. **Be prepared to adapt** if something doesn't work as expected

---

### Success Metrics

A successful demo should:
- Show voice recognition working reliably
- Demonstrate clear intent understanding
- Display accurate outfit recommendations
- Show status updates persisting correctly
- Illustrate automatic replanning when items unavailable
- Highlight integration with existing workflow
- Complete within 10-12 minutes
- Leave time for questions

---

**End of Demo Script**
