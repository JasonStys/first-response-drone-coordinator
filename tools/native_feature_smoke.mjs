/** Jason Stys: actual packaged planning UI, role separation, file edits, review and exact export. Lines: docs/SOURCE_MAP.md. */
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import { chromium, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const [base, output] = process.argv.slice(2);
assert(base && output && process.env.NATIVE_TEST_PASSWORD);
const origin = new URL(base).origin;
const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 1440, height: 1000 },
  acceptDownloads: true,
  reducedMotion: "reduce",
});
const page = await context.newPage();
const errors = [];
const external = [];
page.on("pageerror", (error) => errors.push(error.message));
page.on("request", (request) => {
  if (
    /^https?:/.test(request.url()) &&
    new URL(request.url()).origin !== origin
  )
    external.push(request.url());
});

/** Sign in through the real form with the ephemeral isolated profile's roles. */
async function login(role) {
  await page.goto(base);
  await page.getByLabel("Username", { exact: true }).fill(role);
  await page
    .getByLabel("Password", { exact: true })
    .fill(process.env.NATIVE_TEST_PASSWORD);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Refresh", exact: true }),
  ).toBeEnabled();
}

/** Inspect actual browser-downloaded JSON rather than a fabricated endpoint response. */
async function download(name) {
  const event = page.waitForEvent("download");
  await page.getByRole("link", { name }).click();
  const file = await (await event).path();
  assert(file);
  return JSON.parse(await fs.readFile(file, "utf8"));
}

try {
  await login("planner");
  await expect(
    page.getByText("Application v0.2.0", { exact: false }),
  ).toBeVisible();
  const original = await (
    await page.request.get(new URL("api/workspace", base).href)
  ).json();
  assert.equal(original.revision, 1);
  const scenario = structuredClone(original.scenario);
  scenario.name = "Fictional harbor observation exercise";
  await page
    .getByText("Scenario editor & exercise templates", { exact: true })
    .click();
  await page.getByLabel("Open scenario JSON", { exact: true }).setInputFiles({
    name: "harbor.json",
    mimeType: "application/json",
    buffer: Buffer.from(
      JSON.stringify({
        scenario,
        notice: "synthetic exported scenario only",
      }),
    ),
  });
  await expect(page.getByRole("status")).toContainText("editor only");
  await fs.writeFile(
    path.join(output, "label-diagnostics.json"),
    JSON.stringify(
      await page.locator("textarea").evaluateAll((elements) =>
        elements.map((element) => ({
          id: element.id,
          labels: Array.from(element.labels ?? []).map((label) =>
            label.textContent?.slice(0, 300),
          ),
        })),
      ),
      null,
      2,
    ),
  );
  assert.deepEqual(
    JSON.parse(
      await page.getByLabel("Scenario JSON", { exact: true }).inputValue(),
    ),
    scenario,
  );
  const notSaved = await (
    await page.request.get(new URL("api/workspace", base).href)
  ).json();
  assert.deepEqual(notSaved, original);
  await page.getByRole("button", { name: "Save scenario revision" }).click();
  await expect(page.getByRole("status")).toContainText("new revision");
  await page.getByRole("button", { name: "Generate alternatives" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Alternatives generated",
  );
  await expect(
    page.getByText("Authorization not recorded", { exact: true }).first(),
  ).toBeVisible();
  await expect(
    page.getByLabel("Planning alternative").locator("option"),
  ).toHaveCount(3);
  await expect(
    page.getByRole("button", { name: "Record planning review" }),
  ).toHaveCount(0);
  const saved = await download("Export evidence");
  assert.equal(saved.revision, 2);
  assert.deepEqual(saved.scenario, scenario);
  assert.equal(saved.proposals.length, 1);
  assert.equal(saved.proposals[0].creator, "planner");
  assert.equal(saved.proposals[0].stale, false);
  assert.match(saved.notice, /No aircraft dispatched/);
  const beforeInvalid = await page
    .getByLabel("Scenario JSON", { exact: true })
    .inputValue();
  await page.getByLabel("Open scenario JSON", { exact: true }).setInputFiles({
    name: "bad.json",
    mimeType: "application/json",
    buffer: Buffer.from([0xc3, 0x28]),
  });
  await expect(page.getByRole("alert")).toBeVisible();
  assert.equal(
    await page.getByLabel("Scenario JSON", { exact: true }).inputValue(),
    beforeInvalid,
  );
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await expect(page.getByRole("alert")).toHaveCount(0);
  assert.deepEqual(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
        .analyze()
    ).violations,
    [],
  );
  await page.screenshot({
    path: path.join(output, "01-imported-resource-plan.png"),
    fullPage: true,
  });
  await page.getByRole("button", { name: "Sign out" }).click();
  await login("reviewer");
  await expect(
    page.getByLabel("Open scenario JSON", { exact: true }),
  ).toHaveCount(0);
  await page
    .getByLabel("Review note", { exact: true })
    .fill(
      "Independent fictional planning review: inspect model bounds and missing authorization.",
    );
  await page
    .getByLabel(
      "I reviewed the model limits, gaps and authorization requirements.",
    )
    .check();
  await page.getByRole("button", { name: "Record planning review" }).click();
  await expect(page.getByRole("status")).toContainText(
    "No flight authorization",
  );
  const reviewed = await download("Export evidence");
  assert.equal(reviewed.proposals[0].reviewed_by, "reviewer");
  assert.equal(reviewed.proposals[0].stale, false);
  await page
    .getByRole("heading", { name: "Independent planning review" })
    .locator("..")
    .screenshot({
      path: path.join(output, "02-independent-planning-review.png"),
    });
  await page.getByRole("button", { name: "Sign out" }).click();
  await login("observer");
  await expect(
    page.getByRole("button", { name: "Generate alternatives" }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Record planning review" }),
  ).toHaveCount(0);
  await expect(
    page.getByLabel("Open scenario JSON", { exact: true }),
  ).toHaveCount(0);
  await page.setViewportSize({ width: 390, height: 844 });
  const allocationRegion = page.getByRole("region", {
    name: "Planning task allocations",
    exact: true,
  });
  await allocationRegion.focus();
  await expect(allocationRegion).toBeFocused();
  assert(
    await allocationRegion.evaluate(
      (element) => element.scrollWidth > element.clientWidth,
    ),
  );
  await allocationRegion.press("ArrowRight");
  await expect
    .poll(() => allocationRegion.evaluate((element) => element.scrollLeft))
    .toBeGreaterThan(0);
  assert(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  );
  assert.deepEqual(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
        .analyze()
    ).violations,
    [],
  );
  assert.deepEqual(
    await page.evaluate(() => [localStorage.length, sessionStorage.length]),
    [0, 0],
  );
  const cookies = await context.cookies();
  assert.equal(cookies.length, 1);
  assert.equal(cookies[0].name, process.env.NATIVE_TEST_COOKIE_NAME);
  assert.equal(cookies[0].httpOnly, true);
  assert.equal(cookies[0].sameSite, "Strict");
  assert.deepEqual(external, []);
  assert.deepEqual(errors, []);
  await fs.writeFile(
    path.join(output, "feature.json"),
    JSON.stringify(
      {
        passed: true,
        actual_roles: ["planner", "reviewer", "observer"],
        imported_scenario_saved_revision: 2,
        independent_review: "reviewer",
        invalid_import_retained_editor: true,
        exact_real_downloads: true,
        no_flight_authorization: true,
        mobile_width: 390,
        outside_requests: 0,
      },
      null,
      2,
    ) + "\n",
  );
} finally {
  await context.close();
  await browser.close();
}
