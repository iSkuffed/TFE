#!/usr/bin/env bash
# Drive EU5 inside gamescope: a window on the desktop to watch, or hidden with --headless (Novum's QA way).
# Menu path (1280x720 shot coords): New Game 176,292 -> click the country on the map -> move the mouse away
# (its tooltip hides the button) -> "Play as" 640,592. The console opens with the grave key (-debug_mode).
#   eu5ctl start [--headless] | wait | stop | status   (wait: until loading or new-game generation is done)
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
tree() { local p; for p in $(pgrep -P "$1"); do echo "$p"; tree "$p"; done; }
# after a crash the reporter window takes the input, and a stray Return would submit the report
crashed() { tree "$(gs_pid)" | xargs -r ps -o comm= -p | grep -qi crash; }
x() {
  gs_pid >/dev/null || { echo "eu5ctl: not running" >&2; exit 1; }
  if crashed; then echo "eu5ctl: game crashed (crash reporter open), not sending input" >&2; exit 1; fi
  DISPLAY=$(gs_env DISPLAY) xdotool "$@"
}

case "${1:-}" in
  start)
    if gs_pid >/dev/null; then echo "already running (pid $(gs_pid))"; exit 0; fi
    # a game started from Steam shares the Wine prefix; ours would hang waiting for it (and the log would be theirs)
    if pgrep -f 'binaries\\eu5[.]exe' >/dev/null; then echo "eu5ctl: EU5 is already open outside eu5ctl; close it first" >&2; exit 1; fi
    # a stop during loading leaves this behind, and the next boot then disables mods and un-marks the playset
    rm -f "$DOCS/.force_disable_mods_sentinel.txt" "$DOCS/logs/game.log"   # the log: so `wait` sees only this run
    cd "$GAME/binaries"
    STEAM_COMPAT_DATA_PATH="$PREFIX" STEAM_COMPAT_CLIENT_INSTALL_PATH="$STEAM" SteamAppId=3450310 SteamGameId=3450310 \
      nohup gamescope $([[ ${2:-} == --headless ]] && echo --backend headless) -W $W -H $H -w $W -h $H -- \
      "$PROTON" waitforexitandrun "$GAME/binaries/eu5.exe" -debug_mode > "$STATE/gamescope.log" 2>&1 &
    echo $! > "$STATE/pid"; echo "started (pid $!); loading takes a minute or two, watch with: eu5ctl shot" ;;
  stop)
    # gamescope ignores SIGTERM while its child lives, and Proton leaves winedevice.exe orphans behind:
    # quit through the console, then kill whatever is left in our own process tree (and nothing else).
    pid=$(gs_pid) || { echo "not running"; exit 0; }
    "$0" cmd quit 2>/dev/null || true
    for _ in $(seq 30); do tree "$pid" | xargs -r ps -o comm= -p | grep -q eu5 || break; sleep 1; done
    kids=$(tree "$pid"); kill $kids 2>/dev/null || true; sleep 3; kill -9 $kids 2>/dev/null || true
    for _ in $(seq 10); do kill -0 "$pid" 2>/dev/null || break; sleep 1; done
    kill -0 "$pid" 2>/dev/null && kill -9 "$pid"
    rm -f "$STATE/pid"; echo stopped ;;
  status) gs_pid >/dev/null && echo "running (pid $(gs_pid))" || echo "not running" ;;
  wait)   # until game.log has been quiet for 15 s: boot finished, or a new game finished generating
    prev=-1 quiet=0
    for _ in $(seq 200); do
      n=$(wc -c < "$DOCS/logs/game.log" 2>/dev/null || echo 0)
      if [[ $n == "$prev" && $n -gt 0 ]]; then quiet=$((quiet + 1)); else quiet=0; fi
      prev=$n; (( quiet >= 5 )) && break; sleep 3
    done ;;
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
