/* eslint-disable no-console */
const { Board } = require("dgtchess");

function parseArgs(argv) {
  const out = {
    apiBase: null,
    eventId: null,
    sessionId: null,
    boardSerial: null,
    role: "system_admin",
    port: null,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = i + 1 < argv.length ? argv[i + 1] : null;
    if (arg === "--api-base") {
      out.apiBase = next;
      i += 1;
    } else if (arg === "--event-id") {
      out.eventId = next;
      i += 1;
    } else if (arg === "--session-id") {
      out.sessionId = next;
      i += 1;
    } else if (arg === "--board-serial") {
      out.boardSerial = next;
      i += 1;
    } else if (arg === "--x-role") {
      out.role = next || out.role;
      i += 1;
    } else if (arg === "--port") {
      out.port = next;
      i += 1;
    }
  }
  return out;
}

function extractFen(position) {
  if (!position) return null;
  if (typeof position.fen === "string") return position.fen;
  if (typeof position.fenString === "string") return position.fenString;
  if (typeof position.toFen === "function") return position.toFen();
  return null;
}

async function postEvent(settings, payload) {
  const url = `${settings.apiBase.replace(/\/$/, "")}/v1/otb/board-events`;
  try {
    await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Role": settings.role,
      },
      body: JSON.stringify(payload),
    });
  } catch {
    // swallow transient network errors
  }
}

async function run() {
  const settings = parseArgs(process.argv.slice(2));
  if (!settings.apiBase || !settings.eventId || !settings.port) {
    console.error("Usage: node index.js --api-base http://localhost:8000 --event-id EVENT123 --port COM3 [--session-id SESSION1] [--board-serial SERIAL] [--x-role system_admin]");
    process.exit(2);
  }

  const board = new Board(settings.port);
  const resetInfo = await board.reset();
  if (resetInfo && resetInfo.serialNr && !settings.boardSerial) {
    settings.boardSerial = resetInfo.serialNr;
  }

  board.on("data", async (position) => {
    const fen = extractFen(position);
    const payload = {
      event_id: settings.eventId,
      session_id: settings.sessionId,
      board_serial: settings.boardSerial,
      move_uci: null,
      ply: null,
      fen,
      clock_ms: null,
      raw: position || {},
    };
    await postEvent(settings, payload);
  });
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
