from __future__ import annotations

import csv
import io
from datetime import UTC, datetime
import html
from typing import Any

from sentinel.config import settings

def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _section(title: str, body: str | list[str]) -> dict[str, Any]:
    if isinstance(body, list):
        text = "\n".join(body)
    else:
        text = body
    return {"title": title, "body": text}


def _non_accusatory_conclusion(risk_tier: str) -> str:
    base = (
        "This report does not assert cheating. It summarizes statistical and behavioral indicators "
        "that may warrant human review."
    )
    if risk_tier in {"HIGH_STATISTICAL_ANOMALY", "ELEVATED"}:
        return (
            f"{base} The observed patterns are elevated relative to expected variation for similar-rated players."
        )
    return f"{base} The observed patterns are within expected variation for similar-rated players."


def build_structured_report(
    analysis: dict[str, Any],
    evidence: dict[str, Any] | None,
    notes: list[dict[str, Any]] | None,
    mode: str,
) -> dict[str, Any]:
    mode = mode.lower().strip()
    now = datetime.now(UTC).isoformat()
    risk_tier = str(analysis.get("risk_tier") or "LOW")
    confidence = _safe_float(analysis.get("confidence")) or 0.0
    player_id = analysis.get("player_id")
    event_id = analysis.get("event_id")
    analyzed_moves = analysis.get("analyzed_move_count")

    summary_lines = [
        f"Player: {player_id}",
        f"Event: {event_id}",
        f"Risk tier: {risk_tier}",
        f"Confidence: {confidence:.2f}",
        f"Analyzed moves: {analyzed_moves}",
    ]
    if mode == "technical":
        summary_lines.append(f"Weighted risk score: {analysis.get('weighted_risk_score')}")

    methodology_lines = [
        "Analysis is based on engine-assisted evaluation, Maia alignment metrics,",
        "statistical thresholds by rating band, and timing/complexity-adjusted signals.",
        "Signals are fused into a weighted risk score with conservative override rules.",
    ]
    if mode == "legal":
        methodology_lines.append(
            "The methodology does not produce cheating verdicts and is intended for human review."
        )

    findings_lines: list[str] = []
    signals = analysis.get("signals") or []
    for sig in signals:
        if not isinstance(sig, dict):
            continue
        if sig.get("triggered"):
            findings_lines.append(f"{sig.get('name')}: {sig.get('score')} (threshold {sig.get('threshold')})")
    if not findings_lines:
        findings_lines.append("No signals exceeded thresholds.")

    statistical_lines = [
        f"Regan Z: {analysis.get('regan_z_score')}",
        f"Regan threshold: {analysis.get('regan_threshold')}",
        f"Natural occurrence probability: {analysis.get('natural_occurrence_probability')}",
    ]
    if evidence:
        statistical_lines.append(f"Anomaly score: {evidence.get('anomaly_score')}")
        statistical_lines.append(f"Engine match %: {evidence.get('engine_match_percentage')}")
        if evidence.get("maia_agreement_percentage") is not None:
            statistical_lines.append(f"Maia agreement %: {evidence.get('maia_agreement_percentage')}")

    limitations_lines = [
        "Findings are statistical and depend on available game data quality.",
        "Online behavioral signals may be limited without platform integrations.",
        "This report should be interpreted by qualified arbiters or committees.",
    ]

    behavioral_lines: list[str] = []
    behavioral_metrics = analysis.get("behavioral_metrics") or {}
    if isinstance(behavioral_metrics, dict) and behavioral_metrics:
        for key in sorted(behavioral_metrics.keys()):
            value = behavioral_metrics.get(key)
            if value is None:
                continue
            behavioral_lines.append(f"{key}: {value}")
    environment_metrics = analysis.get("environmental_metrics") or {}
    if isinstance(environment_metrics, dict) and environment_metrics:
        for key in sorted(environment_metrics.keys()):
            value = environment_metrics.get(key)
            if value is None:
                continue
            behavioral_lines.append(f"environment.{key}: {value}")
    identity_confidence = analysis.get("identity_confidence") or {}
    if isinstance(identity_confidence, dict) and identity_confidence:
        for key in sorted(identity_confidence.keys()):
            value = identity_confidence.get(key)
            if value is None:
                continue
            behavioral_lines.append(f"identity.{key}: {value}")
    if not behavioral_lines:
        behavioral_lines.append("No behavioral telemetry supplied.")

    if mode == "arbiter":
        methodology_lines = ["Summary of standard Sentinel analysis and rating-band thresholds."]
        statistical_lines = [line for line in statistical_lines if "None" not in str(line)]
        limitations_lines = ["Statistical indicators require human review and context."]
    elif mode == "legal":
        findings_lines.append(
            "No assertion of misconduct is made; findings are presented as statistical observations."
        )

    notes_block: list[str] = []
    for note in notes or []:
        text = note.get("text")
        if text:
            notes_block.append(text)
    if not notes_block:
        notes_block.append("No arbiter notes attached.")

    sections = [
        _section("Overview", summary_lines),
        _section("Methodology", methodology_lines),
        _section("Findings", findings_lines),
        _section("Statistical Interpretation", statistical_lines),
        _section("Behavioral Signals", behavioral_lines),
        _section("Limitations", limitations_lines),
        _section("Conclusion", _non_accusatory_conclusion(risk_tier)),
    ]
    return {
        "generated_at": now,
        "mode": mode,
        "player_id": player_id,
        "event_id": event_id,
        "sections": sections,
        "arbiter_notes": notes_block,
    }


def report_to_csv(report: dict[str, Any]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["section", "content"])
    for section in report.get("narrative_sections") or []:
        title = section.get("title")
        body = section.get("body")
        writer.writerow([f"AI Narrative - {title}", body])
    for section in report.get("sections") or []:
        title = section.get("title")
        body = section.get("body")
        writer.writerow([title, body])
    return output.getvalue()


def report_to_html(report: dict[str, Any]) -> str:
    def esc(value: Any) -> str:
        return html.escape("" if value is None else str(value))

    narrative_sections = report.get("narrative_sections") or []
    data_sections = report.get("sections") or []
    title = f"Sentinel Report ({report.get('mode')})"
    generated_at = report.get("generated_at") or ""
    css = """
    body { font-family: "Segoe UI", Arial, sans-serif; margin: 32px; color: #111; }
    h1 { font-size: 22px; margin-bottom: 4px; }
    h2 { font-size: 16px; margin-top: 24px; margin-bottom: 6px; }
    .meta { font-size: 12px; color: #555; margin-bottom: 16px; }
    .section { margin-bottom: 12px; }
    .note { margin: 6px 0; }
    .divider { border-top: 1px solid #ddd; margin: 18px 0; }
    .muted { color: #666; font-size: 12px; }
    pre { white-space: pre-wrap; font-family: inherit; }
    """
    parts = [
        "<html><head><meta charset='utf-8'/>",
        f"<style>{css}</style>",
        "</head><body>",
        f"<h1>{esc(title)}</h1>",
        f"<div class='meta'>Generated at {esc(generated_at)}</div>",
    ]

    if narrative_sections:
        parts.append("<h2>AI Narrative</h2>")
        for section in narrative_sections:
            parts.append(f"<div class='section'><strong>{esc(section.get('title'))}</strong>")
            parts.append(f"<pre>{esc(section.get('body'))}</pre></div>")
        parts.append("<div class='divider'></div>")

    parts.append("<h2>Data Appendix</h2>")
    for section in data_sections:
        parts.append(f"<div class='section'><strong>{esc(section.get('title'))}</strong>")
        parts.append(f"<pre>{esc(section.get('body'))}</pre></div>")

    parts.append("<h2>Arbiter Notes</h2>")
    notes = report.get("arbiter_notes") or []
    if notes:
        for note in notes:
            parts.append(f"<div class='note'>- {esc(note)}</div>")
    else:
        parts.append("<div class='note muted'>No arbiter notes attached.</div>")

    disclaimer = settings.legal_disclaimer_text
    if disclaimer:
        parts.append(f"<div class='divider'></div><div class='muted'>{esc(disclaimer)}</div>")

    parts.append("</body></html>")
    return "\n".join(parts)


def report_to_pdf(report: dict[str, Any]) -> bytes:
    engine = (report.get("pdf_engine") or settings.report_pdf_engine or "auto").lower()
    if engine in {"auto", "weasyprint"}:
        try:
            from weasyprint import HTML  # type: ignore

            html_doc = report_to_html(report)
            return HTML(string=html_doc).write_pdf()
        except Exception:
            if engine == "weasyprint":
                raise

    # Minimal single-page PDF writer (no external deps).
    lines: list[str] = []
    lines.append(f"Sentinel Report ({report.get('mode')})")
    lines.append("")
    if report.get("narrative_sections"):
        lines.append("AI NARRATIVE")
        lines.append("")
        for section in report.get("narrative_sections") or []:
            lines.append(str(section.get("title") or "").upper())
            body = section.get("body") or ""
            for part in str(body).splitlines():
                lines.append(part)
            lines.append("")
    for section in report.get("sections") or []:
        lines.append(str(section.get("title") or "").upper())
        body = section.get("body") or ""
        for part in str(body).splitlines():
            lines.append(part)
        lines.append("")
    lines.append("Arbiter Notes:")
    for note in report.get("arbiter_notes") or []:
        lines.append(f"- {note}")

    # PDF text content
    text_lines = []
    y = 760
    for line in lines:
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        text_lines.append(f"1 0 0 1 50 {y} Tm ({safe}) Tj")
        y -= 14
        if y < 60:
            break
    text_stream = "BT /F1 11 Tf " + " ".join(text_lines) + " ET"
    content = text_stream.encode("latin-1", errors="ignore")

    # Build minimal PDF
    objects = []
    objects.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj")
    objects.append(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj")
    objects.append(
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj"
    )
    objects.append(b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj")
    objects.append(b"5 0 obj << /Length " + str(len(content)).encode("ascii") + b" >> stream\n" + content + b"\nendstream endobj")

    xref_positions = []
    pdf = bytearray()
    pdf.extend(b"%PDF-1.4\n")
    for obj in objects:
        xref_positions.append(len(pdf))
        pdf.extend(obj + b"\n")
    xref_start = len(pdf)
    pdf.extend(b"xref\n0 6\n0000000000 65535 f \n")
    for pos in xref_positions:
        pdf.extend(f"{pos:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n" + str(xref_start).encode("ascii") + b"\n%%EOF"
    )
    return bytes(pdf)
