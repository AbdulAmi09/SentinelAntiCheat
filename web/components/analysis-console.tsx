"use client";

import { FormEvent, useMemo, useState } from "react";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Cell, ReferenceLine,
} from "recharts";

// ─── Types ────────────────────────────────────────────────────────────────────

type Signal = {
  name: string;
  triggered: boolean;
  score: number;
  threshold: number;
  reasons: string[];
};

type ExplainabilityItem = {
  feature: string;
  contribution: number;
  direction: string;
};

type AnalyzeResponse = {
  player_id: string;
  event_id: string;
  risk_tier: string;
  confidence: number;
  analyzed_move_count: number;
  triggered_signals: number;
  weighted_risk_score: number;
  signals: Signal[];
  explanation: string[];
  audit_id: string;
  persisted_to_supabase: boolean;
  natural_occurrence_statement?: string;
  natural_occurrence_probability?: number | null;
  regan_z_score?: number | null;
  regan_threshold?: number | null;
  pep_score?: number | null;
  superhuman_move_rate?: number | null;
  rating_adjusted_move_probability?: number | null;
  opening_familiarity_index?: number | null;
  opponent_strength_correlation?: number | null;
  round_anomaly_clustering_score?: number | null;
  complex_blunder_rate?: number | null;
  zero_blunder_in_complex_games_flag?: boolean | null;
  move_quality_uniformity_score?: number | null;
  time_variance_anomaly_score?: number | null;
  time_clustering_anomaly_flag?: boolean | null;
  break_timing_correlation?: number | null;
  timing_confidence_score?: number | null;
  stockfish_maia_divergence?: number | null;
  maia_humanness_score?: number | null;
  maia_personalization_confidence?: number | null;
  maia_model_version?: string | null;
  rolling_12m_weighted_acl?: number | null;
  historical_volatility_score?: number | null;
  opponent_pool_adjustment?: number | null;
  multi_tournament_anomaly_score?: number | null;
  career_growth_curve_score?: number | null;
  ml_fusion_source?: string | null;
  ml_primary_score?: number | null;
  ml_secondary_score?: number | null;
  explainability_method?: string | null;
  explainability_items?: ExplainabilityItem[];
  legal_disclaimer_text?: string | null;
  legal_disclaimer_enforced?: boolean;
  report_version?: number;
  report_locked?: boolean;
  report_locked_at?: string | null;
  confidence_intervals?: Record<string, [number, number] | null>;
};

type TournamentGameSummary = {
  game_id: string;
  analyzed_move_count: number;
  ipr_estimate: number;
  pep_score: number;
  regan_z_score: number;
  regan_threshold: number;
};

type TournamentSummaryResponse = {
  player_id: string;
  event_id: string;
  event_type: string;
  games_count: number;
  analyzed_move_count: number;
  ipr_estimate: number;
  pep_score: number;
  regan_z_score: number;
  regan_threshold: number;
  confidence_intervals?: Record<string, [number, number] | null>;
  per_game: TournamentGameSummary[];
};

type Props = {
  apiBase: string;
  apiRole: string;
  apiFederationId: string;
};

// ─── Constants ────────────────────────────────────────────────────────────────

const SAMPLE_PGN = `[Event "Test Event"]
[Site "Online"]
[Date "2026.03.01"]
[Round "1"]
[White "Player A"]
[Black "Player B"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 1-0`;

const RISK_COLORS: Record<string, string> = {
  HIGH_STATISTICAL_ANOMALY: "#ef4444",
  ELEVATED: "#f97316",
  MODERATE: "#eab308",
  LOW: "#22c55e",
};

const getRiskColor = (tier: string) => RISK_COLORS[tier] ?? "#64748b";

// ─── Shared style helpers ─────────────────────────────────────────────────────

const mono: React.CSSProperties = { fontFamily: "var(--font-mono, 'DM Mono', monospace)" };

function prettyLabel(value: string) {
  return value
    .replace(/_/g, " ")
    .replace(/\b[a-z]/g, (char) => char.toUpperCase())
    .replace(/\bAcl\b/g, "ACL")
    .replace(/\bIpr\b/g, "IPR")
    .replace(/\bRegan Z Score\b/g, "Regan Z Score")
    .replace(/\bMl\b/g, "ML");
}

function formatSigned(value: number, digits = 3) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(digits)}`;
}

function label(text: string) {
  return (
    <div style={{
      ...mono, fontSize: "0.58rem", letterSpacing: "0.12em", textTransform: "uppercase",
      color: "#475569", marginBottom: 4,
    }}>{text}</div>
  );
}

function inputStyle(focused = false): React.CSSProperties {
  return {
    ...mono, fontSize: "0.72rem", width: "100%",
    background: focused ? "#0a0e18" : "#070a10",
    border: `1px solid ${focused ? "rgba(59,130,246,0.4)" : "rgba(99,130,170,0.15)"}`,
    borderRadius: 3, color: "#cbd5e1", padding: "7px 10px",
    outline: "none", transition: "border-color 0.15s",
  };
}

function ChartTooltip({ active, payload, label: lbl }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "#0d1117", border: "1px solid rgba(99,130,170,0.2)",
      borderRadius: 4, padding: "8px 12px", fontSize: "0.65rem", ...mono,
    }}>
      <div style={{ color: "#64748b", marginBottom: 3 }}>{lbl}</div>
      {payload.map((p: any) => (
        <div key={p.name} style={{ color: p.color || "#e2e8f0" }}>
          {p.name}: <strong>{typeof p.value === "number" ? p.value.toFixed(3) : p.value}</strong>
        </div>
      ))}
    </div>
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function StatBox({ lbl, val, sub, color }: { lbl: string; val: string | number; sub?: string; color?: string }) {
  return (
    <div style={{
      background: "rgba(6,8,16,0.7)", border: "1px solid rgba(99,130,170,0.1)",
      borderRadius: 4, padding: "12px 14px", display: "flex", flexDirection: "column", gap: 2,
    }}>
      <div style={{ ...mono, fontSize: "0.57rem", letterSpacing: "0.12em", color: "#475569", textTransform: "uppercase" }}>{lbl}</div>
      <div style={{ ...mono, fontSize: "1.1rem", fontWeight: 600, color: color ?? "#e2e8f0", lineHeight: 1 }}>{val}</div>
      {sub && <div style={{ ...mono, fontSize: "0.58rem", color: "#334155", marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

function MetricStrip({
  label,
  value,
  display,
  min = 0,
  max = 1,
  center,
  color = "#60a5fa",
}: {
  label: string;
  value: number;
  display: string;
  min?: number;
  max?: number;
  center?: number;
  color?: string;
}) {
  const pct = Math.max(0, Math.min(100, ((value - min) / Math.max(max - min, 1e-9)) * 100));
  const centerPct = center == null ? null : Math.max(0, Math.min(100, ((center - min) / Math.max(max - min, 1e-9)) * 100));

  return (
    <div style={{
      display: "grid",
      gap: 6,
      padding: "9px 10px",
      borderRadius: 4,
      background: "rgba(99,130,170,0.04)",
      border: "1px solid rgba(99,130,170,0.08)",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center" }}>
        <span style={{ ...mono, fontSize: "0.61rem", color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.08em" }}>{label}</span>
        <span style={{ ...mono, fontSize: "0.66rem", color: color }}>{display}</span>
      </div>
      <div style={{ position: "relative", height: 6, borderRadius: 999, background: "rgba(15,23,42,0.9)", overflow: "hidden" }}>
        {centerPct != null ? (
          <span style={{
            position: "absolute",
            left: `${centerPct}%`,
            top: -2,
            width: 1,
            height: 10,
            background: "rgba(226,232,240,0.5)",
          }} />
        ) : null}
        <span style={{
          display: "block",
          height: "100%",
          width: `${pct}%`,
          borderRadius: 999,
          background: `linear-gradient(90deg, ${color}70, ${color})`,
        }} />
      </div>
    </div>
  );
}

function MetricGroup({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section style={{
      background: "rgba(6,8,16,0.55)",
      border: "1px solid rgba(99,130,170,0.1)",
      borderRadius: 5,
      padding: "12px 14px",
      display: "grid",
      gap: 10,
    }}>
      <div style={{
        ...mono,
        fontSize: "0.58rem",
        letterSpacing: "0.12em",
        textTransform: "uppercase",
        color: "#475569",
      }}>
        {title}
      </div>
      <div style={{ display: "grid", gap: 8 }}>
        {children}
      </div>
    </section>
  );
}

function SignalBar({ signal }: { signal: Signal }) {
  const pct = Math.min(signal.score / (signal.threshold * 2), 1) * 100;
  const thresholdPct = Math.min(signal.threshold / (signal.threshold * 2), 1) * 100;
  const color = signal.triggered ? "#ef4444" : "#22c55e";
  const [open, setOpen] = useState(false);

  return (
    <div style={{
      background: signal.triggered ? "rgba(239,68,68,0.04)" : "rgba(6,8,16,0.5)",
      border: `1px solid ${signal.triggered ? "rgba(239,68,68,0.18)" : "rgba(99,130,170,0.08)"}`,
      borderRadius: 4, padding: "10px 14px", cursor: "pointer",
      transition: "background 0.15s",
    }} onClick={() => setOpen(o => !o)}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{
            width: 6, height: 6, borderRadius: "50%", background: color,
            boxShadow: signal.triggered ? `0 0 6px ${color}` : "none", flexShrink: 0,
          }} />
          <span style={{ ...mono, fontSize: "0.68rem", color: "#cbd5e1", fontWeight: 500 }}>{signal.name}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ ...mono, fontSize: "0.6rem", color: color, fontWeight: 700 }}>
            {signal.score.toFixed(3)}
          </span>
          <span style={{ ...mono, fontSize: "0.55rem", color: "#334155" }}>/ {signal.threshold.toFixed(3)}</span>
          <span style={{
            ...mono, fontSize: "0.52rem", letterSpacing: "0.1em", padding: "2px 6px", borderRadius: 2,
            background: signal.triggered ? "rgba(239,68,68,0.15)" : "rgba(34,197,94,0.12)",
            color, border: `1px solid ${color}30`,
          }}>{signal.triggered ? "TRIGGERED" : "PASS"}</span>
          <span style={{ ...mono, fontSize: "0.55rem", color: "#334155" }}>{open ? "▴" : "▾"}</span>
        </div>
      </div>

      {/* Progress bar */}
      <div style={{ position: "relative", height: 3, background: "rgba(99,130,170,0.08)", borderRadius: 2, overflow: "visible" }}>
        <div style={{
          position: "absolute", left: 0, top: 0, height: "100%", borderRadius: 2,
          width: `${pct}%`, background: `linear-gradient(90deg, ${color}50, ${color})`,
          transition: "width 0.6s ease",
        }} />
        <div style={{
          position: "absolute", top: -3, width: 1, height: 9, background: "#eab308",
          left: `${thresholdPct}%`,
        }} />
      </div>

      {open && signal.reasons.length > 0 && (
        <ul style={{ marginTop: 10, paddingLeft: 14, display: "flex", flexDirection: "column", gap: 4 }}>
          {signal.reasons.map(r => (
            <li key={r} style={{ ...mono, fontSize: "0.65rem", color: "#64748b", lineHeight: 1.4 }}>{r}</li>
          ))}
        </ul>
      )}
      {open && signal.reasons.length === 0 && (
        <div style={{ ...mono, fontSize: "0.62rem", color: "#334155", marginTop: 8 }}>No additional signal reasons.</div>
      )}
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export function AnalysisConsole({ apiBase, apiRole, apiFederationId }: Props) {
  const [playerId, setPlayerId] = useState("fide-123");
  const [eventId, setEventId] = useState("event-2026-03");
  const [opponentId, setOpponentId] = useState("opponent-unknown");
  const [elo, setElo] = useState("1820");
  const [eventType, setEventType] = useState<"online" | "otb">("online");
  const [playerColor, setPlayerColor] = useState<"white" | "black">("white");
  const [pgnText, setPgnText] = useState(SAMPLE_PGN);
  const [highStakes, setHighStakes] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [summary, setSummary] = useState<TournamentSummaryResponse | null>(null);
  const [activeTab, setActiveTab] = useState<"signals" | "metrics" | "tournament" | "audit">("signals");
  const [focusedField, setFocusedField] = useState<string | null>(null);

  const endpoint = useMemo(() => `${apiBase}/v1/analyze-pgn`, [apiBase]);
  const summaryEndpoint = useMemo(() => `${apiBase}/v1/tournament-summary`, [apiBase]);
  const apiHeaders = useMemo(() => {
    const headers: Record<string, string> = {
      "X-Role": apiRole,
    };
    if (apiFederationId) headers["X-Federation-Id"] = apiFederationId;
    return headers;
  }, [apiRole, apiFederationId]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    setSummary(null);

    try {
      const payload = {
        player_id: playerId.trim(),
        event_id: eventId.trim(),
        opponent_player_id: opponentId.trim() || "opponent-unknown",
        official_elo: Number(elo),
        event_type: eventType,
        player_color: playerColor,
        high_stakes_event: highStakes,
        pgn_text: pgnText,
        historical: { games_count: 0 },
      };

      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...apiHeaders },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { detail?: string };
        throw new Error(body.detail || `Request failed: ${res.status}`);
      }

      const data = (await res.json()) as AnalyzeResponse;
      setResult(data);
      setActiveTab("signals");

      const summaryRes = await fetch(summaryEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...apiHeaders },
        body: JSON.stringify(payload),
      });
      if (summaryRes.ok) {
        setSummary((await summaryRes.json()) as TournamentSummaryResponse);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  // Chart data derived from result
  const radarData = result?.signals.map(s => ({
    name: s.name.replace("Layer ", "L").split(":")[0].trim(),
    score: s.score,
    threshold: s.threshold,
  })) ?? [];

  const barData = result?.signals.map(s => ({
    name: s.name.split(":")[0].trim(),
    score: s.score,
    threshold: s.threshold,
    triggered: s.triggered,
  })) ?? [];

  const explainabilityData = (result?.explainability_items ?? [])
    .map((item) => ({
      ...item,
      label: prettyLabel(item.feature),
      fill: item.contribution >= 0 ? "#f97316" : "#22c55e",
    }))
    .sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));

  const confidenceIntervalData = Object.entries(result?.confidence_intervals ?? {})
    .filter((entry): entry is [string, [number, number]] => Array.isArray(entry[1]))
    .map(([metric, bounds]) => ({
      metric,
      label: prettyLabel(metric),
      low: bounds[0],
      high: bounds[1],
      span: bounds[1] - bounds[0],
      midpoint: (bounds[0] + bounds[1]) / 2,
    }));

  const riskColor = result ? getRiskColor(result.risk_tier) : "#64748b";

  const metricGroups = result ? [
    {
      title: "Move Quality And Context",
      items: [
        { label: "Superhuman Move Rate", value: result.superhuman_move_rate ?? 0, display: (result.superhuman_move_rate ?? 0).toFixed(3), min: 0, max: 1, center: 0.2, color: "#f97316" },
        { label: "Rating-Adjusted Probability", value: result.rating_adjusted_move_probability ?? 0, display: (result.rating_adjusted_move_probability ?? 0).toFixed(3), min: 0, max: 3, center: 1, color: "#60a5fa" },
        { label: "Uniformity Score", value: result.move_quality_uniformity_score ?? 0, display: (result.move_quality_uniformity_score ?? 0).toFixed(3), min: 0, max: 1, center: 0.7, color: "#a78bfa" },
        { label: "Opening Familiarity", value: result.opening_familiarity_index ?? 0, display: (result.opening_familiarity_index ?? 0).toFixed(3), min: 0, max: 1, center: 0.5, color: "#38bdf8" },
        { label: "Opponent Strength Correlation", value: result.opponent_strength_correlation ?? 0, display: formatSigned(result.opponent_strength_correlation ?? 0), min: -1, max: 1, center: 0, color: "#f59e0b" },
        { label: "Complex Blunder Rate", value: result.complex_blunder_rate ?? 0, display: (result.complex_blunder_rate ?? 0).toFixed(3), min: 0, max: 1, center: 0.2, color: "#ef4444" },
      ],
    },
    {
      title: "Timing And Rhythm",
      items: [
        { label: "Time Variance Anomaly", value: result.time_variance_anomaly_score ?? 0, display: (result.time_variance_anomaly_score ?? 0).toFixed(3), min: 0, max: 2, center: 0.75, color: "#fb7185" },
        { label: "Timing Confidence", value: result.timing_confidence_score ?? 0, display: (result.timing_confidence_score ?? 0).toFixed(3), min: 0, max: 1, center: 0.6, color: "#22c55e" },
        { label: "Break-Time Correlation", value: result.break_timing_correlation ?? 0, display: formatSigned(result.break_timing_correlation ?? 0), min: -1, max: 1, center: 0, color: "#06b6d4" },
        { label: "Time Clustering Flag", value: result.time_clustering_anomaly_flag ? 1 : 0, display: result.time_clustering_anomaly_flag ? "YES" : "NO", min: 0, max: 1, color: result.time_clustering_anomaly_flag ? "#ef4444" : "#22c55e" },
      ],
    },
    {
      title: "Maia And Historical",
      items: [
        { label: "SF-Maia Divergence", value: result.stockfish_maia_divergence ?? 0, display: (result.stockfish_maia_divergence ?? 0).toFixed(3), min: 0, max: 1, center: 0.16, color: "#f97316" },
        { label: "Maia Humanness", value: result.maia_humanness_score ?? 0, display: (result.maia_humanness_score ?? 0).toFixed(3), min: 0, max: 1, center: 0.5, color: "#22c55e" },
        { label: "Maia Personalization", value: result.maia_personalization_confidence ?? 0, display: (result.maia_personalization_confidence ?? 0).toFixed(3), min: 0, max: 1, center: 0.4, color: "#8b5cf6" },
        { label: "Rolling 12M ACL", value: result.rolling_12m_weighted_acl ?? 0, display: (result.rolling_12m_weighted_acl ?? 0).toFixed(3), min: 0, max: 150, center: 50, color: "#60a5fa" },
        { label: "Historical Volatility", value: result.historical_volatility_score ?? 0, display: (result.historical_volatility_score ?? 0).toFixed(3), min: 0, max: 2, center: 0.7, color: "#f43f5e" },
        { label: "Career Growth Curve", value: result.career_growth_curve_score ?? 0, display: formatSigned(result.career_growth_curve_score ?? 0), min: -2, max: 2, center: 0, color: "#14b8a6" },
        { label: "Multi-Tournament Anomaly", value: result.multi_tournament_anomaly_score ?? 0, display: (result.multi_tournament_anomaly_score ?? 0).toFixed(3), min: 0, max: 1.5, center: 1, color: "#eab308" },
      ],
    },
    {
      title: "Fusion Outputs",
      items: [
        { label: "ML Primary Score", value: result.ml_primary_score ?? 0, display: result.ml_primary_score != null ? result.ml_primary_score.toFixed(3) : "N/A", min: 0, max: 1, center: 0.5, color: "#60a5fa" },
        { label: "ML Secondary Score", value: result.ml_secondary_score ?? 0, display: result.ml_secondary_score != null ? result.ml_secondary_score.toFixed(3) : "N/A", min: 0, max: 1, center: 0.5, color: "#f59e0b" },
        { label: "Round Clustering", value: result.round_anomaly_clustering_score ?? 0, display: (result.round_anomaly_clustering_score ?? 0).toFixed(3), min: 0, max: 1, center: 0.18, color: "#f97316" },
        { label: "Opponent Pool Adjustment", value: result.opponent_pool_adjustment ?? 0, display: formatSigned(result.opponent_pool_adjustment ?? 0), min: -1, max: 1, center: 0, color: "#38bdf8" },
      ],
    },
  ] : [];

  // Shared field focus handlers
  const fo = (f: string) => () => setFocusedField(f);
  const fb = () => setFocusedField(null);

  const selectStyle: React.CSSProperties = {
    ...inputStyle(), appearance: "none", cursor: "pointer",
    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12'%3E%3Cpath fill='%2364748b' d='M2 4l4 4 4-4'/%3E%3C/svg%3E")`,
    backgroundRepeat: "no-repeat", backgroundPosition: "right 8px center", backgroundSize: "12px",
  };

  return (
    <>
      <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>

        {/* ─── Endpoint badge ────────────────────────────────────────────── */}
        <div style={{
          display: "flex", alignItems: "center", gap: 8, padding: "8px 0 14px",
          borderBottom: "1px solid rgba(99,130,170,0.1)", marginBottom: 14,
        }}>
          <span style={{
            ...mono, fontSize: "0.55rem", letterSpacing: "0.1em", padding: "2px 7px",
            borderRadius: 2, background: "rgba(59,130,246,0.1)", color: "#60a5fa",
            border: "1px solid rgba(59,130,246,0.2)", textTransform: "uppercase",
          }}>POST</span>
          <span style={{ ...mono, fontSize: "0.62rem", color: "#334155" }}>{endpoint}</span>
        </div>

        {/* ─── Form ─────────────────────────────────────────────────────── */}
        <form onSubmit={onSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>

          {/* Field grid */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 10 }}>
            {([
              { key: "playerId", lbl: "Player ID", val: playerId, set: setPlayerId, type: "text" },
              { key: "eventId", lbl: "Event ID", val: eventId, set: setEventId, type: "text" },
              { key: "opponentId", lbl: "Opponent ID", val: opponentId, set: setOpponentId, type: "text" },
              { key: "elo", lbl: "Official Elo", val: elo, set: setElo, type: "number" },
            ] as const).map(f => (
              <div key={f.key}>
                {label(f.lbl)}
                <input
                  className="ac-form-field"
                  value={f.val}
                  onChange={e => (f.set as (v: string) => void)(e.target.value)}
                  type={f.type}
                  required
                  onFocus={fo(f.key)}
                  onBlur={fb}
                  style={inputStyle(focusedField === f.key)}
                />
              </div>
            ))}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
            <div>
              {label("Event Type")}
              <select value={eventType} onChange={e => setEventType(e.target.value as "online" | "otb")} style={selectStyle}>
                <option value="online">Online</option>
                <option value="otb">OTB</option>
              </select>
            </div>
            <div>
              {label("Player Color")}
              <select value={playerColor} onChange={e => setPlayerColor(e.target.value as "white" | "black")} style={selectStyle}>
                <option value="white">White</option>
                <option value="black">Black</option>
              </select>
            </div>
            <div>
              {label("High-Stakes Event")}
              <select value={highStakes ? "yes" : "no"} onChange={e => setHighStakes(e.target.value === "yes")} style={selectStyle}>
                <option value="yes">Yes</option>
                <option value="no">No</option>
              </select>
            </div>
          </div>

          <div>
            {label("PGN Text")}
            <textarea
              className="ac-form-field"
              value={pgnText}
              onChange={e => setPgnText(e.target.value)}
              rows={9}
              required
              onFocus={fo("pgn")}
              onBlur={fb}
              placeholder="Paste one or more PGN games here…"
              style={{
                ...inputStyle(focusedField === "pgn"),
                resize: "vertical", lineHeight: 1.6,
              }}
            />
          </div>

          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <button
              type="submit"
              disabled={loading}
              className="ac-submit"
              style={{
                ...mono, fontSize: "0.65rem", letterSpacing: "0.1em", textTransform: "uppercase",
                fontWeight: 600, padding: "9px 20px", border: "1px solid rgba(59,130,246,0.35)",
                borderRadius: 3, background: "rgba(59,130,246,0.12)", color: "#60a5fa",
                cursor: "pointer", transition: "all 0.15s", display: "flex", alignItems: "center", gap: 8,
              }}
            >
              {loading ? (
                <>
                  <span style={{
                    display: "inline-block", width: 10, height: 10, border: "1.5px solid #60a5fa",
                    borderTopColor: "transparent", borderRadius: "50%",
                    animation: "spin 0.7s linear infinite",
                  }} />
                  Analyzing…
                </>
              ) : "▶ Run Engine Analysis"}
            </button>
            <button
              type="button"
              className="ac-secondary"
              onClick={() => setPgnText(SAMPLE_PGN)}
              style={{
                ...mono, fontSize: "0.62rem", letterSpacing: "0.1em", textTransform: "uppercase",
                padding: "9px 16px", border: "1px solid rgba(99,130,170,0.15)",
                borderRadius: 3, background: "transparent", color: "#64748b", cursor: "pointer",
                transition: "all 0.15s",
              }}
            >
              Load Sample
            </button>
          </div>
        </form>

        {/* ─── Error ─────────────────────────────────────────────────────── */}
        {error && (
          <div style={{
            marginTop: 14, padding: "10px 14px", borderRadius: 4,
            background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)",
            ...mono, fontSize: "0.68rem", color: "#ef4444",
          }}>
            ⚠ {error}
          </div>
        )}

        {/* ─── Result Panel ──────────────────────────────────────────────── */}
        {result && (
          <div style={{
            marginTop: 16, display: "flex", flexDirection: "column", gap: 14,
            animation: "slideIn 0.25s ease"
          }}>

            {/* Risk Tier Banner */}
            <div style={{
              padding: "16px 20px", borderRadius: 5,
              background: `${riskColor}0d`,
              border: `1px solid ${riskColor}30`,
              display: "flex", alignItems: "center", justifyContent: "space-between",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                <div style={{
                  width: 10, height: 10, borderRadius: "50%", background: riskColor,
                  boxShadow: `0 0 10px ${riskColor}`,
                  animation: result.risk_tier !== "LOW" ? "pulse 2s infinite" : "none",
                }} />
                <div>
                  <div style={{
                    ...mono, fontSize: "0.57rem", color: `${riskColor}90`,
                    letterSpacing: "0.14em", textTransform: "uppercase", marginBottom: 2
                  }}>Risk Tier</div>
                  <div style={{
                    ...mono, fontSize: "1.2rem", fontWeight: 700, color: riskColor,
                    letterSpacing: "0.08em"
                  }}>{result.risk_tier.replace(/_/g, " ")}</div>
                </div>
              </div>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <StatBox lbl="Weighted Risk" val={result.weighted_risk_score.toFixed(3)} color={riskColor} />
                <StatBox lbl="Confidence" val={result.confidence.toFixed(3)} />
                <StatBox lbl="Analyzed Moves" val={result.analyzed_move_count} />
                <StatBox lbl="Triggered Signals" val={`${result.triggered_signals} / ${result.signals.length}`}
                  color={result.triggered_signals > 0 ? "#f97316" : "#22c55e"} />
              </div>
            </div>

            {/* Secondary metrics */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
              <StatBox lbl="Regan Z-Score"
                val={result.regan_z_score != null ? result.regan_z_score.toFixed(3) : "n/a"}
                sub={`Threshold: ${result.regan_threshold?.toFixed(3) ?? "n/a"}`}
                color={result.regan_z_score != null && result.regan_threshold != null && result.regan_z_score > result.regan_threshold ? "#ef4444" : undefined}
              />
              <StatBox lbl="PEP Score"
                val={result.pep_score != null ? result.pep_score.toFixed(4) : "n/a"}
              />
              <StatBox lbl="Natural Occurrence"
                val={result.natural_occurrence_probability != null
                  ? result.natural_occurrence_probability.toExponential(2) : "n/a"}
                sub={result.natural_occurrence_statement?.slice(0, 60).concat("…") ?? undefined}
              />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
              <StatBox lbl="Explainability" val={result.explainability_method ?? "n/a"} />
              <StatBox lbl="ML Fusion Source" val={result.ml_fusion_source ?? "n/a"} />
              <StatBox lbl="Report Version" val={result.report_version ?? "n/a"} />
              <StatBox lbl="Report Locked" val={result.report_locked == null ? "n/a" : result.report_locked ? "yes" : "no"} />
            </div>
            <div style={{
              ...mono,
              fontSize: "0.66rem",
              color: "#64748b",
              padding: "8px 2px 2px",
            }}>
              Detailed phase metrics are grouped under the Metrics tab. Explainability drivers and audit material are grouped under Audit.
            </div>

            {/* Charts */}
            {result.signals.length > 0 && (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                {/* Radar */}
                <div style={{
                  background: "rgba(6,8,16,0.6)", border: "1px solid rgba(99,130,170,0.1)",
                  borderRadius: 5, padding: "12px 14px",
                }}>
                  <div style={{
                    ...mono, fontSize: "0.58rem", letterSpacing: "0.12em",
                    color: "#475569", textTransform: "uppercase", marginBottom: 8
                  }}>
                    ▸ Signal Radar — Score vs Threshold
                  </div>
                  <ResponsiveContainer width="100%" height={200}>
                    <RadarChart data={radarData}>
                      <PolarGrid stroke="rgba(99,130,170,0.1)" />
                      <PolarAngleAxis dataKey="name"
                        tick={{ fontSize: 8, fontFamily: "var(--font-mono, 'DM Mono', monospace)", fill: "#64748b" }} />
                      <Radar name="Score" dataKey="score" stroke={riskColor} fill={riskColor} fillOpacity={0.18} strokeWidth={2} />
                      <Radar name="Threshold" dataKey="threshold" stroke="#334155" fill="#334155"
                        fillOpacity={0.08} strokeDasharray="4 4" strokeWidth={1} />
                      <Tooltip content={<ChartTooltip />} />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>

                {/* Bar chart */}
                <div style={{
                  background: "rgba(6,8,16,0.6)", border: "1px solid rgba(99,130,170,0.1)",
                  borderRadius: 5, padding: "12px 14px",
                }}>
                  <div style={{
                    ...mono, fontSize: "0.58rem", letterSpacing: "0.12em",
                    color: "#475569", textTransform: "uppercase", marginBottom: 8
                  }}>
                    ▸ Score vs Threshold by Layer
                  </div>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={barData} layout="vertical" margin={{ top: 0, right: 20, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,130,170,0.06)" horizontal={false} />
                      <XAxis type="number" tick={{ fontSize: 8, fontFamily: "var(--font-mono, 'DM Mono', monospace)", fill: "#475569" }}
                        axisLine={false} tickLine={false} />
                      <YAxis type="category" dataKey="name" width={70}
                        tick={{ fontSize: 7, fontFamily: "var(--font-mono, 'DM Mono', monospace)", fill: "#475569" }}
                        axisLine={false} tickLine={false} />
                      <Tooltip content={<ChartTooltip />} />
                      <Bar dataKey="threshold" name="Threshold" fill="#1e293b" radius={[0, 2, 2, 0]} barSize={6} />
                      <Bar dataKey="score" name="Score" radius={[0, 2, 2, 0]} barSize={10}>
                        {barData.map((entry, i) => (
                          <Cell key={i} fill={entry.triggered ? "#ef4444" : "#22c55e"} fillOpacity={0.8} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {/* Confidence Intervals */}
            {result.confidence_intervals && (
              <div style={{
                background: "rgba(6,8,16,0.5)", border: "1px solid rgba(99,130,170,0.08)",
                borderRadius: 4, padding: "12px 14px",
              }}>
                <div style={{
                  ...mono, fontSize: "0.58rem", letterSpacing: "0.12em",
                  color: "#475569", textTransform: "uppercase", marginBottom: 10
                }}>
                  ▸ Confidence Intervals (95%)
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 8 }}>
                  {Object.entries(result.confidence_intervals).map(([k, v]) => (
                    <div key={k} style={{
                      background: "rgba(99,130,170,0.04)", borderRadius: 3, padding: "8px 10px",
                      border: "1px solid rgba(99,130,170,0.06)",
                    }}>
                      <div style={{ ...mono, fontSize: "0.57rem", color: "#475569", marginBottom: 3, textTransform: "uppercase" }}>{prettyLabel(k)}</div>
                      <div style={{ ...mono, fontSize: "0.72rem", color: v ? "#94a3b8" : "#334155" }}>
                        {v ? `[${v[0].toFixed(4)}, ${v[1].toFixed(4)}]` : "n/a"}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tabs */}
            <div>
              <div style={{ display: "flex", borderBottom: "1px solid rgba(99,130,170,0.1)", marginBottom: 12 }}>
                {(["signals", "metrics", "tournament", "audit"] as const).map(tab => (
                  <button
                    key={tab}
                    type="button"
                    className="ac-tab"
                    onClick={() => setActiveTab(tab)}
                    style={{
                      ...mono, fontSize: "0.6rem", letterSpacing: "0.1em", textTransform: "uppercase",
                      padding: "8px 16px", border: "none",
                      borderBottom: activeTab === tab ? "2px solid #3b82f6" : "2px solid transparent",
                      background: "transparent",
                      color: activeTab === tab ? "#e2e8f0" : "#475569",
                      cursor: "pointer", transition: "all 0.15s", fontWeight: activeTab === tab ? 600 : 400,
                    }}
                  >
                    {tab === "signals"
                      ? `Signals (${result.signals.length})`
                      : tab === "metrics"
                        ? "Metrics"
                        : tab === "tournament"
                          ? "Tournament"
                          : "Audit"}
                  </button>
                ))}
              </div>

              {/* Signals tab */}
              {activeTab === "signals" && (
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {result.signals.map(s => <SignalBar key={s.name} signal={s} />)}
                </div>
              )}

              {/* Metrics tab */}
              {activeTab === "metrics" && (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 12 }}>
                  {metricGroups.map((group) => (
                    <MetricGroup key={group.title} title={group.title}>
                      {group.items.map((item) => (
                        <MetricStrip
                          key={item.label}
                          label={item.label}
                          value={item.value}
                          display={item.display}
                          min={item.min}
                          max={item.max}
                          center={item.center}
                          color={item.color}
                        />
                      ))}
                    </MetricGroup>
                  ))}
                </div>
              )}

              {/* Tournament tab */}
              {activeTab === "tournament" && (
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {summary ? (
                    <>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 10 }}>
                        <StatBox lbl="Games" val={summary.games_count} />
                        <StatBox lbl="Analyzed Moves" val={summary.analyzed_move_count} />
                        <StatBox lbl="IPR Estimate" val={summary.ipr_estimate.toFixed(1)} />
                        <StatBox lbl="PEP Score" val={summary.pep_score.toFixed(4)} />
                        <StatBox lbl="Regan Z / T" val={`${summary.regan_z_score.toFixed(2)} / ${summary.regan_threshold.toFixed(2)}`}
                          color={summary.regan_z_score > summary.regan_threshold ? "#ef4444" : undefined} />
                      </div>

                      {summary.confidence_intervals && (
                        <div style={{
                          background: "rgba(6,8,16,0.5)", border: "1px solid rgba(99,130,170,0.08)",
                          borderRadius: 4, padding: "10px 14px"
                        }}>
                          <div style={{
                            ...mono, fontSize: "0.57rem", color: "#475569", textTransform: "uppercase",
                            letterSpacing: "0.12em", marginBottom: 8
                          }}>Tournament CI</div>
                          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                            {Object.entries(summary.confidence_intervals).map(([k, v]) => (
                              <div key={k} style={{ ...mono, fontSize: "0.65rem", color: "#64748b" }}>
                                <span style={{ color: "#475569" }}>{k}:</span>{" "}
                                {v ? `[${v[0].toFixed(4)}, ${v[1].toFixed(4)}]` : "n/a"}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {summary.per_game.length > 0 && (
                        <div style={{
                          background: "rgba(6,8,16,0.5)", border: "1px solid rgba(99,130,170,0.08)",
                          borderRadius: 4, overflow: "hidden"
                        }}>
                          <div style={{
                            ...mono, fontSize: "0.57rem", color: "#475569", textTransform: "uppercase",
                            letterSpacing: "0.12em", padding: "10px 14px",
                            borderBottom: "1px solid rgba(99,130,170,0.08)"
                          }}>Per-Game Breakdown</div>
                          <table style={{ width: "100%", borderCollapse: "collapse" }}>
                            <thead>
                              <tr style={{ background: "rgba(99,130,170,0.04)" }}>
                                {["Game ID", "Moves", "IPR", "PEP", "Regan Z", "Threshold"].map(h => (
                                  <th key={h} style={{
                                    ...mono, fontSize: "0.57rem", color: "#475569",
                                    letterSpacing: "0.1em", textTransform: "uppercase", padding: "7px 12px",
                                    textAlign: "left", borderBottom: "1px solid rgba(99,130,170,0.08)", fontWeight: 500
                                  }}>{h}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {summary.per_game.map(g => (
                                <tr key={g.game_id} style={{ borderBottom: "1px solid rgba(99,130,170,0.05)" }}>
                                  <td style={{ ...mono, fontSize: "0.65rem", color: "#64748b", padding: "7px 12px" }}>{g.game_id}</td>
                                  <td style={{ ...mono, fontSize: "0.65rem", color: "#94a3b8", padding: "7px 12px" }}>{g.analyzed_move_count}</td>
                                  <td style={{ ...mono, fontSize: "0.65rem", color: "#94a3b8", padding: "7px 12px" }}>{g.ipr_estimate.toFixed(1)}</td>
                                  <td style={{ ...mono, fontSize: "0.65rem", color: "#94a3b8", padding: "7px 12px" }}>{g.pep_score.toFixed(4)}</td>
                                  <td style={{
                                    ...mono, fontSize: "0.65rem", padding: "7px 12px",
                                    color: g.regan_z_score > g.regan_threshold ? "#ef4444" : "#94a3b8",
                                    fontWeight: g.regan_z_score > g.regan_threshold ? 700 : 400
                                  }}>
                                    {g.regan_z_score.toFixed(3)}
                                  </td>
                                  <td style={{ ...mono, fontSize: "0.65rem", color: "#475569", padding: "7px 12px" }}>{g.regan_threshold.toFixed(3)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </>
                  ) : (
                    <div style={{ ...mono, fontSize: "0.68rem", color: "#334155", padding: "20px 0", textAlign: "center" }}>
                      Tournament summary unavailable.
                    </div>
                  )}
                </div>
              )}

              {/* Audit tab */}
              {activeTab === "audit" && (
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                    <StatBox lbl="Audit ID" val={result.audit_id} />
                    <StatBox lbl="Supabase Persistence"
                      val={result.persisted_to_supabase ? "Saved" : "Not Saved"}
                      color={result.persisted_to_supabase ? "#22c55e" : "#64748b"} />
                  </div>

                  {explainabilityData.length > 0 && (
                    <div style={{
                      background: "rgba(6,8,16,0.55)",
                      border: "1px solid rgba(99,130,170,0.1)",
                      borderRadius: 5,
                      padding: "12px 14px",
                    }}>
                      <div style={{
                        ...mono, fontSize: "0.58rem", letterSpacing: "0.12em",
                        color: "#475569", textTransform: "uppercase", marginBottom: 10
                      }}>
                        Explainability Contribution Map
                      </div>
                      <ResponsiveContainer width="100%" height={220}>
                        <BarChart data={explainabilityData} layout="vertical" margin={{ top: 0, right: 24, left: 20, bottom: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,130,170,0.06)" horizontal={false} />
                          <XAxis
                            type="number"
                            domain={[-1, 1]}
                            tick={{ fontSize: 8, fontFamily: "var(--font-mono, 'DM Mono', monospace)", fill: "#475569" }}
                            axisLine={false}
                            tickLine={false}
                          />
                          <YAxis
                            type="category"
                            dataKey="label"
                            width={110}
                            tick={{ fontSize: 8, fontFamily: "var(--font-mono, 'DM Mono', monospace)", fill: "#94a3b8" }}
                            axisLine={false}
                            tickLine={false}
                          />
                          <ReferenceLine x={0} stroke="rgba(226,232,240,0.45)" />
                          <Tooltip content={<ChartTooltip />} />
                          <Bar dataKey="contribution" name="Contribution" radius={[0, 2, 2, 0]} barSize={12}>
                            {explainabilityData.map((entry, i) => (
                              <Cell key={`${entry.feature}-${i}`} fill={entry.fill} fillOpacity={0.85} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {confidenceIntervalData.length > 0 && (
                    <div style={{
                      background: "rgba(6,8,16,0.55)",
                      border: "1px solid rgba(99,130,170,0.1)",
                      borderRadius: 5,
                      padding: "12px 14px",
                    }}>
                      <div style={{
                        ...mono, fontSize: "0.58rem", letterSpacing: "0.12em",
                        color: "#475569", textTransform: "uppercase", marginBottom: 10
                      }}>
                        Confidence Interval Ranges
                      </div>
                      <ResponsiveContainer width="100%" height={240}>
                        <BarChart data={confidenceIntervalData} layout="vertical" margin={{ top: 0, right: 24, left: 20, bottom: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,130,170,0.06)" horizontal={false} />
                          <XAxis
                            type="number"
                            tick={{ fontSize: 8, fontFamily: "var(--font-mono, 'DM Mono', monospace)", fill: "#475569" }}
                            axisLine={false}
                            tickLine={false}
                          />
                          <YAxis
                            type="category"
                            dataKey="label"
                            width={110}
                            tick={{ fontSize: 8, fontFamily: "var(--font-mono, 'DM Mono', monospace)", fill: "#94a3b8" }}
                            axisLine={false}
                            tickLine={false}
                          />
                          <Tooltip content={<ChartTooltip />} />
                          <Bar dataKey="low" name="Lower Bound" stackId="ci" fill="rgba(0,0,0,0)" isAnimationActive={false} />
                          <Bar dataKey="span" name="CI Width" stackId="ci" fill="#38bdf8" radius={[0, 2, 2, 0]} barSize={10} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {result.explainability_items && result.explainability_items.length > 0 && (
                    <div style={{
                      background: "rgba(6,8,16,0.5)", border: "1px solid rgba(99,130,170,0.08)",
                      borderRadius: 4, padding: "12px 14px"
                    }}>
                      <div style={{
                        ...mono, fontSize: "0.57rem", color: "#475569", textTransform: "uppercase",
                        letterSpacing: "0.12em", marginBottom: 8
                      }}>Explainability Top Drivers</div>
                      <ol style={{ paddingLeft: 16, display: "flex", flexDirection: "column", gap: 5 }}>
                        {result.explainability_items.map((it, i) => (
                          <li key={`${it.feature}-${i}`} style={{ ...mono, fontSize: "0.68rem", color: "#64748b", lineHeight: 1.5 }}>
                            {prettyLabel(it.feature)}: {formatSigned(it.contribution, 4)} ({it.direction})
                          </li>
                        ))}
                      </ol>
                    </div>
                  )}

                  {result.natural_occurrence_statement && (
                    <div style={{
                      background: "rgba(6,8,16,0.5)", border: "1px solid rgba(99,130,170,0.08)",
                      borderRadius: 4, padding: "12px 14px"
                    }}>
                      <div style={{
                        ...mono, fontSize: "0.57rem", color: "#475569", textTransform: "uppercase",
                        letterSpacing: "0.12em", marginBottom: 6
                      }}>Natural Occurrence Statement</div>
                      <div style={{ ...mono, fontSize: "0.7rem", color: "#64748b", lineHeight: 1.5 }}>
                        {result.natural_occurrence_statement}
                      </div>
                    </div>
                  )}

                  {result.legal_disclaimer_text && (
                    <div style={{
                      background: "rgba(6,8,16,0.5)", border: "1px solid rgba(99,130,170,0.08)",
                      borderRadius: 4, padding: "12px 14px"
                    }}>
                      <div style={{
                        ...mono, fontSize: "0.57rem", color: "#475569", textTransform: "uppercase",
                        letterSpacing: "0.12em", marginBottom: 6
                      }}>Legal Disclaimer</div>
                      <div style={{ ...mono, fontSize: "0.7rem", color: "#64748b", lineHeight: 1.5 }}>
                        {result.legal_disclaimer_text}
                      </div>
                    </div>
                  )}

                  {result.explanation.length > 0 && (
                    <div style={{
                      background: "rgba(6,8,16,0.5)", border: "1px solid rgba(99,130,170,0.08)",
                      borderRadius: 4, padding: "12px 14px"
                    }}>
                      <div style={{
                        ...mono, fontSize: "0.57rem", color: "#475569", textTransform: "uppercase",
                        letterSpacing: "0.12em", marginBottom: 8
                      }}>Explanation</div>
                      <ol style={{ paddingLeft: 16, display: "flex", flexDirection: "column", gap: 5 }}>
                        {result.explanation.map((line, i) => (
                          <li key={i} style={{ ...mono, fontSize: "0.68rem", color: "#64748b", lineHeight: 1.5 }}>{line}</li>
                        ))}
                      </ol>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
