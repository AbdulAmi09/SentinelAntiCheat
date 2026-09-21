"use client";

type SelectedGame = {
  player_id: string;
  event_id: string;
  move_number: number;
  confidence: number;
  risk_tier: string;
  audit_id: string;
};

type AuditMove = {
  ply: number;
  player_move: string;
  engine_best: string;
  cp_loss: number;
  complexity_score?: number;
  maia_probability?: number | null;
  time_spent_seconds?: number | null;
  is_opening_book?: boolean;
  is_tablebase?: boolean;
  is_forced?: boolean;
};

type CaseRecord = {
  id: string;
  created_at?: string;
  updated_at?: string;
  title: string;
  status: string;
  event_id?: string | null;
  players: string[];
  summary?: string | null;
  tags?: string[];
  priority?: string | null;
  assigned_to?: string | null;
};

type CaseNote = {
  id: string;
  created_at: string;
  author?: string | null;
  note_type?: string | null;
  text?: string | null;
  structured?: Record<string, unknown>;
};

type CaseFlag = {
  id: string;
  created_at?: string;
  flag_type?: string;
  severity?: string;
  message?: string;
  metadata?: Record<string, unknown>;
};

type CaseEvidence = {
  id: string;
  created_at?: string;
  evidence_type?: string;
  label?: string | null;
  path?: string | null;
  metadata?: Record<string, unknown>;
};

type LinkedAnalysis = {
  audit_id: string;
  player_id: string;
  event_id: string;
  risk_tier: string;
  weighted_risk_score: number;
  created_at?: string;
};

type PlayerProfileResponse = {
  player_id: string;
  profile: Record<string, unknown>;
  history: Array<Record<string, unknown>>;
};

type PartnerKey = {
  id: string;
  key: string;
  secret: string;
  partner_name: string;
  webhook_url?: string | null;
  rate_limit_per_minute: number;
  active: boolean;
  created_at?: string;
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
};

type BatchRun = {
  id: string;
  created_at: string;
  updated_at: string;
  event_id?: string | null;
  source_name?: string | null;
  status: string;
  response?: {
    players_analyzed?: number;
    games_parsed?: number;
    analyses_generated?: number;
    rows?: Array<{ regan_row?: Record<string, unknown> }>;
    failures?: Array<Record<string, string>>;
  } | null;
  csv_text?: string | null;
  error_text?: string | null;
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

function renderMiniBar(value: number, scale = 1, tone: "risk" | "neutral" = "risk") {
  const width = `${Math.max(0, Math.min(100, Math.round((value / Math.max(scale, 0.0001)) * 100)))}%`;
  return (
    <div className="riskBar">
      <span style={{ width }} />
    </div>
  );
}

function formatMaybe(value: unknown, digits = 3): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(digits) : "None";
}

function numeric(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

export function DeepDiveSection({
  selectedGame,
  selectedCase,
  deepDiveNote,
  setDeepDiveNote,
  deepDiveMoves,
  auditRequest,
  auditResponse,
  cpLossSeries,
  impliedRatingSeries,
  renderRiskPill,
  renderSparkline,
  onGenerateReport,
  onOpenPlayer,
  onCopyAuditId,
  onAddNoteToCase,
  onOpenCases,
}: {
  selectedGame: SelectedGame | null;
  selectedCase: CaseRecord | null;
  deepDiveNote: string;
  setDeepDiveNote: (value: string) => void;
  deepDiveMoves: AuditMove[];
  auditRequest?: { official_elo?: number } | null;
  auditResponse?: {
    weighted_risk_score?: number;
    behavioral_metrics?: Record<string, unknown>;
    environmental_metrics?: Record<string, unknown>;
    identity_confidence?: Record<string, unknown>;
    human_explanations?: string[];
  } | null;
  cpLossSeries: number[];
  impliedRatingSeries: number[];
  renderRiskPill: (tier: string | null) => React.ReactNode;
  renderSparkline: (values: number[]) => React.ReactNode;
  onGenerateReport: () => void;
  onOpenPlayer: () => void;
  onCopyAuditId: () => void;
  onAddNoteToCase: () => void;
  onOpenCases: () => void;
}) {
  return (
    <section className="stacked">
      <article className="panel">
        <div className="panelHead">
          <h2>Game Deep Dive</h2>
          {renderRiskPill(selectedGame?.risk_tier ?? null)}
        </div>
        {selectedGame ? (
          <>
            <div className="muted">
              Player: {selectedGame.player_id || "None"} | Event: {selectedGame.event_id || "None"} | Move: {selectedGame.move_number || "None"} |
              Confidence: {Number.isFinite(selectedGame.confidence) ? selectedGame.confidence.toFixed(3) : "None"} |
              Audit ID: <span className="monoData">{selectedGame.audit_id || "None"}</span>
            </div>
            <div className="buttonRow" style={{ marginTop: 12 }}>
              <button className="ghostBtn" type="button" onClick={onGenerateReport}>Generate Report</button>
              <button className="ghostBtn" type="button" onClick={onOpenPlayer}>Open Player Profile</button>
              <button className="ghostBtn" type="button" onClick={onCopyAuditId}>Copy Audit ID</button>
            </div>
          </>
        ) : (
          <div className="muted">None</div>
        )}
      </article>
      <article className="panel">
        <h3>Charts</h3>
        {deepDiveMoves.length ? (
          <div className="statsRow">
            <div><span className="monoData">{formatMaybe(auditRequest?.official_elo, 0)}</span><div className="muted">Official ELO</div></div>
            <div><span className="monoData">{formatMaybe(auditResponse?.weighted_risk_score)}</span><div className="muted">Weighted Risk</div></div>
            <div><span className="monoData">{formatMaybe(cpLossSeries.reduce((sum, val) => sum + val, 0) / Math.max(1, cpLossSeries.length))}</span><div className="muted">Avg CPL</div></div>
            <div><span className="monoData">{formatMaybe(impliedRatingSeries.reduce((sum, val) => sum + val, 0) / Math.max(1, impliedRatingSeries.length), 0)}</span><div className="muted">Avg Implied Rating</div></div>
          </div>
        ) : (
          <div className="muted">No move visuals available for this audit.</div>
        )}
        {cpLossSeries.length ? renderSparkline(cpLossSeries.map((value) => Math.min(1, value / 100))) : null}
        {impliedRatingSeries.length ? renderSparkline(impliedRatingSeries.map((value) => Math.min(1, value / 3200))) : null}
      </article>
      <article className="panel">
        <h3>Behavioral Metrics</h3>
        {auditResponse ? (
          <pre className="previewPane">
            {JSON.stringify({
              behavioral_metrics: auditResponse.behavioral_metrics ?? {},
              environmental_metrics: auditResponse.environmental_metrics ?? {},
              identity_confidence: auditResponse.identity_confidence ?? {},
            }, null, 2)}
          </pre>
        ) : (
          <div className="muted">No behavioral telemetry available.</div>
        )}
      </article>
      <article className="panel">
        <h3>Move-by-Move Table</h3>
        {deepDiveMoves.length ? (
          <div className="alertList">
            {deepDiveMoves.slice(0, 80).map((move) => (
              <article className="alertItem" key={`mv-${move.ply}`}>
                <div className="cardRow">
                  <strong>Ply {move.ply}</strong>
                  <span className={numeric(move.cp_loss) > 50 ? "miniBadge pending" : "miniBadge reviewed"}>
                    CPL {formatMaybe(move.cp_loss, 0)}
                  </span>
                </div>
                <div className="monoData">Played {move.player_move} | Engine {move.engine_best}</div>
                <div className="muted">
                  Complexity {move.complexity_score ?? "None"} | Maia {formatMaybe(move.maia_probability)} | Time {formatMaybe(move.time_spent_seconds, 1)}s
                </div>
                <div className="muted">
                  Opening {move.is_opening_book ? "yes" : "no"} | Tablebase {move.is_tablebase ? "yes" : "no"} | Forced {move.is_forced ? "yes" : "no"}
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="muted">No move list found in the selected audit payload.</div>
        )}
      </article>
      <article className="panel">
        <h3>Arbiter Notes</h3>
        <div className="muted">Selected case: {selectedCase ? selectedCase.title : "None"}</div>
        <textarea rows={4} placeholder="Add an arbiter note for this game..." value={deepDiveNote} onChange={(e) => setDeepDiveNote(e.target.value)} />
        <div className="buttonRow" style={{ marginTop: 10 }}>
          <button className="ghostBtn" type="button" onClick={onAddNoteToCase} disabled={!selectedCase || !deepDiveNote.trim()}>Add Note To Case</button>
          <button className="ghostBtn" type="button" onClick={onOpenCases}>Open Cases</button>
        </div>
        {auditResponse?.human_explanations?.length ? (
          <div className="alertList" style={{ marginTop: 14 }}>
            {auditResponse.human_explanations.map((item, idx) => (
              <div className="alertItem" key={`hx-${idx}`}>{item}</div>
            ))}
          </div>
        ) : null}
      </article>
    </section>
  );
}

export function PlayerSection({
  playerQuery,
  setPlayerQuery,
  playerStatus,
  playerProfile,
  onLoad,
  onCopy,
}: {
  playerQuery: string;
  setPlayerQuery: (value: string) => void;
  playerStatus: string;
  playerProfile: PlayerProfileResponse | null;
  onLoad: () => void;
  onCopy: (value: string) => void;
}) {
  return (
    <section className="stacked">
      <article className="panel">
        <div className="panelHead">
          <h2>Player Profile</h2>
          <button className="ghostBtn" type="button" onClick={onLoad}>Load</button>
        </div>
        <div className="formGrid">
          <input placeholder="Player ID" value={playerQuery} onChange={(e) => setPlayerQuery(e.target.value)} />
          <div className="muted">{playerStatus || "Search by player ID to load historical risk snapshots."}</div>
        </div>
      </article>
      <article className="panel">
        {playerProfile ? (
          <>
            <div className="cardRow">
              <strong className="monoData">{playerProfile.player_id}</strong>
              <button className="ghostBtn" type="button" onClick={() => onCopy(playerProfile.player_id)}>Copy</button>
            </div>
            <pre className="previewPane">{JSON.stringify(playerProfile.profile ?? {}, null, 2)}</pre>
            <div className="alertList">
              {(playerProfile.history ?? []).map((entry, idx) => {
                const snapshot = (entry.snapshot as Record<string, unknown>) ?? {};
                return (
                  <article className="alertItem" key={`ph-${idx}`}>
                    <div className="cardRow">
                      <strong>{String(entry.event_id ?? snapshot.event_id ?? "event")}</strong>
                      <span className="miniBadge pending">{String(snapshot.risk_tier ?? "unknown")}</span>
                    </div>
                    <div className="muted">
                      Weighted risk {formatMaybe(snapshot.weighted_risk_score)} | Moves {String(snapshot.analyzed_move_count ?? "None")}
                    </div>
                    <div className="muted">{String(entry.created_at ?? "")}</div>
                  </article>
                );
              })}
            </div>
          </>
        ) : (
          <div className="muted">No player profile loaded.</div>
        )}
      </article>
    </section>
  );
}

export function CasesSection({
  cases,
  selectedCase,
  caseTitle,
  caseEventId,
  casePlayers,
  caseSummary,
  caseTags,
  casePriority,
  caseAssignedTo,
  setCaseTitle,
  setCaseEventId,
  setCasePlayers,
  setCaseSummary,
  setCaseTags,
  setCasePriority,
  setCaseAssignedTo,
  caseNoteAuthor,
  caseNoteType,
  caseNoteText,
  caseReviewUserId,
  caseReviewAction,
  caseReviewRationale,
  caseSignoffUserId,
  caseSignoffRole,
  caseSignoffDecision,
  caseSignoffNote,
  setCaseNoteAuthor,
  setCaseNoteType,
  setCaseNoteText,
  setCaseReviewUserId,
  setCaseReviewAction,
  setCaseReviewRationale,
  setCaseSignoffUserId,
  setCaseSignoffRole,
  setCaseSignoffDecision,
  setCaseSignoffNote,
  caseNotes,
  caseReviews,
  caseSignoffs,
  caseFlags,
  caseEvidence,
  caseStatusUpdate,
  caseStatusMessage,
  evidenceType,
  evidenceLabel,
  evidencePath,
  evidenceStatus,
  setEvidenceType,
  setEvidenceLabel,
  setEvidencePath,
  setCaseStatusUpdate,
  linkedAnalyses,
  autoFlagAuditId,
  autoFlagStatus,
  setAutoFlagAuditId,
  onCreateCase,
  onSelectCase,
  onAddNote,
  onAddReview,
  onAddSignoff,
  onUpdateStatus,
  onAddEvidence,
  onAutoFlag,
  onOpenAnalysis,
}: {
  cases: CaseRecord[];
  selectedCase: CaseRecord | null;
  caseTitle: string;
  caseEventId: string;
  casePlayers: string;
  caseSummary: string;
  caseTags: string;
  casePriority: string;
  caseAssignedTo: string;
  setCaseTitle: (value: string) => void;
  setCaseEventId: (value: string) => void;
  setCasePlayers: (value: string) => void;
  setCaseSummary: (value: string) => void;
  setCaseTags: (value: string) => void;
  setCasePriority: (value: string) => void;
  setCaseAssignedTo: (value: string) => void;
  caseNoteAuthor: string;
  caseNoteType: string;
  caseNoteText: string;
  caseReviewUserId: string;
  caseReviewAction: string;
  caseReviewRationale: string;
  caseSignoffUserId: string;
  caseSignoffRole: string;
  caseSignoffDecision: string;
  caseSignoffNote: string;
  setCaseNoteAuthor: (value: string) => void;
  setCaseNoteType: (value: string) => void;
  setCaseNoteText: (value: string) => void;
  setCaseReviewUserId: (value: string) => void;
  setCaseReviewAction: (value: string) => void;
  setCaseReviewRationale: (value: string) => void;
  setCaseSignoffUserId: (value: string) => void;
  setCaseSignoffRole: (value: string) => void;
  setCaseSignoffDecision: (value: string) => void;
  setCaseSignoffNote: (value: string) => void;
  caseNotes: CaseNote[];
  caseReviews: Array<{ id: string; reviewer_user_id?: string | null; action: string; rationale?: string | null; created_at: string }>;
  caseSignoffs: Array<{ id: string; signer_user_id?: string | null; signer_role: string; decision: string; note?: string | null; created_at: string }>;
  caseFlags: CaseFlag[];
  caseEvidence: CaseEvidence[];
  caseStatusUpdate: string;
  caseStatusMessage: string;
  evidenceType: string;
  evidenceLabel: string;
  evidencePath: string;
  evidenceStatus: string;
  setEvidenceType: (value: string) => void;
  setEvidenceLabel: (value: string) => void;
  setEvidencePath: (value: string) => void;
  setCaseStatusUpdate: (value: string) => void;
  linkedAnalyses: LinkedAnalysis[];
  autoFlagAuditId: string;
  autoFlagStatus: string;
  setAutoFlagAuditId: (value: string) => void;
  onCreateCase: () => void;
  onSelectCase: (caseId: string) => void;
  onAddNote: () => void;
  onAddReview: () => void;
  onAddSignoff: () => void;
  onUpdateStatus: () => void;
  onAddEvidence: () => void;
  onAutoFlag: () => void;
  onOpenAnalysis: (auditId: string) => void;
}) {
  const workflow = ["opened", "under_review", "analysis_completed", "escalated", "closed"];

  return (
    <section className="stacked">
      <article className="panel">
        <div className="panelHead">
          <h2>Create Case</h2>
          <button className="ghostBtn" type="button" onClick={onCreateCase}>Create</button>
        </div>
        <div className="formGrid">
          <input placeholder="Title" value={caseTitle} onChange={(e) => setCaseTitle(e.target.value)} />
          <input placeholder="Event ID (optional)" value={caseEventId} onChange={(e) => setCaseEventId(e.target.value)} />
          <input placeholder="Players (comma-separated)" value={casePlayers} onChange={(e) => setCasePlayers(e.target.value)} />
          <input placeholder="Tags (comma-separated)" value={caseTags} onChange={(e) => setCaseTags(e.target.value)} />
          <select value={casePriority} onChange={(e) => setCasePriority(e.target.value)}>
            <option value="">Priority</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
          <input placeholder="Assigned to" value={caseAssignedTo} onChange={(e) => setCaseAssignedTo(e.target.value)} />
        </div>
        <textarea rows={3} placeholder="Case summary (optional)" value={caseSummary} onChange={(e) => setCaseSummary(e.target.value)} />
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
            {cases.map((item) => (
              <article key={item.id} className="alertItem" onClick={() => onSelectCase(item.id)}>
                <div className="cardRow">
                  <strong>{item.title}</strong>
                  <span className="miniBadge pending">{item.status}</span>
                </div>
                <div className="muted">Event: {item.event_id || "None"}</div>
                <div className="muted">Players: {item.players.join(", ") || "None"}</div>
                <div className="muted">Priority: {item.priority || "None"} | Assigned: {item.assigned_to || "None"}</div>
              </article>
            ))}
          </div>
        )}
      </article>
      <article className="panel">
        <div className="panelHead">
          <h2>Case Detail</h2>
          <div className="muted">{selectedCase ? selectedCase.id : "No case selected"}</div>
        </div>
        {selectedCase ? (
          <>
            <div className="cardRow">
              <strong>{selectedCase.title}</strong>
              <span className="miniBadge pending">{selectedCase.priority || "unprioritized"}</span>
            </div>
            <div className="muted">Assigned: {selectedCase.assigned_to || "None"} | Event: {selectedCase.event_id || "None"}</div>
            <div className="muted">Tags: {selectedCase.tags?.join(", ") || "None"}</div>
            <div className="muted">Summary: {selectedCase.summary || "None"}</div>
            <div className="statsRow" style={{ marginTop: 14 }}>
              {workflow.map((status) => (
                <div key={status}>
                  <span className={selectedCase.status === status ? "monoData" : "muted"}>{status.replaceAll("_", " ")}</span>
                </div>
              ))}
            </div>
            <div className="formGrid" style={{ marginTop: 14 }}>
              <select value={caseStatusUpdate} onChange={(e) => setCaseStatusUpdate(e.target.value)}>
                <option value="opened">Opened</option>
                <option value="under_review">Under Review</option>
                <option value="analysis_completed">Analysis Completed</option>
                <option value="escalated">Escalated</option>
                <option value="closed">Closed</option>
              </select>
            </div>
            <div className="buttonRow" style={{ marginTop: 10 }}>
              <button className="ghostBtn" type="button" onClick={onUpdateStatus}>Update Status</button>
              <div className="muted">{caseStatusMessage || ""}</div>
            </div>
          </>
        ) : (
          <div className="muted">Select a case to see its detail workspace.</div>
        )}
      </article>
      <article className="panel notesPanel">
        <div className="panelHead">
          <h2>Case Notes</h2>
          <button className="ghostBtn" type="button" onClick={onAddNote}>Add Note</button>
        </div>
        <div className="muted">Selected case: {selectedCase ? selectedCase.title : "None"}</div>
        <div className="formGrid">
          <input placeholder="Author" value={caseNoteAuthor} onChange={(e) => setCaseNoteAuthor(e.target.value)} />
          <input placeholder="Note type" value={caseNoteType} onChange={(e) => setCaseNoteType(e.target.value)} />
        </div>
        <textarea rows={4} placeholder="Add arbiter note..." value={caseNoteText} onChange={(e) => setCaseNoteText(e.target.value)} />
        <div className="alertList">
          {caseNotes.length ? caseNotes.map((note) => (
            <div className="alertItem" key={note.id}>
              <div className="cardRow">
                <strong>{note.author || "Arbiter"}</strong>
                <span className="miniBadge reviewed">{note.created_at ? new Date(note.created_at).toLocaleTimeString() : ""}</span>
              </div>
              <div className="muted">{note.note_type || "note"}</div>
              <div>{note.text || "Note"}</div>
              {note.structured && Object.keys(note.structured).length ? (
                <pre className="previewPane">{JSON.stringify(note.structured, null, 2)}</pre>
              ) : null}
            </div>
          )) : <div className="muted">No notes yet.</div>}
        </div>
      </article>
      <article className="panel">
        <div className="panelHead">
          <h2>Reviews</h2>
          <button className="ghostBtn" type="button" onClick={onAddReview} disabled={!selectedCase}>Add Review</button>
        </div>
        <div className="formGrid">
          <input placeholder="Reviewer user ID" value={caseReviewUserId} onChange={(e) => setCaseReviewUserId(e.target.value)} />
          <select value={caseReviewAction} onChange={(e) => setCaseReviewAction(e.target.value)}>
            <option value="note">Note</option>
            <option value="request_more_data">Request More Data</option>
            <option value="recommend_monitoring">Recommend Monitoring</option>
            <option value="recommend_escalation">Recommend Escalation</option>
            <option value="close_case">Close Case</option>
          </select>
        </div>
        <textarea rows={3} placeholder="Review rationale" value={caseReviewRationale} onChange={(e) => setCaseReviewRationale(e.target.value)} />
        <div className="alertList">
          {caseReviews.length ? caseReviews.map((review) => (
            <article className="alertItem" key={review.id}>
              <div className="cardRow">
                <strong>{review.action}</strong>
                <span className="miniBadge reviewed">{review.created_at ? new Date(review.created_at).toLocaleString() : ""}</span>
              </div>
              <div className="muted">{review.reviewer_user_id || "reviewer"}</div>
              <div>{review.rationale || "No rationale"}</div>
            </article>
          )) : <div className="muted">No reviews yet.</div>}
        </div>
      </article>
      <article className="panel">
        <div className="panelHead">
          <h2>Signoffs</h2>
          <button className="ghostBtn" type="button" onClick={onAddSignoff} disabled={!selectedCase}>Add Signoff</button>
        </div>
        <div className="formGrid">
          <input placeholder="Signer user ID" value={caseSignoffUserId} onChange={(e) => setCaseSignoffUserId(e.target.value)} />
          <input placeholder="Signer role" value={caseSignoffRole} onChange={(e) => setCaseSignoffRole(e.target.value)} />
          <select value={caseSignoffDecision} onChange={(e) => setCaseSignoffDecision(e.target.value)}>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="returned_for_review">Returned For Review</option>
          </select>
        </div>
        <textarea rows={3} placeholder="Signoff note" value={caseSignoffNote} onChange={(e) => setCaseSignoffNote(e.target.value)} />
        <div className="alertList">
          {caseSignoffs.length ? caseSignoffs.map((signoff) => (
            <article className="alertItem" key={signoff.id}>
              <div className="cardRow">
                <strong>{signoff.decision}</strong>
                <span className="miniBadge reviewed">{signoff.signer_role}</span>
              </div>
              <div className="muted">{signoff.signer_user_id || "signer"} | {signoff.created_at ? new Date(signoff.created_at).toLocaleString() : ""}</div>
              <div>{signoff.note || "No note"}</div>
            </article>
          )) : <div className="muted">No signoffs yet.</div>}
        </div>
      </article>
      <article className="panel">
        <div className="panelHead">
          <h2>Flags</h2>
          <button className="ghostBtn" type="button" onClick={onAutoFlag} disabled={!selectedCase || !autoFlagAuditId.trim()}>Auto-Flag From Audit</button>
        </div>
        <div className="formGrid">
          <input placeholder="Audit ID for auto-flags" value={autoFlagAuditId} onChange={(e) => setAutoFlagAuditId(e.target.value)} />
          <div className="muted">{autoFlagStatus || "Use an audit ID to import triggered signals into this case."}</div>
        </div>
        <div className="alertList">
          {caseFlags.length ? caseFlags.map((flag) => (
            <article className="alertItem" key={flag.id}>
              <div className="cardRow">
                <strong>{flag.flag_type || "flag"}</strong>
                <span className="miniBadge pending">{flag.severity || "info"}</span>
              </div>
              <div>{flag.message || "No message"}</div>
              {flag.metadata && Object.keys(flag.metadata).length ? (
                <pre className="previewPane">{JSON.stringify(flag.metadata, null, 2)}</pre>
              ) : null}
            </article>
          )) : <div className="muted">No flags yet.</div>}
        </div>
      </article>
      <article className="panel">
        <div className="panelHead">
          <h2>Evidence Locker</h2>
          <button className="ghostBtn" type="button" onClick={onAddEvidence} disabled={!selectedCase}>Attach Evidence</button>
        </div>
        <div className="formGrid">
          <input placeholder="Evidence type" value={evidenceType} onChange={(e) => setEvidenceType(e.target.value)} />
          <input placeholder="Label" value={evidenceLabel} onChange={(e) => setEvidenceLabel(e.target.value)} />
          <input placeholder="Path or URL" value={evidencePath} onChange={(e) => setEvidencePath(e.target.value)} />
        </div>
        <div className="muted">{evidenceStatus || "Attach generated reports, screenshots, exports, or external storage paths."}</div>
        <div className="alertList" style={{ marginTop: 14 }}>
          {caseEvidence.length ? caseEvidence.map((item) => (
            <article className="alertItem" key={item.id}>
              <div className="cardRow">
                <strong>{item.label || item.evidence_type || "evidence"}</strong>
                <span className="miniBadge reviewed">{item.evidence_type || "file"}</span>
              </div>
              <div className="monoData">{item.path || "No path"}</div>
              <div className="muted">{item.created_at ? new Date(item.created_at).toLocaleString() : ""}</div>
              {item.metadata && Object.keys(item.metadata).length ? (
                <pre className="previewPane">{JSON.stringify(item.metadata, null, 2)}</pre>
              ) : null}
            </article>
          )) : <div className="muted">No evidence attached.</div>}
        </div>
      </article>
      <article className="panel">
        <div className="panelHead">
          <h2>Linked Analyses</h2>
          <div className="muted">{linkedAnalyses.length} matches</div>
        </div>
        <div className="alertList">
          {linkedAnalyses.length ? linkedAnalyses.map((analysis) => (
            <article className="alertItem" key={analysis.audit_id} onClick={() => onOpenAnalysis(analysis.audit_id)}>
              <div className="cardRow">
                <strong className="monoData">{analysis.audit_id}</strong>
                <span className="miniBadge pending">{analysis.risk_tier}</span>
              </div>
              <div className="muted">Player: {analysis.player_id} | Event: {analysis.event_id || "None"}</div>
              <div className="muted">Weighted risk {formatMaybe(analysis.weighted_risk_score)} | {analysis.created_at ? new Date(analysis.created_at).toLocaleString() : ""}</div>
              {renderMiniBar(analysis.weighted_risk_score, 1)}
            </article>
          )) : <div className="muted">No linked analyses found from the current dashboard feed.</div>}
        </div>
      </article>
    </section>
  );
}

export function ReportSection({
  reportAuditId,
  reportCaseId,
  reportMode,
  reportFormat,
  reportUseAi,
  reportProvider,
  reportModel,
  reportApiUrl,
  reportApiKey,
  reportOutput,
  reportStatus,
  batchPgnFileName,
  batchTrackedPlayerName,
  batchTrackedPlayerId,
  batchDefaultElo,
  batchMaxGames,
  batchAnalyzeBoth,
  batchResponseFormat,
  batchStatus,
  batchPreview,
  batchRuns,
  setReportAuditId,
  setReportCaseId,
  setReportMode,
  setReportFormat,
  setReportUseAi,
  setReportProvider,
  setReportModel,
  setReportApiUrl,
  setReportApiKey,
  setBatchTrackedPlayerName,
  setBatchTrackedPlayerId,
  setBatchDefaultElo,
  setBatchMaxGames,
  setBatchAnalyzeBoth,
  setBatchResponseFormat,
  onGenerate,
  onBatchFileSelected,
  onSubmitBatchPgn,
  onDownloadBatchCsv,
}: {
  reportAuditId: string;
  reportCaseId: string;
  reportMode: string;
  reportFormat: string;
  reportUseAi: boolean;
  reportProvider: string;
  reportModel: string;
  reportApiUrl: string;
  reportApiKey: string;
  reportOutput: string;
  reportStatus: string;
  batchPgnFileName: string;
  batchTrackedPlayerName: string;
  batchTrackedPlayerId: string;
  batchDefaultElo: string;
  batchMaxGames: string;
  batchAnalyzeBoth: boolean;
  batchResponseFormat: string;
  batchStatus: string;
  batchPreview: string;
  batchRuns: BatchRun[];
  setReportAuditId: (value: string) => void;
  setReportCaseId: (value: string) => void;
  setReportMode: (value: string) => void;
  setReportFormat: (value: string) => void;
  setReportUseAi: (value: boolean) => void;
  setReportProvider: (value: string) => void;
  setReportModel: (value: string) => void;
  setReportApiUrl: (value: string) => void;
  setReportApiKey: (value: string) => void;
  setBatchTrackedPlayerName: (value: string) => void;
  setBatchTrackedPlayerId: (value: string) => void;
  setBatchDefaultElo: (value: string) => void;
  setBatchMaxGames: (value: string) => void;
  setBatchAnalyzeBoth: (value: boolean) => void;
  setBatchResponseFormat: (value: string) => void;
  onGenerate: () => void;
  onBatchFileSelected: (file: File | null) => void;
  onSubmitBatchPgn: () => void;
  onDownloadBatchCsv: (runId: string, sourceName?: string | null) => void;
}) {
  return (
    <section className="stacked">
      <article className="panel">
        <div className="panelHead">
          <h2>Report Composer</h2>
          <button className="ghostBtn" type="button" onClick={onGenerate}>Generate</button>
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
        <div className="formGrid">
          <label className="muted" style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <input type="checkbox" checked={reportUseAi} onChange={(e) => setReportUseAi(e.target.checked)} />
            Use AI narrative
          </label>
          <div className="muted">{reportStatus || "Use the selected audit ID from deep dive or enter one manually."}</div>
        </div>
        {reportUseAi ? (
          <div className="formGrid">
            <select value={reportProvider} onChange={(e) => setReportProvider(e.target.value)}>
              <option value="openai">OpenAI-compatible</option>
              <option value="anthropic">Anthropic</option>
            </select>
            <input placeholder="Model" value={reportModel} onChange={(e) => setReportModel(e.target.value)} />
            <input placeholder="API URL" value={reportApiUrl} onChange={(e) => setReportApiUrl(e.target.value)} />
            <input placeholder="API Key" value={reportApiKey} onChange={(e) => setReportApiKey(e.target.value)} />
          </div>
        ) : null}
        {reportFormat === "pdf" && reportOutput ? (
          <a className="ghostBtn" href={reportOutput} target="_blank" rel="noreferrer">Open PDF</a>
        ) : null}
        {reportOutput ? <pre className="previewPane">{reportOutput}</pre> : <div className="muted">No report generated yet.</div>}
      </article>
      <article className="panel">
        <div className="panelHead">
          <h2>Batch PGN Analysis</h2>
          <button className="ghostBtn" type="button" onClick={onSubmitBatchPgn}>Run Batch</button>
        </div>
        <div className="formGrid">
          <input placeholder="Tracked player name (optional)" value={batchTrackedPlayerName} onChange={(e) => setBatchTrackedPlayerName(e.target.value)} />
          <input placeholder="Tracked player ID override (optional)" value={batchTrackedPlayerId} onChange={(e) => setBatchTrackedPlayerId(e.target.value)} />
          <input placeholder="Default ELO fallback" value={batchDefaultElo} onChange={(e) => setBatchDefaultElo(e.target.value)} />
          <input placeholder="Max games" value={batchMaxGames} onChange={(e) => setBatchMaxGames(e.target.value)} />
          <select value={batchResponseFormat} onChange={(e) => setBatchResponseFormat(e.target.value)}>
            <option value="json">JSON</option>
            <option value="csv">CSV</option>
          </select>
          <label className="muted" style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <input type="checkbox" checked={batchAnalyzeBoth} onChange={(e) => setBatchAnalyzeBoth(e.target.checked)} />
            Analyze both players
          </label>
        </div>
        <input type="file" accept=".pgn" onChange={(e) => onBatchFileSelected(e.target.files?.[0] ?? null)} />
        <div className="muted">
          File: {batchPgnFileName || "None"} | {batchStatus || "Upload a tournament PGN to generate player-level Regan-style rows."}
        </div>
        {batchPreview ? <pre className="previewPane">{batchPreview}</pre> : null}
      </article>
      <article className="panel">
        <div className="panelHead">
          <h2>Batch Runs</h2>
          <div className="muted">{batchRuns.length} recent</div>
        </div>
        <div className="alertList">
          {batchRuns.length ? batchRuns.map((run) => (
            <article className="alertItem" key={run.id}>
              <div className="cardRow">
                <strong>{run.source_name || run.event_id || run.id}</strong>
                <span className="miniBadge pending">{run.status}</span>
              </div>
              <div className="muted">
                Players {run.response?.players_analyzed ?? 0} | Games {run.response?.games_parsed ?? 0} | Analyses {run.response?.analyses_generated ?? 0}
              </div>
              <div className="muted">{run.created_at ? new Date(run.created_at).toLocaleString() : ""}</div>
              {run.csv_text ? <button className="ghostBtn" type="button" onClick={() => onDownloadBatchCsv(run.id, run.source_name)}>Download CSV</button> : null}
              {run.error_text ? <div>{run.error_text}</div> : null}
              {run.response && !run.csv_text ? <pre className="previewPane">{JSON.stringify(run.response, null, 2).slice(0, 3000)}</pre> : null}
            </article>
          )) : <div className="muted">No batch runs yet.</div>}
        </div>
      </article>
    </section>
  );
}

export function PartnerSection({
  apiBase,
  partnerName,
  partnerWebhook,
  partnerRateLimit,
  partnerStatus,
  partnerKeys,
  partnerJobs,
  partnerSessions,
  partnerSelectedKeyId,
  partnerTestGameId,
  partnerTestPlayerId,
  partnerTestColor,
  partnerTestElo,
  partnerTestPgn,
  partnerTestStatus,
  partnerSessionGameId,
  partnerSessionPlayerId,
  partnerSessionStatus,
  setPartnerName,
  setPartnerWebhook,
  setPartnerRateLimit,
  setPartnerSelectedKeyId,
  setPartnerTestGameId,
  setPartnerTestPlayerId,
  setPartnerTestColor,
  setPartnerTestElo,
  setPartnerTestPgn,
  setPartnerSessionGameId,
  setPartnerSessionPlayerId,
  onCreate,
  onCopy,
  onRotate,
  onDisable,
  onCreateSession,
  onRunAnalyze,
  onRefreshPartnerOps,
}: {
  apiBase: string;
  partnerName: string;
  partnerWebhook: string;
  partnerRateLimit: string;
  partnerStatus: string;
  partnerKeys: PartnerKey[];
  partnerJobs: PartnerJob[];
  partnerSessions: PartnerSession[];
  partnerSelectedKeyId: string;
  partnerTestGameId: string;
  partnerTestPlayerId: string;
  partnerTestColor: string;
  partnerTestElo: string;
  partnerTestPgn: string;
  partnerTestStatus: string;
  partnerSessionGameId: string;
  partnerSessionPlayerId: string;
  partnerSessionStatus: string;
  setPartnerName: (value: string) => void;
  setPartnerWebhook: (value: string) => void;
  setPartnerRateLimit: (value: string) => void;
  setPartnerSelectedKeyId: (value: string) => void;
  setPartnerTestGameId: (value: string) => void;
  setPartnerTestPlayerId: (value: string) => void;
  setPartnerTestColor: (value: string) => void;
  setPartnerTestElo: (value: string) => void;
  setPartnerTestPgn: (value: string) => void;
  setPartnerSessionGameId: (value: string) => void;
  setPartnerSessionPlayerId: (value: string) => void;
  onCreate: () => void;
  onCopy: (value: string) => void;
  onRotate: (keyId: string) => void;
  onDisable: (keyId: string) => void;
  onCreateSession: () => void;
  onRunAnalyze: () => void;
  onRefreshPartnerOps: () => void;
}) {
  const selectedKey = partnerKeys.find((item) => item.id === partnerSelectedKeyId) ?? partnerKeys[0] ?? null;

  return (
    <section className="stacked">
      <article className="panel">
        <div className="panelHead">
          <h2>Partner Keys</h2>
          <div className="buttonRow">
            <button className="ghostBtn" type="button" onClick={onRefreshPartnerOps}>Refresh</button>
            <button className="ghostBtn" type="button" onClick={onCreate}>Create</button>
          </div>
        </div>
        <div className="formGrid">
          <input placeholder="Partner name" value={partnerName} onChange={(e) => setPartnerName(e.target.value)} />
          <input placeholder="Webhook URL (optional)" value={partnerWebhook} onChange={(e) => setPartnerWebhook(e.target.value)} />
          <input placeholder="Rate limit / min" value={partnerRateLimit} onChange={(e) => setPartnerRateLimit(e.target.value)} />
          <div className="muted">{partnerStatus || "Create a key, then give partners the API key and secret shown below."}</div>
        </div>
      </article>
      <article className="panel">
        {partnerKeys.length ? (
          <div className="alertList">
            {partnerKeys.map((item) => (
              <div className="alertItem" key={item.id}>
                <div className="cardRow">
                  <strong>{item.partner_name}</strong>
                  <span className="miniBadge reviewed">{item.active ? "active" : "disabled"}</span>
                </div>
                <div className="monoData">Key: {item.key}</div>
                <div className="monoData">Secret: {item.secret}</div>
                <div className="muted">Webhook: {item.webhook_url || "None"}</div>
                <div className="muted">Rate limit: {item.rate_limit_per_minute}/min</div>
                <div className="muted">Created: {item.created_at ? new Date(item.created_at).toLocaleString() : "None"}</div>
                <div className="buttonRow">
                  <button className="ghostBtn" type="button" onClick={() => setPartnerSelectedKeyId(item.id)}>
                    {partnerSelectedKeyId === item.id ? "Selected" : "Select"}
                  </button>
                  <button className="ghostBtn" type="button" onClick={() => onCopy(item.key)}>Copy Key</button>
                  <button className="ghostBtn" type="button" onClick={() => onCopy(item.secret)}>Copy Secret</button>
                  <button className="ghostBtn" type="button" onClick={() => onRotate(item.id)}>Rotate</button>
                  <button className="ghostBtn" type="button" onClick={() => onDisable(item.id)}>{item.active ? "Deactivate" : "Disabled"}</button>
                </div>
                <pre className="previewPane">{`curl -X POST ${apiBase}/v1/partner/analyze \\
  -H "x-api-key: ${item.key}" \\
  -H "Content-Type: application/json" \\
  -d '{"game_id":"game-1","player_id":"player-1","pgn":"<PGN>","player_color":"white","official_elo":1800}'`}</pre>
              </div>
            ))}
          </div>
        ) : <div className="muted">No partner keys.</div>}
      </article>

      <article className="panel">
        <div className="panelHead">
          <h2>Partner Session</h2>
          <button className="ghostBtn" type="button" onClick={onCreateSession} disabled={!selectedKey || !selectedKey.active}>Create Session</button>
        </div>
        <div className="formGrid">
          <select value={partnerSelectedKeyId} onChange={(e) => setPartnerSelectedKeyId(e.target.value)}>
            {partnerKeys.length ? partnerKeys.map((item) => (
              <option key={item.id} value={item.id}>{item.partner_name} ({item.key_last4 || "key"})</option>
            )) : <option value="">No keys</option>}
          </select>
          <input placeholder="Game ID" value={partnerSessionGameId} onChange={(e) => setPartnerSessionGameId(e.target.value)} />
          <input placeholder="Player ID" value={partnerSessionPlayerId} onChange={(e) => setPartnerSessionPlayerId(e.target.value)} />
          <div className="muted">{partnerSessionStatus || "Create a partner live session for SDK or streaming use."}</div>
        </div>
      </article>

      <article className="panel">
        <div className="panelHead">
          <h2>Partner Analyze Test</h2>
          <button className="ghostBtn" type="button" onClick={onRunAnalyze} disabled={!selectedKey || !selectedKey.active}>Submit</button>
        </div>
        <div className="formGrid">
          <input placeholder="Game ID" value={partnerTestGameId} onChange={(e) => setPartnerTestGameId(e.target.value)} />
          <input placeholder="Player ID" value={partnerTestPlayerId} onChange={(e) => setPartnerTestPlayerId(e.target.value)} />
          <select value={partnerTestColor} onChange={(e) => setPartnerTestColor(e.target.value)}>
            <option value="white">White</option>
            <option value="black">Black</option>
          </select>
          <input placeholder="Official ELO" value={partnerTestElo} onChange={(e) => setPartnerTestElo(e.target.value)} />
        </div>
        <textarea rows={8} placeholder="Paste PGN for partner analysis..." value={partnerTestPgn} onChange={(e) => setPartnerTestPgn(e.target.value)} />
        <div className="muted" style={{ marginTop: 10 }}>{partnerTestStatus || "Use the selected partner key to queue a real partner analysis and then inspect the job below."}</div>
      </article>

      <article className="panel">
        <div className="panelHead">
          <h2>Partner Jobs</h2>
          <div className="muted">{partnerJobs.length} jobs</div>
        </div>
        {partnerJobs.length ? (
          <div className="alertList">
            {partnerJobs.map((job) => (
              <article className="alertItem" key={job.job_id}>
                <div className="cardRow">
                  <strong className="monoData">{job.job_id}</strong>
                  <span className="miniBadge pending">{job.status}</span>
                </div>
                <div className="muted">Partner: {job.partner_name || "None"} | Player: {job.player_id} | Game: {job.game_id}</div>
                <div className="muted">Risk: {job.risk_level || "None"} | Score: {formatMaybe(job.risk_score)}</div>
                <div className="muted">Webhook: {job.webhook_delivered ? "delivered" : "pending/failed"} | Attempts: {job.webhook_attempts}</div>
                <div className="muted">{job.created_at ? new Date(job.created_at).toLocaleString() : ""}{job.completed_at ? ` -> ${new Date(job.completed_at).toLocaleString()}` : ""}</div>
                {job.result ? <pre className="previewPane">{JSON.stringify(job.result, null, 2)}</pre> : null}
              </article>
            ))}
          </div>
        ) : <div className="muted">No partner jobs yet.</div>}
      </article>

      <article className="panel">
        <div className="panelHead">
          <h2>Partner Sessions</h2>
          <div className="muted">{partnerSessions.length} sessions</div>
        </div>
        {partnerSessions.length ? (
          <div className="alertList">
            {partnerSessions.map((session) => (
              <article className="alertItem" key={session.session_id}>
                <div className="cardRow">
                  <strong className="monoData">{session.session_id}</strong>
                  <span className="miniBadge reviewed">{session.status}</span>
                </div>
                <div className="muted">Partner: {session.partner_name || "None"} | Player: {session.player_id || "None"} | Game: {session.game_id || "None"}</div>
                <div className="muted">Created: {session.created_at ? new Date(session.created_at).toLocaleString() : "None"}</div>
              </article>
            ))}
          </div>
        ) : <div className="muted">No partner sessions yet.</div>}
      </article>
    </section>
  );
}

export function LiveSection({
  liveSessionId,
  liveEvents,
  liveRisk,
  setLiveSessionId,
  onConnect,
}: {
  liveSessionId: string;
  liveEvents: Array<Record<string, unknown>>;
  liveRisk: Record<string, unknown> | null;
  setLiveSessionId: (value: string) => void;
  onConnect: () => void;
}) {
  const moveEvents = liveEvents.filter((event) => String(event.event_type ?? event.type ?? "").toLowerCase().includes("move"));
  const copyEvents = liveEvents.filter((event) => String(event.event_type ?? event.type ?? "").toLowerCase().includes("copy"));
  const focusEvents = liveEvents.filter((event) => String(event.event_type ?? event.type ?? "").toLowerCase().includes("focus"));

  return (
    <section className="stacked">
      <article className="panel">
        <div className="panelHead">
          <h2>Live Monitor</h2>
          <button className="ghostBtn" type="button" onClick={onConnect}>Connect</button>
        </div>
        <div className="formGrid">
          <input placeholder="Session ID" value={liveSessionId} onChange={(e) => setLiveSessionId(e.target.value)} />
          <div className="muted">Connect to a live session to stream moves, focus changes, and risk recalculations.</div>
        </div>
        <div className="statsRow" style={{ marginTop: 14 }}>
          <div><span className="monoData">{liveSessionId || "None"}</span><div className="muted">Session</div></div>
          <div><span className="monoData">{liveEvents.length}</span><div className="muted">Events</div></div>
          <div><span className="monoData">{moveEvents.length}</span><div className="muted">Moves</div></div>
          <div><span className="monoData">{copyEvents.length}</span><div className="muted">Copy/Paste</div></div>
          <div><span className="monoData">{focusEvents.length}</span><div className="muted">Focus Events</div></div>
        </div>
      </article>

      <article className="panel">
        <div className="panelHead">
          <h2>Rolling Risk</h2>
          <div className="muted">Updates from `/v1/live/sessions/:id/risk`</div>
        </div>
        {liveRisk ? (
          <>
            <div className="statsRow">
              <div><span className="monoData">{String(liveRisk.risk_tier ?? "None")}</span><div className="muted">Risk Tier</div></div>
              <div><span className="monoData">{formatMaybe(liveRisk.risk_score)}</span><div className="muted">Risk Score</div></div>
              <div><span className="monoData">{formatMaybe(liveRisk.engine_alignment_avg)}</span><div className="muted">Engine Align</div></div>
              <div><span className="monoData">{formatMaybe(liveRisk.maia_alignment_avg)}</span><div className="muted">Maia Align</div></div>
              <div><span className="monoData">{formatMaybe(liveRisk.timing_variance)}</span><div className="muted">Timing Variance</div></div>
            </div>
            {typeof liveRisk.risk_score === "number" ? renderMiniBar(liveRisk.risk_score, 1) : null}
            {Array.isArray(liveRisk.notes) && liveRisk.notes.length ? (
              <div className="alertList" style={{ marginTop: 14 }}>
                {(liveRisk.notes as unknown[]).map((note, idx) => (
                  <div className="alertItem" key={`lr-note-${idx}`}>{String(note)}</div>
                ))}
              </div>
            ) : null}
          </>
        ) : (
          <div className="muted">No live risk snapshot yet.</div>
        )}
      </article>

      <article className="panel">
        <div className="panelHead">
          <h2>Live Event Stream</h2>
          <div className="muted">Newest first</div>
        </div>
        <div className="alertList">
          {liveEvents.length ? liveEvents.map((event, idx) => (
            <article className="alertItem" key={`evt-${idx}`}>
              <div className="cardRow">
                <strong>{String(event.event_type ?? event.type ?? "event")}</strong>
                <span className="miniBadge pending">{String(event.ply ?? event.move_number ?? "live")}</span>
              </div>
              <div className="muted">
                {String(event.timestamp ?? event.created_at ?? "")}
              </div>
              <pre className="previewPane">{JSON.stringify(event, null, 2)}</pre>
            </article>
          )) : <div className="muted">No events yet.</div>}
        </div>
      </article>
    </section>
  );
}

export function TournamentSection({
  tournamentEventId,
  tournamentPlayers,
  tournamentAlerts,
  onOpenPlayer,
}: {
  tournamentEventId: string;
  tournamentPlayers: Array<Record<string, unknown>>;
  tournamentAlerts: Array<Record<string, unknown>>;
  onOpenPlayer: (playerId: string) => void;
}) {
  const avgRisk = tournamentPlayers.length
    ? tournamentPlayers.reduce((sum, player) => sum + numeric(player.avg_risk_score), 0) / tournamentPlayers.length
    : 0;

  return (
    <section className="stacked">
      <article className="panel">
        <div className="panelHead">
          <h2>Tournament Dashboard</h2>
          <div className="muted">Event {tournamentEventId || "All events"}</div>
        </div>
        <div className="statsRow">
          <div><span className="monoData">{tournamentPlayers.length}</span><div className="muted">Players</div></div>
          <div><span className="monoData">{tournamentAlerts.length}</span><div className="muted">Alerts</div></div>
          <div><span className="monoData">{formatMaybe(avgRisk)}</span><div className="muted">Avg Risk</div></div>
        </div>
      </article>

      <article className="panel">
        <div className="panelHead">
          <h2>Player Leaderboard</h2>
          <div className="muted">Sorted by average risk score</div>
        </div>
        {tournamentPlayers.length ? (
          <div className="alertList">
            {tournamentPlayers.map((player, idx) => {
              const playerId = String(player.player_id ?? "player");
              const score = numeric(player.avg_risk_score);
              return (
                <article className="alertItem" key={`tp-${playerId}-${idx}`} onClick={() => onOpenPlayer(playerId)}>
                  <div className="cardRow">
                    <strong className="monoData">{playerId}</strong>
                    <span className="miniBadge pending">{String(player.risk_tier ?? "unknown")}</span>
                  </div>
                  <div className="muted">Average risk score {score.toFixed(3)}</div>
                  {renderMiniBar(score, 1)}
                </article>
              );
            })}
          </div>
        ) : <div className="muted">No tournament data yet.</div>}
      </article>

      <article className="panel">
        <div className="panelHead">
          <h2>Alerts</h2>
          <div className="muted">Tournament-level rollup</div>
        </div>
        {tournamentAlerts.length ? (
          <div className="alertList">
            {tournamentAlerts.map((alert, idx) => (
              <div className="alertItem" key={`ta-${idx}`}>
                <div className="cardRow">
                  <strong>{String(alert.message ?? "Alert")}</strong>
                  <span className="miniBadge reviewed">{formatMaybe(alert.score)}</span>
                </div>
                {typeof alert.score === "number" ? renderMiniBar(alert.score as number, 1) : null}
              </div>
            ))}
          </div>
        ) : <div className="muted">No alerts.</div>}
      </article>
    </section>
  );
}

export function OTBSection({
  cases,
  otbEventId,
  otbConnectStatus,
  otbCameraEvents,
  otbBoardEvents,
  otbIncidents,
  otbIncidentPlayerId,
  otbIncidentCaseId,
  otbIncidentType,
  otbIncidentSeverity,
  otbIncidentDescription,
  otbIncidentOccurredAt,
  otbIncidentStatus,
  setOtbEventId,
  setOtbIncidentPlayerId,
  setOtbIncidentCaseId,
  setOtbIncidentType,
  setOtbIncidentSeverity,
  setOtbIncidentDescription,
  setOtbIncidentOccurredAt,
  onConnectDgt,
  onCreateIncident,
}: {
  cases: Array<{ id: string; title: string }>;
  otbEventId: string;
  otbConnectStatus: string;
  otbCameraEvents: OTBCameraEvent[];
  otbBoardEvents: DGTBoardEvent[];
  otbIncidents: OTBIncidentRecord[];
  otbIncidentPlayerId: string;
  otbIncidentCaseId: string;
  otbIncidentType: string;
  otbIncidentSeverity: string;
  otbIncidentDescription: string;
  otbIncidentOccurredAt: string;
  otbIncidentStatus: string;
  setOtbEventId: (value: string) => void;
  setOtbIncidentPlayerId: (value: string) => void;
  setOtbIncidentCaseId: (value: string) => void;
  setOtbIncidentType: (value: string) => void;
  setOtbIncidentSeverity: (value: string) => void;
  setOtbIncidentDescription: (value: string) => void;
  setOtbIncidentOccurredAt: (value: string) => void;
  onConnectDgt: () => void;
  onCreateIncident: () => void;
}) {
  return (
    <section className="stacked">
      <article className="panel">
        <div className="panelHead">
          <h2>OTB Monitor</h2>
          <div className="muted">Camera events, DGT boards, and manual incidents</div>
        </div>
        <div className="formGrid">
          <input placeholder="Event ID (optional)" value={otbEventId} onChange={(e) => setOtbEventId(e.target.value)} />
          <div className="muted">Filter by event to isolate one tournament, round, or board cluster.</div>
        </div>
        <div className="buttonRow" style={{ marginTop: 10 }}>
          <button className="ghostBtn" type="button" onClick={onConnectDgt}>Connect DGT Board</button>
          {otbConnectStatus ? <div className="muted">{otbConnectStatus}</div> : null}
        </div>
      </article>

      <article className="panel">
        <div className="panelHead">
          <h2>Log Incident</h2>
          <button className="ghostBtn" type="button" onClick={onCreateIncident}>Save Incident</button>
        </div>
        <div className="formGrid">
          <input placeholder="Player ID" value={otbIncidentPlayerId} onChange={(e) => setOtbIncidentPlayerId(e.target.value)} />
          <select value={otbIncidentType} onChange={(e) => setOtbIncidentType(e.target.value)}>
            <option value="device_detected">Device detected</option>
            <option value="player_left_board">Player left board</option>
            <option value="suspicious_behavior">Suspicious behavior</option>
            <option value="refused_scan">Refused scan</option>
            <option value="other">Other</option>
          </select>
          <select value={otbIncidentSeverity} onChange={(e) => setOtbIncidentSeverity(e.target.value)}>
            <option value="info">Info</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
          <select value={otbIncidentCaseId} onChange={(e) => setOtbIncidentCaseId(e.target.value)}>
            <option value="">No linked case</option>
            {cases.map((item) => (
              <option key={item.id} value={item.id}>{item.title}</option>
            ))}
          </select>
          <input type="datetime-local" value={otbIncidentOccurredAt} onChange={(e) => setOtbIncidentOccurredAt(e.target.value)} />
        </div>
        <textarea
          rows={3}
          placeholder="Describe what the arbiter observed..."
          value={otbIncidentDescription}
          onChange={(e) => setOtbIncidentDescription(e.target.value)}
        />
        <div className="muted" style={{ marginTop: 10 }}>{otbIncidentStatus || "Create a structured incident record and optionally attach it to a case."}</div>
      </article>

      <article className="panel">
        <div className="panelHead">
          <h2>Incident Log</h2>
          <div className="muted">{otbIncidents.length} incidents</div>
        </div>
        {otbIncidents.length ? (
          <div className="alertList">
            {otbIncidents.map((incident) => (
              <article className="alertItem" key={incident.id}>
                <div className="cardRow">
                  <strong className="monoData">{incident.player_id || "Unknown player"}</strong>
                  <span className="miniBadge pending">{incident.severity}</span>
                </div>
                <div>{incident.incident_type}</div>
                <div className="muted">
                  Event {incident.event_id || "None"} | Case {incident.case_id || "None"} | {incident.occurred_at || incident.created_at}
                </div>
                <div>{incident.description || "No description"}</div>
              </article>
            ))}
          </div>
        ) : (
          <div className="muted">No incidents logged yet.</div>
        )}
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
  );
}

export function AdminSection({
  systemStatus,
  systemStatusError,
  missingEnvVars,
}: {
  systemStatus: {
    generated_at_utc: string;
    app_env?: string;
    model_version?: string;
    feature_schema_version?: string;
    report_schema_version?: string;
    calibration?: Record<string, unknown>;
    ml_fusion?: Record<string, unknown>;
    maia?: Record<string, unknown>;
    engine?: Record<string, unknown>;
    opening_book?: Record<string, unknown>;
    tablebase?: Record<string, unknown>;
    supabase_configured?: boolean;
    analysis_pipeline_operational?: boolean;
    ml_models_loaded?: boolean;
    warnings: string[];
  } | null;
  systemStatusError: string | null;
  missingEnvVars: string[];
}) {
  return (
    <section className="adminGrid">
      <article className="panel">
        <div className="panelHead">
          <h2>System Status</h2>
          <span className="badge on">Live</span>
        </div>
        {systemStatus ? (
          <>
            <div className="muted">Updated {new Date(systemStatus.generated_at_utc).toLocaleTimeString()}</div>
            <div className="statsRow" style={{ marginTop: 14 }}>
              <div><span className="monoData">{systemStatus.analysis_pipeline_operational ? "Yes" : "No"}</span><div className="muted">Pipeline</div></div>
              <div><span className="monoData">{systemStatus.supabase_configured ? "Yes" : "No"}</span><div className="muted">Supabase</div></div>
              <div><span className="monoData">{systemStatus.ml_models_loaded ? "Loaded" : "Not Loaded"}</span><div className="muted">ML</div></div>
              <div><span className="monoData">{systemStatus.warnings.length}</span><div className="muted">Warnings</div></div>
            </div>
            {systemStatus.warnings.length ? (
              <div className="alertList" style={{ marginTop: 14 }}>
                {systemStatus.warnings.map((warning) => (
                  <div className="alertItem" key={warning}>{warning}</div>
                ))}
              </div>
            ) : (
              <div className="miniBadge safe" style={{ marginTop: 14 }}>No warnings</div>
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
            <div className="muted">Source: {String(systemStatus.calibration?.source ?? "unknown")}</div>
            <div className="monoData">Version: {String(systemStatus.calibration?.profile_version ?? "unknown")}</div>
            <div className="monoData">Bands: {String(systemStatus.calibration?.band_count ?? "None")}</div>
            <div className="muted">
              Coverage: {String(systemStatus.calibration?.coverage_min_elo ?? "None")} to {String(systemStatus.calibration?.coverage_max_elo ?? "None")}
            </div>
            <div className="muted">QA: {systemStatus.calibration?.qa && (systemStatus.calibration.qa as { ok?: boolean }).ok === false ? "Failed" : "OK"}</div>
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
            <div className="monoData">Primary: {systemStatus.ml_fusion?.primary && (systemStatus.ml_fusion.primary as { exists?: boolean }).exists ? "Present" : "Missing"}</div>
            <div className="monoData">Secondary: {systemStatus.ml_fusion?.secondary && (systemStatus.ml_fusion.secondary as { exists?: boolean }).exists ? "Present" : "Missing"}</div>
            <div className="muted">Maia Buckets: {String(systemStatus.maia?.available_count ?? 0)}</div>
            <div className="muted">Maia LC0: {systemStatus.maia?.lc0_path ? "Configured" : "Missing"}</div>
            <div className="muted">Maia Version: {String(systemStatus.maia?.version ?? "unknown")}</div>
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
        <div className="muted">App Env: {String(systemStatus?.app_env ?? "unknown")}</div>
        <div className="muted">Model Version: {String(systemStatus?.model_version ?? "unknown")}</div>
        <div className="muted">Feature Schema: {String(systemStatus?.feature_schema_version ?? "unknown")}</div>
        <div className="muted">Report Schema: {String(systemStatus?.report_schema_version ?? "unknown")}</div>
      </article>
    </section>
  );
}
