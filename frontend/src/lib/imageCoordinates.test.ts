import { describe, expect, it } from "vitest";

import { coverPointToNormalizedImage } from "./imageCoordinates";

const rect = (width: number, height: number, left = 0, top = 0) => ({
  left,
  top,
  width,
  height,
});

describe("coverPointToNormalizedImage", () => {
  it("maps a square card directly to a square source", () => {
    expect(
      coverPointToNormalizedImage(
        { clientX: 50, clientY: 75 },
        rect(100, 100),
        { width: 400, height: 400 },
      ),
    ).toEqual({ x: 0.5, y: 0.75 });
  });

  it("accounts for horizontally cropped source pixels", () => {
    expect(
      coverPointToNormalizedImage(
        { clientX: 0, clientY: 100 },
        rect(200, 200),
        { width: 400, height: 200 },
      ),
    ).toEqual({ x: 0.25, y: 0.5 });
    expect(
      coverPointToNormalizedImage(
        { clientX: 100, clientY: 100 },
        rect(200, 200),
        { width: 400, height: 200 },
      ),
    ).toEqual({ x: 0.5, y: 0.5 });
  });

  it("accounts for vertically cropped source pixels and card offsets", () => {
    expect(
      coverPointToNormalizedImage(
        { clientX: 120, clientY: 70 },
        rect(200, 100, 20, 20),
        { width: 200, height: 200 },
      ),
    ).toEqual({ x: 0.5, y: 0.5 });
  });

  it("rejects points outside the rendered image or invalid dimensions", () => {
    expect(
      coverPointToNormalizedImage(
        { clientX: -1, clientY: 50 },
        rect(100, 100),
        { width: 400, height: 400 },
      ),
    ).toBeNull();
    expect(
      coverPointToNormalizedImage(
        { clientX: 10, clientY: 10 },
        rect(0, 100),
        { width: 400, height: 400 },
      ),
    ).toBeNull();
  });
});
