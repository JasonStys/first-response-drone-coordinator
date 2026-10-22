# Contributing

Use a topic branch and a pull request with the scenario/constraint being changed, tests, risk analysis and documentation updates. Keep the application synthetic and advisory. No aircraft commands, radio endpoints, actual incident/person data, credentials or automatic authorization bypasses belong here.

Install hash-locked Python and npm dependencies using README commands. Run lint, formatting, branch-aware coverage, helper tests, production build, audits, browser journeys and repository contracts. Run `python tools/docs_index.py` **after** formatting or adding files, and commit both generated indexes. Every authored code file needs an author/responsibility/source-map header; functions/classes need documentation. Choose descriptive names; comments should explain constraints and intent, not repeat syntax.

An optimizer change needs independent-oracle cases and direct adversarial validation. An authorization/state change needs wrong-role, stale revision and concurrent-write checks. Do not suppress a failing job, lower acceptance thresholds, replace actual-service acceptance with mocked transport or claim a not-run check passed. Lock updates need fresh audits and cross-platform validation. No Actions artifacts/caches are uploaded by these workflows; logs remain inspectable on GitHub.

Source author/contact: [Jason Stys](https://github.com/JasonStys), [LinkedIn](https://www.linkedin.com/in/jason-stys-31b30b351/).
