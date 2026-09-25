# Integrating an online chess platform with Sentinel

This is for an engineer wiring up an existing online chess platform (game
server, tournament site, etc.) to send completed games to Sentinel for
statistical integrity analysis.

**Status:** This path is implemented and has been verified end to end
(key creation → job submission → real Stockfish/Maia analysis → result
delivery). It is not yet running in a production deployment — someone
needs to host the backend somewhere reachable from your platform (see
"Deployment" at the end).

## How it works, in one sentence

Your platform POSTs a completed game's PGN (plus optional behavioral
telemetry) to Sentinel, gets a `job_id` back immediately, and receives the
analysis either via a webhook you register or by polling.

This is **post-game batch analysis**, not live move-by-move analysis. A
separate `/v1/live/*` endpoint set exists in the API but expects the
*caller* to already have computed engine-match and Maia-probability numbers
per move — it does not run analysis itself. Don't use it for a real
integration; use `/v1/partner/analyze` below instead, calling it right
after each game ends.

## 1. Get a partner API key

An admin on the Sentinel side runs:

```bash
curl -X POST https://<sentinel-host>/v1/partner/keys/create \
  -H "X-Role: system_admin" \
  -H "Content-Type: application/json" \
  -d '{
    "partner_name": "your-platform-name",
    "rate_limit_per_minute": 60
  }'
```

Response includes `key` (send this as `x-api-key` on every request below)
and `secret` (used to verify webhook signatures — see step 4). **The
secret is only ever returned once, at creation time** — store it securely
on your side.

## 2. (Optional but recommended) Register a webhook

```bash
curl -X POST https://<sentinel-host>/v1/partner/webhook/register \
  -H "x-api-key: <your-key>" \
  -H "Content-Type: application/json" \
  -d '{"webhook_url": "https://your-platform.example.com/sentinel-webhook"}'
```

If you skip this, you can still get results by polling (step 5).

## 3. Submit a completed game

```bash
curl -X POST https://<sentinel-host>/v1/partner/analyze \
  -H "x-api-key: <your-key>" \
  -H "Content-Type: application/json" \
  -d @game.json
```

Minimum required fields in `game.json`:

```json
{
  "game_id": "your-internal-game-id",
  "player_id": "your-internal-player-id",
  "player_color": "white",
  "pgn": "[Event \"...\"]\n...\n1. e4 e5 ..."
}
```

`official_elo` (int) should be included whenever you have it — the
statistical model calibrates against the player's rated strength, so
omitting it materially weakens the analysis.

`games_played` (int) should be included whenever you have it too — it
sets whether this player is treated as cold-start (fewer than 10 games:
detection stays active but confidence is explicitly downgraded rather
than over-trusting a thin history). Omitting it defaults to 0, i.e.
every player is treated as brand-new.

Optional fields that improve detection quality, if your client can capture
them (all optional, all additive — send what you have). Only the ones
marked "read today" are actually consumed by the analysis right now;
the others are accepted and stored but not yet used, so don't prioritize
matching their shape:

| Field | What it's for | Status |
|---|---|---|
| `window_events` | tab/focus-loss signal — only `{"type"/"event": "blur"}` is counted | read today |
| `page_events` | copy/paste/cut detection — `{"type"/"event": "copy"\|"paste"\|"cut"}` | read today |
| `per_move_summary` | per-move behavioral timing — see field list below | read today |
| `mouse_events`, `click_timing`, `keyboard_events`, `touch_events` | counted, not yet deeply parsed | partial |
| `move_history`, `connection_events` | accepted, not yet wired into analysis | not yet used |
| `environment` | browser/device metadata, passed through | read today |
| `device_fingerprint` | pass `fingerprint_hash` directly, or `fingerprint_raw` and Sentinel will hash it server-side — the raw value is never stored | read today |
| `camera_events` + `consent` | only relevant if your platform does webcam proctoring; requires explicit consent flags, see below | read today |

`per_move_summary` is a list, one entry per move, with any of these
optional numeric keys: `path_straightness`, `time_spent_seconds`,
`drag_duration_ms`, `hover_dwell_on_played_square_ms`,
`squares_visited_count`, `reaction_time_ms`.

Response:

```json
{"status": "accepted", "job_id": "job_xxxxxxxx", "message": "..."}
```

**Idempotent submission.** Resubmitting the same `game_id` + `player_id`
(scoped to your API key) returns the existing job instead of running a
second analysis, as long as that job didn't fail:

```json
{"status": "accepted", "job_id": "job_xxxxxxxx", "message": "Already submitted; returning the existing job instead of re-analyzing.", "duplicate": true}
```

A job whose *analysis* failed does not block a resubmission — that gets
a fresh attempt with a new job.

**Camera data note:** if you send `camera_events`, set
`camera_storage_mode` to `"safe"` (default) unless you specifically need
raw frames retained, which additionally requires `consent: {"camera_raw":
true}` and is disabled server-side by default. In `"safe"` mode only a
derived summary (face-missing counts, gaze-away counts, etc.) is kept —
raw frames are never stored.

## 4. Receive results via webhook

Sentinel POSTs to your registered `webhook_url` when analysis completes:

```json
{
  "job_id": "job_xxxxxxxx",
  "game_id": "your-internal-game-id",
  "player_id": "your-internal-player-id",
  "status": "complete",
  "risk_level": "LOW | MODERATE | ELEVATED | HIGH_STATISTICAL_ANOMALY",
  "risk_score": 0.54,
  "summary": "Statistical analysis complete. Human review recommended for elevated findings.",
  "signals": [ { "name": "...", "triggered": false, "score": 0, "threshold": 0 }, ... ],
  "behavioral": { ... },
  "timestamp": "2026-09-25T07:55:00Z"
}
```

**Verify the signature.** Every webhook request carries:
- `X-Sentinel-Job-Id`: the job id
- `X-Sentinel-Signature`: HMAC-SHA256 of the raw request body, keyed with
  your partner `secret` from step 1

```python
import hmac, hashlib

def verify(raw_body: bytes, signature_header: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)
```

Reject anything that doesn't verify. Return **HTTP 200** to acknowledge —
anything else triggers retries at 30s, 5min, and 30min, after which the
job is marked `webhook_failed` (still retrievable via polling).

## 5. Or poll instead

```bash
curl https://<sentinel-host>/v1/partner/result/job_xxxxxxxx \
  -H "x-api-key: <your-key>"
```

Same payload shape as the webhook, plus `"status"` will be one of
`queued`, `complete`, `webhook_failed`, or `failed`.

## 6. Data retention and deletion

Submitted games/results/telemetry are auto-purged after 90 days by
default (server-configurable). To delete sooner — e.g. a player closes
their account — call either of these (scoped to your own API key; you
can only delete data you submitted):

```bash
curl -X DELETE https://<sentinel-host>/v1/partner/data/player/<player_id> \
  -H "x-api-key: <your-key>"

curl -X DELETE https://<sentinel-host>/v1/partner/data/game/<game_id> \
  -H "x-api-key: <your-key>"
```

Both return `{"<player_id|game_id>": "...", "jobs_deleted": N}`.

## Rate limits

Default 60 requests/minute per API key (set at key creation, adjustable).
`429` is returned once exceeded. Increase `rate_limit_per_minute` at key
creation if your expected game volume needs it.

## Deployment

None of this is publicly reachable yet — `<sentinel-host>` above is a
placeholder. Before a real platform can integrate:

1. The FastAPI backend (`backend/`) needs to run somewhere with a stable,
   HTTPS-reachable URL (not `localhost`).
2. `STOCKFISH_PATH` / `MAIA_LC0_PATH` need real binaries provisioned on
   that host — see `stockfish/build_stockfish7.sh` and `README.md`.
3. The `X-Role` header used for admin-only calls (like creating partner
   keys) is currently unauthenticated — anyone can set it themselves. Fine
   for creating the first partner key from a trusted internal shell; not
   fine to expose publicly until that's fixed. Don't put key-creation
   behind a public endpoint yet.
