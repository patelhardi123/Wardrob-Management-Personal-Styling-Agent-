# Automatic RSS fashion trend research

## What changed

The inspected `backend/agent_graph.py` returned five hardcoded signals and claimed live research. The actual `backend/wardrobe.db` had no `trend_notes` table. The existing pipeline passes a Pydantic shared state between sequential agent nodes; its orchestration was retained rather than replacing the other agents with a different graph.

Modified/added files:
- `backend/trend_research.py`: feed retrieval, keyword extraction, optional local normalization, scoring, migrations, cache, cross-process lease, worker and verification CLI.
- `backend/trend_sources.json`: operator-configurable publisher feeds and independent publisher groups.
- `backend/agent_graph.py`: real cached signals and metadata in shared state, truthful trace/outfit label, suitability threshold excludes trend bonus.
- `backend/fashion/compatibility_engine.py`: bounded score-weighted matching of current extracted tags against owned outfit items. Existing 5% trend weight retained.
- `backend/main.py`: worker startup/shutdown and read-only `GET /api/trends/status`.
- `backend/requirements.txt`: adds `feedparser>=6.0.11,<7`; httpx was already required.
- `frontend/src/components/AgentHubPage.jsx`: actual source names, signal count, cache mode and last successful internet update on the trend card and backend trace. Offline animation makes no research claims.
- `backend/test_trend_research.py`: isolated temporary SQLite databases and mocked failure/access cases.
- `.gitignore`: excludes local verification dependencies/databases and baseline comparison script.

## Install and run

Use an installed Python 3.10+ interpreter and the project's normal environment:

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

This machine's existing `backend/venv` points to a missing Python 3.10 installation. Recreate it with an installed interpreter if needed. Verification used the desktop app's bundled Python 3.12 and project-local `.trend-test-deps`; that directory is only a test aid, not a runtime requirement.

The background worker checks the persisted due time every five minutes and refreshes approximately every 24 hours, including on startup when due. No refresh occurs while the backend is stopped. Multiple processes share an atomic SQLite lease and persisted last-attempt time. Lease ownership is renewed during article processing, overlapping jobs are refused, and crash leases expire after an hour. Failed scheduled attempts retry at the next daily interval. The operator CLI can request an earlier refresh; it still honors active leases.

## Sources and access

Defaults are the official RSS URLs `https://www.vogue.com/feed/rss` and `https://www.vogue.in/feed/rss`. Set `TREND_SOURCES_FILE` to an absolute path to another JSON source list with `name`, `url` and `independent_group`. This is trusted server configuration, not a user-supplied URL API. Use sources whose terms permit your intended use and remove any source if permission changes. RSS availability and robots permission do not grant blanket reuse rights.

Only RSS titles, summaries and publisher-supplied RSS content are read. There is no article-page scraping, login, CAPTCHA bypass or access-restriction workaround. Robots errors or denials, HTTP errors, redirects and oversized feeds fail closed. Each source is bounded to 100 entries and 2 MB; requests have timeouts and respect robots crawl delays up to 30 seconds (longer requirements cause the source to be skipped). TLS verification remains enabled and uses the operating system trust store. Cached evidence survives source failures. Full article text is not persisted.

Both Vogue feeds use `independent_group: conde-nast`, so their agreement does not count as independent corroboration. Add unrelated publishers with their own groups for broader evidence.

`TREND_USE_OLLAMA=true` optionally enables localhost-only `llama3.2:1b` JSON normalization. It is off by default. Outputs must be bounded lists of known vocabulary values; invalid JSON and failures preserve keyword results. The model can only narrow keyword evidence, not invent claims, URLs, dates or scores.

`TREND_SEASON` optionally overrides the default northern-hemisphere meteorological season, e.g. `monsoon`. The initial agent has no location-specific season input, so this is a deployment setting rather than a claim about every user's climate.

## Database changes

The idempotent migration creates `trend_notes` if absent and otherwise only adds missing columns. No existing trend rows are deleted or replaced:

- `source_url`, `publication_date`, `extraction_confidence`, `trend_tags` (JSON), `last_updated`
- `attributes_json` (category, garment type, fit, silhouette, colors, patterns, season, style tags)
- `source_name`, `independent_group`, `article_key`, `article_title`

New supporting tables: `trend_articles` records processed canonical URLs, including irrelevant entries; `trend_refresh` records the lease, attempts, last successful fetch and per-source report. A nullable unique index on `trend_notes.article_key` deduplicates new evidence without affecting legacy rows. Existing legacy text is interpreted conservatively as fallback without assigning internet provenance or a current label. Existing additional columns are retained. A custom legacy schema with mandatory columns that have no defaults may need an insert adapter; the inspected project had no such table.

URLs are normalized with tracking parameters removed. Previously processed articles are not re-extracted; seeing them in a successful feed updates only cache validation time, never publication time. Missing publication dates remain unknown, and future dates are never current.

## Scores and safeguards

Scores are evidence-strength heuristics, not popularity percentages: 40% publication recency (45-day horizon), 25% corroboration across independent publisher groups, 15% seasonal relevance and 20% keyword extraction confidence. A single article has zero independent-corroboration contribution; `widely_supported` requires at least three publisher groups. Repeated articles from one publisher cannot inflate that contribution.

Current evidence requires both a publication age of at most 45 days and cache validation within 48 hours. If none qualifies, stored evidence remains available as `stale_fallback`, with `current: false`; otherwise an empty cache is `unavailable`. Only current signals influence outfit ranking. The request pipeline always reads a cache and accurately says so, even immediately after a background internet fetch.

Signals are small ranking hints over owned items. Availability, explicit item/color/garment constraints, dress-code checks and the existing critic remain in force. The critic's minimum compatibility threshold is evaluated without the trend bonus, so it cannot rescue an otherwise below-threshold outfit. Other frontend pages and other agent behavior were retained.

## Verify genuine internet retrieval

From `backend`, with dependencies installed:

```powershell
python trend_research.py --refresh
```

This calls the real default HTTP fetcher, checks robots, parses the returned RSS and prints per-source statuses, newly processed articles, new evidence records and a snapshot of scored tags with original article URLs. Repeating it should report zero newly processed entries for unchanged feeds, while keeping cached signals. `--refresh` is an operator command, not an unauthenticated web mutation endpoint.

Open `http://localhost:8000/api/trends/status` or the frontend Agent Hub. Inspect `refresh.sources`, `last_successful_update`, `mode`, and `signals[].source_urls`. All request traces say `RSS cache`; failed or empty feeds do not create a fake success timestamp. A successful fetch can find zero new trends, so inspect the per-source report as well as its timestamp.

For direct evidence, query SQLite:

```sql
SELECT source_name, article_title, source_url, publication_date,
       extraction_confidence, trend_tags, attributes_json, last_updated
FROM trend_notes
WHERE article_key IS NOT NULL
ORDER BY last_updated DESC;
```

Compare an article title/URL/date with its publisher's RSS feed. Disconnect the network and run the command again: source errors should be visible while previous records and the previous last-success timestamp remain. Missing-date or expired evidence must show `stale_fallback` and cannot receive a current trend bonus.

Live verification on 3 November 2026: both default sources succeeded with TLS verification and robots checks enabled, returning 30 entries each. Nine articles contained extractable clothing evidence (four Vogue, five Vogue India). The separate verification database/report are `.trend-verification.db` and `.trend-verification.json`. These contain genuine retrieved evidence, not seeded signals. Counts can change on subsequent fetches.

## Tests

```powershell
cd backend
python -m pytest test_trend_research.py -q
python -m pytest test_fashion_engine.py test_availability.py -q
```

The focused suite covers real feedparser parsing, feed/network failures, missing dates, duplicate URLs, irrelevant content, strict invalid model JSON, stale publication and validation times, publisher independence, persisted scheduling, overlapping/nested refreshes, legacy migration, partial-source failure, access denials/redirects and shared-state/trace integration. Local verification results follow.

Final verification results:
- Focused trend tests: 26 passed in 5.73 seconds after the final transaction-scope adjustment.
- Frontend production build: passed (Vite, 1492 modules).
- Python syntax compilation: passed for changed modules.
- Existing fashion suite: 25 passed, 6 failed. An in-memory comparison restoring the original hardcoded trend node, original keyword scoring and original critic threshold reproduced the same six failures: rain/canvas filtering and scenarios 8, 9, 10, 14 and 22. These were left outside this change's scope. Weather requests in that suite also reported existing certificate errors.
- Availability regression suite: could not collect in the temporary verification environment because the existing `rembg` dependency is not installed. Full application startup therefore was not exercised in this temporary environment; normal project requirements include rembg.
- Live RSS checks succeeded for both configured feeds. The production `backend/wardrobe.db` cache was also refreshed: 60 entries processed, 9 article evidence records, 16 current tags. All have one independent publisher group and no widespread-popularity claim. The current snapshot endpoint reads this cache without making a live request.
