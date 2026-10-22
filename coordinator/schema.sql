-- Jason Stys: private SQLite workspace, revision-guarded proposals, sessions and audit evidence.
-- Schema is created idempotently; incompatible future versions require explicit migration.
-- Function/variable source navigation: docs/SOURCE_MAP.md; table responsibilities: docs/FILE_CATALOG.md.
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS workspace (
    id INTEGER PRIMARY KEY CHECK (id = 1), revision INTEGER NOT NULL,
    scenario TEXT NOT NULL, schema_version INTEGER NOT NULL CHECK (schema_version = 1)
);
CREATE TABLE IF NOT EXISTS users (
    name TEXT PRIMARY KEY, password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('planner', 'reviewer', 'observer'))
);
CREATE TABLE IF NOT EXISTS sessions (
    digest TEXT PRIMARY KEY, username TEXT NOT NULL REFERENCES users(name),
    csrf TEXT NOT NULL, expires REAL NOT NULL, created REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS sessions_user ON sessions(username);
CREATE TABLE IF NOT EXISTS attempts (client TEXT PRIMARY KEY, count INTEGER NOT NULL, started REAL NOT NULL);
CREATE TABLE IF NOT EXISTS proposals (
    id INTEGER PRIMARY KEY, revision INTEGER NOT NULL, creator TEXT NOT NULL REFERENCES users(name),
    scenario_hash TEXT NOT NULL, result TEXT NOT NULL, created TEXT NOT NULL,
    reviewed_by TEXT REFERENCES users(name), selected TEXT, note TEXT
);
CREATE TABLE IF NOT EXISTS audit (
    id INTEGER PRIMARY KEY, at TEXT NOT NULL, actor TEXT NOT NULL,
    event TEXT NOT NULL, revision INTEGER NOT NULL, detail TEXT NOT NULL
);
