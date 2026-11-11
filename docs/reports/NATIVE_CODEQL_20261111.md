<!-- Jason Stys: dated current-main CodeQL quality corrections and retained validation boundaries. -->
# Native CodeQL quality follow-up — 2026-11-11

These changes respond to actual full-main CodeQL quality notes before the first0.2.0 desktop release. They do not suppress, dismiss or exclude queries. No already-published release or installed user profile is altered.

## Corrections

- Moved actual Tcl/Tk package identity validation into `runtime_gui.py`, shared by the launcher and owner window without a circular import. Existing actual Tk mismatch/runtime-info tests still exercise it.
- Narrowed ordinary server-thread failures to `Exception`. Explicit `KeyboardInterrupt`/`SystemExit` become a retained interrupted-service failure with the original cause, followed by the same listener closure/readiness signal. They do not become normal success. Three real owned-thread startup failures prove readiness refuses, listener closes and owner stop reports failure.
- Console Ctrl+C now acknowledges draining before the existing completion-based finally block. Existing actual-host regression verifies listener/thread completion and profile-lock reacquisition.

## Local observation

| Gate | Observed result |
| --- | --- |
| Full original Python package suite | 211 passed; 95.11% coverage against unchanged90% floor |
| Original TypeScript test denominator | 30 helpers,100% all four metrics |
| Original strict UI build, formatting and Ruff | Passed |
| Generated source/file navigation and original public-source hygiene | Passed after regeneration |

No policy, role, database schema, UI workflow or secret-bearing data path is changed. Native build/3OS acceptance, original browser checks and a new full-main CodeQL analysis must pass on the eventual exact merged source before release. Earlier accepted package measurements remain bound to their earlier commits; they are not rebound to this correction. The original educational/offline boundaries, unsigned-portable limits and manual desktop-opener limitations remain.
