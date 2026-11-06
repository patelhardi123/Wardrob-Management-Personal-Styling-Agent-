import json
import sqlite3
import time
from datetime import datetime, timedelta, timezone

import feedparser
import pytest
import trend_research as tr


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(tr.database, 'DB_PATH', str(tmp_path / 'trends.db'))
    monkeypatch.setattr(tr, 'sources', lambda: [{'name': 'Vogue', 'url': 'https://www.vogue.com/feed/rss', 'independent_group': 'conde-nast'}])
    monkeypatch.delenv('TREND_USE_OLLAMA', raising=False)
    tr.ensure_schema()


def entry(title='Oversized blue shirts for winter', date=True, url='https://www.vogue.com/article/shirts'):
    result = {'title': title, 'summary': 'Relaxed striped shirts and jeans', 'link': url}
    if date:
        result['published_parsed'] = time.gmtime()
    return result


def test_real_feedparser():
    parsed = feedparser.parse(b'<rss version="2.0"><channel><title>Fashion</title><item><title>Blue shirts</title><link>https://example.org/shirts</link></item></channel></rss>')
    assert parsed.version == 'rss20'
    assert parsed.entries[0].title == 'Blue shirts'


def test_feed_failure_and_unavailable_internet():
    def offline(source):
        raise OSError('internet unavailable')
    result = tr.refresh(force=True, fetcher=offline)
    assert result['sources'][0]['status'] == 'error'
    assert tr.snapshot()['mode'] == 'unavailable'
    assert tr.snapshot()['last_successful_update'] is None


def test_missing_publication_date_is_never_current():
    tr.refresh(force=True, fetcher=lambda _: [entry(date=False)])
    data = tr.snapshot()
    assert data['mode'] == 'stale_fallback'
    assert data['signals'] and not any(s['current'] for s in data['signals'])


def test_duplicate_article_canonical_url():
    tr.refresh(force=True, fetcher=lambda _: [entry(), entry(url=entry()['link'] + '?utm_source=rss')])
    tr.refresh(force=True, fetcher=lambda _: [entry()])
    with tr.connection() as conn:
        assert conn.execute('SELECT count(*) FROM trend_notes').fetchone()[0] == 1
        assert conn.execute('SELECT count(*) FROM trend_articles').fetchone()[0] == 1


def test_irrelevant_content():
    tr.refresh(force=True, fetcher=lambda _: [{'title': 'New skincare serum and beauty routines', 'link': 'https://example.org/beauty'}])
    assert not tr.snapshot()['signals']


@pytest.mark.parametrize('raw', ['not json', '[]', '{"colors":"blue"}', '{"colors":["invented"]}', '{"score":100}', '{"colors":[42]}'])
def test_invalid_llm_json(raw):
    assert tr.validate_llm_json(raw) is None


def test_valid_llm_json():
    assert tr.validate_llm_json('{"colors":["blue"]}') == {'colors': ['blue']}


def test_stale_cache_survives_failure():
    tr.refresh(force=True, fetcher=lambda _: [entry()])
    with tr.connection() as conn:
        conn.execute('UPDATE trend_notes SET publication_date=?', ((datetime.now(timezone.utc) - timedelta(days=90)).isoformat(),))
    previous = tr.snapshot()['last_successful_update']
    def offline(_):
        raise OSError('offline')
    tr.refresh(force=True, fetcher=offline)
    data = tr.snapshot()
    assert data['mode'] == 'stale_fallback'
    assert data['last_successful_update'] == previous
    assert data['signals'] and all(not s['current'] for s in data['signals'])


def test_single_publisher_never_widely_supported(monkeypatch):
    monkeypatch.setattr(tr, 'sources', lambda: [
        {'name': 'Vogue', 'url': 'https://www.vogue.com/feed/rss', 'independent_group': 'conde-nast'},
        {'name': 'Vogue India', 'url': 'https://www.vogue.in/feed/rss', 'independent_group': 'conde-nast'}])
    tr.refresh(force=True, fetcher=lambda s: [entry(url=s['url'] + '/article')])
    assert all(s['independent_sources'] == 1 and not s['widely_supported'] for s in tr.snapshot()['signals'])


def test_refresh_daily_and_lock(monkeypatch):
    tr.refresh(fetcher=lambda _: [entry()])
    assert tr.refresh(fetcher=lambda _: pytest.fail('duplicate job'))['skipped']
    with tr.connection() as conn:
        conn.execute('UPDATE trend_refresh SET lease_until=?', (time.time()+300,))
    assert tr.refresh(force=True, fetcher=lambda _: pytest.fail('overlap'))['skipped']


def test_nested_refresh_cannot_overlap():
    def fetch(_):
        assert tr.refresh(force=True, fetcher=lambda _: pytest.fail('overlap'))['skipped']
        return [entry()]
    tr.refresh(force=True, fetcher=fetch)


def test_legacy_schema_preserved():
    with tr.connection() as conn:
        conn.execute('DROP TABLE trend_notes')
        conn.execute('CREATE TABLE trend_notes (id INTEGER PRIMARY KEY, note TEXT)')
        conn.execute("INSERT INTO trend_notes(note) VALUES ('Oversized linen shirts')")
    tr.ensure_schema()
    tr.ensure_schema()
    data = tr.snapshot()
    assert data['mode'] == 'stale_fallback'
    assert data['signals']
    with tr.connection() as conn:
        assert conn.execute('SELECT note FROM trend_notes').fetchone()[0] == 'Oversized linen shirts'


def test_partial_failure(monkeypatch):
    monkeypatch.setattr(tr, 'sources', lambda: [{'name': 'broken', 'url': 'https://example.org/rss'}, {'name': 'working', 'url': 'https://example.net/rss'}])
    def fetch(source):
        if source['name'] == 'broken':
            raise OSError('timeout')
        return [entry()]
    report = tr.refresh(force=True, fetcher=fetch)
    assert [s['status'] for s in report['sources']] == ['error', 'ok']
    assert tr.snapshot()['mode'] == 'cached'


def test_trend_bonus_cannot_override_gates():
    from fashion.compatibility_engine import default_engine
    item = {'title': 'Blue casual shirt', 'category': 'tops', 'color': 'blue'}
    base = default_engine.evaluate_candidate_outfit(item, {'title': 'Jeans', 'category': 'bottoms'}, context={'occasion': 'college'})
    stale = default_engine.evaluate_candidate_outfit(item, {'title': 'Jeans', 'category': 'bottoms'}, trend_signals=[{'tag': 'blue', 'score': 100, 'current': False}], context={'occasion': 'college'})
    fresh = default_engine.evaluate_candidate_outfit(item, {'title': 'Jeans', 'category': 'bottoms'}, trend_signals=[{'tag': 'blue', 'score': 100, 'current': True}], context={'occasion': 'college'})
    assert stale['sub_scores']['trend'] == base['sub_scores']['trend']
    assert fresh['sub_scores']['trend'] > base['sub_scores']['trend']
    assert fresh['sub_scores']['occasion'] == base['sub_scores']['occasion']
    assert fresh['issues'] == base['issues']

@pytest.mark.parametrize('robots_status,robots_body,feed_status', [
    (200, 'User-agent: *\nDisallow: /feed', 200),
    (403, '', 200),
    (200, 'User-agent: *\nAllow: /', 403),
    (200, 'User-agent: *\nAllow: /', 302),
])
def test_access_restrictions_are_not_bypassed(monkeypatch, robots_status, robots_body, feed_status):
    import httpx
    requests = []
    def handler(request):
        requests.append(str(request.url))
        if request.url.path == '/robots.txt':
            return httpx.Response(robots_status, text=robots_body)
        return httpx.Response(feed_status, text='<html>Access denied</html>')
    original_client = httpx.Client
    monkeypatch.setattr(tr.httpx, 'Client', lambda **kw: original_client(transport=httpx.MockTransport(handler), **kw))
    monkeypatch.setattr(tr.time, 'sleep', lambda _: None)
    with pytest.raises((ValueError, httpx.HTTPError)):
        tr.fetch_feed({'url': 'https://example.org/feed/rss'})
    assert len(requests) <= 2
    if robots_status == 403 or 'Disallow' in robots_body:
        assert len(requests) == 1


def test_invalid_local_model_output_keeps_keywords(monkeypatch):
    import httpx
    monkeypatch.setenv('TREND_USE_OLLAMA', 'true')
    monkeypatch.setattr(tr.httpx, 'post', lambda *a, **kw: httpx.Response(200, json={'response': '{"colors":["made up"]}'}, request=httpx.Request('POST', 'http://localhost:11434/api/generate')))
    attrs, _, _ = tr.extract('Blue shirts')
    assert tr.normalize_optional(attrs, 'Blue shirts') == attrs


def test_expired_refresh_is_stale_even_for_recent_article():
    tr.refresh(force=True, fetcher=lambda _: [entry()])
    with tr.connection() as conn:
        conn.execute('UPDATE trend_notes SET last_updated=?', ((datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),))
    assert tr.snapshot()['mode'] == 'stale_fallback'


def test_actual_shared_state_and_trace():
    from agent_graph import AgentGraphState, trend_research_agent_node
    tr.refresh(force=True, fetcher=lambda _: [entry()])
    state = trend_research_agent_node(AgentGraphState())
    assert state.trend_research_signals[0]['source_urls']
    assert state.trend_research_metadata['mode'] == 'cached'
    assert state.execution_trace[-1]['last_successful_update']
    assert 'RSS cache' in state.execution_trace[-1]['summary']
    assert 'live' not in state.execution_trace[-1]['summary'].lower()
