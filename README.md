# StarworksDev/.github

Org-wide GitHub defaults and shared actions for Starworks repositories.

## `actions/discord-ci-notify`

Posts a repo's CI result to its thread in the Discord `⚙️・ci-builds` forum. Add a final job to a CI workflow:

```yaml
  notify:
    name: Discord notify
    needs: [build]            # every job whose result should be reported
    if: always() && github.event_name != 'pull_request'
    runs-on: ubuntu-24.04
    timeout-minutes: 5
    permissions: { actions: read, contents: read }
    steps:
      - uses: StarworksDev/.github/actions/discord-ci-notify@<commit sha> # discord-ci-notify-v1.0.0
        with:
          needs: ${{ toJSON(needs) }}
          webhook: ${{ secrets.DISCORD_CI_WEBHOOK }}
          threads: ${{ vars.DISCORD_CI_THREADS }}
          github-token: ${{ github.token }}
```

**What it posts:**

| Outcome | Rule (over the jobs in `needs`) | Post |
|---|---|---|
| failure | any job failed | **FAILED**, every time, naming the failed jobs/legs |
| cancelled | else any job was cancelled | nothing |
| incomplete | else any job was skipped (it never ran) | **INCOMPLETE**, every time, naming the skipped jobs; never counts as a recovery |
| success | every job succeeded | **RECOVERED** if the previous completed non-PR run on the branch failed; **PASSED** for a manual run; otherwise nothing |

`needs` should list only jobs that are expected to run. A job that is skipped by design (e.g. path-filtered) belongs out of the notify job's `needs`.

**Pin it.** Reference the action by the full commit SHA of a release tag (`discord-ci-notify-v<major>.<minor>.<patch>`), with the tag in a comment, never `@main`. An action change is merged, `.github/workflows/test.yml` passes, the tag is cut, and then the callers are bumped deliberately.

- `DISCORD_CI_WEBHOOK` (org secret) and `DISCORD_CI_THREADS` (org variable, `{"<repo>": "<thread id>"}`) are set at the org.
  On GitHub Free, org secrets reach public repos only; a private repo sets the same names as repo secret/variable.
- A new repo gets a forum post in Discord and an entry in `DISCORD_CI_THREADS`.
- `result` (a pre-aggregated success/failure/cancelled string) is the v0 interface. v1 still accepts it so callers can migrate; it cannot see skipped jobs, so prefer `needs`.

## Audits

- [`docs/ci-audit-2026-10-12.md`](docs/ci-audit-2026-10-12.md): the GitHub Actions audit across Arcane, Astra, Manifold2D and Mosaic, covering confirmed issues, proposals and their disposition.
