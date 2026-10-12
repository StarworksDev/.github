#!/usr/bin/env bash
# notify.sh -- discord-ci-notify's body (action.yml passes everything as env).
# Posts this run's result into the repo's thread of the Discord CI forum:
#   failure     -> FAILED (every red run), naming the failed jobs
#   incomplete  -> INCOMPLETE (every run in which a needed job never ran),
#                  naming the skipped jobs -- never counted as a recovery
#   success     -> RECOVERED when the previous completed non-PR run on this
#                  branch failed; PASSED for a manual (workflow_dispatch) run;
#                  otherwise silent (green after green)
#   cancelled   -> silent
# The outcome comes from classify.sh (NEEDS, or the legacy RESULT).
# Optional plumbing: no webhook / no thread for this repo -> skip; a Discord
# or GitHub API error never fails the job.
#
# NOTIFY_DECIDE_ONLY=1 (tests): takes OUTCOME and PREV from the env, prints
# "<title>|<color>" or "skip", and touches nothing else.
set -euo pipefail
name="${REPO#*/}"

decide() {   # decide <outcome> <prev conclusion> -> "title|color" or "skip"
    case "$1" in
        failure)    echo "FAILED: $name CI on $BRANCH|15158332" ;;
        incomplete) echo "INCOMPLETE: $name CI on $BRANCH|15105570" ;;
        success)
            if [ "$2" = failure ]; then echo "RECOVERED: $name CI on $BRANCH|3066993"
            elif [ "$EVENT" = workflow_dispatch ]; then echo "PASSED: $name CI on $BRANCH (manual run)|3066993"
            else echo skip; fi ;;
        *) echo skip ;;
    esac
}

if [ "${NOTIFY_DECIDE_ONLY:-}" = 1 ]; then
    decide "$OUTCOME" "$PREV"
    exit 0
fi

if ! line=$(bash "$(dirname "$0")/classify.sh"); then
    echo "::warning::discord-ci-notify: pass needs: \${{ toJSON(needs) }} (or a result) -- nothing posted"
    exit 0
fi
IFS=$'\t' read -r outcome failed_needs skipped_needs <<< "$line"
echo "discord-ci-notify: outcome $outcome (failed: ${failed_needs:-none}; skipped: ${skipped_needs:-none})"

if [ -z "${DISCORD_WEBHOOK:-}" ]; then echo "no webhook; skipping"; exit 0; fi
map="${THREADS:-}"; if [ -z "$map" ]; then map='{}'; fi
thread=$(printf '%s' "$map" | jq -r --arg r "$name" '.[$r] // empty' 2> /dev/null || true)
if [ -z "$thread" ]; then echo "no forum thread for $name in DISCORD_CI_THREADS; skipping"; exit 0; fi

prev=none
if [ "$outcome" = success ]; then
    wf=$(gh api "repos/$REPO/actions/runs/$RUN_ID" --jq .workflow_id 2> /dev/null || echo "")
    if [ -n "$wf" ]; then
        prev=$(gh api "repos/$REPO/actions/workflows/$wf/runs?branch=$BRANCH&status=completed&per_page=20" \
                 --jq "[.workflow_runs[] | select(.id != $RUN_ID and .event != \"pull_request\" and (.conclusion == \"success\" or .conclusion == \"failure\"))][0].conclusion // \"none\"" \
               2> /dev/null || echo none)
    fi
fi

decision=$(decide "$outcome" "$prev")
if [ "$decision" = skip ]; then echo "outcome $outcome, previous run $prev: nothing to post"; exit 0; fi
title="${decision%|*}"
color="${decision##*|}"

subject=$(printf '%s' "${HEAD_MSG:-}" | head -n1 | cut -c1-200)
desc="Branch \`$BRANCH\` at \`${SHA:0:8}\`"
if [ -n "$subject" ]; then desc="$desc: $subject"; fi
if [ "$outcome" = failure ]; then
    # Matrix legs by name (the needs list only knows the job ids).
    failed=$(gh api "repos/$REPO/actions/runs/$RUN_ID/jobs?per_page=100" \
               --jq '[.jobs[] | select(.conclusion == "failure") | .name] | join(", ")' 2> /dev/null || true)
    if [ -z "$failed" ]; then failed="$failed_needs"; fi
    if [ -n "$failed" ]; then desc="$desc"$'\n'"**Failed:** $failed"; fi
fi
if [ "$outcome" = incomplete ] && [ -n "$skipped_needs" ]; then
    desc="$desc"$'\n'"**Did not run:** $skipped_needs"
fi

jq -n --arg t "$title" --arg d "$desc" --arg u "https://github.com/$REPO/actions/runs/$RUN_ID" --argjson c "$color" \
   '{username: "GitHub Actions", embeds: [{title: $t, description: $d, url: $u, color: $c}]}' \
  | curl -fsS -H "Content-Type: application/json" -d @- "${DISCORD_WEBHOOK}?thread_id=${thread}" > /dev/null \
  || echo "Discord post failed (ignored)"
