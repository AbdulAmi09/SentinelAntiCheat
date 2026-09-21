Got it. Here is exactly what to paste into your AI builder:

---

## Sentinel — Online & Hybrid Integration: Build Instructions for AI

---

### What you are building and why

Sentinel currently works as a standalone platform where arbiters manually upload PGNs. We need to extend it so that **external chess websites can plug Sentinel into their platform** using a script tag, and Sentinel will silently collect player data, analyse it, and return results automatically. We also need a **hybrid mode** where an arbiter on the Sentinel dashboard can watch a live game happening on an external site in real time.

This requires four connected components built in this order: **SDK → API → Webhook → WebSocket**. Each does a different job. Build them as described below.

---

### Component 1 — The JavaScript SDK

**What it is:** A single JavaScript file hosted on the Sentinel server. External chess sites integrate it by adding one script tag to their HTML. That is the entire effort required from the partner site. Everything else happens automatically inside our script.

**How the partner site embeds it:**
```html
<script 
  src="https://sentinel.yourdomain.com/sdk/sentinel.js"
  data-api-key="THEIR_API_KEY"
  data-callback-url="https://theirsite.com/sentinel-results"
  data-mode="standard">
</script>
```

For hybrid mode they add one extra attribute:
```html
  data-mode="hybrid"
  data-session-id="UNIQUE_GAME_SESSION_ID"
```

**What the SDK must collect while the game is running:**

1. **Mouse trajectory** — listen to `mousemove` events. Record `{x, y, timestamp, velocity, acceleration}` throttled to every 100ms. Also record `mousedown`, `mouseup`, `dragstart`, `dragend` with coordinates and timestamps. Compute and attach path straightness (ratio of straight-line distance to actual cursor path length) per move.

2. **Click and interaction timing per move** — for each move record: time from opponent's last move to piece pickup, time from piece pickup to piece drop, drag duration in milliseconds, which squares the cursor hovered over before the move was played, dwell time on each square, whether the cursor went directly to the played square or visited alternatives.

3. **Window and tab behavior** — listen to `visibilitychange`, `blur`, and `focus` events on `window`. Record each event with timestamp, type, and duration. Record which ply was active when focus was lost. Count total tab switches and total focus loss milliseconds.

4. **Keyboard and input events** — record premove set and cancel events with timestamps, draw offer events, resign clicks, and Escape key presses.

5. **Copy and paste events** — listen to `copy`, `cut`, and `paste` events on the document. Record timestamp and which ply was active. This is a critical signal — copying during a game suggests FEN or move string being passed to an external engine.

6. **Connection and session data** — record `online`/`offline` events with timestamps and duration. Record which ply was active during disconnects. Sample page ping or latency if available from the platform.

7. **Touch events (mobile)** — if the device is touch-based, record `touchstart` and `touchend` with `{x, y, timestamp, pressure, radiusX, radiusY}`.

8. **Board and environment data** — on initialisation, record the board element's bounding rectangle `{x, y, width, height}`, screen resolution, viewport size, device pixel ratio, browser, OS, and whether touch is enabled. This is needed to normalise mouse coordinates to chess squares.

9. **Game data** — observe the board DOM using a `MutationObserver` to detect move updates. Extract each move in UCI and SAN format with the FEN before the move, clock before, clock after, and timestamp. On game end extract the full PGN.

10. **Per-move summary** — after each move the SDK computes and stores a summary object: `{ply, time_spent_seconds, reaction_time_ms, mouse_path_length_px, path_straightness, squares_visited_count, hover_dwell_on_played_square_ms, tab_switched_this_move, copy_paste_this_move, premove_used, drag_duration_ms}`.

**What the SDK does at game end:**

Bundle everything into a single JSON payload and send it via `fetch` POST to `POST /v1/partner/analyze` on the Sentinel API. Include the `api_key` in the request header as `x-api-key`.

**The complete payload structure:**
```json
{
  "game_id": "partner-internal-id",
  "player_id": "username-on-their-platform",
  "player_color": "white",
  "pgn": "full PGN string",
  "fen_history": [],
  "move_history": [],
  "mouse_events": [],
  "click_timing": [],
  "window_events": {},
  "keyboard_events": [],
  "page_events": [],
  "touch_events": [],
  "connection_events": [],
  "environment": {},
  "session": {},
  "per_move_summary": []
}
```

**SDK security requirements:**
- The SDK must not activate unless a valid `data-api-key` is present
- Add a visible but unobtrusive indicator on the partner page that Sentinel monitoring is active — required for player consent
- The SDK must not be tamper-detectable by the player — do not expose internal variable names
- Throttle all event listeners to prevent performance impact on the host site
- The SDK file must be loadable cross-origin with correct CORS headers served from Sentinel

---

### Component 2 — The Sentinel Partner REST API

**What it is:** New endpoints added to the existing Sentinel FastAPI backend that receive data from the SDK, queue analysis jobs, and manage partner authentication.

**New endpoints to build:**

```
POST   /v1/partner/analyze          
GET    /v1/partner/result/{job_id}  
POST   /v1/partner/webhook/register 
GET    /v1/partner/keys             
POST   /v1/partner/keys/create      
DELETE /v1/partner/keys/{key_id}    
```

**How `POST /v1/partner/analyze` works step by step:**

1. Read `x-api-key` from request header. Look it up in the `partner_api_keys` table. If missing or invalid return `401 Unauthorized`.
2. Check rate limit for that key against Redis. If exceeded return `429 Too Many Requests` with a `Retry-After` header.
3. Validate the payload — confirm PGN is parseable, `game_id` and `player_id` are present. If invalid return `422 Unprocessable Entity` with a specific error message.
4. Save the raw payload to the `partner_jobs` table with status `queued`.
5. Immediately return `202 Accepted` with a `job_id`. Do not make the partner wait.
6. Push the `job_id` to a background task worker.
7. The background worker runs the full Sentinel pipeline — PGN parsing, Stockfish analysis, Maia scoring, all signal layers including the new behavioral and environmental layers, and ML fusion — on the submitted data.
8. When complete update the job status to `complete` and store the result.
9. Trigger the outgoing webhook to the partner's registered `callback_url`.

**`202 Accepted` response:**
```json
{
  "status": "accepted",
  "job_id": "job_abc123",
  "message": "Analysis queued. Results will be delivered to your callback URL."
}
```

**API key authentication:** Every request must include `x-api-key` in the header. Keys are stored in a `partner_api_keys` database table with columns: `id`, `key`, `partner_name`, `webhook_url`, `rate_limit_per_minute`, `active`, `created_at`. Keys are generated as cryptographically random 32-character strings.

**Rate limiting:** Use Redis to track request counts per API key per minute. Default limit is 60 requests per minute per key. Return specific error codes: `401` invalid key, `422` bad payload, `429` rate limit, `503` engine unavailable.

**New database tables to add:**
```sql
partner_api_keys (
  id, key, partner_name, webhook_url,
  rate_limit_per_minute, active, created_at
)

partner_jobs (
  id, job_id, api_key_id, game_id, player_id,
  raw_payload_json, status, risk_level, risk_score,
  result_json, webhook_delivered, webhook_attempts,
  created_at, completed_at
)

live_sessions (
  id, session_id, api_key_id, game_id,
  player_id, status, created_at, ended_at
)
```

---

### Component 3 — The Outgoing Webhook

**What it is:** When Sentinel finishes analysing a job, it sends an HTTP POST request to the partner's registered `callback_url` with the results. The partner does not poll Sentinel — Sentinel calls them.

**What Sentinel sends to the partner's webhook URL:**

```http
POST https://theirsite.com/sentinel-results
Content-Type: application/json
X-Sentinel-Signature: hmac_sha256_of_body_signed_with_shared_secret
X-Sentinel-Job-Id: job_abc123
```

```json
{
  "job_id": "job_abc123",
  "game_id": "partner-internal-id",
  "player_id": "username",
  "status": "complete",
  "risk_level": "ELEVATED",
  "risk_score": 0.84,
  "summary": "Statistical analysis identified move quality significantly exceeding the expected range for this rating band. Behavioral signals including focus loss before critical moves and above-average mouse path straightness reinforce the statistical findings. This is not a cheating determination — human review by a qualified arbiter is recommended.",
  "signals": {
    "engine_match_pct": 94.2,
    "maia_humanness_score": 0.31,
    "avg_centipawn_loss": 8.4,
    "timing_anomaly": true,
    "tab_switch_count": 3,
    "focus_loss_before_critical_moves": 2,
    "avg_mouse_path_straightness": 0.96,
    "copy_paste_events": 0
  },
  "flagged_moves": [14, 21, 27, 33],
  "report_url": "https://sentinel.yourdomain.com/reports/job_abc123",
  "timestamp": "2026-03-19T14:23:00Z"
}
```

**Signature verification:** Generate the `X-Sentinel-Signature` as `HMAC-SHA256(raw_json_body, partner_shared_secret)`. The partner uses this to verify the webhook is genuinely from Sentinel and has not been tampered with. The shared secret is given to the partner when they register their API key.

**Retry logic:** If the partner's server returns anything other than `200 OK`, retry the webhook 3 times with exponential backoff — 30 seconds, then 5 minutes, then 30 minutes. After 3 failed attempts mark the delivery as `failed` in the `partner_jobs` table and log it. Never drop a result silently.

---

### Component 4 — WebSocket live stream for hybrid mode

**What it is:** For the hybrid scenario where a game is happening on a partner site and an arbiter wants to monitor it live on the Sentinel dashboard simultaneously. The SDK streams every event in real time over a persistent WebSocket connection instead of waiting for game end.

**How the WebSocket session works end to end:**

**Step 1 — Partner starts a hybrid game.** The partner calls `POST /v1/partner/session/create` with their API key and a `game_id`. Sentinel creates a record in `live_sessions` and returns a `session_id`.

**Step 2 — SDK opens the socket.** When `data-mode="hybrid"` is set, the SDK opens a WebSocket connection to `wss://sentinel.yourdomain.com/ws/live/{session_id}` immediately when the game starts.

**Step 3 — SDK streams events.** Every event the SDK collects is immediately emitted over the socket as a JSON packet instead of being buffered:

```json
{ "session_id": "abc123", "type": "mouse",      "x": 412, "y": 308, "t": 1700000010123, "velocity": 2.4 }
{ "session_id": "abc123", "type": "move",        "uci": "e2e4", "san": "e4", "fen": "...", "clock": 174.3, "t": 1700000015000 }
{ "session_id": "abc123", "type": "blur",        "t": 1700000020000 }
{ "session_id": "abc123", "type": "focus",       "t": 1700000024200, "duration_ms": 4200 }
{ "session_id": "abc123", "type": "click",       "x": 412, "y": 308, "t": 1700000010500 }
{ "session_id": "abc123", "type": "copy",        "t": 1700000022500 }
{ "session_id": "abc123", "type": "premove",     "t": 1700000012000 }
{ "session_id": "abc123", "type": "disconnect",  "t": 1700000050000 }
{ "session_id": "abc123", "type": "ping",        "latency_ms": 42, "t": 1700000030000 }
```

**Step 4 — Arbiter attaches on the Sentinel dashboard.** The arbiter opens the Live Monitor page on our dashboard and enters or scans the `session_id`. The dashboard opens its own WebSocket connection to the same session endpoint and starts receiving the streamed packets.

**Step 5 — Dashboard renders live.** As packets arrive the dashboard updates in real time:
- A chessboard that advances position on every `move` packet
- A mouse heatmap that lights up where the cursor is moving on the partner site
- A behavioral event log showing every blur, focus, copy, and disconnect with timestamps and the ply that was active
- A rolling risk indicator that recalculates every 10 moves and shows `LOW / MODERATE / ELEVATED / HIGH` — this is for arbiter awareness only, not a decision
- A timeline showing move number on the x-axis with think time, mouse straightness, and behavioral events overlaid

**Step 6 — Game ends.** When the SDK detects game end it sends a `{ "type": "game_end", "pgn": "..." }` packet and closes the socket. The Sentinel backend automatically queues the full job for complete post-game analysis exactly as it would in standard mode. The arbiter can then view the full analysis report on the same case.

**WebSocket server requirements:**
- Use `fastapi-websocket` or a dedicated WebSocket server alongside the existing FastAPI app
- Each session channel is isolated — only the SDK client and authenticated Sentinel dashboard clients can join a session
- Authenticate the arbiter dashboard connection using their Sentinel session token
- Handle reconnection gracefully — if the SDK drops and reconnects, resume streaming to the same session
- Store all streamed packets to the `live_sessions` table for post-game analysis even if the arbiter was not watching live

---

### How all four components connect

```
Partner site                Sentinel server              Arbiter dashboard
────────────                ───────────────              ─────────────────

SDK collects data
      │
      │  (standard mode)
      ├──POST /v1/partner/analyze──►  validate API key
      │                               queue job
      │◄──202 Accepted + job_id ──────
      │
      │                               background worker runs
      │                               full analysis pipeline
      │
      │◄──POST to callback_url ───────  webhook with results
      │   (outgoing webhook)
      │
      │
      │  (hybrid mode)
      ├──WebSocket connect ──────────► session channel opens
      │  wss://.../ws/live/SESSION_ID
      │
      │  stream events live ─────────► broadcast to arbiter dashboard
      │  every 100ms                    live board + heatmap + risk indicator
      │
      │  game ends                      queue full post-game analysis job
      └──POST /v1/partner/analyze ────► same pipeline as standard mode
```

---

### Summary of everything to build

| What | Type | Purpose |
|---|---|---|
| `sentinel.js` | JavaScript file | Embeds on partner site, collects all player data |
| `POST /v1/partner/analyze` | REST endpoint | Receives SDK payload, queues analysis job |
| `GET /v1/partner/result/{job_id}` | REST endpoint | Optional poll for result status |
| `POST /v1/partner/session/create` | REST endpoint | Creates hybrid session, returns session_id |
| Background worker | Python async task | Runs full Sentinel analysis pipeline |
| Outgoing webhook | HTTP POST from Sentinel | Delivers results to partner callback URL |
| HMAC signature | Security layer | Verifies webhook authenticity |
| Webhook retry logic | Background task | 3 retries with exponential backoff |
| WebSocket server | `wss://` endpoint | Streams live events from SDK to arbiter |
| Live monitor page | Sentinel dashboard UI | Arbiter attaches to session, sees live board and heatmap |
| `partner_api_keys` table | Database | Stores partner keys, webhook URLs, rate limits |
| `partner_jobs` table | Database | Stores all submitted jobs and results |
| `live_sessions` table | Database | Stores hybrid session records and streamed packets |
| API key management UI | Sentinel admin UI | Partners register and manage their keys |
| Rate limiting | Redis | Protects API from abuse per partner key |

---

These four components are plumbing that feeds new data sources into the existing pipeline and routes results back out to partners. The engine treats online behavioral data as additional signal inputs on top of PGN — it does not replace PGN analysis.