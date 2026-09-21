Screen 1 — Arbiter dashboard (home)
This is the first screen an arbiter sees. It shows the current state of all activity.
Top KPI bar — 4 stat cards side by side:

Total games analyzed today — from summary.total_games_analyzed_today
Games elevated or above — from summary.games_elevated_or_above
Awaiting review — from summary.awaiting_review_count
Average Regan Z score today — from summary.average_regan_z_score, shown as a number with a color accent based on severity

Alert feed — scrollable list, most recent first:
Each alert from alerts[] shows: player ID as a monospace chip, risk layer name (alerts[].layer), score as a horizontal bar, threshold as a small number, description as text, timestamp formatted as relative time. Color the left border of each alert card by severity.
Recent games table — sortable:
Columns: player ID, event ID, risk tier badge (color-coded), weighted risk score as a mini horizontal bar, sparkline chart of per-game anomaly trend (games[].sparkline), move count, confidence as a percentage, created at timestamp. Clicking any row navigates to the Analysis Detail screen for that audit.
System status strip — fixed at bottom:
Show green/amber/red indicators for: Stockfish engine (engine.exists), Maia models (maia.available_count — show count), ML models (ml_fusion.models_loaded), Supabase (supabase_configured), calibration profile (calibration.valid). If any indicator is red or amber show a warning icon. Clicking opens the System Status screen.

Screen 2 — Analysis detail
This is the primary arbiter working screen. It opens when an arbiter clicks a game from the dashboard or completes an analysis.
Header bar:
Player ID (monospace, large), risk tier badge (large, color-coded), weighted risk score as a gauge 0–1, confidence percentage, audit ID (monospace, small, copy button), event ID, report version, report locked indicator (padlock icon).
Natural occurrence statement:
Full-width highlighted text block showing natural_occurrence_statement — this is the plain-English odds statement. Style it prominently — it is the most important single piece of text in the system. Below it show natural_occurrence_probability as a small scientific notation number.
Human explanations:
Show human_explanations as a bulleted list of plain-English findings. Each bullet prefixed with a severity icon.
Legal disclaimer:
Show legal_disclaimer_text in a bordered box with a muted style — always visible, never hidden.
Tab layout — 6 tabs:
Tab 1: Board replay
A full interactive chess board using react-chessboard. Left panel shows the move list table with columns: ply number, player move in SAN, engine best move in SAN, centipawn loss (color-coded — 0 is green, >50 is red), top1 match indicator (checkmark or cross), top3 match indicator, complexity score as a small bar, Maia probability as a small bar, time spent in seconds, is_opening_book badge, is_tablebase badge, is_forced badge. Clicking any row advances the board to that position. The board shows the current FEN. Below the board show an eval bar (best_eval_cp) that updates per move. Highlight the played move and engine best move in different colors on the board when they differ.
Tab 2: Statistical charts
Six charts stacked vertically with labels:
Chart 1 — Move strength over game: line chart, x-axis is ply number, y-axis is implied_rating from move_strength[].implied_rating. Draw a horizontal reference line at the player's official ELO. Color the area above the line amber.
Chart 2 — Centipawn loss per move: bar chart, x-axis ply, y-axis cp_loss. Color bars green if 0-10, amber 10-50, red >50. Overlay a line showing running average.
Chart 3 — Engine vs Maia alignment: dual line chart per ply. One line for engine_vs_maia[].engine_alignment, one for engine_vs_maia[].maia_alignment. The gap between lines is the disagreement — shade it.
Chart 4 — Player consistency: line chart showing player_consistency[].variance per ply with player_consistency[].expected_band shown as a shaded reference band.
Chart 5 — Timing vs complexity: scatter plot with x-axis as timing_correlation[].complexity_score and y-axis as timing_correlation[].time_spent. A human player should show positive correlation — flat or negative correlation is suspicious. Draw a regression line.
Chart 6 — Suspicion heatmap: a horizontal timeline showing move ranges from suspicion_heatmap[]. Each segment colored by score intensity — low score is neutral, high score is red. Clicking a segment jumps the board to that move range.
Tab 3: Signal layers
Seven expandable cards, one per signal layer (Layer 1 through Layer 7). Each card shows: layer name, score as a horizontal progress bar with threshold marker, triggered badge (red if triggered, green if not), and an expandable list of reason strings. The reason strings are the most important arbiter-facing content — style them clearly as plain English findings, not technical labels.
Tab 4: ML fusion and explainability
Three panels side by side:
Panel 1 — ML scores: show ml_primary_score and ml_secondary_score as gauges, ml_fusion_source as a label, weighted risk score as a large gauge.
Panel 2 — Explainability: a horizontal bar chart of explainability_items[] sorted by contribution magnitude. Bars pointing right are risk-increasing (color amber/red), bars pointing left are risk-decreasing (color green). Feature name on y-axis, contribution value on x-axis. Label explainability_method above.
Panel 3 — Confidence intervals: a table showing four rows — engine_match_pct, top3_match_pct, avg_centipawn_loss, regan_z_score, pep_score — each with its point estimate and CI lower/upper bounds shown as an error bar.
Tab 5: Behavioral signals
Only show this tab if behavioral data exists.
KPI row: tab_switch_count, focus_loss_count, copy_paste_events, mouse_event_count — all as stat cards.
Behavioral metrics table: avg_move_time_seconds, avg_reaction_time_ms, avg_mouse_path_straightness, avg_hover_dwell_played_square_ms, avg_drag_duration_ms, avg_squares_visited — each with a reference range indicator showing whether the value is within normal human bounds.
Camera events section (if present): show event_count, face_missing_count, gaze_away_count, multiple_faces_count, low_light_count, motion_detected_count as a grid of KPI cards. Each with an icon and color coding — zero is green, any count above zero is amber or red.
Identity confidence section: show identity_confidence as a gauge. If identity_shared_device is true show a prominent red alert saying the device fingerprint has been seen across multiple player IDs.
Environmental metrics: show as a structured data panel.
Tab 6: Evidence report
The full evidence report as a structured document layout.
Top section: anomaly_score as a large gauge, anomaly_source label, risk tier badge.
Centipawn loss statistics: a mini table showing min, max, avg, median, variance in a 5-column row.
Position difficulty metrics: a table showing avg_position_complexity, avg_candidate_moves, avg_engine_gap_cp, avg_engine_rank, hard_best_move_rate, complexity_accuracy_ratio, critical_moment_accuracy, accuracy_in_complex_positions — all labeled in plain English.
Style fingerprint: style_deviation_score as a horizontal bar, style_baseline_games as a count.
Player anomaly trend: a mini sparkline of player_anomaly_scores across games, rolling average line, spike count badge, trend direction indicator (arrow up/down).
Analysis layers breakdown: a compact table showing each layer name, status badge, and key metrics.
Behavioral and environmental summaries if present.
Conclusion: the full conclusion text in a styled card.
Action bar — fixed at bottom of this screen:
Buttons: Generate Report (opens report modal), Add to Case (opens case selector), Lock Report (with confirmation), Add Note. Show report_version and report_locked_at timestamp.

Screen 3 — Generate report modal
Triggered from the analysis detail action bar.
Form fields: Report Type (dropdown — Technical, Arbiter, Legal/Committee), Export Format (PDF, JSON, CSV), Use AI narrative (toggle), AI Provider (dropdown — only shown if AI toggle is on), AI Model (text).
Preview panel on the right showing the narrative sections that will be generated: overview, methodology, findings, statistical_interpretation, behavioral_signals, limitations, conclusion — each as an expandable accordion showing the section body text.
Download button generates the file. Show a loading state during generation.

Screen 4 — Cases
Case list view:
Sortable table with columns: title, player IDs (as chips), status badge (Opened/Under Review/Analysis Completed/Escalated/Closed), priority badge, event ID, assigned to, created at, updated at. Filter bar at top: filter by status, priority, assigned to, event ID. Search by player ID or title.
Case detail view:
Header: title (editable), status workflow stepper (5 steps), priority badge, assigned to (editable), tags as chips.
Four column layout:
Column 1 — Notes feed: chronological list of case notes. Each note shows: note_type badge, author, timestamp, text body. Structured notes (JSON) shown as a collapsible key-value panel. Add note button at top.
Column 2 — Flags: list of auto and manual flags. Each flag shows: flag_type, severity badge, message, metadata key values (score, threshold, superhuman_move_rate, time_variance_anomaly_score, engine_maia_disagreement). Color border by severity.
Column 3 — Evidence locker: list of attached evidence items. Each shows: evidence_type badge, label, path or storage link, created at. Upload button to attach new evidence.
Column 4 — Linked analyses: list of analysis records linked to the case. Each shows audit ID (monospace), risk tier badge, weighted risk score bar, created at. Button to run a new analysis and link it.
Below the four columns: Reviews section showing case_reviews with reviewer, action, rationale, timestamp. Signoffs section showing case_signoffs with signer, role, decision, note, timestamp. Both as timeline feeds.

Screen 5 — Tournament dashboard
Header: Event ID, event type badge (OTB/Online), games count, analyzed move count, Regan Z score, PEP score, confidence intervals as error bars.
Player leaderboard table — sorted by avg_risk_score descending:
Columns: player ID, risk tier badge (color-coded), avg risk score as a horizontal bar, last analysis timestamp. Top 3 rows highlighted. Clicking a row opens that player's profile.
Alert list: tournament-level alerts showing message and score bar for each.
Per-game breakdown table:
Columns: game ID, analyzed move count, IPR estimate, PEP score, Regan Z score vs threshold (shown as ratio), risk tier badge. Clicking opens that game's analysis detail.
Cross-player comparison chart:
A scatter plot where each point is a player. X-axis is official ELO, Y-axis is weighted risk score. Points colored by risk tier. Hovering shows player ID and key metrics. Players above a risk threshold line are highlighted.

Screen 6 — Player profile
Header: Player ID, last risk tier badge, last weighted risk score bar, last event ID, last analyzed move count, profile updated at.
Risk history chart:
Line chart of weighted_risk_score over time across all historical snapshots. X-axis is created_at timestamp, Y-axis is score 0–1. Color the line by risk tier at each point. Draw a threshold reference line.
History table:
Each row is one analysis snapshot: event ID, risk tier badge, weighted risk score, analyzed move count, created at. Clicking opens that analysis detail.

Screen 7 — Live monitor
Session entry: text input for session_id, connect button.
Once connected:
Left panel — live chessboard:
Board updates position on every move packet received over WebSocket. Move list below the board showing ply, UCI move, clock remaining, engine match indicator, Maia probability, complexity score, time spent.
Right panel — live signals:
Rolling risk indicator badge (LOW/MODERATE/ELEVATED/HIGH) that recalculates every 10 moves from risk_score and risk_tier. Engine alignment average and Maia alignment average as gauges. Timing variance as a number with color coding.
Bottom panel — behavioral event log:
Chronological feed of all events received: move, blur, focus, copy, premove, disconnect, ping. Each entry shows event type badge, timestamp, and which ply was active. Copy/paste events shown in red. Focus loss events shown in amber with duration.
Live heatmap overlay:
A miniaturized board showing mouse position density as a heat overlay, updating in real time from mouse packets.
Notes panel from notes returned by the risk endpoint.

Screen 8 — OTB incident log
Incident list: sortable table showing player ID, incident type, severity badge, occurred at, description, event ID, case ID. Filter by incident type and severity.
Log new incident form: player ID, incident type dropdown (device detected, player left board, suspicious behavior, refused scan, other), severity dropdown, description text area, occurred at datetime picker, attach to case selector.
Camera events section: list of camera event records showing camera ID, player ID, session ID, storage mode badge, summary text, event count. Expandable to show individual events.
DGT board events section: table showing board serial, ply, move UCI, clock in ms, FEN (with a mini board preview on hover), session ID.

Screen 9 — Partner API management
API keys table: columns — partner name, key (masked, show last 4 digits), webhook URL, rate limit per minute as a bar showing usage vs limit, active badge, created at. Actions: copy key, rotate key, deactivate, delete.
Create new key form: partner name, webhook URL, rate limit per minute.
Partner jobs table: columns — job ID (monospace), partner name, game ID, player ID, status badge, risk level badge, risk score bar, webhook delivered badge, webhook attempts count, created at, completed at. Clicking opens the full result JSON in a collapsible inspector.
Webhook delivery log: for each job show attempt count, delivered boolean, and a retry button if delivery failed.

Screen 10 — System status
Engine status grid: each system component as a status card with green/amber/red indicator:

Stockfish: path, exists boolean
Maia: lc0 path, available bucket count, available buckets list, version
ML models: primary loaded, secondary loaded, enabled toggle, min moves threshold, weight distribution (heuristic/primary/secondary) as a small pie chart
Calibration: profile version, band count, coverage min/max ELO, source, QA status (ok boolean, failed checks list, alert counts)
Opening book: exists
Tablebase: exists
Supabase: configured boolean
Redis: URL configured boolean
Analysis pipeline: operational boolean

Warnings list: show all warnings[] as amber alert cards.
Version info footer: app env, model version, feature schema version, report schema version, generated at timestamp.

Screen 11 — Demo mode
This is the public-facing entry point requiring no authentication.
Single card layout:
PGN text area (large, paste or upload), player color selector (White/Black), player ID field, official ELO field, event type selector (Online/OTB), high stakes toggle.
Submit button labeled "Analyze" with a loading state.
On completion render a condensed version of the Analysis Detail screen — board replay tab, statistical charts tab, signal layers tab, and the natural occurrence statement prominently at the top. Include a "Generate Report" button. Do not show case management features in demo mode.

Global navigation
Left sidebar with icons and labels: Dashboard, Cases, Tournament, Player Profile (search), Live Monitor, OTB Incidents, Partner API, System Status, Demo Mode.
Top bar: federation ID display, role badge (arbiter/chief_arbiter/federation_admin/system_admin), user display name.
All player IDs, audit IDs, and job IDs everywhere in the UI must be monospace with a one-click copy button. No exceptions.