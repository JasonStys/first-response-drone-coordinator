/** Jason Stys: bounded strict UTF-8 object-file import for the existing JSON editor. Lines: docs/SOURCE_MAP.md. */
export const MAX_IMPORT_BYTES = 60_000;

/** Validate syntax/finite values and bounded depth/work; domain schemas remain authoritative on the server. */
export function objectFromText(text: string): Record<string, unknown> {
  if (new TextEncoder().encode(text).length > MAX_IMPORT_BYTES)
    throw new Error("JSON file exceeds 60,000 UTF-8 bytes");
  const value: unknown = JSON.parse(text);
  if (value === null || typeof value !== "object" || Array.isArray(value))
    throw new Error("Choose a JSON object, not an array or scalar");
  const stack: [unknown, number][] = [[value, 0]];
  let visited = 0;
  while (stack.length) {
    // The checked nonempty stack is owned here and has no external callbacks.
    const [node, depth] = stack.pop() as [unknown, number];
    if (++visited > 10_000 || depth > 64)
      throw new Error("JSON structure exceeds the depth/work bound");
    if (typeof node === "number" && !Number.isFinite(node))
      throw new Error("JSON numbers must be finite");
    if (node !== null && typeof node === "object")
      for (const child of Object.values(node)) stack.push([child, depth + 1]);
  }
  return value as Record<string, unknown>;
}

/** Check both advertised and actual bytes; malformed UTF-8 is rejected rather than silently repaired. */
export async function readObjectFile(
  file: File,
): Promise<Record<string, unknown>> {
  if (file.size > MAX_IMPORT_BYTES)
    throw new Error("JSON file exceeds 60,000 UTF-8 bytes");
  const bytes = await file.arrayBuffer();
  if (bytes.byteLength > MAX_IMPORT_BYTES)
    throw new Error("JSON file exceeds 60,000 UTF-8 bytes");
  return objectFromText(
    new TextDecoder("utf-8", { fatal: true }).decode(bytes),
  );
}
