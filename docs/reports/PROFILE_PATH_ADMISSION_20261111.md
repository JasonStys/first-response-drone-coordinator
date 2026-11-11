<!-- Jason Stys: actual profile-alias reproduction, pre-mutation repair and explicit local/native evidence boundaries. -->
# Profile path admission — 11 November 2026

## Reproduced boundary

The earlier accepted source `9f77d47a88fff5b2928c07c86c9d3078ec314769` checked only the final directory's symbolic-link flag before creating/resolving a profile. Actual Windows directory junctions, both at the selected path and above a nonexistent child, were accepted and created identity/lock/SQLite files in an initially empty owned target. Separate inert `sys.frozen`/executable/internal-root contexts demonstrated that the same real `Profile` implementation also admitted profile creation under program directories. These were synthetic empty fixtures, not private accounts or installed-user-directory changes.

This is a practical trusted-OS-owner path-selection/alias error, not a demonstrated remote privilege escalation. No production data, live aircraft/hardware or Docker was used. Earlier 0.2.0 release bytes and results remain historical and are not overwritten by this patch.

## Repair

The 0.2.1 source adds `coordinator/profile_paths.py`: inspect every existing ancestor without following aliases before mkdir; reject symbolic links and Windows reparse points/junctions; refuse frozen executable/internal trees and enclosing `.app` bundles. Inspect the marker, lock, database and journal/WAL/SHM companions before workspace mutation. Existing files must be regular and singly linked. Descriptor identity/regular-file checks precede lock writes, and missing read-only identities cannot create files.

The marker schema, database schema, account provisioning, HTTP roles/CSRF, cookie namespace, supported file workflows and domain calculations are unchanged. Ordinary external profiles reopen without reset or migration.

## Local validation

On patched Python 3.14.10, the complete original parent suite plus new regressions passed **218 parent tests**, with **95.56%** branch-aware package coverage (unchanged 90% minimum). The parent suite also mandates thirteen actual Tcl/Tk notice cases in a fresh bounded interpreter; these are reported separately, not padded into the parent total. No parent tests were skipped.

The new file contributes 15 meaningful admission cases: actual Windows final/ancestor junctions; real hardlinked marker/lock/DB/recovery members; frozen executable/internal/macOS bundle boundaries; directory/type/traversal errors; missing-read refusal; a real precreated identity replacement and descriptor closure. The original profile tests retain genuine account hashing/login, exclusive owner locking and exact database-dump persistence checks.

The 30 TypeScript helper tests and production type/build gates passed with their existing coverage requirements. Original Python lint/format, source navigation/privacy/pin checks and compiled-application acceptance remain required. The native consumer additionally invokes `tools/profile_admission_smoke.py`: the actual frozen executable must reject four real selections (program/internal/final alias/ancestor alias), return an error and leave program/empty-target files unchanged before the original full application journey proceeds. Hosted and exact-clean native results are pending for this patch until their recorded runs complete; this report does not claim them in advance.

## Actual Windows candidate checkpoint

The actual produced/extracted 0.2.1 Windows executable passed all four new refusal cases, with program files and empty alias targets unchanged, followed by the original full application browser/file/role/domain/export/Quit/persistence journey. Its source identity is explicitly **dirty local candidate**, not a clean hosted build or published-release identity. Archive SHA256: `8016e45c9e2d0e1e2fa5fcc0b33643d2ec5ca5582e381dd4ed3d8635d1a13d0b`. No installed app, real account, existing data, shortcut, older release or Docker installation was changed.

The first local candidate correctly failed an obsolete native-consumer footer expectation (0.2.0 expected; actual compiled UI 0.2.1). That failed output/log was preserved. Only the current-version expectation was corrected; the entire unchanged consumer passed against a new candidate output with every original deadline and assertion retained.

## Limits

The same OS account/administrator is trusted. These admission and descriptor-identity checks do not establish a race-proof namespace against concurrent same-user file replacement; SQLite still uses pathname-based connections. This is an unsigned portable application, not a signed installer, clean-OS transaction or security certification. No existing application, profile, shortcut or published archive was replaced during source validation.

## Hosted Windows notice-fixture correction

Validation run 42982811615, Windows core job 130396947798, failed one original notice fixture with an empty TclError and errorCode(NONE);225 other parent tests passed. The exact hosted cause is not proven, and the failure was preserved instead of rerun. Other three core platforms/browser/CodeQL and all three native desktop jobs passed. The original 226-test local count included thirteen direct notice cases; it was not 226 plus thirteen isolated cases.

The thirteen original assertions and parametrized case IDs are retained in `tests/runtime_notice_cases.py`; the test-function ASTs were compared for exact equality before changing only interpreter/capture ownership. The mandatory runner invokes them once in a fresh bounded interpreter with capture=sys, requires thirteen unique successful JUnit records, rejects skips/failures/count mismatches and records source hashes. The ordinary parent suite and packager both invoke this runner. Three independent real pytest children prove failure, skip and missing-case controls cannot become a successful receipt. Subprocess execution lives in trusted build tooling; no lint suppression, notice-reader fallback, coverage exclusion or original deadline was added.

The corrected full local result is 218 parent tests plus thirteen actual isolated notice cases at 95.56% combined package coverage, with the original 90% floor. Exact new hosted and clean-main release checks remain required; prior native candidate proof remains explicitly local/dirty and its product runtime did not change in this fixture-only followup.

The next desktop run42984712640 failed on all three OS jobs before executing notice tests: the native setup used runtime+packaging locks and had no pytest. Core/source checks had passed. Native setup now installs the hash-locked development+packaging requirements, matching the mandatory fixture dependency; an explicit workflow/lock regression covers this contract. Original deadlines, case bodies and native application assertions remain unchanged.
