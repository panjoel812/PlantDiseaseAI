import type { TargetPoint } from "../api/types";

interface ClientPoint {
  clientX: number;
  clientY: number;
}

interface RenderedRect {
  left: number;
  top: number;
  width: number;
  height: number;
}

interface NaturalSize {
  width: number;
  height: number;
}

export function coverPointToNormalizedImage(
  point: ClientPoint,
  rect: RenderedRect,
  naturalSize: NaturalSize,
): TargetPoint | null {
  if (
    rect.width <= 0 ||
    rect.height <= 0 ||
    naturalSize.width <= 0 ||
    naturalSize.height <= 0
  ) {
    return null;
  }
  const localX = point.clientX - rect.left;
  const localY = point.clientY - rect.top;
  if (
    localX < 0 ||
    localY < 0 ||
    localX > rect.width ||
    localY > rect.height
  ) {
    return null;
  }
  const scale = Math.max(
    rect.width / naturalSize.width,
    rect.height / naturalSize.height,
  );
  const renderedWidth = naturalSize.width * scale;
  const renderedHeight = naturalSize.height * scale;
  const hiddenX = (renderedWidth - rect.width) / 2;
  const hiddenY = (renderedHeight - rect.height) / 2;
  const sourceX = (localX + hiddenX) / scale;
  const sourceY = (localY + hiddenY) / scale;
  return {
    x: clamp(sourceX / naturalSize.width),
    y: clamp(sourceY / naturalSize.height),
  };
}

function clamp(value: number): number {
  return Math.min(1, Math.max(0, value));
}
