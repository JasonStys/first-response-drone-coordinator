/** @file Jason Stys: actual child-process refusal of malformed browser requests and host bypass; navigation: docs/SOURCE_MAP.md. */
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { test } from "node:test";

/** Execute the real probe before any browser may be acquired or launched. */
function refused(args, extraEnvironment = {}) {
  const environment = { ...process.env };
  delete environment.PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS;
  delete environment.PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD;
  const child = spawnSync(
    process.execPath,
    ["tools/check_browser_host.mjs", ...args],
    {
      encoding: "utf8",
      timeout: 10000,
      env: { ...environment, ...extraEnvironment },
    },
  );
  assert.equal(child.error, undefined);
  assert.equal(child.signal, null);
  assert.notEqual(child.status, 0);
  assert.match(child.stderr, /AssertionError/);
  assert.doesNotMatch(child.stdout, /"launch":"passed"/);
}

test("empty browser requests fail before launch", () => refused([]));
test("unknown engines fail before launch", () => refused(["unexpected"]));
test("duplicate engines fail before launch", () =>
  refused(["chromium", "chromium"]));
for (const key of [
  "PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS",
  "PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD",
]) {
  for (const value of ["1", ""]) {
    test(`${key}=${JSON.stringify(value)} is rejected before launch`, () =>
      refused(["chromium"], { [key]: value }));
  }
}
