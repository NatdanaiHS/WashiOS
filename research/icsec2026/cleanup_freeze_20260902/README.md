# ICSEC FINAL_PASS cleanup protection freeze

This directory records the exact repository state immediately before any cleanup or reorganization. It does not authorize cleanup and does not modify or relocate manuscript, evidence, source, provenance, generation, or backup content.

Protection rule: repository cleanup must not modify the byte content of any row in `PROTECTED_REPOSITORY_FILES.csv` or `PROTECTED_EXTERNAL_BACKUP_FILES.csv`. A later relocation is acceptable only with a complete old-to-new path map and identical pre/post SHA-256 values. Deletion requires explicit Research Director authorization.

`FREEZE_STATE.json` records the branch, FINAL_PASS commit, clean/synchronized start state, final manuscript paths/hash, evidence packages, table/provenance dependencies, evaluated source revisions, protected scopes, and all verified external backups.

The manifest generator is retained for deterministic re-verification. The manifest deliberately excludes its own cleanup-freeze directory from the protected repository tree to avoid self-referential hashes; the freeze directory is protected separately by `FREEZE_PACKAGE_SHA256SUMS.csv` after generation. It also excludes the mutable control records `SESSION_STATE.md` and `NEXT_TASK.md`; those files may continue recording reviewed work, but they do not authorize changing any protected scientific/manuscript content.
