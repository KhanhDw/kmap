import { describe, expect, it } from "vitest";
import { pickVariant } from "./photoVariant";

describe("pickVariant", () => {
  it("uses the mobile image when WebGL texture capacity is below 8192", () => {
    expect(pickVariant(4096, false)).toBe("mobile");
  });

  it("uses the mobile image for mobile-like devices", () => {
    expect(pickVariant(16384, true)).toBe("mobile");
  });

  it("uses the display image when the device supports 8192 textures", () => {
    expect(pickVariant(8192, false)).toBe("display");
  });
});
