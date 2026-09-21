(function () {
  function getScript() {
    var scripts = document.getElementsByTagName("script");
    for (var i = scripts.length - 1; i >= 0; i--) {
      var src = scripts[i].getAttribute("src") || "";
      if (src.indexOf("/sdk/sentinel.js") !== -1) return scripts[i];
    }
    return null;
  }

  var script = getScript();
  if (!script) return;
  var apiKey = script.getAttribute("data-api-key");
  if (!apiKey) return;

  var apiBase = script.getAttribute("data-api-base") || "";
  if (!apiBase) {
    var src = script.getAttribute("src") || "";
    var parts = src.split("/sdk/");
    apiBase = parts[0] || "";
  }
  var callbackUrl = script.getAttribute("data-callback-url") || "";
  var mode = script.getAttribute("data-mode") || "standard";
  var sessionId = script.getAttribute("data-session-id") || "";
  var cameraMode = script.getAttribute("data-camera-mode") || "safe";
  var cameraConsent = (script.getAttribute("data-camera-consent") || "").toLowerCase() === "true";
  var deviceFpMode = script.getAttribute("data-device-fingerprint") || "auto";
  var dgtMode = script.getAttribute("data-dgt-mode") || "";
  var otbEventId = script.getAttribute("data-otb-event-id") || "";
  var otbRole = script.getAttribute("data-otb-role") || "system_admin";

  var payload = {
    game_id: "",
    player_id: "",
    player_color: "white",
    pgn: "",
    fen_history: [],
    move_history: [],
    mouse_events: [],
    click_timing: [],
    window_events: [],
    keyboard_events: [],
    page_events: [],
    touch_events: [],
    connection_events: [],
    environment: {},
    session: {},
    per_move_summary: [],
    camera_events: [],
    camera_storage_mode: cameraMode,
    consent: { camera_raw: cameraConsent, timestamp: new Date().toISOString() },
    device_fingerprint: {},
  };

  function nowMs() { return Date.now(); }

  function captureEnv() {
    payload.environment = {
      viewport: { w: window.innerWidth, h: window.innerHeight },
      screen: { w: window.screen.width, h: window.screen.height },
      device_pixel_ratio: window.devicePixelRatio || 1,
      user_agent: navigator.userAgent,
      touch: "ontouchstart" in window,
    };
  }

  function addIndicator() {
    var el = document.createElement("div");
    el.textContent = cameraMode === "raw" ? "Sentinel Monitoring + Camera Active" : "Sentinel Monitoring Active";
    el.style.position = "fixed";
    el.style.bottom = "12px";
    el.style.right = "12px";
    el.style.zIndex = "99999";
    el.style.padding = "6px 10px";
    el.style.fontSize = "12px";
    el.style.background = "rgba(10,20,35,0.9)";
    el.style.color = "#bcd7ff";
    el.style.border = "1px solid #2b5076";
    el.style.borderRadius = "999px";
    el.style.fontFamily = "sans-serif";
    document.body.appendChild(el);
  }

  var lastMouse = 0;
  function onMouseMove(e) {
    var t = nowMs();
    if (t - lastMouse < 100) return;
    lastMouse = t;
    payload.mouse_events.push({
      x: e.clientX, y: e.clientY, t: t,
    });
    if (ws && ws.readyState === 1) ws.send(JSON.stringify({ type: "mouse", x: e.clientX, y: e.clientY, t: t }));
  }

  function onWindowEvent(type) {
    return function () {
      var t = nowMs();
      payload.window_events.push({ type: type, t: t });
      if (ws && ws.readyState === 1) ws.send(JSON.stringify({ type: type, t: t }));
    };
  }

  function onCopy(type) {
    return function () {
      var t = nowMs();
      payload.page_events.push({ type: type, t: t });
      if (ws && ws.readyState === 1) ws.send(JSON.stringify({ type: type, t: t }));
    };
  }

  function onKey(e) {
    payload.keyboard_events.push({ key: e.key, t: nowMs() });
  }

  function sendFinal() {
    if (!apiBase) return;
    if (!payload.pgn) {
      if (window.SENTINEL_PGN) payload.pgn = window.SENTINEL_PGN;
    }
    if (!payload.pgn) return;
    fetch(apiBase + "/v1/partner/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": apiKey,
      },
      body: JSON.stringify(payload),
    }).catch(function () {});
  }

  function postOtbBoardEvent(evt) {
    if (!apiBase) return;
    fetch(apiBase + "/v1/otb/board-events", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Role": otbRole,
      },
      body: JSON.stringify(evt),
    }).catch(function () {});
  }

  function extractFen(position) {
    if (!position) return null;
    if (typeof position.fen === "string") return position.fen;
    if (typeof position.fenString === "string") return position.fenString;
    if (typeof position.toFen === "function") return position.toFen();
    return null;
  }

  function attachDgtBoard(board, options) {
    if (!board) return;
    var opts = options || {};
    var boardSerial = opts.boardSerial || "";
    var eventId = opts.eventId || otbEventId || payload.game_id || sessionId || "otb-event";
    var session = opts.sessionId || sessionId || null;
    if (typeof board.reset === "function") {
      try {
        Promise.resolve(board.reset()).then(function (info) {
          if (!boardSerial && info && (info.serialNr || info.serial || info.serialNumber)) {
            boardSerial = info.serialNr || info.serial || info.serialNumber;
          }
        }).catch(function () {});
      } catch (e) {}
    }

    if (typeof board.on === "function") {
      board.on("data", function (position) {
        var fen = extractFen(position);
        var evt = {
          event_id: eventId,
          session_id: session,
          board_serial: boardSerial || null,
          move_uci: null,
          ply: null,
          fen: fen,
          clock_ms: null,
          raw: position || {},
        };
        postOtbBoardEvent(evt);
      });
    }
  }

  function connectDgtWebSerial(options) {
    var opts = options || {};
    var BoardCtor = opts.Board || window.DgtChessBoard || (window.dgtchess && window.dgtchess.Board) || (window.DgtChess && window.DgtChess.Board);
    if (!BoardCtor) return Promise.reject(new Error("DGT Board class not available. Provide opts.Board or load dgtchess."));
    if (!navigator.serial || !navigator.serial.requestPort) return Promise.reject(new Error("Web Serial API not available."));
    return navigator.serial.requestPort({}).then(function (port) {
      var board = new BoardCtor(port);
      attachDgtBoard(board, opts);
      return board;
    });
  }

  var ws = null;
  if (mode === "hybrid" && sessionId) {
    var wsUrl = apiBase.replace(/^http/, "ws") + "/ws/live/" + sessionId + "?api_key=" + encodeURIComponent(apiKey);
    ws = new WebSocket(wsUrl);
  }

  captureEnv();
  addIndicator();
  if (deviceFpMode === "auto") computeFingerprint();

  document.addEventListener("mousemove", onMouseMove);
  document.addEventListener("copy", onCopy("copy"));
  document.addEventListener("cut", onCopy("cut"));
  document.addEventListener("paste", onCopy("paste"));
  window.addEventListener("blur", onWindowEvent("blur"));
  window.addEventListener("focus", onWindowEvent("focus"));
  document.addEventListener("keydown", onKey);

  window.addEventListener("sentinel:game_end", function (evt) {
    var detail = (evt && evt.detail) || {};
    payload.game_id = detail.game_id || payload.game_id || sessionId || "game-unknown";
    payload.player_id = detail.player_id || payload.player_id || "player-unknown";
    payload.player_color = detail.player_color || payload.player_color || "white";
    payload.pgn = detail.pgn || payload.pgn;
    if (ws && ws.readyState === 1) ws.send(JSON.stringify({ type: "game_end", pgn: payload.pgn, game_id: payload.game_id, player_id: payload.player_id, player_color: payload.player_color }));
    sendFinal();
  });

  window.SentinelSDK = {
    setGameMeta: function (gameId, playerId, color) {
      payload.game_id = gameId;
      payload.player_id = playerId;
      payload.player_color = color || payload.player_color;
    },
    setConsent: function (type, value) {
      payload.consent[type] = !!value;
      payload.consent.timestamp = new Date().toISOString();
    },
    recordCameraEvent: function (evt) {
      if (!evt) return;
      if (cameraMode === "raw" && !payload.consent.camera_raw) return;
      payload.camera_events.push(evt);
      if (ws && ws.readyState === 1) ws.send(JSON.stringify({ type: "camera", data: evt, t: nowMs() }));
    },
    setDeviceFingerprint: function (fp) {
      payload.device_fingerprint = fp || {};
    },
    recordMove: function (move) {
      payload.move_history.push(move || {});
      if (ws && ws.readyState === 1) ws.send(JSON.stringify({ type: "move", uci: move.uci, ply: move.ply, t: nowMs() }));
    },
    endGame: function (pgn) {
      payload.pgn = pgn || payload.pgn;
      var event = new CustomEvent("sentinel:game_end", { detail: { pgn: payload.pgn } });
      window.dispatchEvent(event);
    },
    attachDgtBoard: attachDgtBoard,
    connectDgtWebSerial: connectDgtWebSerial,
  };

  function computeFingerprint() {
    try {
      var tz = "";
      try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ""; } catch (e) {}
      var raw = [
        navigator.userAgent,
        screen.width + "x" + screen.height,
        navigator.language || "",
        tz,
        String(window.devicePixelRatio || 1),
      ].join("|");
      if (window.crypto && window.crypto.subtle && window.TextEncoder) {
        var enc = new TextEncoder();
        window.crypto.subtle.digest("SHA-256", enc.encode(raw)).then(function (buf) {
          var bytes = new Uint8Array(buf);
          var hex = Array.prototype.map.call(bytes, function (b) { return ("00" + b.toString(16)).slice(-2); }).join("");
          payload.device_fingerprint = { fingerprint_hash: hex, source: "sdk_auto" };
        }).catch(function () {
          payload.device_fingerprint = { fingerprint_raw: raw, source: "sdk_fallback" };
        });
      } else {
        payload.device_fingerprint = { fingerprint_raw: raw, source: "sdk_fallback" };
      }
    } catch (e) {}
  }

  if (dgtMode === "web-serial") {
    // Must be called from a user gesture for Web Serial to work.
    console.log("SentinelSDK: call SentinelSDK.connectDgtWebSerial() from a user gesture to connect DGT board.");
  }
})();
