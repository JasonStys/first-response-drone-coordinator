/** Jason Stys: real File/byte/depth/finite-value import contracts, independent of domain validation. Lines: docs/SOURCE_MAP.md. */
import { describe, expect, it } from "vitest";
import {
  MAX_IMPORT_BYTES,
  objectFromText,
  readObjectFile,
} from "./import_file";

describe("supported object files", () => {
  it("retains exact Unicode/scalars/nested arrays without interpreting strings as markup", async () => {
    const value = {
      name: "Fictional Δ unit",
      nested: [0, true, null, { note: "<script>inert</script>" }],
    };
    expect(
      await readObjectFile(new File([JSON.stringify(value)], "exercise.json")),
    ).toEqual(value);
    expect(objectFromText("{}")).toEqual({});
  });

  it.each(["null", "[]", "1", '"value"', "false", "not JSON"])(
    "rejects unsupported root/syntax %s",
    (text) => {
      expect(() => objectFromText(text)).toThrow();
    },
  );

  it("rejects advertised and actual oversized bytes and UTF-8 replacement", async () => {
    await expect(
      readObjectFile(
        new File([new Uint8Array(MAX_IMPORT_BYTES + 1)], "huge.json"),
      ),
    ).rejects.toThrow("60,000");
    const incorrectMetadata = {
      size: 1,
      arrayBuffer: async () => new Uint8Array(MAX_IMPORT_BYTES + 1).buffer,
    } as File;
    await expect(readObjectFile(incorrectMetadata)).rejects.toThrow("60,000");
    await expect(
      readObjectFile(new File([new Uint8Array([0xc3, 0x28])], "invalid.json")),
    ).rejects.toThrow();
    expect(() =>
      objectFromText('"' + "x".repeat(MAX_IMPORT_BYTES) + '"'),
    ).toThrow("60,000");
  });

  it("rejects overflow numbers and deeply nested or excessive work without recursive traversal", () => {
    expect(() => objectFromText('{"value":1e999}')).toThrow("finite");
    expect(() =>
      objectFromText('{"value":' + "[".repeat(65) + "0" + "]".repeat(65) + "}"),
    ).toThrow("depth/work");
    expect(() =>
      objectFromText(
        JSON.stringify({ values: Array.from({ length: 10_001 }, () => 0) }),
      ),
    ).toThrow("depth/work");
  });
});
