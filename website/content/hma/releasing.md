# Releasing HMA

## Cutting a release

1. Create a PR that bumps `version.txt` to the new version (e.g. `1.1.3`).

2. Ensure all tests are passing before merging.

3. Merge the PR. The rest happens automatically:
   - Docker images are built and pushed to GHCR as `:latest` and `:1.1.3`
   - A git tag `hma-v1.1.3` is created
   - A GitHub Release titled "HMA 1.1.3" is published, with release notes auto-generated from PRs merged since the previous release

4. Monitor the [release workflow](https://github.com/facebook/ThreatExchange/actions/workflows/hma-release.yaml) to confirm the build succeeds.

5. Once the GitHub Release is published, add an entry for the new version at the top of [`CHANGELOG.md`](https://github.com/facebook/ThreatExchange/blob/main/hasher-matcher-actioner/CHANGELOG.md), following the entry template at the bottom of that file:
   - Move anything under `## Unreleased` into the new `## 1.1.3 (YYYY-MM-DD)` section.
   - Copy the `# Full Changelog` line items verbatim from the "What's Changed" list on the [GitHub Release](https://github.com/facebook/ThreatExchange/releases) page for that version — do not paraphrase or re-derive them from the commits/PRs yourself.
   - Add `# Highlights` when the release has a headline feature, `# Breaking Changes` for anything that requires consumers to change their code or config, and `# Migrating from <prev> to <new>` whenever a database migration is included or manual steps are needed.

6. Test the new image locally by pulling the versioned tag:
   ```bash
   docker pull ghcr.io/facebook/threatexchange/hma:1.1.3
   ```

**Notes:**
- The changelog entry can't be written until after the release is published, since its `# Full Changelog` section is copied from that release's auto-generated notes — this makes it a small follow-up PR, not part of the version bump.
- The auto-generated GitHub Release notes list every PR merged to the repo since the previous tag, not just `hasher-matcher-actioner/` changes; `CHANGELOG.md` keeps the same line items verbatim, but adds migration and breaking-change guidance the raw release notes don't have.
- For breaking changes, increment the major version (e.g. `2.0.0`).

## Subscribing to release notifications

To get notified when a new HMA release is published:

- **GitHub**: Watch this repo → Custom → check **Releases**
- **Slack**: Use the GitHub app — `/github subscribe facebook/ThreatExchange releases`
- **RSS**: Subscribe to `https://github.com/facebook/ThreatExchange/releases.atom`
