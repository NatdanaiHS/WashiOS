# Active path-only cleanup records

`PATH_RELOCATION.csv` is the active map from the pre-cleanup paths to the canonical submission
and archived manuscript paths. Every relocation preserves the pre-cleanup byte count and SHA-256.
No protected file was deleted or content-modified, and external backups remained read-only.

The immutable pre-cleanup freeze remains at `../cleanup_freeze_20260902/`. The canonical active
package is now `../submission/`; historical manuscript trees are under `../archive/manuscripts/`.

The earlier cleanup attempt exposed a pre-existing inconsistency between four historical entries
in `paper/tables/TABLE_PROVENANCE.json` and the already-frozen generator/table bytes. The cleanup
did not cause or conceal that bookkeeping conflict: the current bytes continue to match the
protected pre-cleanup manifest. See `CLEANUP_REPORT.md` and `POST_CLEANUP_VALIDATION.json`.
