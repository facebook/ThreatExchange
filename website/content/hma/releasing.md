# Releasing HMA

## Cutting a release

1. Create a PR that bumps `version.txt` to the new version (e.g. `1.1.3`).

2. In the same PR, add an entry for the new version at the top of [`CHANGELOG.md`](https://github.com/facebook/ThreatExchange/blob/main/hasher-matcher-actioner/CHANGELOG.md), following the entry template at the bottom of that file:
   - Move anything under `## Unreleased` into the new `## 1.1.3 (YYYY-MM-DD)` section.
   - Only include the sections that apply. Most releases just need a `# Full Changelog` with the relevant `#### :rocket:`/`#### :bug:`/etc. callouts.
   - Add `# Highlights` when the release has a headline feature, `# Breaking Changes` for anything that requires consumers to change their code or config, and `# Migrating from <prev> to <new>` whenever a database migration is included or manual steps are needed.

3. Ensure all tests are passing before merging.

4. Merge the PR. The rest happens automatically:
   - Docker images are built and pushed to GHCR as `:latest` and `:1.1.3`
   - A git tag `hma-v1.1.3` is created
   - A GitHub Release titled "HMA 1.1.3" is published, with release notes auto-generated from PRs merged since the previous release

5. Monitor the [release workflow](https://github.com/facebook/ThreatExchange/actions/workflows/hma-release.yaml) to confirm the build succeeds.

6. Test the new image locally by pulling the versioned tag:
   ```bash
   docker pull ghcr.io/facebook/threatexchange/hma:1.1.3
   ```

**Notes:**
- Do the version bump and changelog entry on their own PR, separate from code changes.
- The auto-generated GitHub Release notes are a raw list of merged PRs; `CHANGELOG.md` is the curated, categorized history, with migration and breaking-change guidance. Keep both.
- For breaking changes, increment the major version (e.g. `2.0.0`).

## Subscribing to release notifications

To get notified when a new HMA release is published:

- **GitHub**: Watch this repo → Custom → check **Releases**
- **Slack**: Use the GitHub app — `/github subscribe facebook/ThreatExchange releases`
- **RSS**: Subscribe to `https://github.com/facebook/ThreatExchange/releases.atom`
