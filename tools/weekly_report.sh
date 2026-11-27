#!/bin/sh
# Weekly question-quality summary -> Matteo's phone via /home/riccioserver/projects/server-ops/scripts/notify.sh (ntfy).
# Open player reports + questions whose real correct rate disagrees with their difficulty
# (server/question_stats.py, DB opened read-only). Silent when there's nothing to look at.
#
#   tools/weekly_report.sh                 # send (if anything to report)
#   DRY_RUN=1 tools/weekly_report.sh       # print instead of sending
#   QUIZ_DB=/tmp/q/hh-test.db DRY_RUN=1 tools/weekly_report.sh
#
# Cron (Mondays 08:40 UK) reads the live shared DB:
#   40 8 * * 1 QUIZ_DB=/mnt/ssdstorage/share/quiz-shared/data/hh/hiphop-quiz.db tools/weekly_report.sh >> /tmp/hh-report.log 2>&1
cd "$(dirname "$0")/.." || exit 1
DB="${QUIZ_DB:-$PWD/data/hiphop-quiz.db}"
NOTIFY="${NOTIFY:-/home/riccioserver/projects/server-ops/scripts/notify.sh}"
[ -f "$DB" ] || { echo "no database at $DB" >&2; exit 1; }
TEXT=$(python3 server/question_stats.py --db "$DB" --short) || exit 1
case "$TEXT" in
  "0 open reports on 0 questions; 0 misgraded"*) [ -n "$ALWAYS" ] || { echo "nothing to report"; exit 0; } ;;
esac
if [ -n "$DRY_RUN" ]; then
  echo "$TEXT"
else
  "$NOTIFY" "Hip Hop Quiz: weekly question check" "$TEXT" 3 earth_africa
fi
