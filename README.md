# Hip Hop Quiz

Sister app to Football Quiz and World Knowledge Quiz, running on the same shared API server.
Artists, albums, songs & lyrics, history & eras, awards & records, and hip hop around the world.
Same shell (daily quiz, classic, survival, blitz, higher or lower, guess the artist,
50:50, challenges, private leagues, weekly divisions, achievements, push) with a gold-on-charcoal
theme. No build step: vanilla JS (iOS 12 / ES2017 safe) + a stdlib Python server.

- `docs/` is the whole site (GitHub Pages folder, https://teo2301.github.io/hiphop-quiz/)
- `docs/questions.json`: `id` (topic prefix + number, e.g. `art001`), `l`
  (`art|alb|lyr|era|awd|glb`), `d` (1-3), `q`, `a` (right answer), `w` (3 wrong), `x` (fact).
- `docs/stats.json` feeds Higher or lower, `docs/clues.json` feeds Guess the artist (mode id `career`).
- `python3 validate.py` checks all three files.
- Bump `VERSION` in `docs/sw.js` after changing any app file. Data files are network-first.

## Checks

    python3 validate.py
    node tools/lint_es2017.js docs/js/*.js docs/sw.js
    /mnt/ssdstorage/share/world-quiz/.venv/bin/python server/test_leaderboard.py
    python3 server/test_live.py

`server/live.py`, `server/test_live.py` and `docs/js/live.js` must stay byte-identical to the
other two quizzes. Branding there comes only from `LIVE_BOT_TAG` / `LIVE_BOT_NAMES` (server) and
`core.js` (client).

## Preview (never touches anything live)

`tools/preview_start.sh` restarts the test API (127.0.0.1:8194, fresh `/tmp/q/hh-test.db`) and the
preview (docs/ on :8198, `/api` proxied). Open http://192.168.0.69:8198.
`python3 tools/drive_preview.py both` screenshots every screen at 390x844 into `preview-shots/`.

## Server

All three quizzes share one container (`quiz-shared`, 127.0.0.1:8200) with one router and one
process per quiz, each with its own DB and VAPID key:

    /q/fq/api/...    football-quiz
    /q/wq/api/...    world-quiz
    /q/hh/api/...    this quiz

Public: `https://riccioserver.tail0d3eb6.ts.net:10000/q/hh/api/...` (a path on the existing Funnel).
This quiz's data lives in `/mnt/ssdstorage/share/quiz-shared/data/hh/hiphop-quiz.db`; content is
read from this repo's `docs/`; VAPID key at `~/keys/hiphop-quiz-vapid.json` (never in git).
`server/leaderboard.py` env overrides: QUIZ_DB, QUESTIONS_PATH, STATS_PATH, CLUES_PATH,
VAPID_PATH, QUIZ_ORIGINS, QUIZ_HOST, QUIZ_PORT. See `../../quiz-shared/docker-compose.yml`
and `tools/PUBLISH.md` for the full runbook.
