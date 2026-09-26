#!/usr/bin/env bash
# Drive EU5 in a hidden (headless) gamescope display, the way Novum's QA runs: no window on the desktop.
# Menu path (1280x720 shot coords): New Game 176,292 -> click the country on the map -> move the mouse away
# (its tooltip hides the button) -> "Play as" 640,592. The console opens with the grave key (-debug_mode).
#   eu5ctl start | stop | status
#   eu5ctl shot [name]            -> prints a 1280x720 jpg path (click coordinates use this space)
#   eu5ctl click X Y [button]     eu5ctl key KEY...     eu5ctl type TEXT
#   eu5ctl cmd "tag HAS"          open console, run one command, close console
#   eu5ctl run FILE               copy an effect file into Documents/.../run/ and `run` it
#   eu5ctl log [N] [file]         last N lines of a log (default 40 of debug.log, where debug_log output lands)
set -euo pipefail

STEAM=~/.local/share/Steam
GAME="$STEAM/steamapps/common/Europa Universalis V"
PREFIX="$STEAM/steamapps/compatdata/3450310"
DOCS="$PREFIX/pfx/drive_c/users/steamuser/Documents/Paradox Interactive/Europa Universalis V"
PROTON="$STEAM/compatibilitytools.d/GE-Proton11-5-x86_64/proton"
STATE=/tmp/eu5ctl
W=1920 H=1080 SHOT_W=1280            # game resolution; screenshots are scaled to SHOT_W
mkdir -p "$STATE"

gs_pid() { [[ -f $STATE/pid ]] && kill -0 "$(cat "$STATE/pid")" 2>/dev/null && cat "$STATE/pid"; }

# DISPLAY / GAMESCOPE_WAYLAND_DISPLAY of our gamescope, read from its game child's environment
gs_env() {
  local child
  child=$(pgrep -P "$(gs_pid)" | head -1) || { echo "eu5ctl: not running" >&2; exit 1; }
  tr '\0' '\n' < "/proc/$child/environ" | grep -E "^$1=" | cut -d= -f2-
}
x() { DISPLAY=$(gs_env DISPLAY) xdotool "$@"; }

case "${1:-}" in
  start)
    if gs_pid >/dev/null; then echo "already running (pid $(gs_pid))"; exit 0; fi
    cd "$GAME/binaries"
    STEAM_COMPAT_DATA_PATH="$PREFIX" STEAM_COMPAT_CLIENT_INSTALL_PATH="$STEAM" SteamAppId=3450310 SteamGameId=3450310 \
      nohup gamescope --backend headless -W $W -H $H -w $W -h $H -- \
      "$PROTON" waitforexitandrun "$GAME/binaries/eu5.exe" -debug_mode > "$STATE/gamescope.log" 2>&1 &
    echo $! > "$STATE/pid"; echo "started (pid $!); loading takes a minute or two, watch with: eu5ctl shot" ;;
  stop)
    pid=$(gs_pid) || { echo "not running"; exit 0; }
    kill "$pid"; for _ in $(seq 30); do kill -0 "$pid" 2>/dev/null || break; sleep 1; done
    rm -f "$STATE/pid"; echo stopped ;;
  status) gs_pid >/dev/null && echo "running (pid $(gs_pid))" || echo "not running" ;;
  shot)
    name=${2:-shot}; png="$STATE/$name.png"; rm -f "$png"
    GAMESCOPE_WAYLAND_DISPLAY=$(gs_env GAMESCOPE_WAYLAND_DISPLAY) gamescopectl screenshot "$png" >/dev/null 2>&1
    for _ in $(seq 20); do [[ -s $png ]] && break; sleep 0.25; done
    magick "$png" -resize ${SHOT_W}x -quality 80 "$STATE/$name.jpg"; echo "$STATE/$name.jpg" ;;
  click)
    s=$(( W * 1000 / SHOT_W ))       # screenshot space -> game space
    x mousemove $(( $2 * s / 1000 )) $(( $3 * s / 1000 )); sleep 0.1; x click "${4:-1}" ;;
  key) shift; x key --delay 80 "$@" ;;
  type) x type --delay 30 "$2" ;;
  cmd)
    x key grave; sleep 0.4; x type --delay 20 "$2"; x key Return; sleep 0.4; x key grave ;;
  run)
    # debug.log is buffered: a second run of filler lines pushes the probe's output onto disk
    mkdir -p "$DOCS/run"; cp "$2" "$DOCS/run/"
    for i in $(seq 80); do echo "debug_log = \"eu5ctl flush $i $(printf '%.0s.' {1..80})\""; done > "$DOCS/run/eu5ctl_flush.txt"
    "$0" cmd "run $(basename "$2")"; sleep 0.5; "$0" cmd "run eu5ctl_flush.txt"; sleep 1
    # print what the last run of FILE logged, minus the engine's validation chatter
    awk -v f="run $(basename "$2")" 'index($0, "console command: " f) { buf = "" }
      index($0, "console command: run eu5ctl_flush.txt") { out = buf } { buf = buf $0 "\n" } END { printf "%s", out }' \
      "$DOCS/logs/debug.log" | grep -a -v -E 'PostInitAndValidate|^$' ;;
  log) tail -n "${2:-40}" "$DOCS/logs/${3:-debug}.log" ;;
  *) sed -n '2,10p' "$0"; exit 1 ;;
esac
