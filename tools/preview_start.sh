#!/bin/sh
# (Re)start the Hip Hop Quiz preview: test API on 127.0.0.1:8194 (DB /tmp/q/hh-test.db, created
# fresh by the server's init) + static/proxy server on :8198. Logs in /tmp/q/hh-*.log.
# Never touches any live container or DB.
cd "$(dirname "$0")/.." || exit 1
pkill -f "hh-preview-marker" 2>/dev/null
sleep 1
mkdir -p /tmp/q
rm -f /tmp/q/hh-test.db /tmp/q/hh-test.db-wal /tmp/q/hh-test.db-shm   # fresh test DB each start (the server creates it)
# The venv (gitignored) has pywebpush, so the test server can send pushes; plain python3
# still runs it, just without sending. VAPID key: ~/keys/hiphop-quiz-vapid.json (outside git).
# PUSH_EXTRA_HOSTS lets drive_preview's fake push service (127.0.0.1:8199) receive them.
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
QUIZ_DB=/tmp/q/hh-test.db QUESTIONS_PATH="$PWD/docs/questions.json" QUIZ_HOST=127.0.0.1 QUIZ_PORT=8194 \
  VAPID_PATH="$HOME/keys/hiphop-quiz-vapid.json" PUSH_EXTRA_HOSTS=127.0.0.1:8199 \
  setsid nohup $PY -u server/leaderboard.py hh-preview-marker > /tmp/q/hh-api.log 2>&1 < /dev/null &
setsid nohup python3 -u tools/preview.py hh-preview-marker > /tmp/q/hh-preview.log 2>&1 < /dev/null &
sleep 1
echo "preview: http://192.168.0.69:8198"
