#!/usr/bin/env bash
# Tests for actions/discord-ci-notify: classify.sh (the run's outcome from the
# caller's `needs`) and notify.sh's post decision (title per outcome x the
# previous run). Needs bash + jq; no network (notify.sh runs in its
# NOTIFY_DECIDE_ONLY mode). Run by .github/workflows/test.yml.
set -euo pipefail
HERE=$(cd "$(dirname "$0")/.." && pwd)
fails=0
ok()  { echo "ok   $1"; }
bad() { echo "FAIL $1" >&2; fails=$((fails + 1)); }

# expect_classify <name> <expected tsv> [VAR=value...]
expect_classify() {
    local name=$1 want=$2; shift 2
    local got
    got=$(env -u NEEDS -u RESULT "$@" bash "$HERE/classify.sh" 2>/dev/null) || got="exit $?"
    [ "$got" = "$want" ] && ok "$name" || bad "$name: want [$want] got [$got]"
}
T=$'\t'
j() { printf '{%s}' "$1"; }
job() { printf '"%s":{"result":"%s","outputs":{}}' "$1" "$2"; }

expect_classify "all success"            "success${T}${T}"                        NEEDS="$(j "$(job build success),$(job test success)")"
expect_classify "a failure wins"         "failure${T}test${T}"                    NEEDS="$(j "$(job build success),$(job test failure)")"
expect_classify "failure beats cancel"   "failure${T}a${T}"                       NEEDS="$(j "$(job a failure),$(job b cancelled)")"
expect_classify "cancelled"              "cancelled${T}${T}"                      NEEDS="$(j "$(job a success),$(job b cancelled)")"
expect_classify "one skipped = incomplete" "incomplete${T}${T}determinism"        NEEDS="$(j "$(job build-test success),$(job determinism skipped)")"
expect_classify "all skipped = incomplete" "incomplete${T}${T}a, b"               NEEDS="$(j "$(job a skipped),$(job b skipped)")"
expect_classify "cancel beats skip"      "cancelled${T}${T}b"                     NEEDS="$(j "$(job a cancelled),$(job b skipped)")"
expect_classify "empty needs refused"    "exit 2"                                 NEEDS='{}'
expect_classify "legacy result success"  "success${T}${T}"                        RESULT=success
expect_classify "legacy result failure"  "failure${T}${T}"                        RESULT=failure
expect_classify "legacy skipped"         "incomplete${T}${T}"                     RESULT=skipped
expect_classify "needs beats result"     "failure${T}x${T}"                       NEEDS="$(j "$(job x failure)")" RESULT=success
expect_classify "nothing given refused"  "exit 2"
expect_classify "junk result refused"    "exit 2"                                 RESULT=green

# expect_decide <name> <expected> OUTCOME PREV EVENT
expect_decide() {
    local name=$1 want=$2 outcome=$3 prev=$4 event=$5 got
    got=$(env NOTIFY_DECIDE_ONLY=1 OUTCOME="$outcome" PREV="$prev" EVENT="$event" REPO=StarworksDev/Arcane BRANCH=main \
          bash "$HERE/notify.sh" 2>/dev/null) || got="exit $?"
    [ "$got" = "$want" ] && ok "$name" || bad "$name: want [$want] got [$got]"
}
expect_decide "failure posts FAILED"            "FAILED: Arcane CI on main|15158332"     failure    success push
expect_decide "failure after failure posts"     "FAILED: Arcane CI on main|15158332"     failure    failure push
expect_decide "green after red = RECOVERED"     "RECOVERED: Arcane CI on main|3066993"   success    failure push
expect_decide "green after green is silent"     "skip"                                   success    success push
expect_decide "first green ever is silent"      "skip"                                   success    none    push
expect_decide "manual green posts PASSED"       "PASSED: Arcane CI on main (manual run)|3066993" success success workflow_dispatch
expect_decide "incomplete always posts"         "INCOMPLETE: Arcane CI on main|15105570" incomplete success push
expect_decide "incomplete after red is not RECOVERED" "INCOMPLETE: Arcane CI on main|15105570" incomplete failure push
expect_decide "cancelled is silent"             "skip"                                   cancelled  failure push

echo
[ "$fails" -eq 0 ] && echo "test-notify: all passed" || echo "test-notify: $fails failure(s)"
[ "$fails" -eq 0 ]
