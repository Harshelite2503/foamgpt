#!/usr/bin/env bash
# ============================================================
#  Linux practice lab for a Trade Ops Engineer interview.
#  Creates a fake trading-system environment under ~/linuxlab
#  Safe: touches nothing outside that directory. No root needed.
#  Run:  bash linux-lab-setup.sh
#  Wipe: rm -rf ~/linuxlab
# ============================================================
set -uo pipefail

LAB="${HOME}/linuxlab"
rm -rf "$LAB"
mkdir -p "$LAB"/{logs,data,archive,bin,tmp,refdata,run}

echo "Building lab in $LAB ..."

# ------------------------------------------------------------------
# 1. Application log — trading-system flavoured
# ------------------------------------------------------------------
awk 'BEGIN{
  srand(7);
  split("md_handler order_router risk_engine strategy_alpha strategy_beta", comp, " ");
  split("INFO INFO INFO INFO INFO WARN WARN ERROR DEBUG", lvl, " ");
  split("Connection reset by peer|Order rejected: price band|Heartbeat timeout|Sequence gap detected|Risk limit breached|Slow consumer detected|Login failed for session|Feed A packet loss", msg, "|");
  for (i=0; i<20000; i++) {
    h = int(i/1400) + 8; m = int(rand()*60); s = int(rand()*60);
    L = lvl[int(rand()*9)+1];
    C = comp[int(rand()*5)+1];
    lat = int(rand()*900)+40;
    oid = 100000 + int(rand()*50000);
    printf "2026-08-29 %02d:%02d:%02d %-5s [%s] order_id=%d latency_us=%d ", h, m, s, L, C, oid, lat;
    if (L == "ERROR" || L == "WARN") printf "%s\n", msg[int(rand()*8)+1];
    else printf "processed ok\n";
  }
}' > "$LAB/logs/app.log"

# ------------------------------------------------------------------
# 2. Web access log — for the classic top-N-IPs drill
# ------------------------------------------------------------------
awk 'BEGIN{
  srand(11);
  split("/health /api/positions /api/orders /dashboard /api/pnl /static/app.js", url, " ");
  split("200 200 200 200 304 404 500 503", code, " ");
  for (i=0;i<8000;i++){
    a=10; b=int(rand()*3)+1; c=int(rand()*4); d=int(rand()*12)+1;
    printf "%d.%d.%d.%d - - [29/Aug/2026:%02d:%02d:%02d +0530] \"GET %s HTTP/1.1\" %s %d\n",
      a,b,c,d, int(rand()*24), int(rand()*60), int(rand()*60),
      url[int(rand()*6)+1], code[int(rand()*8)+1], int(rand()*9000)+200;
  }
}' > "$LAB/logs/access.log"

# ------------------------------------------------------------------
# 3. Trades CSV — for awk aggregation drills
# ------------------------------------------------------------------
{
  echo "trade_id,symbol,side,qty,price,venue"
  awk 'BEGIN{
    srand(3);
    split("RELIANCE INFY TCS HDFCBANK SBIN NIFTYFUT BANKNIFTYFUT", sym, " ");
    split("BUY SELL", side, " ");
    split("NSE BSE NSE NSE", ven, " ");
    for(i=1;i<=5000;i++){
      s=sym[int(rand()*7)+1];
      printf "T%05d,%s,%s,%d,%.2f,%s\n", i, s, side[int(rand()*2)+1],
        (int(rand()*20)+1)*25, rand()*3000+100, ven[int(rand()*4)+1];
    }
  }'
} > "$LAB/data/trades.csv"

# ------------------------------------------------------------------
# 4. Reference data files — some present, one deliberately empty
# ------------------------------------------------------------------
for d in $(seq 0 5); do
  day=$(date -d "-$d day" +%Y%m%d 2>/dev/null || date -v-"${d}"d +%Y%m%d)
  f="$LAB/refdata/instruments_${day}.csv"
  if [ "$d" -eq 1 ]; then
    : > "$f"                       # <-- landed but EMPTY. A real failure mode.
  else
    seq 1 5000 | awk '{print "INST"$1",TOKEN"$1",EQ"}' > "$f"
  fi
done

# ------------------------------------------------------------------
# 5. Old + large files, for find / du drills
# ------------------------------------------------------------------
for i in $(seq 1 12); do
  head -c $((i * 200000)) /dev/urandom > "$LAB/archive/dump_$i.bin"
done
touch -d "40 days ago" "$LAB/archive/dump_1.bin" "$LAB/archive/dump_2.bin" 2>/dev/null
touch -d "10 days ago" "$LAB/archive/dump_3.bin" 2>/dev/null
mkdir -p "$LAB/data/deep/nested/tree"
head -c 9000000 /dev/urandom > "$LAB/data/deep/nested/tree/bigfile.dat"
for i in $(seq 1 300); do : > "$LAB/tmp/session_$i.tmp"; done

# ------------------------------------------------------------------
# 6. Fake "services" — long-running processes with recognisable names
# ------------------------------------------------------------------
cat > "$LAB/bin/md_handler" <<'EOF'
#!/usr/bin/env bash
trap 'echo "$(date +%T) caught SIGTERM, shutting down cleanly" >> "$HOME/linuxlab/logs/md_handler.log"; exit 0' TERM
trap 'echo "$(date +%T) caught SIGHUP, reloading config" >> "$HOME/linuxlab/logs/md_handler.log"' HUP
echo "$(date +%T) md_handler started pid=$$" >> "$HOME/linuxlab/logs/md_handler.log"
while true; do sleep 1; done
EOF

cat > "$LAB/bin/order_router" <<'EOF'
#!/usr/bin/env bash
echo "$(date +%T) order_router started pid=$$" >> "$HOME/linuxlab/logs/order_router.log"
while true; do sleep 1; done
EOF

cat > "$LAB/bin/cpu_hog" <<'EOF'
#!/usr/bin/env bash
# Burns one core. This is your "runaway process" to hunt down.
while :; do :; done
EOF

chmod +x "$LAB/bin/"*

cat > "$LAB/bin/start_services.sh" <<'EOF'
#!/usr/bin/env bash
# Starts the fake services and records PIDs. PID files are the safe way to
# stop a service later -- see the pkill warning in the drills.
LAB="$HOME/linuxlab"
mkdir -p "$LAB/run"
for svc in md_handler order_router cpu_hog; do
    "$LAB/bin/$svc" &
    echo $! > "$LAB/run/$svc.pid"
    printf "%-13s pid %s\n" "$svc" "$!"
done
disown -a 2>/dev/null
EOF
chmod +x "$LAB/bin/start_services.sh"

cat > "$LAB/bin/stop_services.sh" <<'EOF'
#!/usr/bin/env bash
# Stops by PID file, not by name. Safer: pkill -f can match your own shell.
LAB="$HOME/linuxlab"
for svc in md_handler order_router cpu_hog; do
    f="$LAB/run/$svc.pid"
    if [[ -f "$f" ]]; then
        pid=$(cat "$f")
        if kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" && echo "stopped $svc (pid $pid)"
        else
            echo "$svc not running (stale pid file)"
        fi
        rm -f "$f"
    else
        echo "$svc has no pid file"
    fi
done
EOF
chmod +x "$LAB/bin/stop_services.sh"

# ------------------------------------------------------------------
# 7. Permission puzzle
# ------------------------------------------------------------------
echo "secret=hunter2" > "$LAB/data/credentials.conf"; chmod 600 "$LAB/data/credentials.conf"
echo "port=9001"      > "$LAB/data/app.conf";         chmod 644 "$LAB/data/app.conf"
echo '#!/bin/sh'      > "$LAB/bin/deploy.sh";         chmod 750 "$LAB/bin/deploy.sh"
ln -sf "$LAB/logs/app.log" "$LAB/logs/current.log"
ln    "$LAB/data/app.conf" "$LAB/data/app.conf.hardlink" 2>/dev/null

echo
echo "Done. Lab is at: $LAB"
echo "  logs/app.log        20,000 lines of trading log"
echo "  logs/access.log      8,000 lines of web access log"
echo "  data/trades.csv      5,000 trades"
echo "  refdata/             6 daily files, one is broken on purpose"
echo "  archive/, data/deep/ files of varying size and age"
echo "  bin/start_services.sh   launches 3 fake processes (one burns CPU)"
echo "  bin/stop_services.sh    kills them"
echo
echo "Now open linux-lab-drills.md and work through it."