"use client";

import { useEffect, useMemo, useState } from "react";
<<<<<<< HEAD
import { useRouter, useSearchParams } from "next/navigation";

import { AnalysisConsole } from "./analysis-console";
import {
  AdminSection,
  CasesSection,
  DeepDiveSection,
  LiveSection,
  OTBSection,
  PartnerSection,
  PlayerSection,
  ReportSection,
  TournamentSection,
} from "./workspace-sections";
=======

import { AnalysisConsole } from "./analysis-console";
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674

type DashboardPage =
  | "command"
  | "deep-dive"
  | "player"
  | "report"
  | "cases"
  | "live"
  | "tournament"
  | "partner"
  | "otb"
  | "admin";
type RiskTier = "LOW" | "MODERATE" | "ELEVATED" | "HIGH_STATISTICAL_ANOMALY";

type FeedGame = {
  game_id: string;
  event_id: string;
  player_id: string;
  official_elo: number;
  move_number: number;
  risk_tier: string;
  confidence: number;
  weighted_risk_score: number;
  sparkline: number[];
  audit_id: string;
  created_at: string;
};

type FeedAlert = {
  id: string;
  timestamp: string;
  event_id: string;
  player_id: string;
  layer: string;
  score: number;
  threshold: number;
  description: string;
  audit_id: string;
};

type FeedSummary = {
  total_games_analyzed_today: number;
  games_elevated_or_above: number;
  awaiting_review_count: number;
  average_regan_z_score: number;
};

type DashboardFeedResponse = {
  generated_at_utc: string;
  games: FeedGame[];
  alerts: FeedAlert[];
  summary: FeedSummary;
};

type SystemStatus = {
  generated_at_utc: string;
<<<<<<< HEAD
  app_env?: string;
  model_version?: string;
  feature_schema_version?: string;
  report_schema_version?: string;
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
  calibration: {
    source?: string;
    profile_version?: string;
    band_count?: number;
    coverage_min_elo?: number | null;
    coverage_max_elo?: number | null;
    qa?: { ok?: boolean; failed_checks?: string[] };
  };
  ml_fusion: {
    enabled?: boolean;
    models_present?: boolean;
    primary?: { exists?: boolean; load_ok?: boolean | null };
    secondary?: { exists?: boolean; load_ok?: boolean | null };
  };
  maia: {
    path?: string | null;
    models_dir?: string | null;
    available_count?: number;
    version?: string;
    lc0_path?: string | null;
  };
  engine: { exists?: boolean };
  opening_book: { exists?: boolean };
  tablebase: { exists?: boolean };
<<<<<<< HEAD
  supabase_configured?: boolean;
  analysis_pipeline_operational?: boolean;
  ml_models_loaded?: boolean;
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
  warnings: string[];
};

type CaseRecord = {
  id: string;
  created_at: string;
  updated_at: string;
  status: string;
  title: string;
  event_id?: string | null;
  players: string[];
  summary?: string | null;
<<<<<<< HEAD
  tags?: string[];
  priority?: string | null;
  assigned_to?: string | null;
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
};

type CaseNote = {
  id: string;
  created_at: string;
  author?: string | null;
  note_type?: string | null;
  text?: string | null;
<<<<<<< HEAD
  structured?: Record<string, unknown>;
};

type CaseReview = {
  id: string;
  case_id: string;
  reviewer_user_id?: string | null;
  action: string;
  rationale?: string | null;
  payload?: Record<string, unknown>;
  created_at: string;
};

type CaseSignoff = {
  id: string;
  case_id: string;
  signer_user_id?: string | null;
  signer_role: string;
  decision: string;
  note?: string | null;
  created_at: string;
};

type BatchRunRow = {
  Name: string;
  Rating: number;
  "Rating Used": number;
  IPR12?: number | null;
  CombZ?: number | null;
  PredZ?: number | null;
  "#turns": number;
  wtfactor: number;
  "IPR diff"?: number | null;
  "2sigma"?: number | null;
  ChallFaced?: number | null;
  s?: number | null;
  c?: number | null;
  MMZ?: number | null;
  EVZ?: number | null;
  ASDZ?: number | null;
  ELWZ?: number | null;
  Engine?: string;
  Weights?: string;
  T2Z?: number | null;
  T3Z?: number | null;
  T3thr50Z?: number | null;
  sOfIPR?: number | null;
  cOfIPR?: number | null;
  "CombZ+"?: number | null;
  "Pred+"?: number | null;
};

type BatchRun = {
  id: string;
  created_at: string;
  updated_at: string;
  event_id?: string | null;
  source_name?: string | null;
  status: string;
  response?: {
    batch_run_id?: string | null;
    players_analyzed?: number;
    games_parsed?: number;
    analyses_generated?: number;
    rows?: Array<{ regan_row?: BatchRunRow }>;
    failures?: Array<Record<string, string>>;
  } | null;
  csv_text?: string | null;
  error_text?: string | null;
};

type BatchQueueResponse = {
  batch_run_id: string;
  status: string;
  response_format?: string;
  source_name?: string | null;
  message?: string;
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
};

type PartnerKey = {
  id: string;
  key: string;
  secret: string;
  partner_name: string;
  webhook_url?: string | null;
  rate_limit_per_minute: number;
  active: boolean;
  created_at: string;
<<<<<<< HEAD
  key_last4?: string | null;
  secret_last4?: string | null;
};

type PartnerJob = {
  job_id: string;
  api_key_id?: string | null;
  partner_name?: string | null;
  game_id: string;
  player_id: string;
  status: string;
  risk_level?: string | null;
  risk_score?: number | null;
  webhook_delivered: boolean;
  webhook_attempts: number;
  created_at?: string;
  completed_at?: string | null;
  result?: Record<string, unknown> | null;
};

type PartnerSession = {
  session_id: string;
  api_key_id?: string | null;
  partner_name?: string | null;
  game_id?: string | null;
  player_id?: string | null;
  status: string;
  created_at?: string;
  ended_at?: string | null;
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
};

type OTBCameraEvent = {
  id: string;
  event_id?: string | null;
  case_id?: string | null;
  player_id?: string | null;
  session_id?: string | null;
  camera_id?: string | null;
  storage_mode?: string | null;
  summary?: Record<string, unknown>;
  created_at?: string;
};

type DGTBoardEvent = {
  id: string;
  event_id?: string | null;
  session_id?: string | null;
  board_serial?: string | null;
  move_uci?: string | null;
  ply?: number | null;
  clock_ms?: number | null;
<<<<<<< HEAD
  fen?: string | null;
  created_at?: string;
};

type OTBIncidentRecord = {
  id: string;
  case_id?: string | null;
  event_id?: string | null;
  player_id?: string | null;
  incident_type: string;
  severity: string;
  description?: string | null;
  occurred_at?: string | null;
  metadata?: Record<string, unknown>;
  created_at: string;
};

=======
  created_at?: string;
};

>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
type Props = {
  apiBase: string;
  apiRole: string;
  apiFederationId: string;
  apiHealth: "healthy" | "degraded" | "offline" | string;
  apiLatencyMs: number | null;
  apiCheckedAt: string;
  supabaseReady: boolean;
  missingEnvVars: string[];
<<<<<<< HEAD
  initialPage?: DashboardPage;
};

type AuditMove = {
  ply: number;
  player_move: string;
  engine_best: string;
  cp_loss: number;
  top3_match?: boolean;
  complexity_score?: number;
  maia_probability?: number | null;
  time_spent_seconds?: number | null;
  best_eval_cp?: number;
  is_opening_book?: boolean;
  is_tablebase?: boolean;
  is_forced?: boolean;
};

type AuditGame = {
  game_id: string;
  opponent_official_elo?: number | null;
  moves: AuditMove[];
};

type AuditResponseShape = {
  player_id?: string;
  event_id?: string;
  risk_tier?: string;
  confidence?: number;
  weighted_risk_score?: number;
  analyzed_move_count?: number;
  report_version?: number;
  report_locked?: boolean;
  report_locked_at?: string | null;
  natural_occurrence_statement?: string | null;
  natural_occurrence_probability?: number | null;
  human_explanations?: string[];
  legal_disclaimer_text?: string | null;
  ml_fusion_source?: string | null;
  ml_primary_score?: number | null;
  ml_secondary_score?: number | null;
  explainability_method?: string | null;
  explainability_items?: Array<Record<string, unknown>>;
  confidence_intervals?: Record<string, number[] | null>;
  evidence_report?: Record<string, unknown> | null;
  behavioral_metrics?: Record<string, unknown>;
  environmental_metrics?: Record<string, unknown>;
  identity_confidence?: Record<string, unknown>;
  signals?: Array<Record<string, unknown>>;
};

type AuditRecord = {
  id?: string;
  created_at?: string;
  request?: {
    player_id?: string;
    event_id?: string;
    official_elo?: number;
    games?: AuditGame[];
  };
  response?: AuditResponseShape;
};

type CaseEvidence = {
  id: string;
  evidence_type: string;
  label?: string | null;
  path?: string | null;
  created_at: string;
};

type CaseFlag = {
  id: string;
  flag_type: string;
  severity: string;
  message: string;
  metadata?: Record<string, unknown>;
  created_at: string;
};

type PlayerProfileResponse = {
  player_id: string;
  updated_at?: string | null;
  profile: Record<string, unknown>;
  history: Array<Record<string, unknown>>;
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
};

const RISK_CLASS: Record<RiskTier, string> = {
  LOW: "riskLow",
  MODERATE: "riskModerate",
  ELEVATED: "riskElevated",
  HIGH_STATISTICAL_ANOMALY: "riskHigh",
};

function normalizeRiskTier(value: string): RiskTier | null {
  if (value === "LOW" || value === "MODERATE" || value === "ELEVATED" || value === "HIGH_STATISTICAL_ANOMALY") {
    return value;
  }
  return null;
}

function Sparkline({ values }: { values: number[] }) {
  if (!values.length) {
    return <div className="muted">None</div>;
  }
  const points = values
    .map((v, i) => {
      const x = (i / Math.max(1, values.length - 1)) * 100;
      const y = 100 - Math.max(0, Math.min(100, v * 100));
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg viewBox="0 0 100 100" className="sparkline" aria-hidden="true">
      <polyline points={points} />
    </svg>
  );
}

function RiskPill({ tier }: { tier: RiskTier | null }) {
  if (!tier) {
    return <span className="riskPill">NONE</span>;
  }
  return <span className={`riskPill ${RISK_CLASS[tier]}`}>{tier.replaceAll("_", " ")}</span>;
}

function formatClock(now: Date | null): string {
  if (!now) return "--:--:--";
  return now.toLocaleTimeString();
}

<<<<<<< HEAD
function numeric(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function formatMaybe(value: unknown, digits = 3): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(digits) : "None";
}

function formatPercent(value: unknown): string {
  return typeof value === "number" && Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : "None";
}

function copyText(value: string) {
  if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
    void navigator.clipboard.writeText(value);
  }
}

function estimateImpliedRating(cpLoss: number): number {
  return Math.max(100, Math.min(3600, 3300 - (28 * cpLoss)));
}

=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
export function ArbiterDashboard({
  apiBase,
  apiRole,
  apiFederationId,
  apiHealth,
  apiLatencyMs,
  apiCheckedAt,
  supabaseReady,
  missingEnvVars,
<<<<<<< HEAD
  initialPage = "command",
}: Props) {
  const [page, setPage] = useState<DashboardPage>(initialPage);
=======
}: Props) {
  const [page, setPage] = useState<DashboardPage>("command");
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
  const [feedGames, setFeedGames] = useState<FeedGame[]>([]);
  const [feedAlerts, setFeedAlerts] = useState<FeedAlert[]>([]);
  const [feedSummary, setFeedSummary] = useState<FeedSummary | null>(null);
  const [reviewedAlerts, setReviewedAlerts] = useState<Record<string, boolean>>({});
  const [selectedGameId, setSelectedGameId] = useState<string | null>(null);
  const [now, setNow] = useState<Date | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [systemStatusError, setSystemStatusError] = useState<string | null>(null);
  const [cases, setCases] = useState<CaseRecord[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [caseNotes, setCaseNotes] = useState<CaseNote[]>([]);
<<<<<<< HEAD
  const [caseReviews, setCaseReviews] = useState<CaseReview[]>([]);
  const [caseSignoffs, setCaseSignoffs] = useState<CaseSignoff[]>([]);
  const [caseFlags, setCaseFlags] = useState<CaseFlag[]>([]);
  const [caseEvidence, setCaseEvidence] = useState<CaseEvidence[]>([]);
  const [caseTitle, setCaseTitle] = useState("");
  const [caseEventId, setCaseEventId] = useState("");
  const [casePlayers, setCasePlayers] = useState("");
  const [caseSummary, setCaseSummary] = useState("");
  const [caseTags, setCaseTags] = useState("");
  const [casePriority, setCasePriority] = useState("medium");
  const [caseAssignedTo, setCaseAssignedTo] = useState("");
  const [caseStatusUpdate, setCaseStatusUpdate] = useState("opened");
  const [caseStatusMessage, setCaseStatusMessage] = useState("");
  const [caseNoteAuthor, setCaseNoteAuthor] = useState("Arbiter");
  const [caseNoteType, setCaseNoteType] = useState("arbiter_note");
  const [caseNoteText, setCaseNoteText] = useState("");
  const [caseReviewUserId, setCaseReviewUserId] = useState("");
  const [caseReviewAction, setCaseReviewAction] = useState("recommend_monitoring");
  const [caseReviewRationale, setCaseReviewRationale] = useState("");
  const [caseSignoffUserId, setCaseSignoffUserId] = useState("");
  const [caseSignoffRole, setCaseSignoffRole] = useState("chief_arbiter");
  const [caseSignoffDecision, setCaseSignoffDecision] = useState("approved");
  const [caseSignoffNote, setCaseSignoffNote] = useState("");
  const [evidenceType, setEvidenceType] = useState("report");
  const [evidenceLabel, setEvidenceLabel] = useState("");
  const [evidencePath, setEvidencePath] = useState("");
  const [evidenceStatus, setEvidenceStatus] = useState("");
  const [autoFlagAuditId, setAutoFlagAuditId] = useState("");
  const [autoFlagStatus, setAutoFlagStatus] = useState("");
  const [partnerKeys, setPartnerKeys] = useState<PartnerKey[]>([]);
  const [partnerName, setPartnerName] = useState("");
  const [partnerWebhook, setPartnerWebhook] = useState("");
  const [partnerRateLimit, setPartnerRateLimit] = useState("60");
  const [partnerStatus, setPartnerStatus] = useState<string>("");
  const [partnerJobs, setPartnerJobs] = useState<PartnerJob[]>([]);
  const [partnerSessions, setPartnerSessions] = useState<PartnerSession[]>([]);
  const [partnerSelectedKeyId, setPartnerSelectedKeyId] = useState("");
  const [partnerRevealedKeys, setPartnerRevealedKeys] = useState<Record<string, PartnerKey>>({});
  const [partnerSessionGameId, setPartnerSessionGameId] = useState("");
  const [partnerSessionPlayerId, setPartnerSessionPlayerId] = useState("");
  const [partnerSessionStatus, setPartnerSessionStatus] = useState("");
  const [partnerTestGameId, setPartnerTestGameId] = useState("demo-game-1");
  const [partnerTestPlayerId, setPartnerTestPlayerId] = useState("demo-player-1");
  const [partnerTestColor, setPartnerTestColor] = useState("white");
  const [partnerTestElo, setPartnerTestElo] = useState("1800");
  const [partnerTestPgn, setPartnerTestPgn] = useState(`[Event "Sentinel Demo"]
[Site "Local"]
[Date "2026.03.25"]
[Round "1"]
[White "Demo White"]
[Black "Demo Black"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 1-0`);
  const [partnerTestStatus, setPartnerTestStatus] = useState("");
=======
  const [caseTitle, setCaseTitle] = useState("");
  const [caseEventId, setCaseEventId] = useState("");
  const [casePlayers, setCasePlayers] = useState("");
  const [caseNoteText, setCaseNoteText] = useState("");
  const [partnerKeys, setPartnerKeys] = useState<PartnerKey[]>([]);
  const [partnerName, setPartnerName] = useState("");
  const [partnerWebhook, setPartnerWebhook] = useState("");
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
  const [reportAuditId, setReportAuditId] = useState("");
  const [reportCaseId, setReportCaseId] = useState("");
  const [reportMode, setReportMode] = useState("arbiter");
  const [reportFormat, setReportFormat] = useState("json");
<<<<<<< HEAD
  const [reportUseAi, setReportUseAi] = useState(false);
  const [reportProvider, setReportProvider] = useState("openai");
  const [reportModel, setReportModel] = useState("");
  const [reportApiUrl, setReportApiUrl] = useState("");
  const [reportApiKey, setReportApiKey] = useState("");
  const [reportOutput, setReportOutput] = useState<string>("");
  const [reportStatus, setReportStatus] = useState<string>("");
  const [batchPgnFileName, setBatchPgnFileName] = useState("");
  const [batchPgnText, setBatchPgnText] = useState("");
  const [batchTrackedPlayerName, setBatchTrackedPlayerName] = useState("");
  const [batchTrackedPlayerId, setBatchTrackedPlayerId] = useState("");
  const [batchDefaultElo, setBatchDefaultElo] = useState("1800");
  const [batchMaxGames, setBatchMaxGames] = useState("500");
  const [batchAnalyzeBoth, setBatchAnalyzeBoth] = useState(false);
  const [batchResponseFormat, setBatchResponseFormat] = useState("json");
  const [batchStatus, setBatchStatus] = useState("");
  const [batchPreview, setBatchPreview] = useState("");
  const [batchRuns, setBatchRuns] = useState<BatchRun[]>([]);
  const [deepDiveNote, setDeepDiveNote] = useState("");
=======
  const [reportOutput, setReportOutput] = useState<string>("");
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
  const [liveSessionId, setLiveSessionId] = useState("");
  const [liveEvents, setLiveEvents] = useState<Array<Record<string, unknown>>>([]);
  const [liveRisk, setLiveRisk] = useState<Record<string, unknown> | null>(null);
  const [tournamentPlayers, setTournamentPlayers] = useState<Array<Record<string, unknown>>>([]);
  const [tournamentAlerts, setTournamentAlerts] = useState<Array<Record<string, unknown>>>([]);
  const [auditDetails, setAuditDetails] = useState<Record<string, unknown> | null>(null);
<<<<<<< HEAD
  const [playerQuery, setPlayerQuery] = useState("");
  const [playerProfile, setPlayerProfile] = useState<PlayerProfileResponse | null>(null);
  const [playerStatus, setPlayerStatus] = useState("");
  const [otbEventId, setOtbEventId] = useState("");
  const [otbCameraEvents, setOtbCameraEvents] = useState<OTBCameraEvent[]>([]);
  const [otbBoardEvents, setOtbBoardEvents] = useState<DGTBoardEvent[]>([]);
  const [otbIncidents, setOtbIncidents] = useState<OTBIncidentRecord[]>([]);
  const [otbIncidentPlayerId, setOtbIncidentPlayerId] = useState("");
  const [otbIncidentCaseId, setOtbIncidentCaseId] = useState("");
  const [otbIncidentType, setOtbIncidentType] = useState("suspicious_behavior");
  const [otbIncidentSeverity, setOtbIncidentSeverity] = useState("medium");
  const [otbIncidentDescription, setOtbIncidentDescription] = useState("");
  const [otbIncidentOccurredAt, setOtbIncidentOccurredAt] = useState("");
  const [otbIncidentStatus, setOtbIncidentStatus] = useState("");
  const [otbConnectStatus, setOtbConnectStatus] = useState<string>("");
  const router = useRouter();
  const searchParams = useSearchParams();
=======
  const [otbEventId, setOtbEventId] = useState("");
  const [otbCameraEvents, setOtbCameraEvents] = useState<OTBCameraEvent[]>([]);
  const [otbBoardEvents, setOtbBoardEvents] = useState<DGTBoardEvent[]>([]);
  const [otbConnectStatus, setOtbConnectStatus] = useState<string>("");
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674

  useEffect(() => {
    setNow(new Date());
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function refreshFeed() {
      try {
        const headers: Record<string, string> = {
          Accept: "application/json",
          "X-Role": apiRole,
        };
        if (apiFederationId) headers["X-Federation-Id"] = apiFederationId;
        const res = await fetch(`${apiBase}/v1/dashboard-feed?limit=200`, { cache: "no-store", headers });
        if (!res.ok) return;
        const feed = (await res.json()) as DashboardFeedResponse;
        if (cancelled) return;

        const games = Array.isArray(feed.games) ? feed.games : [];
        const alerts = Array.isArray(feed.alerts) ? feed.alerts : [];

        setFeedGames(games);
        setFeedAlerts(alerts);
        setFeedSummary(feed.summary ?? null);
        setSelectedGameId((prev) => (prev && games.some((g) => g.game_id === prev) ? prev : games[0]?.game_id ?? null));
      } catch {
        // Keep current state on network/server error.
      }
    }

    refreshFeed();
    const poll = setInterval(refreshFeed, 20000);
    return () => {
      cancelled = true;
      clearInterval(poll);
    };
  }, [apiBase, apiRole, apiFederationId]);

  useEffect(() => {
    let cancelled = false;

    async function refreshStatus() {
      try {
        setSystemStatusError(null);
        const headers: Record<string, string> = {
          Accept: "application/json",
          "X-Role": apiRole,
        };
        const res = await fetch(`${apiBase}/v1/system-status`, { cache: "no-store", headers });
        if (!res.ok) {
          const body = (await res.json().catch(() => ({}))) as { detail?: string };
          throw new Error(body.detail || `Status unavailable (${res.status})`);
        }
        const status = (await res.json()) as SystemStatus;
        if (!cancelled) setSystemStatus(status);
      } catch (err) {
        if (!cancelled) setSystemStatusError(err instanceof Error ? err.message : "Status unavailable");
      }
    }

    refreshStatus();
    const poll = setInterval(refreshStatus, 30000);
    return () => {
      cancelled = true;
      clearInterval(poll);
    };
  }, [apiBase, apiRole]);

  function authHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      Accept: "application/json",
      "Content-Type": "application/json",
      "X-Role": apiRole,
    };
    if (apiFederationId) headers["X-Federation-Id"] = apiFederationId;
    return headers;
  }

  useEffect(() => {
    let cancelled = false;
    async function loadCases() {
      try {
        const res = await fetch(`${apiBase}/v1/cases?limit=200`, { headers: authHeaders() });
        if (!res.ok) return;
        const data = (await res.json()) as { cases?: CaseRecord[] };
        if (!cancelled) setCases(data.cases ?? []);
      } catch {
        // ignore
      }
    }
    loadCases();
    const poll = setInterval(loadCases, 30000);
    return () => {
      cancelled = true;
      clearInterval(poll);
    };
  }, [apiBase, apiRole, apiFederationId]);

  useEffect(() => {
    let cancelled = false;
    async function loadPartnerKeys() {
      try {
        const res = await fetch(`${apiBase}/v1/partner/keys`, { headers: authHeaders() });
        if (!res.ok) return;
        const data = (await res.json()) as { keys?: PartnerKey[] };
<<<<<<< HEAD
        if (!cancelled) {
          const keys = data.keys ?? [];
          setPartnerKeys(keys);
          setPartnerSelectedKeyId((prev) => prev || keys[0]?.id || "");
        }
=======
        if (!cancelled) setPartnerKeys(data.keys ?? []);
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
      } catch {
        // ignore
      }
    }
    loadPartnerKeys();
    return () => { cancelled = true; };
  }, [apiBase, apiRole, apiFederationId]);

  useEffect(() => {
    let cancelled = false;
<<<<<<< HEAD
    async function loadPartnerOps() {
      if (page !== "partner") return;
      try {
        const [jobsRes, sessionsRes] = await Promise.all([
          fetch(`${apiBase}/v1/partner/jobs?limit=200`, { headers: authHeaders() }),
          fetch(`${apiBase}/v1/partner/sessions?limit=200`, { headers: authHeaders() }),
        ]);
        if (jobsRes.ok) {
          const data = (await jobsRes.json()) as { jobs?: PartnerJob[] };
          if (!cancelled) setPartnerJobs(data.jobs ?? []);
        }
        if (sessionsRes.ok) {
          const data = (await sessionsRes.json()) as { sessions?: PartnerSession[] };
          if (!cancelled) setPartnerSessions(data.sessions ?? []);
        }
      } catch {
        // ignore
      }
    }
    void loadPartnerOps();
    const poll = setInterval(() => { void loadPartnerOps(); }, 15000);
    return () => {
      cancelled = true;
      clearInterval(poll);
    };
  }, [apiBase, apiRole, apiFederationId, page]);

  useEffect(() => {
    let cancelled = false;
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
    async function loadTournament() {
      try {
        const res = await fetch(`${apiBase}/v1/tournament-dashboard?limit=200`, { headers: authHeaders() });
        if (!res.ok) return;
        const data = (await res.json()) as { players?: Array<Record<string, unknown>>; alerts?: Array<Record<string, unknown>> };
        if (!cancelled) {
          setTournamentPlayers(data.players ?? []);
          setTournamentAlerts(data.alerts ?? []);
        }
      } catch {
        // ignore
      }
    }
    loadTournament();
    return () => { cancelled = true; };
  }, [apiBase, apiRole, apiFederationId]);

  useEffect(() => {
    let cancelled = false;
    async function loadOtb() {
      if (page !== "otb") return;
      try {
        const query = otbEventId ? `?event_id=${encodeURIComponent(otbEventId)}` : "";
<<<<<<< HEAD
        const [cameraRes, boardRes, incidentsRes] = await Promise.all([
          fetch(`${apiBase}/v1/otb/camera-events${query}`, { headers: authHeaders() }),
          fetch(`${apiBase}/v1/otb/board-events${query}`, { headers: authHeaders() }),
          fetch(`${apiBase}/v1/otb/incidents${query}`, { headers: authHeaders() }),
=======
        const [cameraRes, boardRes] = await Promise.all([
          fetch(`${apiBase}/v1/otb/camera-events${query}`, { headers: authHeaders() }),
          fetch(`${apiBase}/v1/otb/board-events${query}`, { headers: authHeaders() }),
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
        ]);
        if (cameraRes.ok) {
          const data = (await cameraRes.json()) as { events?: OTBCameraEvent[] };
          if (!cancelled) setOtbCameraEvents(data.events ?? []);
        }
        if (boardRes.ok) {
          const data = (await boardRes.json()) as { events?: DGTBoardEvent[] };
          if (!cancelled) setOtbBoardEvents(data.events ?? []);
        }
<<<<<<< HEAD
        if (incidentsRes.ok) {
          const data = (await incidentsRes.json()) as { incidents?: OTBIncidentRecord[] };
          if (!cancelled) setOtbIncidents(data.incidents ?? []);
        }
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
      } catch {
        // ignore
      }
    }
    loadOtb();
    return () => { cancelled = true; };
  }, [apiBase, apiRole, apiFederationId, page, otbEventId]);

  const games = useMemo(() => [...feedGames].sort((a, b) => b.weighted_risk_score - a.weighted_risk_score), [feedGames]);
  const selectedGame = games.find((g) => g.game_id === selectedGameId) ?? null;
  const awaitingReview = Math.max(0, feedAlerts.filter((a) => !reviewedAlerts[a.id]).length);
<<<<<<< HEAD
  const auditRecord = (auditDetails as AuditRecord | null) ?? null;
  const auditRequest = auditRecord?.request;
  const auditResponse = auditRecord?.response;
  const deepDiveGames = auditRequest?.games ?? [];
  const deepDiveMoves = deepDiveGames.flatMap((game) => game.moves ?? []);
  const selectedCase = cases.find((c) => c.id === selectedCaseId) ?? null;
  const evidenceReport = (auditResponse?.evidence_report ?? null) as Record<string, unknown> | null;
  const impliedRatingSeries = deepDiveMoves.map((move) => estimateImpliedRating(numeric(move.cp_loss)));
  const cpLossSeries = deepDiveMoves.map((move) => numeric(move.cp_loss));
  const linkedAnalyses = useMemo(() => {
    if (!selectedCase) return [];
    return feedGames
      .filter((game) => {
        const matchesEvent = selectedCase.event_id ? game.event_id === selectedCase.event_id : true;
        const matchesPlayer = selectedCase.players.length ? selectedCase.players.includes(game.player_id) : true;
        return matchesEvent && matchesPlayer;
      })
      .map((game) => ({
        audit_id: game.audit_id,
        player_id: game.player_id,
        event_id: game.event_id,
        risk_tier: game.risk_tier,
        weighted_risk_score: game.weighted_risk_score,
        created_at: game.created_at,
      }))
      .sort((a, b) => b.weighted_risk_score - a.weighted_risk_score);
  }, [feedGames, selectedCase]);
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674

  const navItems: Array<{ id: DashboardPage; label: string }> = [
    { id: "command", label: "Command Center" },
    { id: "deep-dive", label: "Game Deep Dive" },
    { id: "cases", label: "Cases" },
    { id: "live", label: "Live Monitor" },
    { id: "player", label: "Player Profile" },
    { id: "report", label: "Report Composer" },
    { id: "tournament", label: "Tournament" },
    { id: "partner", label: "Partner Keys" },
    { id: "otb", label: "OTB Monitor" },
    { id: "admin", label: "System Config" },
  ];

  const apiDotClass = apiHealth === "healthy" ? "ok" : apiHealth === "degraded" ? "warn" : "bad";
  const stockfishDotClass = systemStatus ? (systemStatus.engine?.exists ? "ok" : "bad") : "warn";
  const maiaReady = Boolean(systemStatus?.maia?.available_count && systemStatus?.maia?.lc0_path);
  const maiaDotClass = systemStatus
    ? (maiaReady ? "ok" : systemStatus.maia?.models_dir ? "warn" : "warn")
    : "warn";
  const mlDotClass = systemStatus
    ? (systemStatus.ml_fusion?.enabled
      ? (systemStatus.ml_fusion?.models_present ? "ok" : "warn")
      : "warn")
    : "warn";

<<<<<<< HEAD
  const pageRoutes: Record<DashboardPage, string> = {
    command: "/",
    "deep-dive": "/deep-dive",
    player: "/player",
    report: "/report",
    cases: "/cases",
    live: "/live",
    tournament: "/tournament",
    partner: "/partner",
    otb: "/otb",
    admin: "/system-status",
  };
  const navigate = (href: string) => router.push(href as never);

  useEffect(() => {
    if (selectedGame?.audit_id) {
      loadAudit(selectedGame.audit_id);
      setReportAuditId(selectedGame.audit_id);
=======
  useEffect(() => {
    if (selectedGame?.audit_id) {
      loadAudit(selectedGame.audit_id);
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
    } else {
      setAuditDetails(null);
    }
  }, [selectedGame?.audit_id]);

<<<<<<< HEAD
  useEffect(() => {
    if (selectedCaseId) {
      void loadCaseNotes(selectedCaseId);
      void loadCaseArtifacts(selectedCaseId);
      setReportCaseId(selectedCaseId);
      setCaseStatusMessage("");
      setEvidenceStatus("");
      setAutoFlagStatus("");
    } else {
      setCaseNotes([]);
      setCaseReviews([]);
      setCaseSignoffs([]);
      setCaseFlags([]);
      setCaseEvidence([]);
    }
  }, [selectedCaseId]);

  useEffect(() => {
    void refreshBatchRuns();
    const poll = setInterval(() => {
      void refreshBatchRuns();
    }, 30000);
    return () => clearInterval(poll);
  }, [apiBase, apiRole, apiFederationId]);

  useEffect(() => {
    if (selectedCase?.status) {
      setCaseStatusUpdate(selectedCase.status);
    }
  }, [selectedCase?.status]);

  useEffect(() => {
    const auditId = searchParams.get("auditId");
    const caseId = searchParams.get("caseId");
    const playerId = searchParams.get("playerId");
    if (auditId) {
      setReportAuditId(auditId);
      void loadAudit(auditId);
    }
    if (caseId) {
      setSelectedCaseId(caseId);
    }
    if (playerId) {
      setPlayerQuery(playerId);
      void loadPlayerProfile(playerId);
    }
  }, [searchParams]);

  async function createCase() {
    const players = casePlayers.split(",").map((p) => p.trim()).filter(Boolean);
    const tags = caseTags.split(",").map((tag) => tag.trim()).filter(Boolean);
    const res = await fetch(`${apiBase}/v1/cases`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        title: caseTitle,
        event_id: caseEventId || null,
        players,
        summary: caseSummary || null,
        tags,
        priority: casePriority || null,
        assigned_to: caseAssignedTo || null,
      }),
=======
  async function createCase() {
    const players = casePlayers.split(",").map((p) => p.trim()).filter(Boolean);
    const res = await fetch(`${apiBase}/v1/cases`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ title: caseTitle, event_id: caseEventId || null, players }),
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
    });
    if (!res.ok) return;
    const created = (await res.json()) as CaseRecord;
    setCases((prev) => [created, ...prev]);
    setCaseTitle("");
    setCaseEventId("");
    setCasePlayers("");
<<<<<<< HEAD
    setCaseSummary("");
    setCaseTags("");
    setCasePriority("medium");
    setCaseAssignedTo("");
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
  }

  async function loadCaseNotes(caseId: string) {
    const res = await fetch(`${apiBase}/v1/cases/${caseId}/notes`, { headers: authHeaders() });
    if (!res.ok) return;
    const data = (await res.json()) as { notes?: CaseNote[] };
    setCaseNotes(data.notes ?? []);
  }

<<<<<<< HEAD
  async function loadCaseArtifacts(caseId: string) {
    const [flagsRes, evidenceRes, reviewsRes, signoffsRes] = await Promise.all([
      fetch(`${apiBase}/v1/cases/${caseId}/flags`, { headers: authHeaders() }),
      fetch(`${apiBase}/v1/cases/${caseId}/evidence`, { headers: authHeaders() }),
      fetch(`${apiBase}/v1/cases/${caseId}/reviews`, { headers: authHeaders() }),
      fetch(`${apiBase}/v1/cases/${caseId}/signoffs`, { headers: authHeaders() }),
    ]);
    if (flagsRes.ok) {
      const data = (await flagsRes.json()) as { flags?: CaseFlag[] };
      setCaseFlags(data.flags ?? []);
    }
    if (evidenceRes.ok) {
      const data = (await evidenceRes.json()) as { evidence?: CaseEvidence[] };
      setCaseEvidence(data.evidence ?? []);
    }
    if (reviewsRes.ok) {
      const data = (await reviewsRes.json()) as { reviews?: CaseReview[] };
      setCaseReviews(data.reviews ?? []);
    }
    if (signoffsRes.ok) {
      const data = (await signoffsRes.json()) as { signoffs?: CaseSignoff[] };
      setCaseSignoffs(data.signoffs ?? []);
    }
  }

=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
  async function loadAudit(auditId: string) {
    const res = await fetch(`${apiBase}/v1/audit/${auditId}`, { headers: authHeaders() });
    if (!res.ok) return;
    const data = (await res.json()) as Record<string, unknown>;
    setAuditDetails(data);
  }

  async function addNote() {
    if (!selectedCaseId || !caseNoteText) return;
    const res = await fetch(`${apiBase}/v1/cases/${selectedCaseId}/notes`, {
      method: "POST",
      headers: authHeaders(),
<<<<<<< HEAD
      body: JSON.stringify({ author: caseNoteAuthor, note_type: caseNoteType, text: caseNoteText }),
=======
      body: JSON.stringify({ text: caseNoteText }),
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
    });
    if (!res.ok) return;
    const note = (await res.json()) as CaseNote;
    setCaseNotes((prev) => [note, ...prev]);
    setCaseNoteText("");
  }

<<<<<<< HEAD
  async function addCaseReview() {
    if (!selectedCaseId) return;
    const res = await fetch(`${apiBase}/v1/cases/${selectedCaseId}/reviews`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        reviewer_user_id: caseReviewUserId || null,
        action: caseReviewAction,
        rationale: caseReviewRationale || null,
        payload: { source: "dashboard" },
      }),
    });
    if (!res.ok) return;
    const review = (await res.json()) as CaseReview;
    setCaseReviews((prev) => [review, ...prev]);
    setCaseReviewRationale("");
  }

  async function addCaseSignoff() {
    if (!selectedCaseId) return;
    const res = await fetch(`${apiBase}/v1/cases/${selectedCaseId}/signoffs`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        signer_user_id: caseSignoffUserId || null,
        signer_role: caseSignoffRole,
        decision: caseSignoffDecision,
        note: caseSignoffNote || null,
      }),
    });
    if (!res.ok) return;
    const signoff = (await res.json()) as CaseSignoff;
    setCaseSignoffs((prev) => [signoff, ...prev]);
    setCaseSignoffNote("");
  }

  async function updateCaseStatus() {
    if (!selectedCaseId) return;
    setCaseStatusMessage("");
    const res = await fetch(`${apiBase}/v1/cases/${selectedCaseId}/status`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ status: caseStatusUpdate }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setCaseStatusMessage(typeof body?.detail === "string" ? body.detail : "Status update failed.");
      return;
    }
    const updated = (await res.json()) as CaseRecord;
    setCases((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
    setCaseStatusMessage("Case status updated.");
  }

  async function addEvidence() {
    if (!selectedCaseId || !evidenceType.trim()) return;
    setEvidenceStatus("");
    const res = await fetch(`${apiBase}/v1/cases/${selectedCaseId}/evidence`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        evidence_type: evidenceType.trim(),
        label: evidenceLabel || null,
        path: evidencePath || null,
        metadata: { source: "dashboard", attached_at: new Date().toISOString() },
      }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setEvidenceStatus(typeof body?.detail === "string" ? body.detail : "Evidence attach failed.");
      return;
    }
    const evidence = (await res.json()) as CaseEvidence;
    setCaseEvidence((prev) => [evidence, ...prev]);
    setEvidenceLabel("");
    setEvidencePath("");
    setEvidenceStatus("Evidence attached.");
  }

  async function importAutoFlags() {
    if (!selectedCaseId || !autoFlagAuditId.trim()) return;
    setAutoFlagStatus("");
    const res = await fetch(`${apiBase}/v1/cases/${selectedCaseId}/auto-flags?audit_id=${encodeURIComponent(autoFlagAuditId.trim())}`, {
      method: "POST",
      headers: authHeaders(),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setAutoFlagStatus(typeof body?.detail === "string" ? body.detail : "Auto-flag import failed.");
      return;
    }
    const data = (await res.json()) as { flags?: CaseFlag[] };
    if (data.flags?.length) {
      setCaseFlags((prev) => [...data.flags!, ...prev]);
      setAutoFlagStatus(`Imported ${data.flags.length} flags.`);
      return;
    }
    setAutoFlagStatus("No triggered signals were available for import.");
  }

  async function generateReport() {
    setReportOutput("");
    setReportStatus("Generating report...");
=======
  async function generateReport() {
    setReportOutput("");
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
    const res = await fetch(`${apiBase}/v1/reports/generate`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        audit_id: reportAuditId || null,
        case_id: reportCaseId || null,
        mode: reportMode,
        export_format: reportFormat,
<<<<<<< HEAD
        use_ai: reportUseAi,
        llm_provider: reportUseAi ? reportProvider : "none",
        llm_model: reportUseAi ? reportModel || null : null,
        llm_api_url: reportUseAi ? reportApiUrl || null : null,
        llm_api_key: reportUseAi ? reportApiKey || null : null,
      }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setReportStatus(typeof body?.detail === "string" ? body.detail : "Report generation failed.");
=======
      }),
    });
    if (!res.ok) {
      setReportOutput("Report generation failed.");
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
      return;
    }
    if (reportFormat === "pdf") {
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setReportOutput(url);
<<<<<<< HEAD
      setReportStatus("PDF generated.");
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
      return;
    }
    const data = await res.json();
    setReportOutput(JSON.stringify(data, null, 2));
<<<<<<< HEAD
    setReportStatus("Report generated.");
  }

  async function refreshBatchRuns() {
    const res = await fetch(`${apiBase}/v1/analyze-pgn-batch-runs?limit=50`, { headers: authHeaders() });
    if (!res.ok) return;
    const data = (await res.json()) as { runs?: BatchRun[] };
    setBatchRuns(data.runs ?? []);
  }

  async function fetchBatchRun(runId: string): Promise<BatchRun | null> {
    const res = await fetch(`${apiBase}/v1/analyze-pgn-batch-runs/${encodeURIComponent(runId)}`, { headers: authHeaders() });
    if (!res.ok) return null;
    return (await res.json()) as BatchRun;
  }

  async function downloadBatchCsv(runId: string, fallbackName?: string | null) {
    const headers: Record<string, string> = { Accept: "text/csv", "X-Role": apiRole };
    if (apiFederationId) headers["X-Federation-Id"] = apiFederationId;
    const res = await fetch(`${apiBase}/v1/analyze-pgn-batch-runs/${encodeURIComponent(runId)}/download.csv`, { headers });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(typeof body?.detail === "string" ? body.detail : "CSV download failed.");
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${(fallbackName || "batch").replace(/\\.pgn$/i, "")}-regan-export.csv`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }

  async function pollBatchRunUntilComplete(runId: string, format: string, sourceName?: string | null) {
    for (let attempt = 0; attempt < 120; attempt += 1) {
      const run = await fetchBatchRun(runId);
      if (run) {
        setBatchRuns((prev) => {
          const remaining = prev.filter((item) => item.id !== run.id);
          return [run, ...remaining];
        });
        if (run.status === "completed") {
          if (format === "csv") {
            setBatchPreview("");
            await downloadBatchCsv(runId, sourceName || run.source_name || batchPgnFileName || "batch");
            setBatchStatus("Batch CSV ready and downloaded.");
          } else {
            setBatchPreview(JSON.stringify(run.response ?? {}, null, 2));
            setBatchStatus("Batch analysis complete.");
          }
          return;
        }
        if (run.status === "failed") {
          setBatchStatus(run.error_text || "Batch analysis failed.");
          return;
        }
        if (run.status === "running") {
          setBatchStatus(`Batch analysis running for ${run.source_name || sourceName || "uploaded PGN"}...`);
        } else if (run.status === "queued") {
          setBatchStatus(`Batch queued for ${run.source_name || sourceName || "uploaded PGN"}...`);
        }
      }
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
    setBatchStatus("Batch is still running. Check recent batch runs below.");
  }

  async function submitBatchPgn() {
    if (!batchPgnText.trim()) {
      setBatchStatus("PGN text or file content is required.");
      return;
    }
    const parsedMaxGames = Number.parseInt(batchMaxGames, 10);
    const safeMaxGames = Number.isFinite(parsedMaxGames) ? Math.max(1, Math.min(500, parsedMaxGames)) : 500;
    if (safeMaxGames !== parsedMaxGames) {
      setBatchMaxGames(String(safeMaxGames));
    }
    setBatchStatus("Submitting batch analysis...");
    setBatchPreview("");
    const form = new FormData();
    form.append("file", new Blob([batchPgnText], { type: "application/x-chess-pgn" }), batchPgnFileName || "batch.pgn");
    form.append("event_id", caseEventId || "");
    form.append("tracked_player_name", batchTrackedPlayerName || "");
    form.append("tracked_player_id", batchTrackedPlayerId || "");
    form.append("default_official_elo", batchDefaultElo || "");
    form.append("max_games", String(safeMaxGames));
    form.append("analyze_both_players", String(batchAnalyzeBoth));
    form.append("response_format", batchResponseFormat);
    form.append("default_player_color", "white");
    const headers: Record<string, string> = { Accept: "application/json", "X-Role": apiRole };
    if (apiFederationId) headers["X-Federation-Id"] = apiFederationId;
    const res = await fetch(`${apiBase}/v1/analyze-pgn-batch-file`, {
      method: "POST",
      headers,
      body: form,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setBatchStatus(typeof body?.detail === "string" ? body.detail : "Batch analysis failed.");
      return;
    }
    const data = (await res.json()) as BatchQueueResponse;
    setBatchPreview("");
    setBatchStatus(data.message || `Batch queued: ${data.batch_run_id}`);
    await refreshBatchRuns();
    void pollBatchRunUntilComplete(data.batch_run_id, batchResponseFormat, data.source_name);
  }

  function onBatchFileSelected(file: File | null) {
    if (!file) return;
    setBatchPgnFileName(file.name);
    const reader = new FileReader();
    reader.onload = () => setBatchPgnText(typeof reader.result === "string" ? reader.result : "");
    reader.readAsText(file);
  }

  async function createPartnerKey() {
    setPartnerStatus("");
    const res = await fetch(`${apiBase}/v1/partner/keys/create`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        partner_name: partnerName,
        webhook_url: partnerWebhook || null,
        rate_limit_per_minute: Math.max(1, Number.parseInt(partnerRateLimit || "60", 10) || 60),
      }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setPartnerStatus(typeof body?.detail === "string" ? body.detail : "Partner key creation failed.");
      return;
    }
    const key = (await res.json()) as PartnerKey;
    setPartnerKeys((prev) => [key, ...prev]);
    setPartnerRevealedKeys((prev) => ({ ...prev, [key.id]: key }));
    setPartnerSelectedKeyId(key.id);
    setPartnerName("");
    setPartnerWebhook("");
    setPartnerRateLimit("60");
    setPartnerStatus(`Created partner key for ${key.partner_name}.`);
  }

  async function refreshPartnerOps() {
    const [keysRes, jobsRes, sessionsRes] = await Promise.all([
      fetch(`${apiBase}/v1/partner/keys`, { headers: authHeaders() }),
      fetch(`${apiBase}/v1/partner/jobs?limit=200`, { headers: authHeaders() }),
      fetch(`${apiBase}/v1/partner/sessions?limit=200`, { headers: authHeaders() }),
    ]);
    if (keysRes.ok) {
      const data = (await keysRes.json()) as { keys?: PartnerKey[] };
      const keys = data.keys ?? [];
      setPartnerKeys(keys);
      setPartnerSelectedKeyId((prev) => prev || keys[0]?.id || "");
    }
    if (jobsRes.ok) {
      const data = (await jobsRes.json()) as { jobs?: PartnerJob[] };
      setPartnerJobs(data.jobs ?? []);
    }
    if (sessionsRes.ok) {
      const data = (await sessionsRes.json()) as { sessions?: PartnerSession[] };
      setPartnerSessions(data.sessions ?? []);
    }
  }

  async function rotatePartnerKeyAction(keyId: string) {
    setPartnerStatus("");
    const res = await fetch(`${apiBase}/v1/partner/keys/${encodeURIComponent(keyId)}/rotate`, {
      method: "POST",
      headers: authHeaders(),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setPartnerStatus(typeof body?.detail === "string" ? body.detail : "Partner key rotation failed.");
      return;
    }
    const updated = (await res.json()) as PartnerKey;
    setPartnerKeys((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
    setPartnerRevealedKeys((prev) => ({ ...prev, [updated.id]: updated }));
    setPartnerSelectedKeyId(updated.id);
    setPartnerStatus(`Rotated credentials for ${updated.partner_name}.`);
  }

  async function disablePartnerKeyAction(keyId: string) {
    setPartnerStatus("");
    const res = await fetch(`${apiBase}/v1/partner/keys/${encodeURIComponent(keyId)}`, {
      method: "DELETE",
      headers: authHeaders(),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setPartnerStatus(typeof body?.detail === "string" ? body.detail : "Partner key deactivation failed.");
      return;
    }
    const updated = (await res.json()) as PartnerKey;
    setPartnerKeys((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
    setPartnerStatus(`${updated.partner_name} key deactivated.`);
  }

  function selectedPartnerKey(): PartnerKey | null {
    const listed = partnerKeys.find((item) => item.id === partnerSelectedKeyId) ?? partnerKeys[0] ?? null;
    if (!listed) return null;
    return partnerRevealedKeys[listed.id] ?? listed;
  }

  async function revealPartnerKey(keyId: string): Promise<PartnerKey | null> {
    const existing = partnerRevealedKeys[keyId];
    if (existing?.key && !existing.key.includes("*")) {
      return existing;
    }
    const res = await fetch(`${apiBase}/v1/partner/keys/${encodeURIComponent(keyId)}/reveal`, {
      headers: authHeaders(),
    });
    if (!res.ok) return null;
    const revealed = (await res.json()) as PartnerKey;
    setPartnerRevealedKeys((prev) => ({ ...prev, [keyId]: revealed }));
    setPartnerKeys((prev) => prev.map((item) => (item.id === keyId ? { ...item, key: revealed.key, secret: revealed.secret } : item)));
    return revealed;
  }

  async function createPartnerSessionAction() {
    const selected = selectedPartnerKey();
    const key = selected ? await revealPartnerKey(selected.id) : null;
    if (!key?.key || !key.active) {
      setPartnerSessionStatus("Select an active partner key first.");
      return;
    }
    setPartnerSessionStatus("Creating session...");
    const res = await fetch(`${apiBase}/v1/partner/session/create`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "x-api-key": key.key,
      },
      body: JSON.stringify({
        game_id: partnerSessionGameId || null,
        player_id: partnerSessionPlayerId || null,
      }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setPartnerSessionStatus(typeof body?.detail === "string" ? body.detail : "Partner session creation failed.");
      return;
    }
    const data = (await res.json()) as { session_id?: string };
    setPartnerSessionStatus(`Session created: ${data.session_id || "unknown"}`);
    await refreshPartnerOps();
  }

  async function runPartnerAnalyze() {
    const selected = selectedPartnerKey();
    const key = selected ? await revealPartnerKey(selected.id) : null;
    if (!key?.key || !key.active) {
      setPartnerTestStatus("Select an active partner key first.");
      return;
    }
    if (!partnerTestPgn.trim()) {
      setPartnerTestStatus("PGN is required.");
      return;
    }
    setPartnerTestStatus("Submitting partner analysis...");
    const res = await fetch(`${apiBase}/v1/partner/analyze`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "x-api-key": key.key,
      },
      body: JSON.stringify({
        game_id: partnerTestGameId || "demo-game-1",
        player_id: partnerTestPlayerId || "demo-player-1",
        player_color: partnerTestColor,
        pgn: partnerTestPgn,
        official_elo: Math.max(100, Number.parseInt(partnerTestElo || "1800", 10) || 1800),
      }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setPartnerTestStatus(typeof body?.detail === "string" ? body.detail : "Partner analysis submission failed.");
      return;
    }
    const data = (await res.json()) as { job_id?: string };
    const jobId = data.job_id || "";
    setPartnerTestStatus(`Partner job accepted: ${jobId}. Polling for result...`);
    await refreshPartnerOps();
    if (!jobId) return;
    for (let attempt = 0; attempt < 10; attempt += 1) {
      await new Promise((resolve) => setTimeout(resolve, 1500));
      const poll = await fetch(`${apiBase}/v1/partner/result/${encodeURIComponent(jobId)}`, {
        headers: { Accept: "application/json", "x-api-key": key.key },
      });
      if (!poll.ok) continue;
      const result = (await poll.json()) as { status?: string; risk_level?: string; risk_score?: number };
      await refreshPartnerOps();
      if (result.status && result.status !== "queued") {
        setPartnerTestStatus(`Job ${jobId} ${result.status}. Risk ${result.risk_level || "None"} at ${formatMaybe(result.risk_score)}.`);
        return;
      }
    }
    setPartnerTestStatus(`Job ${jobId} queued. Refresh the jobs list to inspect progress.`);
  }

  async function loadPlayerProfile(playerId?: string) {
    const target = (playerId ?? playerQuery).trim();
    if (!target) return;
    setPlayerStatus("Loading player profile...");
    const res = await fetch(`${apiBase}/v1/players/${encodeURIComponent(target)}/profile`, { headers: authHeaders() });
    if (!res.ok) {
      setPlayerStatus("Player profile unavailable.");
      return;
    }
    const data = (await res.json()) as PlayerProfileResponse;
    setPlayerProfile(data);
    setPlayerStatus(data.history?.length ? "Player profile loaded." : "No historical snapshots found for this player yet.");
  }

  async function addDeepDiveNoteToCase() {
    if (!selectedCaseId || !deepDiveNote.trim()) return;
    setCaseNoteText(deepDiveNote);
    const res = await fetch(`${apiBase}/v1/cases/${selectedCaseId}/notes`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ author: caseNoteAuthor, note_type: "analysis_note", text: deepDiveNote.trim() }),
    });
    if (!res.ok) return;
    const note = (await res.json()) as CaseNote;
    setCaseNotes((prev) => [note, ...prev]);
    setDeepDiveNote("");
=======
  }

  async function createPartnerKey() {
    const res = await fetch(`${apiBase}/v1/partner/keys/create`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ partner_name: partnerName, webhook_url: partnerWebhook || null }),
    });
    if (!res.ok) return;
    const key = (await res.json()) as PartnerKey;
    setPartnerKeys((prev) => [key, ...prev]);
    setPartnerName("");
    setPartnerWebhook("");
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
  }

  async function connectLive() {
    setLiveEvents([]);
    const socketUrl = `${apiBase.replace("http", "ws")}/ws/live/${liveSessionId}?role=${encodeURIComponent(apiRole)}`;
    const ws = new WebSocket(socketUrl);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as Record<string, unknown>;
        setLiveEvents((prev) => [data, ...prev].slice(0, 200));
      } catch {
        // ignore
      }
    };
  }

<<<<<<< HEAD
  async function createOtbIncident() {
    setOtbIncidentStatus("");
    const res = await fetch(`${apiBase}/v1/otb/incidents`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        case_id: otbIncidentCaseId || null,
        event_id: otbEventId || null,
        player_id: otbIncidentPlayerId || null,
        incident_type: otbIncidentType,
        severity: otbIncidentSeverity,
        description: otbIncidentDescription || null,
        occurred_at: otbIncidentOccurredAt || null,
      }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setOtbIncidentStatus(typeof body?.detail === "string" ? body.detail : "Incident creation failed.");
      return;
    }
    const incident = (await res.json()) as OTBIncidentRecord;
    setOtbIncidents((prev) => [incident, ...prev]);
    setOtbIncidentPlayerId("");
    setOtbIncidentCaseId("");
    setOtbIncidentType("suspicious_behavior");
    setOtbIncidentSeverity("medium");
    setOtbIncidentDescription("");
    setOtbIncidentOccurredAt("");
    setOtbIncidentStatus("Incident saved.");
  }

  async function connectDgtBoard() {
    setOtbConnectStatus("");
    const sdk = (window as Window & { SentinelSDK?: { connectDgtWebSerial?: (options: { eventId?: string; sessionId?: string }) => Promise<void> } }).SentinelSDK;
    if (!sdk || typeof sdk.connectDgtWebSerial !== "function") {
      setOtbConnectStatus("Sentinel SDK not loaded or missing DGT support.");
      return;
    }
    try {
      await sdk.connectDgtWebSerial({
        eventId: otbEventId || undefined,
        sessionId: liveSessionId || undefined,
      });
      setOtbConnectStatus("DGT board connected.");
    } catch (err: unknown) {
      setOtbConnectStatus(err instanceof Error ? err.message : "DGT connection failed.");
    }
  }

=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
  useEffect(() => {
    let cancelled = false;
    async function refreshLiveRisk() {
      if (!liveSessionId) return;
      try {
        const res = await fetch(`${apiBase}/v1/live/sessions/${liveSessionId}/risk`, { headers: authHeaders() });
        if (!res.ok) return;
        const data = (await res.json()) as Record<string, unknown>;
        if (!cancelled) setLiveRisk(data);
      } catch {
        // ignore
      }
    }
    refreshLiveRisk();
    const poll = setInterval(refreshLiveRisk, 5000);
    return () => {
      cancelled = true;
      clearInterval(poll);
    };
  }, [apiBase, apiRole, apiFederationId, liveSessionId]);

  return (
    <main className="dashRoot">
      <header className="topBar">
        <div>
          <div className="wordmark">Hamduk Labs Sentinel</div>
          <div className="muted">Forensic Arbiter Assistant</div>
        </div>
        <div className="topCenter">
          <div className="tourney">Sentinel Tournament - Live</div>
          <div className="monoData">
            {formatClock(now)} | Round remaining: None
          </div>
        </div>
        <div className="topRight">
          <div className="statusRow">
            <span className={`statusDot ${apiDotClass}`}>API</span>
            <span className={`statusDot ${supabaseReady ? "ok" : "bad"}`}>Supabase</span>
            <span className={`statusDot ${stockfishDotClass}`}>Stockfish</span>
            <span className={`statusDot ${mlDotClass}`}>ML Fusion</span>
            <span className={`statusDot ${maiaDotClass}`}>Maia</span>
            <span className="statusDot warn">DGT Feed</span>
          </div>
          <div className="arbiterMeta">
            <span className="monoData">Latency: {apiLatencyMs ?? "None"} ms</span>
            <span className="roleBadge">Checked {apiCheckedAt ? new Date(apiCheckedAt).toLocaleTimeString() : "None"}</span>
            <button className="escalateBtn" type="button">Emergency Escalation</button>
          </div>
        </div>
      </header>

      <nav className="dashNav">
        {navItems.map((item) => (
<<<<<<< HEAD
          <button
            key={item.id}
            className={page === item.id ? "navBtn active" : "navBtn"}
            onClick={() => {
              setPage(item.id);
              navigate(pageRoutes[item.id]);
            }}
            type="button"
          >
=======
          <button key={item.id} className={page === item.id ? "navBtn active" : "navBtn"} onClick={() => setPage(item.id)} type="button">
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
            {item.label}
          </button>
        ))}
      </nav>

      {page === "command" ? (
        <section className="commandGrid">
          <section className="panel panelMain">
            <div className="panelHead">
              <h2>Live Game Feed</h2>
              <div className="muted">Sorted by weighted risk score</div>
            </div>
            {games.length === 0 ? (
              <div className="muted">None</div>
            ) : (
              <div className="gameGrid">
                {games.map((g, idx) => {
                  const tier = normalizeRiskTier(g.risk_tier);
                  return (
<<<<<<< HEAD
                    <article key={g.game_id} className="gameCard" onClick={() => { setSelectedGameId(g.game_id); setPage("deep-dive"); navigate(`/deep-dive?auditId=${encodeURIComponent(g.audit_id)}`); }}>
=======
                    <article key={g.game_id} className="gameCard" onClick={() => { setSelectedGameId(g.game_id); setPage("deep-dive"); }}>
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
                      <div className="cardRow">
                        <div>
                          <strong>{g.player_id || "None"}</strong>
                          <div className="muted">FIDE {g.player_id || "None"} | {g.official_elo || "None"}</div>
                        </div>
                        <RiskPill tier={tier} />
                      </div>
                      <div className="muted">Event {g.event_id || "None"} | Move {g.move_number || "None"}</div>
                      <Sparkline values={g.sparkline || []} />
                      <div className="riskBar"><span style={{ width: `${Math.round((g.weighted_risk_score || 0) * 100)}%` }} /></div>
                      <div className="monoData">Weighted Risk: {Number.isFinite(g.weighted_risk_score) ? g.weighted_risk_score.toFixed(3) : "None"}</div>
                      <div className="muted">Board: {idx + 1} | Audit: {g.audit_id || "None"}</div>
                    </article>
                  );
                })}
              </div>
            )}
          </section>

          <aside className="panel panelSide">
            <div className="panelHead">
              <h2>Alert Queue</h2>
              <div className="muted">Chronological triggered signals</div>
            </div>
            {feedAlerts.length === 0 ? (
              <div className="muted">None</div>
            ) : (
              <div className="alertList">
                {feedAlerts.map((a) => (
                  <article className="alertItem" key={a.id}>
                    <div className="cardRow">
                      <strong>{a.timestamp ? new Date(a.timestamp).toLocaleTimeString() : "None"}</strong>
                      <span className={reviewedAlerts[a.id] ? "miniBadge reviewed" : "miniBadge pending"}>
                        {reviewedAlerts[a.id] ? "Reviewed" : "Pending"}
                      </span>
                    </div>
                    <div>{a.player_id || "None"}</div>
                    <div className="muted">{a.layer || "None"}: {(a.score ?? 0).toFixed(2)} / {(a.threshold ?? 0).toFixed(2)}</div>
                    <div>{a.description || "None"}</div>
                    <div className="buttonRow">
                      <button type="button" className="ghostBtn" onClick={() => setReviewedAlerts((prev) => ({ ...prev, [a.id]: true }))}>Mark Reviewed</button>
                      <button type="button" className="warnBtn">Escalate</button>
                    </div>
                  </article>
                ))}
              </div>
            )}
            <div className="statsRow">
              <div><span className="monoData">{feedSummary?.total_games_analyzed_today ?? "None"}</span><div className="muted">Games Today</div></div>
              <div><span className="monoData">{feedSummary?.games_elevated_or_above ?? "None"}</span><div className="muted">Elevated+</div></div>
              <div><span className="monoData">{feedSummary ? awaitingReview : "None"}</span><div className="muted">Awaiting Review</div></div>
              <div><span className="monoData">{feedSummary ? feedSummary.average_regan_z_score.toFixed(3) : "None"}</span><div className="muted">Avg Regan Z</div></div>
            </div>
          </aside>

          <section className="panel pgnWorkbench">
            <div className="panelHead">
              <h2>PGN Analysis Workbench</h2>
              <div className="muted">Run direct PGN analysis from the dashboard</div>
            </div>
            <AnalysisConsole apiBase={apiBase} apiRole={apiRole} apiFederationId={apiFederationId} />
          </section>
        </section>
      ) : null}

      {page === "deep-dive" ? (
<<<<<<< HEAD
        <DeepDiveSection
          selectedGame={selectedGame}
          selectedCase={selectedCase}
          deepDiveNote={deepDiveNote}
          setDeepDiveNote={setDeepDiveNote}
          deepDiveMoves={deepDiveMoves}
          auditRequest={auditRequest}
          auditResponse={auditResponse}
          cpLossSeries={cpLossSeries}
          impliedRatingSeries={impliedRatingSeries}
          renderRiskPill={(tier) => <RiskPill tier={tier ? normalizeRiskTier(tier) : null} />}
          renderSparkline={(values) => <Sparkline values={values} />}
          onGenerateReport={() => {
            if (!selectedGame) return;
            setReportAuditId(selectedGame.audit_id);
            setPage("report");
            navigate(`/report?auditId=${encodeURIComponent(selectedGame.audit_id)}`);
          }}
          onOpenPlayer={() => {
            if (!selectedGame) return;
            setPlayerQuery(selectedGame.player_id);
            setPage("player");
            navigate(`/player?playerId=${encodeURIComponent(selectedGame.player_id)}`);
            void loadPlayerProfile(selectedGame.player_id);
          }}
          onCopyAuditId={() => {
            if (selectedGame) copyText(selectedGame.audit_id);
          }}
          onAddNoteToCase={addDeepDiveNoteToCase}
          onOpenCases={() => {
            setPage("cases");
            navigate(selectedCaseId ? `/cases?caseId=${encodeURIComponent(selectedCaseId)}` : "/cases");
          }}
        />
      ) : null}

      {page === "player" ? (
        <PlayerSection
          playerQuery={playerQuery}
          setPlayerQuery={setPlayerQuery}
          playerStatus={playerStatus}
          playerProfile={playerProfile}
          onLoad={() => void loadPlayerProfile()}
          onCopy={copyText}
        />
      ) : null}

      {page === "cases" ? (
        <CasesSection
          cases={cases}
          selectedCase={selectedCase}
          caseTitle={caseTitle}
          caseEventId={caseEventId}
          casePlayers={casePlayers}
          caseSummary={caseSummary}
          caseTags={caseTags}
          casePriority={casePriority}
          caseAssignedTo={caseAssignedTo}
          setCaseTitle={setCaseTitle}
          setCaseEventId={setCaseEventId}
          setCasePlayers={setCasePlayers}
          setCaseSummary={setCaseSummary}
          setCaseTags={setCaseTags}
          setCasePriority={setCasePriority}
          setCaseAssignedTo={setCaseAssignedTo}
          caseNoteAuthor={caseNoteAuthor}
          caseNoteType={caseNoteType}
          caseNoteText={caseNoteText}
          setCaseNoteAuthor={setCaseNoteAuthor}
          setCaseNoteType={setCaseNoteType}
          setCaseNoteText={setCaseNoteText}
          caseReviewUserId={caseReviewUserId}
          caseReviewAction={caseReviewAction}
          caseReviewRationale={caseReviewRationale}
          caseSignoffUserId={caseSignoffUserId}
          caseSignoffRole={caseSignoffRole}
          caseSignoffDecision={caseSignoffDecision}
          caseSignoffNote={caseSignoffNote}
          setCaseReviewUserId={setCaseReviewUserId}
          setCaseReviewAction={setCaseReviewAction}
          setCaseReviewRationale={setCaseReviewRationale}
          setCaseSignoffUserId={setCaseSignoffUserId}
          setCaseSignoffRole={setCaseSignoffRole}
          setCaseSignoffDecision={setCaseSignoffDecision}
          setCaseSignoffNote={setCaseSignoffNote}
          caseNotes={caseNotes}
          caseReviews={caseReviews}
          caseSignoffs={caseSignoffs}
          caseFlags={caseFlags}
          caseEvidence={caseEvidence}
          caseStatusUpdate={caseStatusUpdate}
          caseStatusMessage={caseStatusMessage}
          evidenceType={evidenceType}
          evidenceLabel={evidenceLabel}
          evidencePath={evidencePath}
          evidenceStatus={evidenceStatus}
          setEvidenceType={setEvidenceType}
          setEvidenceLabel={setEvidenceLabel}
          setEvidencePath={setEvidencePath}
          setCaseStatusUpdate={setCaseStatusUpdate}
          linkedAnalyses={linkedAnalyses}
          autoFlagAuditId={autoFlagAuditId}
          autoFlagStatus={autoFlagStatus}
          setAutoFlagAuditId={setAutoFlagAuditId}
          onCreateCase={createCase}
          onSelectCase={(caseId) => {
            setSelectedCaseId(caseId);
            navigate(`/cases?caseId=${encodeURIComponent(caseId)}`);
          }}
          onAddNote={addNote}
          onAddReview={addCaseReview}
          onAddSignoff={addCaseSignoff}
          onUpdateStatus={updateCaseStatus}
          onAddEvidence={addEvidence}
          onAutoFlag={importAutoFlags}
          onOpenAnalysis={(auditId) => {
            setPage("deep-dive");
            navigate(`/deep-dive?auditId=${encodeURIComponent(auditId)}`);
          }}
        />
      ) : null}

      {page === "live" ? (
        <LiveSection
          liveSessionId={liveSessionId}
          liveEvents={liveEvents}
          liveRisk={liveRisk}
          setLiveSessionId={setLiveSessionId}
          onConnect={connectLive}
        />
      ) : null}

      {page === "report" ? (
        <ReportSection
          reportAuditId={reportAuditId}
          reportCaseId={reportCaseId}
          reportMode={reportMode}
          reportFormat={reportFormat}
          reportUseAi={reportUseAi}
          reportProvider={reportProvider}
          reportModel={reportModel}
          reportApiUrl={reportApiUrl}
          reportApiKey={reportApiKey}
          reportOutput={reportOutput}
          reportStatus={reportStatus}
          batchPgnFileName={batchPgnFileName}
          batchTrackedPlayerName={batchTrackedPlayerName}
          batchTrackedPlayerId={batchTrackedPlayerId}
          batchDefaultElo={batchDefaultElo}
          batchMaxGames={batchMaxGames}
          batchAnalyzeBoth={batchAnalyzeBoth}
          batchResponseFormat={batchResponseFormat}
          batchStatus={batchStatus}
          batchPreview={batchPreview}
          batchRuns={batchRuns}
          setReportAuditId={setReportAuditId}
          setReportCaseId={setReportCaseId}
          setReportMode={setReportMode}
          setReportFormat={setReportFormat}
          setReportUseAi={setReportUseAi}
          setReportProvider={setReportProvider}
          setReportModel={setReportModel}
          setReportApiUrl={setReportApiUrl}
          setReportApiKey={setReportApiKey}
          setBatchTrackedPlayerName={setBatchTrackedPlayerName}
          setBatchTrackedPlayerId={setBatchTrackedPlayerId}
          setBatchDefaultElo={setBatchDefaultElo}
          setBatchMaxGames={setBatchMaxGames}
          setBatchAnalyzeBoth={setBatchAnalyzeBoth}
          setBatchResponseFormat={setBatchResponseFormat}
          onGenerate={generateReport}
          onBatchFileSelected={onBatchFileSelected}
          onSubmitBatchPgn={() => void submitBatchPgn()}
          onDownloadBatchCsv={(runId, sourceName) => void downloadBatchCsv(runId, sourceName)}
        />
      ) : null}

      {page === "tournament" ? (
        <TournamentSection
          tournamentEventId={selectedGame?.event_id ?? ""}
          tournamentPlayers={tournamentPlayers}
          tournamentAlerts={tournamentAlerts}
          onOpenPlayer={(playerId) => {
            setPlayerQuery(playerId);
            setPage("player");
            navigate(`/player?playerId=${encodeURIComponent(playerId)}`);
          }}
        />
      ) : null}

      {page === "partner" ? (
        <PartnerSection
          apiBase={apiBase}
          partnerName={partnerName}
          partnerWebhook={partnerWebhook}
          partnerRateLimit={partnerRateLimit}
          partnerStatus={partnerStatus}
          partnerKeys={partnerKeys}
          partnerJobs={partnerJobs}
          partnerSessions={partnerSessions}
          partnerSelectedKeyId={partnerSelectedKeyId}
          partnerTestGameId={partnerTestGameId}
          partnerTestPlayerId={partnerTestPlayerId}
          partnerTestColor={partnerTestColor}
          partnerTestElo={partnerTestElo}
          partnerTestPgn={partnerTestPgn}
          partnerTestStatus={partnerTestStatus}
          partnerSessionGameId={partnerSessionGameId}
          partnerSessionPlayerId={partnerSessionPlayerId}
          partnerSessionStatus={partnerSessionStatus}
          setPartnerName={setPartnerName}
          setPartnerWebhook={setPartnerWebhook}
          setPartnerRateLimit={setPartnerRateLimit}
          setPartnerSelectedKeyId={setPartnerSelectedKeyId}
          setPartnerTestGameId={setPartnerTestGameId}
          setPartnerTestPlayerId={setPartnerTestPlayerId}
          setPartnerTestColor={setPartnerTestColor}
          setPartnerTestElo={setPartnerTestElo}
          setPartnerTestPgn={setPartnerTestPgn}
          setPartnerSessionGameId={setPartnerSessionGameId}
          setPartnerSessionPlayerId={setPartnerSessionPlayerId}
          onCreate={createPartnerKey}
          onCopy={copyText}
          onRotate={rotatePartnerKeyAction}
          onDisable={disablePartnerKeyAction}
          onCreateSession={createPartnerSessionAction}
          onRunAnalyze={runPartnerAnalyze}
          onRefreshPartnerOps={refreshPartnerOps}
        />
      ) : null}

      {page === "otb" ? (
        <OTBSection
          cases={cases.map((item) => ({ id: item.id, title: item.title }))}
          otbEventId={otbEventId}
          otbConnectStatus={otbConnectStatus}
          otbCameraEvents={otbCameraEvents}
          otbBoardEvents={otbBoardEvents}
          otbIncidents={otbIncidents}
          otbIncidentPlayerId={otbIncidentPlayerId}
          otbIncidentCaseId={otbIncidentCaseId}
          otbIncidentType={otbIncidentType}
          otbIncidentSeverity={otbIncidentSeverity}
          otbIncidentDescription={otbIncidentDescription}
          otbIncidentOccurredAt={otbIncidentOccurredAt}
          otbIncidentStatus={otbIncidentStatus}
          setOtbEventId={setOtbEventId}
          setOtbIncidentPlayerId={setOtbIncidentPlayerId}
          setOtbIncidentCaseId={setOtbIncidentCaseId}
          setOtbIncidentType={setOtbIncidentType}
          setOtbIncidentSeverity={setOtbIncidentSeverity}
          setOtbIncidentDescription={setOtbIncidentDescription}
          setOtbIncidentOccurredAt={setOtbIncidentOccurredAt}
          onConnectDgt={connectDgtBoard}
          onCreateIncident={createOtbIncident}
        />
      ) : null}

      {page === "admin" ? (
        <AdminSection
          systemStatus={systemStatus}
          systemStatusError={systemStatusError}
          missingEnvVars={missingEnvVars}
        />
=======
        <section className="stacked">
          <article className="panel">
            <div className="panelHead">
              <h2>Game Deep Dive</h2>
              <RiskPill tier={selectedGame ? normalizeRiskTier(selectedGame.risk_tier) : null} />
            </div>
            {selectedGame ? (
              <div className="muted">
                Player: {selectedGame.player_id || "None"} | Event: {selectedGame.event_id || "None"} | Move: {selectedGame.move_number || "None"} |
                Confidence: {Number.isFinite(selectedGame.confidence) ? selectedGame.confidence.toFixed(3) : "None"} |
                Audit ID: {selectedGame.audit_id || "None"}
              </div>
            ) : (
              <div className="muted">None</div>
            )}
          </article>
          <article className="panel">
            <h3>Charts</h3>
            <div className="muted">None</div>
          </article>
          <article className="panel">
            <h3>Behavioral Metrics</h3>
            {auditDetails && (auditDetails as any).response ? (
              <pre className="previewPane">
                {JSON.stringify((auditDetails as any).response?.behavioral_metrics ?? {}, null, 2)}
              </pre>
            ) : (
              <div className="muted">No behavioral telemetry available.</div>
            )}
          </article>
          <article className="panel">
            <h3>Move-by-Move Table</h3>
            <div className="muted">None</div>
          </article>
          <article className="panel">
            <h3>Arbiter Notes</h3>
            <div className="muted">None</div>
          </article>
        </section>
      ) : null}

      {page === "player" ? (
        <section className="stacked">
          <article className="panel"><h2>Player Profile</h2><div className="muted">None</div></article>
        </section>
      ) : null}

      {page === "cases" ? (
        <section className="stacked">
          <article className="panel">
            <div className="panelHead">
              <h2>Create Case</h2>
              <button className="ghostBtn" type="button" onClick={createCase}>Create</button>
            </div>
            <div className="formGrid">
              <input placeholder="Title" value={caseTitle} onChange={(e) => setCaseTitle(e.target.value)} />
              <input placeholder="Event ID (optional)" value={caseEventId} onChange={(e) => setCaseEventId(e.target.value)} />
              <input placeholder="Players (comma-separated)" value={casePlayers} onChange={(e) => setCasePlayers(e.target.value)} />
            </div>
          </article>
          <article className="panel">
            <div className="panelHead">
              <h2>Cases</h2>
              <div className="muted">{cases.length} total</div>
            </div>
            {cases.length === 0 ? (
              <div className="muted">None</div>
            ) : (
              <div className="alertList">
                {cases.map((c) => (
                  <article key={c.id} className="alertItem" onClick={() => { setSelectedCaseId(c.id); loadCaseNotes(c.id); }}>
                    <div className="cardRow">
                      <strong>{c.title}</strong>
                      <span className="miniBadge pending">{c.status}</span>
                    </div>
                    <div className="muted">Event: {c.event_id || "None"}</div>
                    <div className="muted">Players: {c.players.join(", ") || "None"}</div>
                  </article>
                ))}
              </div>
            )}
          </article>
          <article className="panel notesPanel">
            <div className="panelHead">
              <h2>Case Notes</h2>
              <button className="ghostBtn" type="button" onClick={addNote}>Add Note</button>
            </div>
            <textarea rows={4} placeholder="Add arbiter note..." value={caseNoteText} onChange={(e) => setCaseNoteText(e.target.value)} />
            <div className="alertList">
              {caseNotes.length ? caseNotes.map((n) => (
                <div className="alertItem" key={n.id}>
                  <div className="cardRow">
                    <strong>{n.author || "Arbiter"}</strong>
                    <span className="miniBadge reviewed">{n.created_at ? new Date(n.created_at).toLocaleTimeString() : ""}</span>
                  </div>
                  <div>{n.text || "Note"}</div>
                </div>
              )) : <div className="muted">No notes yet.</div>}
            </div>
          </article>
        </section>
      ) : null}

      {page === "live" ? (
        <section className="stacked">
          <article className="panel">
            <div className="panelHead">
              <h2>Live Monitor</h2>
              <button className="ghostBtn" type="button" onClick={connectLive}>Connect</button>
            </div>
            <div className="formGrid">
              <input placeholder="Session ID" value={liveSessionId} onChange={(e) => setLiveSessionId(e.target.value)} />
              <div className="muted">Connect to a live session to view events.</div>
            </div>
            <div className="monoData">Risk: {liveRisk ? JSON.stringify(liveRisk) : "None"}</div>
          </article>
          <article className="panel">
            <h2>Live Event Stream</h2>
            <div className="alertList">
              {liveEvents.length ? liveEvents.map((e, idx) => (
                <div className="alertItem" key={`evt-${idx}`}>
                  <pre className="monoData">{JSON.stringify(e)}</pre>
                </div>
              )) : <div className="muted">No events yet.</div>}
            </div>
          </article>
        </section>
      ) : null}

      {page === "report" ? (
        <section className="stacked">
          <article className="panel">
            <div className="panelHead">
              <h2>Report Composer</h2>
              <button className="ghostBtn" type="button" onClick={generateReport}>Generate</button>
            </div>
            <div className="formGrid">
              <input placeholder="Audit ID (optional)" value={reportAuditId} onChange={(e) => setReportAuditId(e.target.value)} />
              <input placeholder="Case ID (optional)" value={reportCaseId} onChange={(e) => setReportCaseId(e.target.value)} />
              <select value={reportMode} onChange={(e) => setReportMode(e.target.value)}>
                <option value="technical">Technical</option>
                <option value="arbiter">Arbiter</option>
                <option value="legal">Legal</option>
              </select>
              <select value={reportFormat} onChange={(e) => setReportFormat(e.target.value)}>
                <option value="json">JSON</option>
                <option value="csv">CSV</option>
                <option value="pdf">PDF</option>
              </select>
            </div>
            {reportFormat === "pdf" && reportOutput ? (
              <a className="ghostBtn" href={reportOutput} target="_blank" rel="noreferrer">Open PDF</a>
            ) : null}
            {reportOutput ? <pre className="previewPane">{reportOutput}</pre> : <div className="muted">No report generated yet.</div>}
          </article>
        </section>
      ) : null}

      {page === "tournament" ? (
        <section className="stacked">
          <article className="panel">
            <h2>Tournament Dashboard</h2>
            {tournamentPlayers.length ? (
              <div className="alertList">
                {tournamentPlayers.map((p, idx) => (
                  <div className="alertItem" key={`tp-${idx}`}>
                    <div className="cardRow">
                      <strong>{String(p.player_id || "player")}</strong>
                      <span className="miniBadge pending">{String(p.risk_tier || "")}</span>
                    </div>
                    <div className="muted">Avg Risk Score: {String(p.avg_risk_score || "")}</div>
                  </div>
                ))}
              </div>
            ) : <div className="muted">No tournament data yet.</div>}
          </article>
          <article className="panel">
            <h2>Alerts</h2>
            {tournamentAlerts.length ? (
              <div className="alertList">
                {tournamentAlerts.map((a, idx) => (
                  <div className="alertItem" key={`ta-${idx}`}>{String(a.message || "")}</div>
                ))}
              </div>
            ) : <div className="muted">No alerts.</div>}
          </article>
        </section>
      ) : null}

      {page === "partner" ? (
        <section className="stacked">
          <article className="panel">
            <div className="panelHead">
              <h2>Partner Keys</h2>
              <button className="ghostBtn" type="button" onClick={createPartnerKey}>Create</button>
            </div>
            <div className="formGrid">
              <input placeholder="Partner name" value={partnerName} onChange={(e) => setPartnerName(e.target.value)} />
              <input placeholder="Webhook URL (optional)" value={partnerWebhook} onChange={(e) => setPartnerWebhook(e.target.value)} />
            </div>
          </article>
          <article className="panel">
            {partnerKeys.length ? (
              <div className="alertList">
                {partnerKeys.map((k) => (
                  <div className="alertItem" key={k.id}>
                    <div className="cardRow">
                      <strong>{k.partner_name}</strong>
                      <span className="miniBadge reviewed">{k.active ? "active" : "disabled"}</span>
                    </div>
                    <div className="monoData">Key: {k.key}</div>
                    <div className="monoData">Secret: {k.secret}</div>
                    <div className="muted">Webhook: {k.webhook_url || "None"}</div>
                  </div>
                ))}
              </div>
            ) : <div className="muted">No partner keys.</div>}
          </article>
        </section>
      ) : null}

      {page === "otb" ? (
        <section className="stacked">
          <article className="panel">
            <div className="panelHead">
              <h2>OTB Monitor</h2>
              <div className="muted">Camera events and DGT board feeds for OTB sessions.</div>
            </div>
            <div className="formGrid">
              <input placeholder="Event ID (optional)" value={otbEventId} onChange={(e) => setOtbEventId(e.target.value)} />
              <div className="muted">Filter by event to isolate a tournament or board batch.</div>
            </div>
            <div className="buttonRow">
              <button
                className="ghostBtn"
                type="button"
                onClick={async () => {
                  setOtbConnectStatus("");
                  const sdk = (window as any).SentinelSDK;
                  if (!sdk || typeof sdk.connectDgtWebSerial !== "function") {
                    setOtbConnectStatus("Sentinel SDK not loaded or missing DGT support.");
                    return;
                  }
                  try {
                    await sdk.connectDgtWebSerial({
                      eventId: otbEventId || undefined,
                      sessionId: liveSessionId || undefined,
                    });
                    setOtbConnectStatus("DGT board connected.");
                  } catch (err: any) {
                    setOtbConnectStatus(err?.message || "DGT connection failed.");
                  }
                }}
              >
                Connect DGT Board
              </button>
              {otbConnectStatus ? <div className="muted">{otbConnectStatus}</div> : null}
            </div>
            <div className="muted">
              Web Serial requires Chrome/Edge over HTTPS (or localhost) and a user gesture to select the board.
            </div>
          </article>
          <article className="panel">
            <div className="panelHead">
              <h2>OTB Camera Events</h2>
              <div className="muted">{otbCameraEvents.length} events</div>
            </div>
            {otbCameraEvents.length ? (
              <div className="alertList">
                {otbCameraEvents.map((evt) => (
                  <article className="alertItem" key={evt.id}>
                    <div className="cardRow">
                      <strong>{evt.player_id || "Unknown player"}</strong>
                      <span className="miniBadge pending">{evt.storage_mode || "safe"}</span>
                    </div>
                    <div className="muted">
                      Event: {evt.event_id || "None"} | Session: {evt.session_id || "None"} | Camera: {evt.camera_id || "None"}
                    </div>
                    <pre className="previewPane">{JSON.stringify(evt.summary ?? {}, null, 2)}</pre>
                  </article>
                ))}
              </div>
            ) : (
              <div className="muted">No camera events.</div>
            )}
          </article>
          <article className="panel">
            <div className="panelHead">
              <h2>DGT Board Events</h2>
              <div className="muted">{otbBoardEvents.length} events</div>
            </div>
            {otbBoardEvents.length ? (
              <div className="alertList">
                {otbBoardEvents.map((evt) => (
                  <article className="alertItem" key={evt.id}>
                    <div className="cardRow">
                      <strong>{evt.board_serial || "Board"}</strong>
                      <span className="miniBadge reviewed">{evt.session_id || "session"}</span>
                    </div>
                    <div className="muted">Event: {evt.event_id || "None"} | Move: {evt.move_uci || "None"} | Ply: {evt.ply ?? "None"}</div>
                    <div className="monoData">Clock: {evt.clock_ms ?? "None"} ms</div>
                  </article>
                ))}
              </div>
            ) : (
              <div className="muted">No DGT board events.</div>
            )}
          </article>
        </section>
      ) : null}

      {page === "admin" ? (
        <section className="adminGrid">
          <article className="panel">
            <div className="panelHead">
              <h2>System Status</h2>
              <span className="badge on">Live</span>
            </div>
            {systemStatus ? (
              <>
                <div className="muted">Updated {new Date(systemStatus.generated_at_utc).toLocaleTimeString()}</div>
                <div className="monoData">Warnings: {systemStatus.warnings.length}</div>
                {systemStatus.warnings.length ? (
                  <div className="alertList">
                    {systemStatus.warnings.map((w) => (
                      <div className="miniBadge danger" key={w}>{w}</div>
                    ))}
                  </div>
                ) : (
                  <div className="miniBadge safe">No warnings</div>
                )}
              </>
            ) : (
              <div className="muted">{systemStatusError ?? "Loading..."}</div>
            )}
          </article>

          <article className="panel">
            <h2>Calibration Profile</h2>
            {systemStatus ? (
              <>
                <div className="muted">Source: {systemStatus.calibration?.source ?? "unknown"}</div>
                <div className="monoData">Version: {systemStatus.calibration?.profile_version ?? "unknown"}</div>
                <div className="monoData">Bands: {systemStatus.calibration?.band_count ?? "None"}</div>
                <div className="muted">
                  Coverage: {systemStatus.calibration?.coverage_min_elo ?? "None"} to {systemStatus.calibration?.coverage_max_elo ?? "None"}
                </div>
                <div className="muted">QA: {systemStatus.calibration?.qa?.ok === false ? "Failed" : "OK"}</div>
              </>
            ) : (
              <div className="muted">{systemStatusError ?? "Loading..."}</div>
            )}
          </article>

          <article className="panel">
            <h2>Model Artifacts</h2>
            {systemStatus ? (
              <>
                <div className="muted">ML Fusion: {systemStatus.ml_fusion?.enabled ? "Enabled" : "Disabled"}</div>
                <div className="monoData">Primary: {systemStatus.ml_fusion?.primary?.exists ? "Present" : "Missing"}</div>
                <div className="monoData">Secondary: {systemStatus.ml_fusion?.secondary?.exists ? "Present" : "Missing"}</div>
                <div className="muted">Maia Buckets: {systemStatus.maia?.available_count ?? 0}</div>
                <div className="muted">Maia LC0: {systemStatus.maia?.lc0_path ? "Configured" : "Missing"}</div>
                <div className="muted">Maia Version: {systemStatus.maia?.version ?? "unknown"}</div>
              </>
            ) : (
              <div className="muted">{systemStatusError ?? "Loading..."}</div>
            )}
          </article>

          <article className="panel">
            <h2>System Config</h2>
            <div className="muted">Missing env: {missingEnvVars.length ? missingEnvVars.join(", ") : "None"}</div>
            <div className="muted">Opening Book: {systemStatus?.opening_book?.exists ? "Present" : "Missing"}</div>
            <div className="muted">Tablebase: {systemStatus?.tablebase?.exists ? "Present" : "Missing"}</div>
          </article>
        </section>
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
      ) : null}

      <footer className="stickyDisclaimer">
        Statistical analysis only. All findings require human adjudication. This system does not determine guilt.
      </footer>
    </main>
  );
}
