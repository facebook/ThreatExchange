# Releasing HMA

## Cutting a release

1. Create a PR that bumps `version.txt` to the new version (e.g. `1.1.3`).

2. Ensure all tests are passing before merging.

3. Merge the PR. The rest happens automatically:
   - Docker images are built and pushed to GHCR as `:latest` and `:1.1.3`
   - A git tag `hma-v1.1.3` is created
   - A GitHub Release titled "HMA 1.1.3" is published, with release notes auto-generated from PRs merged since the previous release

4. Monitor the [release workflow](https://github.com/facebook/ThreatExchange/actions/workflows/hma-release.yaml) to confirm the build succeeds.

5. Test the new image locally by pulling the versioned tag:
   ```bash
   docker pull ghcr.io/facebook/threatexchange/hma:1.1.3
   ```

**Notes:**
- Do the version bump on its own PR, separate from code changes.
- For breaking changes, increment the major version (e.g. `2.0.0`).

## Subscribing to release notifications

To get notified when a new HMA release is published:

- **GitHub**: Watch this repo → Custom → check **Releases**
- **Slack**: Use the GitHub app — `/github subscribe facebook/ThreatExchange releases`
- **RSS**: Subscribe to `https://github.com/facebook/ThreatExchange/releases.atom`
