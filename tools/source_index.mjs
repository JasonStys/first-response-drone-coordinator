/** @file Jason Stys: TypeScript AST declaration/parameter/variable line index; lines: docs/SOURCE_MAP.md. */
import fs from "node:fs";
import path from "node:path";
import ts from "typescript";

/** Recurse through explicitly authored trees only, excluding dependency and runtime output. */
function collect(root) {
  return fs
    .readdirSync(root, { withFileTypes: true })
    .sort((a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0))
    .flatMap((entry) => {
      const name = path.join(root, entry.name);
      return entry.isDirectory()
        ? collect(name)
        : /\.(?:ts|tsx|mjs)$/.test(name)
          ? [name]
          : [];
    });
}
for (const file of [
  ...collect("ui/src"),
  ...collect("tests/browser"),
  ...collect("tools").filter((name) => name.endsWith(".mjs")),
  "vite.config.ts",
  "playwright.config.ts",
]) {
  const source = ts.createSourceFile(
    file,
    fs.readFileSync(file, "utf8"),
    ts.ScriptTarget.Latest,
    true,
  );
  const records = new Map();
  /** Index source declarations without evaluating application or imported package code. */
  function visit(node) {
    if (
      ts.isVariableDeclaration(node) ||
      ts.isFunctionDeclaration(node) ||
      ts.isClassDeclaration(node) ||
      ts.isInterfaceDeclaration(node) ||
      ts.isParameter(node)
    ) {
      if (node.name) {
        const name = node.name
          .getText(source)
          .replace(/\s+/g, " ")
          .replaceAll("|", "/");
        const line =
          source.getLineAndCharacterOfPosition(node.getStart(source)).line + 1;
        records.set(
          `${line}:${name}`,
          `| \`${file.replaceAll("\\", "/")}\` | ${line} | \`${name}\` |`,
        );
      }
    }
    ts.forEachChild(node, visit);
  }
  visit(source);
  for (const row of records.values()) console.log(row);
}
