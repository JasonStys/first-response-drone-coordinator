/** @file Jason Stys: actual three-role exercise previews and unchanged evidence. Map: docs/SOURCE_MAP.md. */
import { test, expect, type Page } from "@playwright/test";
import { readFile } from "node:fs/promises";

async function signIn(page: Page, role: string) {
  await page.goto("/");
  await page.getByLabel("Username", { exact: true }).fill(role);
  await page
    .getByLabel("Password", { exact: true })
    .fill("Synthetic-demo-only-2026!");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();
}

test("planner and reviewer compare saved resource loss without mutating the workspace; observer cannot", async ({
  page,
}) => {
  await signIn(page, "planner");
  const original = await (await page.request.get("/api/workspace")).json();
  await page
    .getByLabel("Unavailable exercise resource")
    .selectOption({ index: 1 });
  await page
    .getByRole("button", { name: "Preview resource loss", exact: true })
    .click();
  await expect(page.getByLabel("Resource-loss comparison")).toContainText(
    "No proposal, review or flight authorization created",
  );
  expect(await (await page.request.get("/api/workspace")).json()).toEqual(
    original,
  );
  const pending = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Download resource-loss comparison" })
    .click();
  const path = await (await pending).path();
  const saved = JSON.parse(await readFile(path!, "utf8"));
  expect(saved.revision).toBe(original.revision);
  expect(saved.before.alternatives.length).toBeGreaterThan(0);
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await expect(page.getByLabel("Resource-loss comparison")).toHaveCount(0);
  await page.getByRole("button", { name: "Sign out" }).click();
  await signIn(page, "reviewer");
  await page
    .getByLabel("Unavailable exercise resource")
    .selectOption({ index: 1 });
  await page
    .getByRole("button", { name: "Preview resource loss", exact: true })
    .click();
  await expect(page.getByLabel("Resource-loss comparison")).toBeVisible();
  await page.getByRole("button", { name: "Sign out" }).click();
  await signIn(page, "observer");
  await expect(
    page.getByRole("heading", { name: "Single-resource-loss exercise" }),
  ).toHaveCount(0);
});
