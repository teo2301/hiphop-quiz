# Publishing Hip Hop Quiz

The three quizzes now share one API container and one Tailscale Funnel path. Football (:10000 root)
and World (/wq) keep working through compatibility aliases. Nothing in this file needs a new port
or a new per-quiz scores container.

Final addresses:
- Site: https://teo2301.github.io/hiphop-quiz/ (GitHub Pages, `main` `/docs`)
- API: https://riccioserver.tail0d3eb6.ts.net:10000/q/hh/api/...
- Shared router: `127.0.0.1:8200` in container `quiz-shared` (`/mnt/ssdstorage/share/quiz-shared`).

## 0. Checks (already green before publishing)

    python3 validate.py
    node tools/lint_es2017.js docs/js/*.js docs/sw.js
    /mnt/ssdstorage/share/world-quiz/.venv/bin/python server/test_leaderboard.py
    python3 server/test_live.py
    cmp server/live.py ../../world-quiz/server/live.py
    cmp docs/js/live.js ../../world-quiz/docs/js/live.js

`docs/sw.js` VERSION is `hh-v1`; bump it after any later app-file edit.

## 1. GitHub repo + Pages

`gh` on this host is logged in as teo2301.

    gh repo create teo2301/hiphop-quiz --public --source . --remote origin \
       --description "Hip Hop Quiz: artists, albums, songs, history and awards"
    git add -A && git commit -m "Hip Hop Quiz: shared-server launch"
    git push -u origin main
    gh api -X POST repos/teo2301/hiphop-quiz/pages -f "source[branch]=main" -f "source[path]=/docs"
    gh api repos/teo2301/hiphop-quiz/pages --jq .status          # wait for "built"
    curl -sI https://teo2301.github.io/hiphop-quiz/ | head -1    # HTTP/2 200

`data/`, `.venv/` and `preview-shots/` are gitignored; the VAPID key lives in `~/keys`.
Pages origin is shared with the other quizzes, so `hh_` storage keys, `hh-v1` cache names, the
`./` SW scope and the distinct path keep them isolated.

## 2. Shared API container

Already built and running; this is the restart/check recipe:

    cd /mnt/ssdstorage/share/quiz-shared
    docker compose up -d --build quiz-shared
    curl -s http://127.0.0.1:8200/q/hh/api/health && echo
    curl -s http://127.0.0.1:8200/q/wq/api/health && echo
    curl -s http://127.0.0.1:8200/q/fq/api/health && echo
    curl -s http://127.0.0.1:8200/api/health && echo      # legacy football alias

One process per quiz, one DB per quiz, one VAPID key per quiz. The router watches and restarts
children. `../{football,world,hiphop}-quiz/{server,docs}` are bind-mounted read-only, so content
updates in the repos are picked up on the next request (mtime-based reload).

## 3. Funnel path (public API)

Keep the existing :10000 handlers; add/replace only `/q`:

    sudo tailscale funnel --bg --https=10000 --set-path=/q http://127.0.0.1:8200

Then check from outside, resolving through public DNS (MagicDNS would test the tailnet path):

    IP=$(dig +short @1.1.1.1 riccioserver.tail0d3eb6.ts.net | tail -1)
    for p in /api /wq/api /q/fq/api /q/wq/api /q/hh/api; do
      curl -s --resolve riccioserver.tail0d3eb6.ts.net:10000:$IP \
        "https://riccioserver.tail0d3eb6.ts.net:10000$p/health"; echo " <- $p"
    done

Never turn off the whole of :10000. To remove just this path:
`sudo tailscale funnel --https=10000 --set-path=/q off`.

## 4. Backup + dead-man's switch

One job covers all three quizzes: `~/projects/services/server-ops/backup_quiz_servers.sh`
(symlink at `~/projects/server-ops/`). It snapshots the three DBs into one tarball under
`/mnt/4tbmedia/Backups/App Backups/Quiz Servers`, keeps 30 days, and checks all public paths.
`check_backups.sh` has one entry: `Quiz servers (fq/wq/hh)|Quiz Servers|quiz-servers_*.tar.gz`.
Run once by hand before relying on cron:

    /home/riccioserver/projects/services/server-ops/backup_quiz_servers.sh

Back up the new VAPID key alongside the others:

    mkdir -p "/mnt/4tbmedia/Backups/App Backups/Quiz Servers/keys"
    cp -p ~/keys/hiphop-quiz-vapid.json "/mnt/4tbmedia/Backups/App Backups/Quiz Servers/keys/"

The old football/world backup jobs stay in cron (those live DBs are still written by their own
clients). `check_backups.sh` now checks all three jobs: Football Quiz, World Quiz and Quiz Servers.

## 5. Cron

Football and World clients still use their original APIs and DBs, so their jobs stay on the
original containers. Only Hip Hop runs on the shared container. Add these lines (UK times,
staggered so nothing overlaps):

    # Hip Hop Quiz on the shared API container (added 2026-11-27)
    4 9 * * *  docker exec quiz-shared python -u /app/push_one.py hh daily    >> /tmp/hh-push.log 2>&1
    9 9 * * 1  docker exec quiz-shared python -u /app/push_one.py hh monday   >> /tmp/hh-push.log 2>&1
    34 18 * * * docker exec quiz-shared python -u /app/push_one.py hh reminder >> /tmp/hh-push.log 2>&1
    40 8 * * 1 QUIZ_DB=/mnt/ssdstorage/share/quiz-shared/data/hh/hiphop-quiz.db /mnt/ssdstorage/share/hiphop-quiz/tools/weekly_report.sh >> /tmp/hh-report.log 2>&1

Test one push: `docker exec quiz-shared python -u /app/push_one.py hh test <player name>`.

## 6. Android app (Trusted Web Activity)

Template: `/mnt/ssdstorage/share/football-quiz-android`. Copy it, don't change the original:

    rsync -a --exclude build --exclude .gradle --exclude app/build --exclude release \
          --exclude 'build*.log' /mnt/ssdstorage/share/football-quiz-android/ /mnt/ssdstorage/share/hiphop-quiz-android/
    cd /mnt/ssdstorage/share/hiphop-quiz-android && git init -b main

Edits:
- `app/build.gradle.kts`: `launchUrl = "https://teo2301.github.io/hiphop-quiz/"`,
  `namespace` / `applicationId` = `io.github.teo2301.hiphopquiz` (never change afterwards),
  `versionCode = 1`, `versionName = "1.0"`. Keep the same upload keystore properties file.
- `settings.gradle.kts`: `rootProject.name = "HipHopQuiz"`.
- `strings.xml`: app name "Hip Hop Quiz". `colors.xml`: from `docs/manifest.json`.
- `build.sh`: output names `HipHopQuiz-$VN.apk/.aab`.
- Icons from `docs/icon-512.png` + `docs/icon-mono.png` (notification icon).
- grep for leftovers: `grep -rniE "football|FootballQuiz" --exclude-dir=build .`

Build detached: `setsid nohup ./build.sh > build.log 2>&1 < /dev/null &`.
The signing fingerprint should be the football one:
`C6:8F:98:0B:BE:6A:83:1E:FD:F5:72:67:45:41:09:C3:2D:05:AF:62:AB:5F:F6:5F:FC:50:32:FF:CF:C3:9A:33`.

## 7. Digital Asset Links

Repo `teo2301/teo2301.github.io`, file `.well-known/assetlinks.json`: keep football and world,
add a **third** statement for `io.github.teo2301.hiphopquiz` with the same fingerprint. Check:

    curl -s "https://digitalassetlinks.googleapis.com/v1/statements:list?source.web.site=https://teo2301.github.io&relation=delegate_permission/common.handle_all_urls"

Attach the APK to a release (the "Get the app" tile links to the latest asset):

    gh release create v1.0 /mnt/ssdstorage/share/hiphop-quiz-android/release/HipHopQuiz-1.0.apk \
       -R teo2301/hiphop-quiz -t "Android app 1.0"

## 8. After going live

- Play one game on the live site from the phone on 4G; check the score on the board.
- Enable notifications, then send a `test` push (step 5).
- Confirm all six `/health` endpoints in step 3 still answer, including the two legacy aliases.
