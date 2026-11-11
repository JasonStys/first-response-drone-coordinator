/** Jason Stys: real authenticated scenario file editing, rejection and deliberately held asynchronous reads. Lines: docs/SOURCE_MAP.md. */
import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

declare global {
  interface Window {
    __heldImport?: boolean;
    __releaseImport?: () => void;
  }
}

/** Sign into the actual disposable source-service fixture through its normal form. */
async function login(page: Page, role = "planner") {
  await page.goto("/");
  await page.getByLabel("Username", { exact: true }).fill(role);
  await page
    .getByLabel("Password", { exact: true })
    .fill("Synthetic-demo-only-2026!");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Refresh", exact: true }),
  ).toBeEnabled();
}

test("file import changes the draft only and rejects actual invalid bytes", async ({
  page,
}) => {
  await login(page);
  const original = await (await page.request.get("/api/workspace")).json();
  const scenario = {
    ...original.scenario,
    name: "Synthetic imported harbor exercise",
  };
  await page
    .getByText("Scenario editor & exercise templates", { exact: true })
    .click();
  const input = page.getByLabel("Open scenario JSON", { exact: true });
  const editor = page.getByLabel("Scenario JSON", { exact: true });
  await expect(editor).toHaveAccessibleName("Scenario JSON");
  await input.setInputFiles({
    name: "harbor.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify({ scenario })),
  });
  await expect(page.getByRole("status")).toContainText("editor only");
  expect(JSON.parse(await editor.inputValue())).toEqual(scenario);
  await expect(editor).toHaveAccessibleName("Scenario JSON");
  expect(await (await page.request.get("/api/workspace")).json()).toEqual(
    original,
  );
  const retained = await editor.inputValue();
  for (const buffer of [
    Buffer.from([0xc3, 0x28]),
    Buffer.alloc(60_001),
    Buffer.from('{"value":1e999}'),
    Buffer.from("[]"),
  ]) {
    await input.setInputFiles({
      name: "invalid.json",
      mimeType: "application/json",
      buffer,
    });
    await expect(page.getByRole("alert")).toBeVisible();
    expect(await editor.inputValue()).toBe(retained);
    expect(await (await page.request.get("/api/workspace")).json()).toEqual(
      original,
    );
  }
});

test("held older files cannot overwrite typing, a newer file or a changed account", async ({
  page,
}) => {
  await login(page);
  await page
    .getByText("Scenario editor & exercise templates", { exact: true })
    .click();
  await page.evaluate(() => {
    const original = File.prototype.arrayBuffer;
    File.prototype.arrayBuffer = function () {
      if (!this.name.startsWith("held-")) return original.call(this);
      window.__heldImport = true;
      return new Promise<ArrayBuffer>((resolve, reject) => {
        window.__releaseImport = () => {
          void original.call(this).then(resolve, reject);
        };
      });
    };
  });
  const input = page.getByLabel("Open scenario JSON", { exact: true });
  const editor = page.getByLabel("Scenario JSON", { exact: true });
  const before = JSON.parse(await editor.inputValue());
  const older = { ...before, name: "Older delayed exercise" };
  const newer = { ...before, name: "Newer chosen exercise" };
  async function hold() {
    await page.evaluate(() => {
      window.__heldImport = false;
    });
    await input.setInputFiles({
      name: "held-scenario.json",
      mimeType: "application/json",
      buffer: Buffer.from(JSON.stringify(older)),
    });
    await page.waitForFunction(() => window.__heldImport === true);
  }
  await hold();
  await editor.fill(JSON.stringify(newer));
  await page.evaluate(() => window.__releaseImport?.());
  await expect(editor).toHaveValue(JSON.stringify(newer));
  await expect(page.getByRole("status")).toContainText("Draft changed");
  await hold();
  await input.setInputFiles({
    name: "newer.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(newer)),
  });
  await expect(page.getByRole("status")).toContainText("editor only");
  await page.evaluate(() => window.__releaseImport?.());
  expect(JSON.parse(await editor.inputValue())).toEqual(newer);
  await hold();
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(
    page.getByRole("button", { name: "Sign in", exact: true }),
  ).toBeVisible();
  await page.evaluate(() => window.__releaseImport?.());
  await expect(editor).toHaveCount(0);
  await expect(page.getByRole("status")).toHaveCount(0);
});

test("nonplanner accounts have no scenario file or save controls", async ({
  page,
}) => {
  await login(page, "observer");
  await expect(
    page.getByLabel("Open scenario JSON", { exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Save scenario revision" }),
  ).toHaveCount(0);
});

test("a populated plan and file editor remain keyboard-accessible on narrow screens", async ({
  page,
}) => {
  await login(page);
  await page
    .getByText("Scenario editor & exercise templates", { exact: true })
    .click();
  await page
    .getByRole("button", { name: "Load wildfire", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("Template loaded");
  await page.getByRole("button", { name: "Save scenario revision" }).click();
  await expect(page.getByRole("status")).toContainText("new revision");
  await page.getByRole("button", { name: "Generate alternatives" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Alternatives generated",
  );
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(
    page.getByLabel("Open scenario JSON", { exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  const region = page.getByRole("region", {
    name: "Planning task allocations",
    exact: true,
  });
  await region.focus();
  await expect(region).toBeFocused();
  expect(
    await region.evaluate(
      (element) => element.scrollWidth > element.clientWidth,
    ),
  ).toBe(true);
  await region.press("ArrowRight");
  await expect
    .poll(() => region.evaluate((element) => element.scrollLeft))
    .toBeGreaterThan(0);
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
});
