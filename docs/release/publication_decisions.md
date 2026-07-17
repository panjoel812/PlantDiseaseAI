# Public Release Decisions

## 2026-07-17 Docker verification waiver

The user chose Apple `container` for local container execution and declined Docker installation. Docker Engine/Desktop documentation is therefore
static-only for this release, and the release evidence remains
`container: not_run`. Windows PowerShell validation is static-only as well.
Neither boundary is evidence of Docker build, health, Linux, or Windows runtime
verification.

## Public source history

The public snapshot will use a clean, minimal Git history with GitHub noreply metadata; development-only installed skill prose and internal SDD reports will
be excluded from that public snapshot. This decision records the later
publication boundary only; this change does not construct or publish that
history.

## Supplied image

The supplied field image is included under the separate
[`ASSET_LICENSES.md`](../../ASSET_LICENSES.md) notice. It and its direct visible
reproductions are outside the repository's MIT code license.
