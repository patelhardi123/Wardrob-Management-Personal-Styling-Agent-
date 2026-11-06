"""Keep optional AI services from delaying wardrobe answers indefinitely."""
from unittest.mock import Mock

from fashion import llm_client
import agent_graph
from fashion.compatibility_engine import CompatibilityEngine


def test_provider_requests_have_bounded_wait_and_no_retries(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    constructor = Mock()
    monkeypatch.setattr(llm_client, "OpenAI", constructor)
    llm_client.get_llm_client_and_model()
    assert constructor.call_args.kwargs["timeout"] == 8.0
    assert constructor.call_args.kwargs["max_retries"] == 0


def test_recommendation_does_not_generate_photos_by_default(monkeypatch):
    for name in (
        "style_profile_agent_node", "trend_research_agent_node", "occasion_agent_node",
        "wardrobe_agent_node", "outfit_stylist_agent_node", "outfit_critic_agent_node",
    ):
        monkeypatch.setattr(agent_graph, name, lambda state: state)
    monkeypatch.setattr(agent_graph, "_apply_weather_context", lambda state, city: state)
    photos = Mock(side_effect=lambda state: state)
    monkeypatch.setattr(agent_graph, "visualization_agent_node", photos)
    agent_graph.run_multi_agent_pipeline({"clothes": []})
    photos.assert_not_called()
    agent_graph.run_multi_agent_pipeline({"clothes": [], "generate_visualizations": True})
    photos.assert_called_once()


def test_trend_scoring_never_reads_uploaded_photo_data():
    class PhotoData:
        def __str__(self):
            raise AssertionError("Trend matching must not scan image data")

    engine = CompatibilityEngine()
    top = {"title": "White linen shirt", "color": "white", "style": "casual"}
    bottom = {"title": "Blue jeans", "color": "blue", "style": "casual"}
    signals = [{"tag": "linen", "score": 100, "current": True}]
    expected = engine.evaluate_candidate_outfit(top, bottom, trend_signals=signals, context={"occasion": "college"})
    actual = engine.evaluate_candidate_outfit(
        dict(top, imageUrl=PhotoData()), bottom, trend_signals=signals, context={"occasion": "college"}
    )
    assert actual == expected
    assert actual["sub_scores"]["trend"] > 7.5
