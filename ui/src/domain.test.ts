/** @file Jason Stys: typed display semantics, stale precedence and safe errors; lines: docs/SOURCE_MAP.md. */
import { describe, expect, it } from "vitest";
import {
  coveredCells,
  errorMessage,
  minutes,
  reviewState,
  usableMinutes,
} from "./domain";
import type { Aircraft, Proposal, Scenario, Alternative } from "./domain";

describe("relative exercise time", () => {
  for (const slot of [0, 1, 6, 12])
    it(`formats slot ${slot}`, () =>
      expect(minutes(slot)).toBe(`T+${String(slot * 5).padStart(2, "0")} min`));
  for (const slot of [-1, 13, 1.5, NaN, Infinity])
    it(`rejects ${slot}`, () => expect(() => minutes(slot)).toThrow());
});
describe("nominal energy display", () => {
  for (const [charge, expected] of [
    [90, 32.5],
    [25, 0],
    [10, 0],
  ])
    it(`charge ${charge}`, () =>
      expect(
        usableMinutes({
          battery_percent: charge,
          reserve_percent: 25,
          endurance_minutes: 50,
        } as Aircraft),
      ).toBe(expected));
});
describe("review state", () => {
  it("stale overrides a recorded review", () =>
    expect(
      reviewState({ revision: 1, reviewed_by: "reviewer" } as Proposal, 2),
    ).toContain("Stale"));
  it("awaits independent review", () =>
    expect(
      reviewState({ revision: 1, reviewed_by: null } as Proposal, 1),
    ).toContain("Awaiting"));
  it("labels only planning review", () =>
    expect(
      reviewState({ revision: 1, reviewed_by: "reviewer" } as Proposal, 1),
    ).toBe("Planning review recorded"));
});
describe("grid and failures", () => {
  const scenario = {
    tasks: [
      { id: "a", cell: "B2" },
      { id: "b", cell: "A1" },
      { id: "c", cell: "B2" },
    ],
  } as Scenario;
  it("no alternative means no coverage", () =>
    expect(coveredCells(scenario)).toEqual([]));
  it("sorts and deduplicates", () =>
    expect(
      coveredCells(scenario, {
        assignments: [{ task: "a" }, { task: "b" }, { task: "c" }],
      } as Alternative),
    ).toEqual(["A1", "B2"]));
  it("ignores unknown references", () =>
    expect(
      coveredCells(scenario, {
        assignments: [{ task: "missing" }],
      } as Alternative),
    ).toEqual([]));
  it("schema errors do not dump user input", () =>
    expect(errorMessage(422, [{ input: "private" }])).not.toContain("private"));
  it("known safe server detail", () =>
    expect(errorMessage(409, "Workspace changed")).toBe("Workspace changed"));
  it("unknown error body", () =>
    expect(errorMessage(500, null)).toContain("500"));
});
