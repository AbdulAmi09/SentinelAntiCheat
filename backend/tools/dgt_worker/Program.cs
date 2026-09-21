using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

namespace DgtWorker;

internal static class Program
{
    public static int Main(string[] args)
    {
        var settings = DgtWorkerSettings.Parse(args);
        if (!settings.Valid)
        {
            Console.Error.WriteLine(settings.ErrorMessage);
            Console.Error.WriteLine("Usage: dgt_worker --api-base http://localhost:8000 --event-id EVENT123 [--session-id S1] [--board-serial SERIAL] [--x-role system_admin] [--stdin-json] [--dll-path C:\\path\\DgtBoard.dll]");
            return 2;
        }

        using var http = new HttpClient();
        http.Timeout = TimeSpan.FromSeconds(5);
        http.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
        http.DefaultRequestHeaders.Add("X-Role", settings.Role);

        using var cts = new CancellationTokenSource();
        Console.CancelKeyPress += (_, e) =>
        {
            e.Cancel = true;
            cts.Cancel();
        };

        if (settings.UseStdinJson)
        {
            return RunStdinMode(http, settings, cts.Token);
        }

        return RunDgtMode(http, settings, cts.Token);
    }

    private static int RunStdinMode(HttpClient http, DgtWorkerSettings settings, CancellationToken token)
    {
        string? line;
        while (!token.IsCancellationRequested && (line = Console.ReadLine()) != null)
        {
            line = line.Trim();
            if (line.Length == 0) continue;
            try
            {
                var raw = JsonSerializer.Deserialize<Dictionary<string, object>>(line) ?? new Dictionary<string, object>();
                var move = GetString(raw, "move_uci") ?? GetString(raw, "move") ?? GetString(raw, "uci");
                var ply = GetInt(raw, "ply");
                var fen = GetString(raw, "fen");
                var clockMs = GetInt(raw, "clock_ms");
                var evt = new DgtBoardEvent(settings.EventId, settings.SessionId, settings.BoardSerial, move, ply, fen, clockMs, raw);
                PostEvent(http, settings, evt, token);
            }
            catch
            {
                continue;
            }
        }
        return 0;
    }

    private static int RunDgtMode(HttpClient http, DgtWorkerSettings settings, CancellationToken token)
    {
        using var client = new DgtBoardClient(settings.DllPath);
        if (!client.TryOpen(out var serial))
        {
            Console.Error.WriteLine("Failed to open DGT board.");
            return 1;
        }

        if (string.IsNullOrWhiteSpace(settings.BoardSerial) && !string.IsNullOrWhiteSpace(serial))
        {
            settings = settings with { BoardSerial = serial };
        }

        var plyCounter = 0;
        while (!token.IsCancellationRequested)
        {
            if (!client.TryReadMessage(out var payload))
            {
                Thread.Sleep(settings.PollMs);
                continue;
            }

            var move = DgtPayloadParser.TryParseMove(payload, out var parsedMove) ? parsedMove : null;
            var fen = DgtPayloadParser.TryParseFen(payload, out var parsedFen) ? parsedFen : null;
            var clockMs = client.TryGetClockMs();
            if (move != null)
            {
                plyCounter += 1;
            }

            var evt = new DgtBoardEvent(
                settings.EventId,
                settings.SessionId,
                settings.BoardSerial,
                move,
                move != null ? plyCounter : null,
                fen,
                clockMs,
                new Dictionary<string, object> { { "payload", payload } }
            );
            PostEvent(http, settings, evt, token);
        }
        return 0;
    }

    private static void PostEvent(HttpClient http, DgtWorkerSettings settings, DgtBoardEvent evt, CancellationToken token)
    {
        var url = settings.ApiBase.TrimEnd('/') + "/v1/otb/board-events";
        var json = JsonSerializer.Serialize(evt);
        using var content = new StringContent(json, Encoding.UTF8, "application/json");
        try
        {
            var response = http.PostAsync(url, content, token).GetAwaiter().GetResult();
            response.Content.ReadAsStringAsync(token).GetAwaiter().GetResult();
        }
        catch
        {
            // Swallow transient errors and continue streaming.
        }
    }

    private static string? GetString(Dictionary<string, object> raw, string key)
    {
        if (!raw.TryGetValue(key, out var val) || val == null) return null;
        return val.ToString();
    }

    private static int? GetInt(Dictionary<string, object> raw, string key)
    {
        if (!raw.TryGetValue(key, out var val) || val == null) return null;
        if (val is JsonElement je)
        {
            if (je.ValueKind == JsonValueKind.Number && je.TryGetInt32(out var num)) return num;
            if (je.ValueKind == JsonValueKind.String && int.TryParse(je.GetString(), out var num2)) return num2;
        }
        if (int.TryParse(val.ToString(), out var num3)) return num3;
        return null;
    }
}
