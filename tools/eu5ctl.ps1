# Drive EU5 on Windows: the Windows twin of eu5ctl.sh, with the same commands. It moves the real mouse and types on
# the real keyboard, so leave them alone while it runs. The game must be the window in front: every command brings it there.
# Menu path (1280-wide shot coords): New Game -> click the country on the map -> move the mouse away (its tooltip hides
# the button) -> "Play as". The console opens with Alt+C (-debug_mode): grave is the other default, but settings can unbind it.
# Observe + `tag X` leaves you an observer: console effects work, but your UI commands (diplomacy, IO laws) are dropped.
#   eu5ctl start | wait | stop | status   (wait: until loading or new-game generation is done)
#   eu5ctl shot [name]            -> prints a 1280-wide jpg path (click coordinates use this space)
#   eu5ctl click X Y [button]     eu5ctl hover X Y     eu5ctl key KEY...     eu5ctl type TEXT
#   eu5ctl cmd "tag HAS"          open console, run one command, close console
#   eu5ctl run FILE               copy an effect file into Documents/.../run/ and `run` it
#   eu5ctl log [N] [file]         last N lines of a log (default 40 of debug.log, where debug_log output lands)
# Call it as: powershell -ExecutionPolicy Bypass -File tools\eu5ctl.ps1 <command> ...
# Keys use eu5ctl.sh's names: Return, Escape, grave, space, Tab, F1..F12, letters, and combos like ctrl+s.
$ErrorActionPreference = "Stop"
$Command = if ($args.Count) { [string]$args[0] } else { "" }
$Rest = @($args | Select-Object -Skip 1)

$GAME = if ($env:EU5_GAME) { $env:EU5_GAME } else { "${env:ProgramFiles(x86)}\Steam\steamapps\common\Europa Universalis V\game" }
$BINARIES = Join-Path (Split-Path $GAME) "binaries"
$DOCS = Join-Path ([Environment]::GetFolderPath("MyDocuments")) "Paradox Interactive\Europa Universalis V"
$STATE = Join-Path $env:TEMP "eu5ctl"
$SHOT_W = 1280
New-Item -ItemType Directory -Force $STATE | Out-Null

Add-Type -AssemblyName System.Drawing
if (-not ("Eu5Ctl" -as [type])) {
    Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class Eu5Ctl {
    [StructLayout(LayoutKind.Sequential)] struct MOUSEINPUT { public int dx, dy; public uint mouseData, dwFlags, time; public IntPtr extra; }
    [StructLayout(LayoutKind.Sequential)] struct KEYBDINPUT { public ushort wVk, wScan; public uint dwFlags, time; public IntPtr extra; }
    [StructLayout(LayoutKind.Explicit)] struct UNION { [FieldOffset(0)] public MOUSEINPUT mi; [FieldOffset(0)] public KEYBDINPUT ki; }
    [StructLayout(LayoutKind.Sequential)] struct INPUT { public uint type; public UNION u; }
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
    [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X, Y; }
    [DllImport("user32.dll")] static extern uint SendInput(uint n, INPUT[] inputs, int size);
    [DllImport("user32.dll")] static extern uint MapVirtualKey(uint code, uint mapType);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr h, ref POINT p);
    [DllImport("user32.dll")] static extern void keybd_event(byte vk, byte scan, uint flags, IntPtr extra);

    static void Send(INPUT i) { SendInput(1, new INPUT[] { i }, Marshal.SizeOf(typeof(INPUT))); }
    public static void Mouse(uint flags) { INPUT i = new INPUT(); i.type = 0; i.u.mi.dwFlags = flags; Send(i); }
    // the virtual key and its scancode both: games reading raw input look at the scancode
    public static void Key(ushort vk, bool up) {
        INPUT i = new INPUT(); i.type = 1; i.u.ki.wVk = vk; i.u.ki.wScan = (ushort)MapVirtualKey(vk, 0);
        i.u.ki.dwFlags = (up ? 2u : 0u) | ((vk >= 0x21 && vk <= 0x2E) ? 1u : 0u);   // arrows, Home/End, PgUp/PgDn, Ins/Del are extended
        Send(i);
    }
    // a character as itself, whatever the keyboard layout (an Arabic layout would turn "run" into Arabic letters)
    public static void Char(char c) {
        foreach (bool up in new bool[] { false, true }) {
            INPUT i = new INPUT(); i.type = 1; i.u.ki.wScan = c; i.u.ki.dwFlags = 4u | (up ? 2u : 0u); Send(i);
        }
    }
    // Windows only lets the process that owns the input hand the foreground away; a released Alt counts as input
    public static void Focus(IntPtr h) {
        if (IsIconic(h)) ShowWindow(h, 9);
        keybd_event(0x12, 0, 0, IntPtr.Zero); keybd_event(0x12, 0, 2, IntPtr.Zero);
        SetForegroundWindow(h);
    }
}
"@
}
[Eu5Ctl]::SetProcessDPIAware() | Out-Null   # real pixels, not the 125%/150% scaled ones

function Game { Get-Process eu5 -ErrorAction SilentlyContinue | Select-Object -First 1 }
function Fail($msg) { [Console]::Error.WriteLine("eu5ctl: $msg"); exit 1 }

# the game window, in front, as (handle, client origin on screen, client size)
function Window {
    $p = Game
    if (-not $p) { Fail "not running" }
    # after a crash the reporter window takes the input, and a stray Return would submit the report
    if (Get-Process | Where-Object { $_.ProcessName -match "crash" -and $_.Path -notmatch "Mozilla|Google|Microsoft\\Edge|BraveSoftware" }) { Fail "game crashed (crash reporter open), not sending input" }
    $h = $p.MainWindowHandle
    if ($h -eq [IntPtr]::Zero) { Fail "the game has no window yet" }
    if ([Eu5Ctl]::GetForegroundWindow() -ne $h) { [Eu5Ctl]::Focus($h); Start-Sleep -Milliseconds 300 }
    $r = New-Object Eu5Ctl+RECT; [Eu5Ctl]::GetClientRect($h, [ref]$r) | Out-Null
    $o = New-Object Eu5Ctl+POINT; [Eu5Ctl]::ClientToScreen($h, [ref]$o) | Out-Null
    [pscustomobject]@{ Handle = $h; X = $o.X; Y = $o.Y; W = $r.Right; H = $r.Bottom }
}

# screenshot space -> screen space
function MoveTo([double]$x, [double]$y) {   # typed: "156" * 2 would be "156156"
    $w = Window; $s = $w.W / $SHOT_W
    [Eu5Ctl]::SetCursorPos([int]($w.X + $x * $s), [int]($w.Y + $y * $s)) | Out-Null
    [Eu5Ctl]::Mouse(1)   # a zero move, so the game sees the cursor arrive
}

$VK = @{ return = 0x0D; enter = 0x0D; escape = 0x1B; tab = 0x09; space = 0x20; backspace = 0x08; delete = 0x2E
         grave = 0xC0; up = 0x26; down = 0x28; left = 0x25; right = 0x27; home = 0x24; end = 0x23; prior = 0x21
         next = 0x22; pause = 0x13; ctrl = 0x11; control_l = 0x11; shift = 0x10; shift_l = 0x10; alt = 0x12; alt_l = 0x12
         plus = 0xBB; minus = 0xBD; comma = 0xBC; period = 0xBE }
function KeyCode($name) {
    $n = $name.ToLower()
    if ($VK.ContainsKey($n)) { return $VK[$n] }
    if ($n -match '^f(\d{1,2})$') { return 0x6F + [int]$matches[1] }
    if ($n -match '^[a-z0-9]$') { return [int][char]$n.ToUpper() }
    Fail "unknown key $name"
}
function Keys($names) {
    Window | Out-Null
    foreach ($combo in $names) {
        $codes = @($combo -split '\+' | ForEach-Object { KeyCode $_ })
        foreach ($c in $codes) { [Eu5Ctl]::Key($c, $false); Start-Sleep -Milliseconds 20 }
        [array]::Reverse($codes)
        foreach ($c in $codes) { [Eu5Ctl]::Key($c, $true); Start-Sleep -Milliseconds 20 }
        Start-Sleep -Milliseconds 80
    }
}
function TypeText($text) {
    Window | Out-Null
    foreach ($c in $text.ToCharArray()) { [Eu5Ctl]::Char($c); Start-Sleep -Milliseconds 30 }
}
function ConsoleCmd($line) {
    Keys @("alt+c"); Start-Sleep -Milliseconds 400; TypeText $line; Keys @("Return"); Start-Sleep -Milliseconds 400; Keys @("alt+c")
}
# a log the game still has open for writing
function ReadLog($name) {
    $f = [IO.File]::Open((Join-Path $DOCS "logs\$name.log"), "Open", "Read", "ReadWrite")
    try { (New-Object IO.StreamReader($f)).ReadToEnd() -split "`r?`n" } finally { $f.Close() }
}

switch ($Command) {
    "start" {
        if ($p = Game) { "already running (pid $($p.Id))"; exit 0 }
        # the game needs Steam for its licence; started without it, it would bounce through Steam and lose -debug_mode
        if (-not (Get-Process steam -ErrorAction SilentlyContinue)) {
            $steam = (Get-ItemProperty HKCU:\Software\Valve\Steam).SteamExe
            Start-Process $steam -ArgumentList "-silent"
            for ($i = 0; $i -lt 60 -and -not (Get-Process steamwebhelper -ErrorAction SilentlyContinue); $i++) { Start-Sleep 1 }
            Start-Sleep 10
        }
        # a stop during loading leaves this behind, and the next boot then disables mods and un-marks the playset
        Remove-Item (Join-Path $DOCS ".force_disable_mods_sentinel.txt"), (Join-Path $DOCS "logs\game.log") -ErrorAction SilentlyContinue   # the log: so `wait` sees only this run
        $env:SteamAppId = "3450310"; $env:SteamGameId = "3450310"
        $p = Start-Process (Join-Path $BINARIES "eu5.exe") -ArgumentList "-debug_mode" -WorkingDirectory $BINARIES -PassThru
        "started (pid $($p.Id)); loading takes a minute or two, watch with: eu5ctl shot"
    }
    "stop" {
        # quit through the console, then kill whatever is left
        $p = Game
        if (-not $p) { "not running"; exit 0 }
        try { ConsoleCmd "quit" } catch {}
        if (-not $p.WaitForExit(30000)) { Stop-Process -Id $p.Id -Force }
        "stopped"
    }
    "status" { if ($p = Game) { "running (pid $($p.Id))" } else { "not running" } }
    "wait" {   # until game.log has been quiet for 15 s: boot finished, or a new game finished generating
        $log = Join-Path $DOCS "logs\game.log"; $prev = -1; $quiet = 0
        for ($i = 0; $i -lt 200; $i++) {
            $n = if (Test-Path $log) { (Get-Item $log).Length } else { 0 }
            if ($n -eq $prev -and $n -gt 0) { $quiet++ } else { $quiet = 0 }
            $prev = $n
            if ($quiet -ge 5) { break }
            Start-Sleep 3
        }
    }
    "shot" {
        $name = if ($Rest.Count) { $Rest[0] } else { "shot" }
        $w = Window; Start-Sleep -Milliseconds 200
        $full = New-Object Drawing.Bitmap $w.W, $w.H
        $g = [Drawing.Graphics]::FromImage($full); $g.CopyFromScreen($w.X, $w.Y, 0, 0, $full.Size); $g.Dispose()
        $small = New-Object Drawing.Bitmap $full, $SHOT_W, ([int]($w.H * $SHOT_W / $w.W))
        $jpg = [Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq "image/jpeg" }
        $q = New-Object Drawing.Imaging.EncoderParameters 1
        $q.Param[0] = New-Object Drawing.Imaging.EncoderParameter ([Drawing.Imaging.Encoder]::Quality), 80L
        $out = Join-Path $STATE "$name.jpg"
        $small.Save($out, $jpg, $q); $small.Dispose(); $full.Dispose()
        $out
    }
    "click" {
        MoveTo $Rest[0] $Rest[1]; Start-Sleep -Milliseconds 100
        $down, $up = switch ("$($Rest[2])") { "3" { 0x08, 0x10 } "2" { 0x20, 0x40 } default { 0x02, 0x04 } }
        [Eu5Ctl]::Mouse($down); Start-Sleep -Milliseconds 50; [Eu5Ctl]::Mouse($up)
    }
    "hover" { MoveTo $Rest[0] $Rest[1] }   # move without clicking, e.g. off a tooltip that hides a button
    "key" { Keys $Rest }
    "type" { TypeText $Rest[0] }
    "cmd" { ConsoleCmd $Rest[0] }
    "run" {
        # debug.log is buffered: a second run of filler lines pushes the probe's output onto disk
        $run = Join-Path $DOCS "run"; New-Item -ItemType Directory -Force $run | Out-Null
        Copy-Item $Rest[0] $run -Force
        $file = Split-Path $Rest[0] -Leaf
        $fill = 1..80 | ForEach-Object { "debug_log = `"eu5ctl flush $_ $('.' * 80)`"" }
        [IO.File]::WriteAllLines((Join-Path $run "eu5ctl_flush.txt"), [string[]]$fill)
        ConsoleCmd "run $file"; Start-Sleep -Milliseconds 500; ConsoleCmd "run eu5ctl_flush.txt"; Start-Sleep 1
        # print what the last run of FILE logged, minus the engine's validation chatter
        $lines = ReadLog "debug"; $s = -1; $from = -1; $to = -1
        for ($i = 0; $i -lt $lines.Count; $i++) {
            if ($lines[$i].Contains("console command: run $file")) { $s = $i }
            if ($lines[$i].Contains("console command: run eu5ctl_flush.txt") -and $s -ge 0) { $from = $s; $to = $i - 1 }
        }
        if ($from -ge 0) { $lines[$from..$to] | Where-Object { $_ -and $_ -notmatch "PostInitAndValidate" } }
    }
    "log" {
        $n = if ($Rest.Count -ge 1) { [int]$Rest[0] } else { 40 }
        $name = if ($Rest.Count -ge 2) { $Rest[1] } else { "debug" }
        ReadLog $name | Select-Object -Last $n
    }
    default { Get-Content $PSCommandPath -TotalCount 13 | Select-Object -Skip 1; exit 1 }
}
