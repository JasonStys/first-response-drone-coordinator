/** @file Jason Stys: real service acceptance, independent review and accessibility; lines: docs/SOURCE_MAP.md. */
import { test, expect } from "@playwright/test";
import type { Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

/** Sign in through the actual form; no route interception or fabricated service responses. */
async function login(page: Page, role: string) {
  await page.goto("/");
  await page.getByLabel("Username", { exact: true }).fill(role);
  await page
    .getByLabel("Password", { exact: true })
    .fill("Synthetic-demo-only-2026!");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();
}
/** Restore a known exercise via supported UI, incrementing rather than resetting revision/audit. */
async function reset(page: Page) {
  await page
    .getByText("Scenario editor & exercise templates", { exact: true })
    .click();
  await page
    .getByRole("button", { name: "Load wildfire", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("Template loaded");
  await page.getByRole("button", { name: "Save scenario revision" }).click();
  await expect(page.getByRole("status")).toContainText("Scenario saved");
}
test("generate, independently review, invalidate and export actual evidence", async ({
  page,
}) => {
  await login(page, "planner");
  await reset(page);
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
  await page.getByRole("button", { name: "Sign out" }).click();
  await login(page, "reviewer");
  await page.getByLabel("Planning alternative").selectOption("1");
  await page
    .getByLabel("Review note")
    .fill("Reviewed nominal resource limits, gaps and external authorization.");
  await page
    .getByLabel(
      "I reviewed the model limits, gaps and authorization requirements.",
    )
    .check();
  await page.getByRole("button", { name: "Record planning review" }).click();
  await expect(page.getByRole("status")).toContainText(
    "No flight authorization",
  );
  await expect(page.getByLabel("Planning alternative")).toHaveValue("1");
  await page.getByRole("button", { name: "Sign out" }).click();
  await login(page, "planner");
  // These controls wait for authoritative server acknowledgement rather than optimistically asserting a hold.
  await page.getByLabel("Crewed aircraft activity", { exact: true }).click();
  await expect(
    page.getByLabel("Crewed aircraft activity", { exact: true }),
  ).toBeChecked();
  await expect(page.getByRole("status")).toContainText("now stale");
  await expect(
    page.getByText("Stale — regenerate", { exact: true }).first(),
  ).toBeVisible();
  await page.getByRole("button", { name: "Generate alternatives" }).click();
  await expect(
    page
      .locator("p.warning")
      .filter({ hasText: /^Crewed aircraft activity: stand down$/ }),
  ).toBeVisible();
  const downloadEvent = page.waitForEvent("download");
  await page.getByRole("link", { name: "Export evidence" }).click();
  const download = await downloadEvent;
  expect(download.suggestedFilename()).toBe("planning-review.json");
  const reportResponse = await page.request.get("/api/report");
  const report = await reportResponse.json();
  expect(report.proposals[0].result.alternatives[0].assignments).toEqual([]);
  expect(report.notice).toContain("No aircraft dispatched");
});
test("templates, schema rejection, resource outage and injection-safe rendering", async ({
  page,
}) => {
  await login(page, "planner");
  await reset(page);
  await page.getByRole("button", { name: "Load flood", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Template loaded");
  await page.getByRole("button", { name: "Save scenario revision" }).click();
  await expect(
    page.getByRole("heading", { name: "Flood assessment exercise" }),
  ).toBeVisible();
  const editor = page.getByLabel("Scenario JSON");
  const scenario = JSON.parse(await editor.inputValue());
  await editor.fill(JSON.stringify({ ...scenario, horizon: 1000 }));
  await page.getByRole("button", { name: "Save scenario revision" }).click();
  await expect(page.getByRole("alert")).toContainText("Invalid scenario");
  await editor.fill(
    JSON.stringify({ ...scenario, name: "<img src=x onerror=alert(1)>" }),
  );
  await page.getByRole("button", { name: "Save scenario revision" }).click();
  await expect(
    page.getByRole("heading", { name: "<img src=x onerror=alert(1)>" }),
  ).toBeVisible();
  expect(await page.locator("img").count()).toBe(0);
  await page
    .getByRole("button", { name: "Mark unavailable", exact: true })
    .first()
    .click();
  await expect(
    page.getByRole("button", { name: "Restore availability" }),
  ).toBeVisible();
});
test("observer boundaries, WCAG checks, mobile and author links", async ({
  page,
}) => {
  await page.goto("/");
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await login(page, "observer");
  await expect(
    page.getByRole("button", { name: "Generate alternatives" }),
  ).toHaveCount(0);
  await expect(
    page.getByLabel("Crewed aircraft activity", { exact: true }),
  ).toBeDisabled();
  expect(
    (
      await page.request.post("/api/proposals", {
        data: { revision: 1 },
        headers: { Origin: "http://127.0.0.1:8862" },
      })
    ).status(),
  ).toBe(403);
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await expect(
    page.getByRole("link", { name: "Jason Stys", exact: true }),
  ).toHaveAttribute("href", "https://github.com/JasonStys");
  await expect(
    page.getByRole("link", { name: "Contact on LinkedIn" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Sign out" }).focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("button", { name: "Sign in", exact: true }),
  ).toBeVisible();
});
test("offline does not queue writes and reconnect requires refresh", async ({
  page,
  context,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await login(page, "planner");
  await reset(page);
  await context.setOffline(true);
  await expect(page.getByRole("alert")).toContainText("Browser offline");
  await expect(
    page.getByRole("button", { name: "Generate alternatives" }),
  ).toBeDisabled();
  await context.setOffline(false);
  await expect(page.getByRole("alert")).toContainText("Refresh required");
  await expect(
    page.getByRole("button", { name: "Generate alternatives" }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Workspace refreshed");
  expect(errors).toEqual([]);
});
