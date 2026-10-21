export type PhotoVariant = "mobile" | "display";

export function pickVariant(
  maxTextureSize: number,
  isMobileLike: boolean,
): PhotoVariant {
  return maxTextureSize < 8192 || isMobileLike ? "mobile" : "display";
}

export function getMaxTextureSize(): number {
  const canvas = document.createElement("canvas");
  const context =
    canvas.getContext("webgl") ??
    canvas.getContext("experimental-webgl");
  if (!context || !("getParameter" in context)) return 0;
  return context.getParameter(context.MAX_TEXTURE_SIZE);
}
