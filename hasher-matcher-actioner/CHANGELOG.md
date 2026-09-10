# Changelog

This document and version tags are for reproducibility and the addition of migration guidance as needed for any breaking changes.

Versions correspond to the contents of `version.txt`, the `ghcr.io/facebook/threatexchange/hma:<version>` container images, and the `hma-v<version>` git tags. See [releasing.md](../website/content/hma/releasing.md) for the release process.

Entries are newest-first. Older entries were reconstructed from git history, so they are less detailed than newer ones. The section template used by each entry is at the [bottom of this file](#entry-template).

## Unreleased

#### :bug: Bug Fix

 - Fix `kwarg` parameter for `relativedelta` (#1993)

## 1.1.7 (2026-06-04)

#### :hammer: Underlying Tools

 - Require `python-threatexchange` >= 1.2.16 (#1988)

## 1.1.6 (2026-05-22)

#### :bug: Bug Fix

 - Route large object reads through the read replica (#1981)

#### :house: Internal

 - Generate the OpenAPI spec during website CI (#1982)

## 1.1.5 (2026-05-08)

# Highlights

A dedicated liveness endpoint (`/status/live`) so orchestrators no longer restart instances that are merely still loading their index, plus a switch to jemalloc to keep long-running matcher memory in check.

# Full Changelog

#### :rocket: New Feature

 - Add `/status/live` liveness endpoint, which deliberately does not check index state; `/status` keeps its readiness semantics and still returns 503 on a stale index (#1974)

#### :nail_care: Enhancement

 - Swap to jemalloc to reduce memory fragmentation (#1971)

#### :memo: Documentation

 - Scaffold out the initial documentation website (#1973)

## 1.1.4 (2026-04-15)

#### :bug: Bug Fix

 - Add explicit connection close for signal ops and clear temporary references (#1968)

#### :house: Internal

 - Switch to the `python-threatexchange` copy of the HMA interfaces (#1965)
 - Add `gh` and shell aliases to the devcontainer (#1966)
 - Add missing copyright headers (#1967)

## 1.1.3 (2026-03-25)

# Highlights

Bank content can now carry a free-text `note` and arbitrary custom metadata. Releases are now published to GitHub Releases with auto-generated notes.

# Migrating from 1.1.2 to 1.1.3

Two database migrations are included (`a1b2c3d4e5f6_add_note_to_bank_content`, `53fb7741007a_add_bank_content_metadata`). Apply them before serving traffic:

```bash
cd src/OpenMediaMatch
flask db upgrade
```

# Full Changelog

#### :rocket: New Feature

 - Add optional `note` field to bank content, with storage layer support (#1931, #1960)
 - Allow storage of custom metadata on bank content (#1949)

#### :bug: Bug Fix

 - Fix broken `hma-ui.md` link in the README (#1948)
 - Revert changes made to the devcontainer Dockerfile (#1950)

#### :nail_care: Enhancement

 - Deduplicate note validation logic in the curation blueprint (#1963)

#### :memo: Documentation

 - Fix documentation inaccuracies in `goals.md` (#1958)

#### :house: Internal

 - Add GitHub Releases with auto-generated release notes (#1957)
 - Local image server for testing (#1953)
 - Ignore Claude working files (#1951)

#### :hammer: Underlying Tools

 - Require `python-threatexchange` 1.2.15 (#1962)

## 1.1.2 (2026-03-02)

#### :rocket: New Feature

 - Provide an exchange schema so the UI can generate exchange configs (#1934)

#### :bug: Bug Fix

 - Fix the exchange status API (#1936)

#### :nail_care: Enhancement

 - Adjust various logging strings (#1916)

#### :memo: Documentation

 - Update `architecture.md` with scaling notes (#1914)

#### :hammer: Underlying Tools

 - Bump `python-threatexchange` and fix the mypy errors it surfaced (#1940)

## 1.1.1 (2026-01-28)

# Highlights

Deployments can now split reads and writes across a primary and one or more read replicas (see `reference_omm_configs/read_write_split_omm_config.py`), and index staleness tolerance is configurable instead of hardcoded.

# Full Changelog

#### :rocket: New Feature

 - Add database replication configurations (#1901)
 - Make index staleness configurable, with more informative `/status` returns (#1912)

#### :nail_care: Enhancement

 - Provide a more detailed error when exchange fields are missing (#1895)
 - Small tweaks and delint (#1896)

#### :house: Internal

 - Get the devcontainer building again (#1910)

## 1.1.0 (2025-11-17)

# Highlights

The API is now self-documenting: HMA serves OpenAPI docs generated with `flask-openapi3`.

# Full Changelog

#### :rocket: New Feature

 - Add OpenAPI docs using `flask-openapi3` (#1891)

## 1.0.22 (2025-11-05)

# Highlights

Lookup endpoints can be restricted to specific banks, deployments get a hook for their own startup wiring, and the docs grew real reference material for status, hashing, and matching.

# Full Changelog

#### :rocket: New Feature

 - Add bank filtering to the lookup endpoints (#1879)
 - Add a hook for setting up deployment-specific details (#1884)

#### :bug: Bug Fix

 - Fail rather than continue if the app hook isn't a function (#1885)
 - Remove HEAD check for files (#1876)

#### :nail_care: Enhancement

 - Use consistent variable naming in the scaled reference configs (#1883)

#### :memo: Documentation

 - Rudimentary docs for the status, hashing, and matching functions (#1866)
 - Update the `api.md` prelude (#1868)
 - Fix SVGs in `architecture.md` (#1869)
 - Add `roadmap.md` and link the discussion issue (#1871, #1872, #1874)

#### :house: Internal

 - Update the postcreate script (#1882)
 - Fix CI on trunk (#1880)

## 1.0.21 (2025-08-29)

#### :nail_care: Enhancement

 - Banks view UI improvements (#1859)
 - Bypass enabled ratio for the UI (#1855)
 - Improve developer experience when using Docker (#1832)

#### :memo: Documentation

 - Split `README.md` into individual documentation files (#1857)

## 1.0.20 (2025-08-27)

#### :rocket: New Feature

 - Make background task schedules configurable (#1848)

#### :bug: Bug Fix

 - Fix crash caused by the `MAX_CONTENT_LENGTH` configuration value (#1843)

#### :hammer: Underlying Tools

 - Upgrade the `python-threatexchange` version (#1853)

## 1.0.19 (2025-08-18)

#### :rocket: New Feature

 - Get signal from content ID (#1838)

#### :house: Internal

 - Fix typing (#1845)

## 1.0.18 (2025-08-12)

#### :rocket: New Feature

 - Update hashing to support `FileHasher`s (#1821)

#### :bug: Bug Fix

 - Clear out memory on index building to prevent bloating (#1839)

#### :nail_care: Enhancement

 - Add URL validation for hashing (#1822)

#### :memo: Documentation

 - Move the new HMA docs to the `hma` folder (#1836)
 - Add reference to the UI docs and images in `README.md` (#1837)

## 1.0.17 (2025-04-28)

Version bump only (#1819); no functional changes to HMA since 1.0.16.

## 1.0.16 (2025-03-28)

#### :bug: Bug Fix

 - Fix bug in HMA redirect logic (#1805)

## 1.0.15 (2025-03-27)

#### :rocket: New Feature

 - Add `UI_ENABLED` config variable (#1803)

## 1.0.14 (2025-03-19)

#### :nail_care: Enhancement

 - Auto-select input type on bank add (#1800)

## 1.0.13 (2025-03-11)

#### :bug: Bug Fix

 - Fix `python-threatexchange` library imports (#1796)

#### :memo: Documentation

 - Add direct reference to extensions in `README.md` (#1779)
 - Fix spelling (#1780)

#### :house: Internal

 - Fix labelling actions (#1775)

## 1.0.12 (2025-02-24)

#### :bug: Bug Fix

 - Align the lookup APIs and fix related bugs (#1770)

## 1.0.11 (2025-02-22)

#### :rocket: New Feature

 - Bank and bank content disable (#1732)

#### :bug: Bug Fix

 - Fix lookup with distance (#1767)

#### :memo: Documentation

 - Fix typos (#1762)

## 1.0.10 (2025-02-04)

#### :rocket: New Feature

 - Implement the exchange delete API (#1733)
 - Change the matching API to return more metadata (#1738)

#### :bug: Bug Fix

 - Fix `cli.storages` -> `storage` (#1749)

#### :house: Internal

 - Remove `IContentTypeConfigStore` (#1745)
 - Reformat with black (#1752)

## 1.0.9 (2025-01-31)

# Breaking Changes

`ISignalTypeConfigStore` was removed from HMA's storage interface (#1724). Custom storage implementations must drop it.

# Full Changelog

#### :bug: Bug Fix

 - Check for the hasher role in the `/lookup` endpoint (#1729)

#### :memo: Documentation

 - Tweak the message for checkpointing sanity check failures (#1737)

#### :house: Internal

 - Remove `ISignalTypeConfigStore` from HMA (#1724)
 - Black format everything (#1740)

#### :hammer: Underlying Tools

 - Require `python-threatexchange` >= 1.2.3 (#1728)

## 1.0.8 (2024-12-13)

#### :bug: Bug Fix

 - Fix hashing images (#1722)

#### :hammer: Underlying Tools

 - Require `python-threatexchange` >= 1.2.2 (#1717)

## 1.0.7 (2024-11-01)

# Highlights

New hash comparison support: a `POST /m/compare` endpoint and hash distance display in the match debug UI.

# Full Changelog

#### :rocket: New Feature

 - Add hash compare endpoint (`POST /m/compare`) (`ff9381d0`, `f45282bf`, `8ef77351`)
 - Add image hash distance to the match debug page (#1651)
 - Add endpoint to delete a content signal from a bank (#1632)

#### :bug: Bug Fix

 - Add recovery from large object (lobj) failure (#1674)
 - Fix broken UI due to the lookup change (#1642)
 - Patch similarity score (#1641)
 - Check dev mode functionality on page load (#1643)
 - Add missing `str_to_bool` import to `development.py` (`b223ff33`)

#### :nail_care: Enhancement

 - Refactor the banks page (#1652)

#### :house: Internal

 - Automatically install available extensions in the devcontainer (`0f1cc504`, `a482716f`)
 - Add more copyright headers (#1658)

## 1.0.6 (2024-10-02)

#### :memo: Documentation

 - Update `CONTRIBUTING.md` to include release instructions (#1631)

#### :house: Internal

 - Fix CI for the new mypy version (#1628)

## 1.0.5 (2024-09-25)

#### :bug: Bug Fix

 - Fix the create exchange API selector (#1603)

#### :house: Internal

 - Add required copyright headers to files missing them (#1625)

## 1.0.4 (2024-07-21)

#### :rocket: New Feature

 - Add metadata to the API (#1593)

#### :bug: Bug Fix

 - Fix content vars missing for template (#1598)
 - Fix redirect to the homepage (#1592)

#### :memo: Documentation

 - README changes to include how-to-use information (#1596)

## 1.0.3 (2024-05-08)

#### :hammer: Underlying Tools

 - Fix typo in build-push (#1588)

## 1.0.2 (2024-05-08)

#### :hammer: Underlying Tools

 - Add multiplatform support to build/push (#1587)

## 1.0.1 (2024-05-08)

#### :hammer: Underlying Tools

 - Add QEMU for binaries building (#1586)

## 1.0.0 (2024-05-08)

# Highlights

HMA 2.0 is the starting point for the current line of tagged versions and releases. It is the promotion of the Open Media Match project (formerly the `open-media-match/` directory) to become Hasher-Matcher-Actioner: a self-hosted Flask service that speaks a REST API and ships as a container image, replacing the AWS/Terraform-based HMA 1.0 (#1557).

This release adds the release and versioning pipeline that publishes `ghcr.io/facebook/threatexchange/hma` images (#1585).

# Migrating from HMA 1.0 to 1.0.0

There is no in-place upgrade path from HMA 1.0. HMA 1.0 was removed from the repository (#1556) and archived on the [`HMA_1.0_archive`](https://github.com/facebook/ThreatExchange/tree/HMA_1.0_archive) branch, which is where its own changelog and Terraform deployment live. HMA 2.0 is a distinct codebase with a distinct deployment model (Docker/Postgres rather than AWS Lambda/DynamoDB) and its own API.

Bring the database schema up to date before serving traffic:

```bash
cd src/OpenMediaMatch
flask db upgrade
```

# Breaking Changes

 - Configuration options can now be supplied via prefixed environment variables (#1575), and the reference `omm_config.py` files moved to `reference_omm_configs/` (#1574).

# Full Changelog

#### :rocket: New Feature

 - Release and versioning for the HMA docker image (#1585)
 - Enable gunicorn task scheduling (#1565)
 - Enable custom logging format (#1582)
 - Add prefixed env to config options (#1575)
 - Flesh out the match debug page (#1581)
 - Docker compose demo setup (#1579)
 - Split the UI home page into subpages (#1576)
 - Add favicon (#1577)

#### :bug: Bug Fix

 - Fix indexing startup for the devcontainer (#1563)

#### :memo: Documentation

 - Add intro to `README.md` (#1561), and further README updates (#1559)
 - Update `CONTRIBUTING.md` (#1560)
 - Point the Open Media Match README at HMA (#1558)

#### :house: Internal

 - Move reference `omm_config`s (#1574)

## 0.0.0 (2022-1-18)

Hasher Matcher Actioner 0.0 is the starting point for tagged versions and "release"

This is the original HMA 1.0 changelog entry, retained for history. HMA 1.0 lives on the [`HMA_1.0_archive`](https://github.com/facebook/ThreatExchange/tree/HMA_1.0_archive) branch.

## Entry template

Template example for each new version:

```
# Highlights

<optional-top-level-additions>

# Migrating from 0.0.x to 0.0.y

<comands or checks to make>

# Breaking Changes

<critical warnings>

# Full Changelog (Optional callouts)

 - 

#### :rocket: New Feature

 - 

#### :bug: Bug Fix

 - 

#### :nail_care: Enhancement

 - 

#### :memo: Documentation

 - 

#### :house: Internal

 - 

#### :hammer: Underlying Tools

 - 
```
