using System.Runtime.InteropServices;
using System.Text;

namespace DgtWorker;

internal sealed class DgtBoardClient : IDisposable
{
    private readonly DgtNativeApi _api;
    private bool _opened;

    public DgtBoardClient(string? dllPath)
    {
        _api = DgtNativeApi.Load(dllPath);
    }

    public bool TryOpen(out string? serial)
    {
        serial = null;
        if (!_api.IsLoaded) return false;
        if (_api.Init() != 0) return false;
        if (_api.Open() != 0) return false;
        _opened = true;
        serial = _api.GetSerial();
        return true;
    }

    public bool TryReadMessage(out string payload)
    {
        payload = string.Empty;
        if (!_opened) return false;
        return _api.TryGetMessage(out payload);
    }

    public int? TryGetClockMs()
    {
        if (!_opened) return null;
        return _api.TryGetClockMs();
    }

    public void Dispose()
    {
        if (_opened)
        {
            _api.Close();
        }
        _api.Dispose();
    }
}

internal sealed class DgtNativeApi : IDisposable
{
    private readonly IntPtr _lib;
    private readonly SimpleFn? _init;
    private readonly SimpleFn? _open;
    private readonly SimpleFn? _close;
    private readonly GetSerialFn? _getSerial;
    private readonly GetMessageFn? _getMessage;
    private readonly GetClockFn? _getClock;

    private DgtNativeApi(
        IntPtr lib,
        SimpleFn? init,
        SimpleFn? open,
        SimpleFn? close,
        GetSerialFn? getSerial,
        GetMessageFn? getMessage,
        GetClockFn? getClock
    )
    {
        _lib = lib;
        _init = init;
        _open = open;
        _close = close;
        _getSerial = getSerial;
        _getMessage = getMessage;
        _getClock = getClock;
    }

    public bool IsLoaded => _lib != IntPtr.Zero && _init != null && _open != null && _close != null && _getMessage != null;

    public static DgtNativeApi Load(string? dllPath)
    {
        IntPtr lib;
        try
        {
            lib = string.IsNullOrWhiteSpace(dllPath) ? NativeLibrary.Load("DgtBoard.dll") : NativeLibrary.Load(dllPath);
        }
        catch
        {
            return new DgtNativeApi(IntPtr.Zero, null, null, null, null, null, null);
        }

        var init = Resolve<SimpleFn>(lib, "DgtBoardInit", "DGT_Init", "Init");
        var open = Resolve<SimpleFn>(lib, "DgtBoardOpen", "DGT_Open", "Open");
        var close = Resolve<SimpleFn>(lib, "DgtBoardClose", "DGT_Close", "Close");
        var getSerial = Resolve<GetSerialFn>(lib, "DgtBoardGetSerialNumber", "GetSerialNumber");
        var getMessage = Resolve<GetMessageFn>(lib, "DgtBoardGetMessage", "GetMessage");
        var getClock = Resolve<GetClockFn>(lib, "DgtBoardGetClock", "GetClock");

        return new DgtNativeApi(lib, init, open, close, getSerial, getMessage, getClock);
    }

    public int Init() => _init?.Invoke() ?? -1;
    public int Open() => _open?.Invoke() ?? -1;
    public int Close() => _close?.Invoke() ?? -1;

    public string? GetSerial()
    {
        if (_getSerial == null) return null;
        var sb = new StringBuilder(64);
        var rc = _getSerial(sb, sb.Capacity);
        if (rc != 0) return null;
        return sb.ToString().Trim();
    }

    public bool TryGetMessage(out string payload)
    {
        payload = string.Empty;
        if (_getMessage == null) return false;
        var buffer = new byte[256];
        var rc = _getMessage(buffer, buffer.Length, out var length);
        if (rc != 0 || length <= 0) return false;
        payload = Encoding.ASCII.GetString(buffer, 0, Math.Min(length, buffer.Length)).Trim('\0', '\r', '\n');
        if (payload.Length == 0)
        {
            payload = Convert.ToBase64String(buffer, 0, Math.Min(length, buffer.Length));
        }
        return true;
    }

    public int? TryGetClockMs()
    {
        if (_getClock == null) return null;
        var clock = new DgtClock();
        var rc = _getClock(ref clock);
        if (rc != 0) return null;
        return clock.WhiteMs > 0 ? clock.WhiteMs : (clock.BlackMs > 0 ? clock.BlackMs : null);
    }

    public void Dispose()
    {
        if (_lib != IntPtr.Zero)
        {
            NativeLibrary.Free(_lib);
        }
    }

    private static T? Resolve<T>(IntPtr lib, params string[] names) where T : class
    {
        foreach (var name in names)
        {
            if (NativeLibrary.TryGetExport(lib, name, out var ptr))
            {
                return Marshal.GetDelegateForFunctionPointer(ptr, typeof(T)) as T;
            }
        }
        return null;
    }

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    private delegate int SimpleFn();

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    private delegate int GetSerialFn(StringBuilder buffer, int len);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    private delegate int GetMessageFn(byte[] buffer, int bufferLen, out int messageLen);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    private delegate int GetClockFn(ref DgtClock clock);

    [StructLayout(LayoutKind.Sequential)]
    private struct DgtClock
    {
        public int WhiteMs;
        public int BlackMs;
        public int Flags;
    }
}
