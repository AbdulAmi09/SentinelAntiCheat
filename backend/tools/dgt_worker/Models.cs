using System.Text.RegularExpressions;

namespace DgtWorker;

internal sealed record DgtWorkerSettings(
    string ApiBase,
    string EventId,
    string? SessionId,
    string? BoardSerial,
    string Role,
    bool UseStdinJson,
    string? DllPath,
    int PollMs,
    bool Valid,
    string ErrorMessage
)
{
    public static DgtWorkerSettings Parse(string[] args)
    {
        string? apiBase = null;
        string? eventId = null;
        string? sessionId = null;
        string? boardSerial = null;
        string role = "system_admin";
        bool stdinJson = false;
        string? dllPath = null;
        int pollMs = 120;

        for (var i = 0; i < args.Length; i++)
        {
            var arg = args[i];
            string? next = i + 1 < args.Length ? args[i + 1] : null;
            switch (arg)
            {
                case "--api-base":
                    apiBase = next;
                    i++;
                    break;
                case "--event-id":
                    eventId = next;
                    i++;
                    break;
                case "--session-id":
                    sessionId = next;
                    i++;
                    break;
                case "--board-serial":
                    boardSerial = next;
                    i++;
                    break;
                case "--x-role":
                    role = next ?? role;
                    i++;
                    break;
                case "--stdin-json":
                    stdinJson = true;
                    break;
                case "--dll-path":
                    dllPath = next;
                    i++;
                    break;
                case "--poll-ms":
                    if (int.TryParse(next, out var poll))
                    {
                        pollMs = Math.Max(20, Math.Min(5000, poll));
                    }
                    i++;
                    break;
            }
        }

        if (string.IsNullOrWhiteSpace(apiBase) || string.IsNullOrWhiteSpace(eventId))
        {
            return new DgtWorkerSettings(apiBase ?? "", eventId ?? "", sessionId, boardSerial, role, stdinJson, dllPath, pollMs, false, "Missing --api-base or --event-id.");
        }

        return new DgtWorkerSettings(apiBase, eventId, sessionId, boardSerial, role, stdinJson, dllPath, pollMs, true, "");
    }
}

internal sealed record DgtBoardEvent(
    string event_id,
    string? session_id,
    string? board_serial,
    string? move_uci,
    int? ply,
    string? fen,
    int? clock_ms,
    Dictionary<string, object> raw
);

internal static class DgtPayloadParser
{
    private static readonly Regex UciRegex = new(@"^[a-h][1-8][a-h][1-8][qrbn]?$", RegexOptions.Compiled | RegexOptions.IgnoreCase);

    public static bool TryParseMove(string payload, out string moveUci)
    {
        moveUci = payload.Trim();
        if (UciRegex.IsMatch(moveUci))
        {
            moveUci = moveUci.ToLowerInvariant();
            return true;
        }
        moveUci = string.Empty;
        return false;
    }

    public static bool TryParseFen(string payload, out string fen)
    {
        fen = payload.Trim();
        if (fen.Contains('/') && fen.Split(' ').Length >= 4)
        {
            return true;
        }
        fen = string.Empty;
        return false;
    }
}
