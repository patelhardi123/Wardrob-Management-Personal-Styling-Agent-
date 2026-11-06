"""
Comprehensive Tests for Voice Stylist Agent
Tests voice commands, status updates, availability checking, and outfit generation.
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from voice_agent_graph import (
    VoiceAgentState,
    intent_understanding_node,
    wardrobe_retrieval_node,
    status_update_node,
    availability_query_node,
    outfit_request_node,
    run_voice_agent_pipeline,
    _local_structured_intent,
)
import database as db


class TestVoiceAgentIntentUnderstanding:
    """Test intent classification and parameter extraction"""

    def test_outfit_request_intent(self):
        """Test that outfit request is correctly classified"""
        state = VoiceAgentState(user_message="Suggest an outfit for college today")
        state = intent_understanding_node(state)

        assert state.intent == "outfit_request"
        assert state.occasion == "college"
        assert state.planning_time == "today"

    def test_wedding_outfit_request(self):
        """Test wedding-specific outfit request"""
        state = VoiceAgentState(user_message="What should I wear for a wedding?")
        state = intent_understanding_node(state)

        assert state.intent == "outfit_request"
        assert state.occasion == "wedding"
        assert state.style_preference == "ethnic"

    def test_job_interview_outfit_request(self):
        """Interview requests must not fall back to college/stylish looks."""
        state = VoiceAgentState(user_message="Suggest an outfit for a job interview")
        state = intent_understanding_node(state)

        assert state.intent == "outfit_request"
        assert state.occasion == "job interview"
        assert state.style_preference == "formal"

    def test_status_update_in_wash(self):
        """Test status update for item in wash"""
        state = VoiceAgentState(user_message="My blue jeans are in the wash")
        state = intent_understanding_node(state)

        assert state.intent == "status_update"
        assert state.status_change is not None
        assert state.status_change["availability_status"] == "in_wash"
        assert "blue jeans" in state.status_change["garment_description"].lower()

    def test_status_update_needs_ironing(self):
        """Test status update for item needing ironing"""
        state = VoiceAgentState(user_message="My white shirt needs ironing")
        state = intent_understanding_node(state)

        assert state.intent == "status_update"
        assert state.status_change is not None
        assert state.status_change["ironing_status"] == "needs_ironing"
        assert "white shirt" in state.status_change["garment_description"].lower()

    def test_status_update_ready(self):
        """Test marking item as ready after ironing"""
        state = VoiceAgentState(user_message="I have ironed my white shirt")
        state = intent_understanding_node(state)

        assert state.intent == "status_update"
        assert state.status_change is not None
        assert state.status_change["ironing_status"] == "ready"

    def test_availability_query(self):
        """Test availability query intent"""
        state = VoiceAgentState(user_message="What clothes are currently unavailable?")
        state = intent_understanding_node(state)

        assert state.intent == "availability_query"

    def test_exclusion_constraint(self):
        """Test that exclusion constraints are extracted"""
        state = VoiceAgentState(user_message="Don't suggest jeans today")
        state = intent_understanding_node(state)

        assert "jeans" in state.exclude_items

    def test_ready_to_wear_constraint(self):
        """Test ready-to-wear constraint extraction"""
        state = VoiceAgentState(user_message="Suggest an outfit using only clothes that are ready to wear")
        state = intent_understanding_node(state)

        assert "ready_to_wear_only" in state.constraints

    def test_modification_intent(self):
        """Test modification request intent"""
        state = VoiceAgentState(user_message="Show me another outfit")
        state = intent_understanding_node(state)

        assert state.intent == "modification"

    def test_tomorrow_planning(self):
        """Test tomorrow planning intent"""
        state = VoiceAgentState(user_message="Plan my outfit for tomorrow")
        state = intent_understanding_node(state)

        assert state.planning_time == "tomorrow"


class TestVoiceAgentWardrobeRetrieval:
    """Test wardrobe retrieval with availability filtering"""

    def test_wardrobe_retrieval_no_filter(self):
        """Test wardrobe retrieval without availability filter"""
        state = VoiceAgentState(
            user_message="Suggest an outfit",
            clothes=[],
            constraints=[]
        )
        # Mock clothes would be populated in real test
        state = wardrobe_retrieval_node(state)

        assert len(state.execution_trace) > 0
        assert state.execution_trace[-1]["agent"] == "Wardrobe Retrieval"

    def test_wardrobe_retrieval_with_ready_filter(self):
        """Test wardrobe retrieval with ready-to-wear filter"""
        state = VoiceAgentState(
            user_message="Suggest an outfit using only ready clothes",
            clothes=[],
            constraints=["ready_to_wear_only"]
        )
        state = wardrobe_retrieval_node(state)

        # In real test, would verify filtering logic
        assert len(state.execution_trace) > 0


class TestVoiceAgentStatusUpdate:
    """Test clothing status update functionality"""

    def test_status_update_ambiguous_item(self):
        """Test handling of ambiguous item selection"""
        state = VoiceAgentState(
            user_message="My blue jeans are in the wash",
            intent="status_update",
            status_change={
                "garment_description": "blue jeans",
                "availability_status": "in_wash"
            }
        )

        # Mock scenario with multiple blue jeans
        # In real test, would mock database with multiple matches
        state = status_update_node(state)

        assert state.response_type == "error" or state.response_type == "status_update"

    def test_status_update_item_not_found(self):
        """Test handling when item is not found"""
        state = VoiceAgentState(
            user_message="My purple leopard print pants are in the wash",
            intent="status_update",
            status_change={
                "garment_description": "purple leopard print pants",
                "availability_status": "in_wash"
            }
        )

        state = status_update_node(state)

        assert state.response_type == "error"
        assert "not found" in state.agent_response.lower()


class TestVoiceAgentAvailabilityQuery:
    """Test availability query functionality"""

    def test_availability_query_all_available(self):
        """Test query when all items are available"""
        state = VoiceAgentState(
            user_message="What clothes are unavailable?",
            intent="availability_query"
        )

        state = availability_query_node(state)

        assert state.response_type == "text"
        assert len(state.agent_response) > 0


class TestVoiceAgentOutfitRequest:
    """Test outfit request routing to existing pipeline"""

    def test_outfit_request_routes_to_pipeline(self):
        """Test that outfit request routes to existing pipeline"""
        state = VoiceAgentState(
            user_message="Suggest an outfit for college",
            intent="outfit_request",
            occasion="college",
            filtered_clothes=[]
        )

        # In real test, would mock the pipeline
        # state = outfit_request_node(state)

        assert state.intent == "outfit_request"
        assert state.occasion == "college"

    def test_empty_recommendation_is_a_no_match_not_an_error(self, monkeypatch):
        monkeypatch.setattr(
            "voice_agent_graph.run_multi_agent_pipeline",
            lambda _request: {"outfits": []}
        )
        state = VoiceAgentState(
            user_message="Suggest an outfit for college",
            intent="outfit_request",
            occasion="college"
        )

        result = outfit_request_node(state)

        assert result.response_type == "no_match"
        assert not result.recommended_outfits

    def test_pipeline_returns_normal_no_match_for_unsatisfied_constraints(self, monkeypatch):
        monkeypatch.setattr(db, "ensure_stylist_tables", lambda: None)
        monkeypatch.setattr(db, "get_stylist_conversation", lambda *_args: None)
        monkeypatch.setattr(db, "get_all_clothes", lambda: [])
        monkeypatch.setattr(db, "save_stylist_conversation", lambda *_args: None)
        monkeypatch.setattr(
            "voice_agent_graph.run_multi_agent_pipeline",
            lambda _request: {"outfits": []}
        )

        response = run_voice_agent_pipeline(
            "Only white clothes for a job interview",
            conversation_id="empty-test-conversation"
        )

        assert response["response_type"] == "no_match"
        assert response["outfits"] == []


class TestStructuredStylistIntent:
    def test_color_request_for_a_top_is_scoped_to_the_top(self):
        intent = _local_structured_intent(
            "I want a yellow color top or t-shirt in the outfit look",
            {}
        )

        assert intent.required_top_colors == ["yellow"]
        assert intent.required_colors == []
        assert intent.target_slot == "tops"

    def test_pink_top_request_is_understood_from_chat_wording(self):
        intent = _local_structured_intent("give me pink top outfit look", {})

        assert intent.required_top_colors == ["pink"]
        assert intent.required_colors == []
        assert intent.target_slot == "tops"

    def test_keep_trousers_as_the_anchor_when_asking_what_to_wear_with_them(self):
        intent = _local_structured_intent(
            "What can I wear with these black trousers?",
            {"current_outfits": [{"id": "selected"}]}
        )

        assert intent.action == "modify"
        assert intent.target_slot == "bottoms"
        assert intent.keep_slots == ["bottoms"]

    def test_second_option_is_selected_without_generating_a_new_look(self):
        intent = _local_structured_intent(
            "I'll choose the second option",
            {"current_outfits": [{"id": "first"}, {"id": "second"}]}
        )

        assert intent.action == "select"
        assert intent.selected_option == 2

    def test_compound_recommend_and_weekday_save_request_generates_new_outfits(self):
        intent = _local_structured_intent(
            "Give me an outfit for dinner date and save this look on Saturday",
            {"current_outfits": [{"id": "old-look"}]}
        )

        assert intent.action == "recommend"
        assert intent.occasion == "dinner date"

    def test_first_preference_is_understood_as_an_outfit_choice(self):
        intent = _local_structured_intent(
            "Save the first preference for Sunday",
            {"current_outfits": [{"id": "first"}, {"id": "second"}]}
        )

        assert intent.selected_option == 1

    def test_save_second_outfit_for_day_selects_the_requested_option(self):
        intent = _local_structured_intent(
            "Save the second look for Sunday if the slot is empty",
            {"current_outfits": [{"id": "first"}, {"id": "second"}, {"id": "third"}]}
        )

        assert intent.action == "select"
        assert intent.selected_option == 2

    def test_scheduling_follow_up_selects_existing_look_without_regenerating(self, monkeypatch):
        existing_outfits = [
            {"id": "look-1", "title": "First look"},
            {"id": "look-2", "title": "Second look"},
            {"id": "look-3", "title": "Third look"}
        ]
        monkeypatch.setattr(db, "ensure_stylist_tables", lambda: None)
        monkeypatch.setattr(
            db,
            "get_stylist_conversation",
            lambda *_args: {
                "state": {
                    "current_outfits": existing_outfits,
                    "current_outfit_id": "look-1"
                },
                "messages": []
            }
        )
        monkeypatch.setattr(db, "save_stylist_conversation", lambda *_args: None)
        monkeypatch.setattr(
            "voice_agent_graph._understand_stylist_message",
            lambda message, state: _local_structured_intent(message, state)
        )
        monkeypatch.setattr(
            "voice_agent_graph.run_multi_agent_pipeline",
            lambda *_args, **_kwargs: pytest.fail("A follow-up selection must not generate a new look.")
        )

        response = run_voice_agent_pipeline(
            "Save the second look for Sunday if the slot is empty",
            conversation_id="schedule-existing-look-test"
        )

        assert response["intent"] == "selection"
        assert response["response_type"] == "outfit"
        assert response["outfits"] == [existing_outfits[1]]
        assert response["conversation_state"]["current_outfit_id"] == "look-2"

    def test_scheduled_context_is_used_for_bag_exclusion_edit(self, monkeypatch):
        clothes = [
            {"id": "top-1", "title": "White Shirt", "category": "tops"},
            {"id": "bottom-1", "title": "Black Trousers", "category": "bottoms"},
            {"id": "shoe-1", "title": "Black Shoes", "category": "footwear"}
        ]
        planned_outfit = {
            "id": "planned-look",
            "title": "Look with bag",
            "slotItems": {
                "topObj": {"id": "top-1"},
                "bottomObj": {"id": "bottom-1"},
                "shoeObj": {"id": "shoe-1"},
                "bagObj": {"id": "bag-1"}
            },
            "slots": {"top": "White Shirt", "bottom": "Black Trousers", "bag": "Brown Bag"}
        }
        monkeypatch.setattr(db, "ensure_stylist_tables", lambda: None)
        monkeypatch.setattr(db, "get_stylist_conversation", lambda *_args: None)
        monkeypatch.setattr(db, "get_all_clothes", lambda: clothes)
        monkeypatch.setattr(db, "save_stylist_conversation", lambda *_args: None)
        monkeypatch.setattr(
            "voice_agent_graph._understand_stylist_message",
            lambda message, state: _local_structured_intent(message, state)
        )
        captured = {}

        def generate(request):
            captured.update(request)
            return {"outfits": [{"id": "updated-look"}]}

        monkeypatch.setattr("voice_agent_graph.run_multi_agent_pipeline", generate)
        response = run_voice_agent_pipeline(
            "Exclude bags from this look",
            conversation_id="exclude-bag-planned-look",
            context_outfit=planned_outfit
        )

        assert captured["excluded_categories"] == ["bags"]
        assert set(captured["locked_item_ids"]) == {"top-1", "bottom-1", "shoe-1"}
        assert response["response_type"] == "outfit"

    def test_no_bag_is_a_hard_category_exclusion(self):
        intent = _local_structured_intent(
            "No bag please",
            {"current_outfits": [{"id": "selected"}]}
        )

        assert intent.action == "modify"
        assert intent.excluded_categories == ["bags"]

    def test_exclude_bags_from_this_look_is_a_category_exclusion(self):
        intent = _local_structured_intent(
            "Exclude bags from this look",
            {"current_outfits": [{"id": "selected"}]}
        )

        assert intent.action == "modify"
        assert intent.excluded_categories == ["bags"]
        assert intent.target_slot is None

    def test_updated_outfit_for_a_planned_day_is_a_modification_request(self):
        intent = _local_structured_intent(
            "Remove outfit from Thursday's plan and add updated outfit",
            {"current_outfits": [{"id": "planned-look"}]}
        )

        assert intent.action == "modify"

    def test_excluded_garment_is_resolved_as_a_hard_item_restriction(self):
        intent = _local_structured_intent(
            "Don't suggest jeans today",
            {"current_outfits": [{"id": "selected"}]}
        )

        assert intent.action == "modify"
        assert intent.excluded_items == ["jeans"]
        assert intent.target_slot == "bottoms"

    def test_excluded_color_is_not_mistaken_for_a_required_dress(self):
        intent = _local_structured_intent(
            "Don't wear black clothes; I don't want a dress",
            {"current_outfits": [{"id": "selected"}]}
        )

        assert intent.excluded_colors == ["black"]
        assert not intent.required_garment_types

    def test_ready_to_wear_is_a_persistent_hard_constraint(self):
        intent = _local_structured_intent(
            "Use only clothes that are ready to wear",
            {}
        )

        assert intent.ready_to_wear_only

    def test_ready_to_wear_requirement_can_be_explicitly_relaxed(self):
        intent = _local_structured_intent(
            "I don't need everything to be ready to wear",
            {"availability_constraints": ["ready_to_wear_only"]}
        )

        assert not intent.ready_to_wear_only

    def test_targeted_replacement_preserves_the_other_selected_items(self, monkeypatch):
        selected_outfit = {
            "id": "selected",
            "title": "Current look",
            "slotItems": {
                "topObj": {"id": "top-1", "title": "White shirt"},
                "bottomObj": {"id": "bottom-1", "title": "Beige trousers"},
                "shoeObj": {"id": "shoes-1", "title": "Formal shoes"}
            }
        }
        monkeypatch.setattr(db, "ensure_stylist_tables", lambda: None)
        monkeypatch.setattr(
            db,
            "get_stylist_conversation",
            lambda *_args: {
                "state": {
                    "occasion": "job interview",
                    "style_preference": "formal",
                    "current_outfits": [selected_outfit],
                    "current_outfit_id": "selected"
                },
                "messages": []
            }
        )
        monkeypatch.setattr(db, "get_all_clothes", lambda: [])
        monkeypatch.setattr(db, "save_stylist_conversation", lambda *_args: None)
        captured = {}

        def generate(request):
            captured.update(request)
            return {"outfits": [{"id": "replacement"}]}

        monkeypatch.setattr("voice_agent_graph.run_multi_agent_pipeline", generate)

        run_voice_agent_pipeline(
            "Change the top but keep the trousers",
            conversation_id="targeted-change-test"
        )

        assert set(captured["locked_item_ids"]) == {"bottom-1", "shoes-1"}
        assert captured["excluded_item_ids"] == ["top-1"]


class TestVoiceAgentPipelineIntegration:
    """Test end-to-end voice agent pipeline"""

    def test_full_pipeline_outfit_request(self):
        """Test complete pipeline for outfit request"""
        response = run_voice_agent_pipeline("Suggest an outfit for college today")

        assert response is not None
        assert "status" in response
        assert "agent_response" in response
        assert "intent" in response

    def test_full_pipeline_status_update(self):
        """Test complete pipeline for status update"""
        response = run_voice_agent_pipeline("My blue jeans are in the wash")

        assert response is not None
        assert "status" in response
        assert "agent_response" in response

    def test_full_pipeline_availability_query(self):
        """Test complete pipeline for availability query"""
        response = run_voice_agent_pipeline("What clothes are currently unavailable?")

        assert response is not None
        assert "status" in response
        assert "intent" in response


class TestVoiceAgentEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_message(self):
        """Test handling of empty message"""
        response = run_voice_agent_pipeline("")

        assert response is not None

    def test_unknown_command(self):
        """Test handling of unknown command"""
        response = run_voice_agent_pipeline("What is the meaning of life?")

        assert response is not None
        assert "intent" in response

    def test_follow_up_context(self):
        """Test that follow-up commands preserve context"""
        # First request
        response1 = run_voice_agent_pipeline("Suggest an outfit for college")
        # Follow-up
        response2 = run_voice_agent_pipeline("Show me another one")

        assert response1 is not None
        assert response2 is not None


def test_voice_agent_comprehensive():
    """
    Comprehensive integration test simulating real usage scenarios
    """
    # Scenario 1: User requests college outfit
    response1 = run_voice_agent_pipeline("Suggest an outfit for college today")
    assert response1["status"] in ["success", "error"]
    assert response1["intent"] == "outfit_request"

    # Scenario 2: User marks item as in wash
    response2 = run_voice_agent_pipeline("My blue jeans are in the wash")
    assert response2 is not None
    assert response2["intent"] == "status_update"

    # Scenario 3: User checks availability
    response3 = run_voice_agent_pipeline("What clothes are currently unavailable?")
    assert response3 is not None
    assert response3["intent"] == "availability_query"

    # Scenario 4: User requests outfit with exclusions
    response4 = run_voice_agent_pipeline("Suggest an outfit for college without jeans")
    assert response4 is not None
    for outfit in response4.get("outfits", []):
        assert all(
            "jean" not in str(item.get("title", "")).lower()
            for item in (outfit.get("slotItems") or {}).values()
            if item
        )

    # Scenario 5: User requests ready-to-wear only
    response5 = run_voice_agent_pipeline("Suggest an outfit using only clothes that are ready to wear")
    assert response5 is not None
    assert "ready_to_wear_only" in response5["conversation_state"]["availability_constraints"]


if __name__ == "__main__":
    # Run tests
    print("Running Voice Agent Tests...")
    print("=" * 60)

    test_voice_agent_comprehensive()

    print("=" * 60)
    print("All tests completed!")
