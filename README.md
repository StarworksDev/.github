# StarworksDev/.github

Org-wide GitHub defaults and shared actions for Starworks repositories.

## `actions/discord-ci-notify`

Posts a repo's CI result to its thread in the Discord `⚙️・ci-builds` forum. Add a final job to a CI workflow:

```yaml
  notify:
    needs: [build]            # every job whose result should be reported
    if: always() && github.event_name != 'pull_request'
    runs-on: ubuntu-24.04
    permissions: { actions: read, contents: read }
    steps:
      - uses: StarworksDev/.github/actions/discord-ci-notify@main
        with:
          result: ${{ contains(needs.*.result, 'failure') && 'failure' || (contains(needs.*.result, 'cancelled') && 'cancelled' || 'success') }}
          webhook: ${{ secrets.DISCORD_CI_WEBHOOK }}
          threads: ${{ vars.DISCORD_CI_THREADS }}
          github-token: ${{ github.token }}
```

- `DISCORD_CI_WEBHOOK` (org secret) and `DISCORD_CI_THREADS` (org variable, `{"<repo>": "<thread id>"}`) are set at the org.
  On GitHub Free, org secrets reach public repos only; a private repo sets the same names as repo secret/variable.
- A new repo gets a forum post in Discord and an entry in `DISCORD_CI_THREADS`.
