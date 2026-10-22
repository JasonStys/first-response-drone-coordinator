/** @file Jason Stys: same-origin responsive planning workspace; function/variable lines: docs/SOURCE_MAP.md. */
import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  coveredCells,
  errorMessage,
  minutes,
  reviewState,
  usableMinutes,
} from "./domain";
import type { User, Workspace } from "./domain";
import "./style.css";

/** A single-workspace UI; server roles, revision checks and CSRF are authoritative. */
function App() {
  const [user, setUser] = useState<User | null>(null);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [editor, setEditor] = useState("");
  const [selected, setSelected] = useState(0);
  const [note, setNote] = useState("");
  const [ack, setAck] = useState(false);
  const [connected, setConnected] = useState(navigator.onLine);
  const [needsRefresh, setNeedsRefresh] = useState(false);

  /** Keep session data only in component memory; HttpOnly cookie is unavailable to scripts. */
  async function api(
    path: string,
    method = "GET",
    data?: unknown,
    session = user,
  ): Promise<any> {
    const response = await fetch(`/api/${path}`, {
      method,
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        ...(session ? { "X-CSRF-Token": session.csrf } : {}),
      },
      ...(data === undefined ? {} : { body: JSON.stringify(data) }),
    });
    const body = await response.json();
    if (!response.ok) {
      if (response.status === 401) {
        setUser(null);
        setWorkspace(null);
      }
      throw new Error(errorMessage(response.status, body.detail));
    }
    return body;
  }

  /** Refresh the snapshot only on successful transport; never silently queue offline writes. */
  async function refresh(session = user) {
    const data: Workspace = await api("workspace", "GET", undefined, session);
    setWorkspace(data);
    setEditor(JSON.stringify(data.scenario, null, 2));
    const latest = data.proposals[0];
    setSelected(
      Math.max(
        0,
        latest?.result.alternatives.findIndex(
          (item) => item.id === latest.selected,
        ) ?? 0,
      ),
    );
    setNeedsRefresh(false);
    setAck(false);
  }
  /** Serialize interactions and surface errors without treating network failures as success. */
  async function action(work: () => Promise<void>) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await work();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    void (async () => {
      try {
        const session: User = await api("me");
        setUser(session);
        await refresh(session);
      } catch {
        /* Signed-out landing is intentional. */
      }
    })();
    const online = () => setConnected(true),
      offline = () => {
        setConnected(false);
        setNeedsRefresh(true);
      };
    window.addEventListener("online", online);
    window.addEventListener("offline", offline);
    return () => {
      window.removeEventListener("online", online);
      window.removeEventListener("offline", offline);
    };
  }, []);

  const scenario = workspace?.scenario;
  const proposal = workspace?.proposals[0];
  const alternative = proposal?.result.alternatives[selected];
  const current = proposal?.revision === workspace?.revision;
  const covered =
    scenario && current ? coveredCells(scenario, alternative) : [];
  const disabled = busy || !connected || needsRefresh;

  return (
    <>
      <a className="skip" href="#main">
        Skip to workspace
      </a>
      <header>
        <a className="brand" href="/" aria-label="First Response home">
          <span className="mark" aria-hidden="true">
            ✚
          </span>
          <span>
            FIRST RESPONSE<small>DRONE COORDINATOR</small>
          </span>
        </a>
        <div className="header-right">
          <span className="pill">SYNTHETIC EXERCISE</span>
          {user && (
            <>
              <span>
                {user.name} / {user.role}
              </span>
              <button
                className="quiet"
                disabled={busy}
                onClick={() =>
                  void action(async () => {
                    await api("logout", "POST", {});
                    setUser(null);
                    setWorkspace(null);
                    setEditor("");
                    setNote("");
                  })
                }
              >
                Sign out
              </button>
            </>
          )}
        </div>
      </header>
      <main id="main">
        <div className="intro">
          <div>
            <p className="eyebrow">RESOURCE PLANNING / HUMAN OVERSIGHT</p>
            <h1>
              Coordinate resources.
              <br />
              <span>Keep people in command.</span>
            </h1>
            <p className="lead">
              Match exercise tasks to available teams and aircraft, compare
              coverage, and record an independent planning review.
            </p>
          </div>
          <aside className="scope">
            <strong>Planning only. Never dispatch.</strong>
            <p>
              No aircraft commands, live locations or automatic emergency
              exemptions. A recorded review is not flight authorization.
            </p>
          </aside>
        </div>
        {(!connected || needsRefresh) && (
          <p className="alert" role="alert">
            {connected
              ? "Connection restored. Refresh required."
              : "Browser offline."}{" "}
            Display may be stale. Writes are disabled and never queued;
            reconnect and refresh before planning.
          </p>
        )}
        {error && (
          <p className="alert" role="alert">
            {error}
          </p>
        )}
        {message && (
          <p className="notice" role="status">
            {message}
          </p>
        )}
        {!user ? (
          <section className="login panel">
            <h2>Open your workspace</h2>
            <p>
              Accounts are provisioned by the local host owner. No public
              registration or external identity service.
            </p>
            <form
              onSubmit={(event) => {
                event.preventDefault();
                void action(async () => {
                  const session: User = await api("login", "POST", {
                    username,
                    password,
                  });
                  setPassword("");
                  setUser(session);
                  await refresh(session);
                });
              }}
            >
              <label>
                Username
                <input
                  required
                  autoComplete="username"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                />
              </label>
              <label>
                Password
                <input
                  required
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />
              </label>
              <button disabled={disabled}>Sign in</button>
            </form>
          </section>
        ) : (
          scenario &&
          workspace && (
            <>
              <section className="toolbar panel">
                <div>
                  <p className="eyebrow">
                    INCIDENT WORKSPACE / REVISION {workspace.revision}
                  </p>
                  <h2>{scenario.name}</h2>
                  <p>
                    {scenario.horizon * 5}-minute fictional horizon • 5-minute
                    slots • no travel model
                  </p>
                </div>
                <div className="actions">
                  <button
                    className="quiet"
                    disabled={busy || !connected}
                    onClick={() =>
                      void action(async () => {
                        await refresh();
                        setMessage(
                          "Workspace refreshed. Review current conditions before proceeding.",
                        );
                      })
                    }
                  >
                    Refresh
                  </button>
                  <a
                    className="button quiet"
                    href="/api/report"
                    download="planning-review.json"
                  >
                    Export evidence
                  </a>
                  {user.role === "planner" && (
                    <button
                      disabled={disabled}
                      onClick={() =>
                        void action(async () => {
                          await api("proposals", "POST", {
                            revision: workspace.revision,
                          });
                          await refresh();
                          setMessage(
                            "Alternatives generated. An independent reviewer must review the chosen plan.",
                          );
                        })
                      }
                    >
                      Generate alternatives
                    </button>
                  )}
                </div>
              </section>
              <section
                className="conditions panel"
                aria-labelledby="conditions"
              >
                <h2 id="conditions">Conditions & stop gates</h2>
                <div className="condition-list">
                  {(
                    [
                      ["communications", "Communications available"],
                      ["crewed_aircraft", "Crewed aircraft activity"],
                      ["weather_hold", "Weather hold"],
                    ] as const
                  ).map(([key, label]) => (
                    <label key={key}>
                      <input
                        type="checkbox"
                        checked={scenario.conditions[key]}
                        disabled={disabled || user.role !== "planner"}
                        onChange={() =>
                          void action(async () => {
                            await api("workspace", "PUT", {
                              revision: workspace.revision,
                              scenario: {
                                ...scenario,
                                conditions: {
                                  ...scenario.conditions,
                                  [key]: !scenario.conditions[key],
                                },
                              },
                            });
                            await refresh();
                            setMessage(
                              "Conditions changed. All previous planning reviews are now stale.",
                            );
                          })
                        }
                      />
                      {label}
                    </label>
                  ))}
                </div>
                <p>
                  Loss of communications, crewed aircraft activity, or weather
                  hold stops all proposed allocations.
                </p>
              </section>
              <div className="stats">
                <section>
                  <span>TASKS REQUESTED</span>
                  <strong>{scenario.tasks.length}</strong>
                </section>
                <section>
                  <span>CURRENT PLAN COVERAGE</span>
                  <strong>
                    {current ? (alternative?.assignments.length ?? 0) : "—"}
                    <small> / {scenario.tasks.length}</small>
                  </strong>
                </section>
                <section>
                  <span>AIRCRAFT AVAILABLE</span>
                  <strong>
                    {scenario.aircraft.filter((item) => item.available).length}
                    <small> / {scenario.aircraft.length}</small>
                  </strong>
                </section>
                <section>
                  <span>PLAN REVIEW</span>
                  <strong className="text-stat">
                    {proposal
                      ? reviewState(proposal, workspace.revision)
                      : "Not generated"}
                  </strong>
                </section>
              </div>
              <div className="two-col">
                <section className="panel">
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">
                        FICTIONAL GRID / NOT A FLIGHT MAP
                      </p>
                      <h2>Coverage overview</h2>
                    </div>
                    <span className="legend">● Covered in selected plan</span>
                  </div>
                  <div
                    className="map-grid"
                    aria-label="Fictional exercise grid"
                  >
                    {["A", "B", "C", "D"].flatMap((row) =>
                      [1, 2, 3, 4].map((column) => {
                        const cell = `${row}${column}`;
                        const task = scenario.tasks.find(
                          (item) => item.cell === cell,
                        );
                        return (
                          <div
                            key={cell}
                            className={`cell ${covered.includes(cell) ? "covered" : ""} ${scenario.conditions.excluded_cells.includes(cell) ? "excluded" : ""}`}
                          >
                            <span>{cell}</span>
                            {task && (
                              <>
                                <strong>{task.sensor}</strong>
                                <small>
                                  {covered.includes(cell)
                                    ? "Covered"
                                    : "Unassigned"}
                                </small>
                              </>
                            )}
                          </div>
                        );
                      }),
                    )}
                  </div>
                </section>
                <section className="panel">
                  <p className="eyebrow">DETERMINISTIC BOUNDED SEARCH</p>
                  <h2>Compare alternatives</h2>
                  {proposal && alternative ? (
                    <>
                      <label>
                        Planning alternative
                        <select
                          value={selected}
                          onChange={(event) => {
                            setSelected(Number(event.target.value));
                            setAck(false);
                          }}
                        >
                          {proposal.result.alternatives.map((item, index) => (
                            <option key={item.id} value={index}>
                              Option {index + 1} / priority {item.score[0]} /{" "}
                              {item.assignments.length} tasks
                              {proposal.selected === item.id
                                ? " / reviewed choice"
                                : ""}
                            </option>
                          ))}
                        </select>
                      </label>
                      {proposal.reviewed_by && (
                        <p className="muted">
                          Review recorded by {proposal.reviewed_by} for the
                          option labelled “reviewed choice” only. Other
                          alternatives remain unreviewed.
                        </p>
                      )}
                      <p
                        className={
                          proposal.result.truncated ? "warning" : "muted"
                        }
                      >
                        {proposal.result.truncated
                          ? "Search limit reached — best found, not proven optimal."
                          : "Exhaustive search completed within model bounds."}{" "}
                        {proposal.result.nodes.toLocaleString()} nodes explored.
                      </p>
                      {!current && (
                        <p className="warning">
                          This proposal is stale. Regenerate against the current
                          revision.
                        </p>
                      )}
                      {proposal.result.holds.map((hold) => (
                        <p key={hold} className="warning">
                          {hold}
                        </p>
                      ))}
                      <h3>Coverage gaps</h3>
                      {alternative.gaps.length ? (
                        <ul className="gap-list">
                          {alternative.gaps.map((gap) => (
                            <li key={gap.task}>
                              <strong>{gap.task}</strong>
                              <span>{gap.reason}</span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p>
                          All tasks allocated within this simplified model. This
                          does not establish real mission feasibility.
                        </p>
                      )}
                    </>
                  ) : (
                    <p>
                      Generate a proposal to compare feasible allocations and
                      see why tasks remain unassigned.
                    </p>
                  )}
                </section>
              </div>
              <section className="panel">
                <div className="section-heading">
                  <div>
                    <p className="eyebrow">
                      NOMINAL CAPACITY / NO RECHARGING MODELED
                    </p>
                    <h2>Resources & task allocations</h2>
                  </div>
                </div>
                <div className="resources">
                  {scenario.aircraft.map((item) => (
                    <article key={item.id}>
                      <h3>{item.label}</h3>
                      <p>{item.sensors.join(" / ")}</p>
                      <strong>
                        {usableMinutes(item).toFixed(1)} min nominal budget
                      </strong>
                      <p>
                        {item.battery_percent}% charge • {item.reserve_percent}%
                        reserve
                      </p>
                      {user.role === "planner" ? (
                        <button
                          className="quiet"
                          disabled={disabled}
                          onClick={() =>
                            void action(async () => {
                              await api("workspace", "PUT", {
                                revision: workspace.revision,
                                scenario: {
                                  ...scenario,
                                  aircraft: scenario.aircraft.map((craft) =>
                                    craft.id === item.id
                                      ? {
                                          ...craft,
                                          available: !craft.available,
                                        }
                                      : craft,
                                  ),
                                },
                              });
                              await refresh();
                            })
                          }
                        >
                          {item.available
                            ? "Mark unavailable"
                            : "Restore availability"}
                        </button>
                      ) : (
                        <p>{item.available ? "Available" : "Unavailable"}</p>
                      )}
                    </article>
                  ))}
                </div>
                <div className="table-wrap">
                  <table>
                    <caption>
                      Exercise tasks and{" "}
                      {current
                        ? "selected allocations"
                        : "current requirements (stale allocations hidden)"}
                    </caption>
                    <thead>
                      <tr>
                        <th scope="col">Task / cell</th>
                        <th scope="col">Priority</th>
                        <th scope="col">Sensor</th>
                        <th scope="col">Window</th>
                        <th scope="col">Selected allocation</th>
                      </tr>
                    </thead>
                    <tbody>
                      {scenario.tasks.map((task) => {
                        const assignment = current
                          ? alternative?.assignments.find(
                              (item) => item.task === task.id,
                            )
                          : undefined;
                        return (
                          <tr key={task.id}>
                            <th scope="row">
                              {task.label}
                              <small>
                                {task.id} / {task.cell}
                              </small>
                            </th>
                            <td>P{task.priority}</td>
                            <td>{task.sensor}</td>
                            <td>
                              {minutes(task.earliest)} – {minutes(task.latest)}
                            </td>
                            <td>
                              {assignment ? (
                                <>
                                  {assignment.aircraft} / {assignment.operator}
                                  <small>
                                    {minutes(assignment.start)} –{" "}
                                    {minutes(assignment.end)}
                                  </small>
                                </>
                              ) : task.authorization_recorded ? (
                                "Unassigned"
                              ) : (
                                "Authorization not recorded"
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
                <p className="muted">
                  Operators:{" "}
                  {scenario.operators
                    .map(
                      (item) =>
                        `${item.label} (${item.available ? item.qualifications.join(", ") : "unavailable"})`,
                    )
                    .join(" • ")}
                </p>
              </section>
              {user.role === "reviewer" && proposal && alternative && (
                <section className="panel">
                  <h2>Independent planning review</h2>
                  <p>
                    Review coverage gaps, search limits, current conditions and
                    outside authorization. This records a planning judgement
                    only. It does not approve a flight.
                  </p>
                  {proposal.reviewed_by ? (
                    <p>
                      Recorded by {proposal.reviewed_by}: {proposal.note}
                    </p>
                  ) : (
                    <form
                      onSubmit={(event) => {
                        event.preventDefault();
                        void action(async () => {
                          await api(
                            `proposals/${proposal.id}/review/${alternative.id}`,
                            "POST",
                            {
                              revision: workspace.revision,
                              note,
                              acknowledge_limits: true,
                            },
                          );
                          await refresh();
                          setNote("");
                          setMessage(
                            "Planning review recorded. No flight authorization or dispatch occurred.",
                          );
                        });
                      }}
                    >
                      <label>
                        Review note
                        <textarea
                          minLength={10}
                          maxLength={500}
                          required
                          value={note}
                          onChange={(event) => setNote(event.target.value)}
                        />
                      </label>
                      <label className="check">
                        <input
                          type="checkbox"
                          required
                          checked={ack}
                          onChange={(event) => setAck(event.target.checked)}
                        />
                        I reviewed the model limits, gaps and authorization
                        requirements.
                      </label>
                      <button
                        disabled={
                          disabled ||
                          !current ||
                          !alternative.assignments.length ||
                          !ack
                        }
                      >
                        Record planning review
                      </button>
                    </form>
                  )}
                </section>
              )}
              {user.role === "planner" && (
                <details className="panel">
                  <summary>Scenario editor & exercise templates</summary>
                  <p>
                    Replace synthetic resources, qualifications, reserve
                    budgets, task windows and grid exclusions. Every save
                    creates a new revision and invalidates old reviews. JSON
                    only, maximum 64 KiB.
                  </p>
                  <div className="actions">
                    {["wildfire", "flood", "search", "restoration"].map(
                      (kind) => (
                        <button
                          key={kind}
                          className="quiet"
                          disabled={disabled}
                          onClick={() =>
                            void action(async () => {
                              const templates = await api("examples");
                              setEditor(
                                JSON.stringify(templates[kind], null, 2),
                              );
                              setMessage(
                                "Template loaded into editor only. Save to change the workspace.",
                              );
                            })
                          }
                        >
                          Load {kind}
                        </button>
                      ),
                    )}
                  </div>
                  <label>
                    Scenario JSON
                    <textarea
                      className="json-editor"
                      spellCheck={false}
                      value={editor}
                      onChange={(event) => setEditor(event.target.value)}
                    />
                  </label>
                  <button
                    disabled={disabled}
                    onClick={() =>
                      void action(async () => {
                        if (new TextEncoder().encode(editor).length > 60000)
                          throw new Error("Scenario is too large");
                        const updated: unknown = JSON.parse(editor);
                        await api("workspace", "PUT", {
                          revision: workspace.revision,
                          scenario: updated,
                        });
                        await refresh();
                        setMessage("Scenario saved as a new revision.");
                      })
                    }
                  >
                    Save scenario revision
                  </button>
                </details>
              )}
              <details className="panel">
                <summary>Planning history & audit trail</summary>
                <ul className="gap-list">
                  {workspace.proposals.map((item) => (
                    <li key={item.id}>
                      <strong>
                        Proposal #{item.id} / revision {item.revision}
                      </strong>
                      <span>
                        {reviewState(item, workspace.revision)} • {item.creator}{" "}
                        • {item.created}
                        {item.reviewed_by &&
                          ` • reviewed by ${item.reviewed_by}`}
                      </span>
                    </li>
                  ))}
                </ul>
                <h3>Recent workspace events</h3>
                <ul className="audit">
                  {workspace.audit.map((item) => (
                    <li key={item.id}>
                      {item.at} / {item.actor} / {item.event} / revision{" "}
                      {item.revision}
                    </li>
                  ))}
                </ul>
              </details>
            </>
          )
        )}
        <details className="panel help">
          <summary>How this works & safety limits</summary>
          <ol>
            <li>
              A planner loads or edits a synthetic exercise. Record
              authorization only after an appropriate external review; this
              application cannot verify it.
            </li>
            <li>
              Generate up to three plans. Priority coverage comes first, then
              task count, then earlier starts. Same crew, airframe or cell
              cannot overlap.
            </li>
            <li>
              A different reviewer inspects the proposal and acknowledges its
              limits. An edit makes old reviews stale.
            </li>
            <li>
              Export planning evidence for an exercise debrief. No flight,
              detection, rescue outcome or real-world safety is implied.
            </li>
          </ol>
          <p>
            Limits: six tasks, four aircraft, four operators, twelve five-minute
            slots, 25,000 search nodes. No transit, terrain, recharge, geodesy,
            live weather, air traffic, collision avoidance or human
            identification. Offline changes are never queued. Accounts and
            reports belong to one trusted local workspace.
          </p>
        </details>
      </main>
      <footer>
        <span>
          Designed & built by{" "}
          <a href="https://github.com/JasonStys">Jason Stys</a>
        </span>
        <a href="https://www.linkedin.com/in/jason-stys-31b30b351/">
          Contact on LinkedIn
        </a>
        <a href="https://github.com/JasonStys/first-response-drone-coordinator">
          Source & documentation
        </a>
        <span>Exercise data only / no telemetry or analytics</span>
      </footer>
    </>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
