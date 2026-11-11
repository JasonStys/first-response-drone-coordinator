# Hosted browser setup correction

By Jason Stys. Observation date: 11 November 2026.

The prior Linux extracted-app job stopped while Ubuntu could not resolve its
archive host to fetch extra font packages. This occurred before application
assertions, and does not establish a global GitHub outage or a product bug.
The full multi-engine job also depended on those operating-system downloads.

The native job now downloads the exact locked Chromium, then requires an actual
normal browser launch and editable Unicode text. A real missing executable must
be rejected. Host validation remains enabled; a missing required library or
failed real launch is fatal. This proves the tested runner, not every clean PC.

The Chromium/Firefox/WebKit browser job uses the matching official Playwright
1.64.1 Noble image as a non-root user, pinned by registry-verified OCI digest
`sha256:2f05f8a734509a7b3f26a912639488ee08f58a7b292d14d62271bcff9038768f`. All three actual engines must pass the same
launch/input/missing-executable probe before the original full browser tests.
Seven actual child-process negatives refuse malformed engine requests and both
validation/download bypass variables, including empty values.

The original app tests, coverage thresholds, roles, mobile projects, native
archive extraction, frozen executable consumers, Tk/Xvfb controls, assertions,
timeouts and dependency audits remain mandatory. There are no retries, ignored
setup failures, alternate browser executables or skip flags. No runtime product
file, dependency lock, installed app, account or Docker setting changes here.

References: [official browser image guidance](https://playwright.dev/docs/docker)
and [official non-root CI guidance](https://playwright.dev/docs/ci).
Hosted results for this exact correction are pending; earlier passing runtime
and installed-app evidence is retained with its original source identity.
