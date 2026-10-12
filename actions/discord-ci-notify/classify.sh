#!/usr/bin/env bash
# classify.sh -- the run's outcome for discord-ci-notify, printed as one
# tab-separated line: <outcome> <failed needs> <skipped needs>
#   outcome: failure | cancelled | incomplete | success
#
# From NEEDS (the caller's `${{ toJSON(needs) }}`): any failure -> failure;
# else any cancelled -> cancelled; else any skipped -> incomplete (a job that
# never ran is not a pass); else success. The lists name the needed jobs
# with that result, comma-separated.
#
# Legacy: without NEEDS, RESULT (the old `result` input: success | failure |
# cancelled | skipped) is mapped as-is, skipped -> incomplete; the job lists
# are then empty.
#
# Exit 2 (nothing printed) when neither is usable -- a caller wiring mistake,
# which the action reports as a warning instead of guessing.
set -euo pipefail

if [ -n "${NEEDS:-}" ]; then
    printf '%s' "$NEEDS" | jq -er '
        if (type != "object") or (length == 0) then error("needs is empty") else . end
        | [to_entries[] | {name: .key, result: (.value.result // "")}] as $jobs
        | ([$jobs[] | select(.result == "failure") | .name] | join(", ")) as $failed
        | ([$jobs[] | select(.result == "skipped") | .name] | join(", ")) as $skipped
        | (if any($jobs[]; .result == "failure") then "failure"
           elif any($jobs[]; .result == "cancelled") then "cancelled"
           elif all($jobs[]; .result == "success") then "success"
           else "incomplete" end) as $outcome
        | [$outcome, $failed, $skipped] | @tsv' 2> /dev/null || {
        echo "classify: needs is not a non-empty JSON object of jobs" >&2
        exit 2
    }
    exit 0
fi

case "${RESULT:-}" in
    success|failure|cancelled) printf '%s\t\t\n' "$RESULT" ;;
    skipped) printf 'incomplete\t\t\n' ;;
    *) echo "classify: no needs and no known result (got '${RESULT:-}')" >&2; exit 2 ;;
esac
