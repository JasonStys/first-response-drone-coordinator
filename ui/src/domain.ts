/** @file Jason Stys: typed planning contracts and pure display helpers; exact lines: docs/SOURCE_MAP.md. */
export interface Aircraft {
  id: string;
  label: string;
  sensors: string[];
  available: boolean;
  battery_percent: number;
  reserve_percent: number;
  endurance_minutes: number;
}
export interface Operator {
  id: string;
  label: string;
  qualifications: string[];
  available: boolean;
}
export interface Task {
  id: string;
  label: string;
  cell: string;
  sensor: string;
  priority: number;
  earliest: number;
  latest: number;
  duration: number;
  authorization_recorded: boolean;
}
export interface Scenario {
  name: string;
  synthetic: true;
  horizon: number;
  aircraft: Aircraft[];
  operators: Operator[];
  tasks: Task[];
  conditions: {
    communications: boolean;
    crewed_aircraft: boolean;
    weather_hold: boolean;
    excluded_cells: string[];
  };
}
export interface Assignment {
  task: string;
  aircraft: string;
  operator: string;
  start: number;
  end: number;
}
export interface Alternative {
  id: string;
  score: number[];
  assignments: Assignment[];
  gaps: { task: string; reason: string }[];
}
export interface Result {
  alternatives: Alternative[];
  nodes: number;
  truncated: boolean;
  optimal: boolean;
  holds: string[];
}
export interface Proposal {
  id: number;
  revision: number;
  creator: string;
  result: Result;
  reviewed_by: string | null;
  selected: string | null;
  note: string | null;
  created: string;
}
export interface Workspace {
  revision: number;
  scenario: Scenario;
  proposals: Proposal[];
  audit: {
    id: number;
    at: string;
    actor: string;
    event: string;
    revision: number;
    detail: string;
  }[];
}
export interface User {
  name: string;
  role: "planner" | "reviewer" | "observer";
  csrf: string;
}

/** Translate finite nonnegative slot indices into relative exercise minutes; never a real departure time. */
export function minutes(slot: number): string {
  if (!Number.isInteger(slot) || slot < 0 || slot > 12)
    throw new Error("Invalid slot");
  return `T+${String(slot * 5).padStart(2, "0")} min`;
}
/** Derive a nominal aggregate battery budget; not physical flight endurance prediction. */
export function usableMinutes(aircraft: Aircraft): number {
  return (
    (Math.max(0, aircraft.battery_percent - aircraft.reserve_percent) *
      aircraft.endurance_minutes) /
    100
  );
}
/** Stale state wins over recorded review so an obsolete plan is never presented as current. */
export function reviewState(proposal: Proposal, revision: number): string {
  if (proposal.revision !== revision) return "Stale — regenerate";
  return proposal.reviewed_by
    ? "Planning review recorded"
    : "Awaiting independent review";
}
/** Resolve selected assignment cell IDs to a stable sorted set for accessible grid display. */
export function coveredCells(
  scenario: Scenario,
  alternative?: Alternative,
): string[] {
  const ids = new Set(alternative?.assignments.map((item) => item.task) ?? []);
  return [
    ...new Set(
      scenario.tasks
        .filter((task) => ids.has(task.id))
        .map((task) => task.cell),
    ),
  ].sort();
}
/** Human readable server errors without dumping schema input, passwords or tracebacks into the UI. */
export function errorMessage(status: number, detail: unknown): string {
  if (status === 422)
    return "Invalid scenario or form. Check field types, IDs, bounds and task windows.";
  return typeof detail === "string"
    ? detail
    : `Request failed (${status}). Refresh and try again.`;
}
