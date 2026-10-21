import { expect, test } from "@playwright/test";

const baseUrl = "http://localhost";
const demoPhotoId = "00000000-0000-0000-0000-00000000d301";

test.use({
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 3,
  isMobile: true,
  hasTouch: true,
});

test("opens a panorama from a mobile map and returns to the same view", async ({
  page,
}, testInfo) => {
  const photoResponse = await page.request.get(
    `${baseUrl}/api/v1/photos/${demoPhotoId}`,
  );
  expect(photoResponse.ok()).toBeTruthy();
  const photo = (await photoResponse.json()) as {
    location: { lat: number; lng: number };
    heading: number | null;
  };
  expect(photo.heading).not.toBeNull();

  await page.goto(
    `${baseUrl}/?lat=${photo.location.lat}&lng=${photo.location.lng}&z=18`,
  );
  const marker = page.locator('path[fill="#e11d48"]');
  const cluster = page.locator(".photo-cluster");
  await expect(cluster).toBeVisible();
  await cluster.click();
  await expect(marker.first()).toBeVisible();

  const externalRequests: string[] = [];
  page.on("request", (request) => {
    if (new URL(request.url()).origin !== baseUrl) {
      externalRequests.push(request.url());
    }
  });
  const mapBounds = await page.locator(".map-canvas").boundingBox();
  expect(mapBounds).not.toBeNull();
  const target = {
    x: mapBounds!.x + mapBounds!.width / 2,
    y: mapBounds!.y + mapBounds!.height / 2,
  };
  const markers = await marker.all();
  let closestMarker = markers[0];
  let closestDistance = Number.POSITIVE_INFINITY;
  for (const candidate of markers) {
    const bounds = await candidate.boundingBox();
    if (!bounds) continue;
    const distance = Math.hypot(
      bounds.x + bounds.width / 2 - target.x,
      bounds.y + bounds.height / 2 - target.y,
    );
    if (distance < closestDistance) {
      closestDistance = distance;
      closestMarker = candidate;
    }
  }
  const initialView = new URL(page.url()).searchParams;
  await closestMarker.click();

  await expect(page).toHaveURL(/\/photo\/00000000-0000-0000-0000-00000000d30[1-4]/);
  const openedPhotoId = new URL(page.url()).pathname.split("/").at(-1);
  expect(openedPhotoId).toBeTruthy();
  const openedPhotoResponse = await page.request.get(
    `${baseUrl}/api/v1/photos/${openedPhotoId}`,
  );
  expect(openedPhotoResponse.ok()).toBeTruthy();
  const openedPhoto = (await openedPhotoResponse.json()) as {
    heading: number | null;
  };
  expect(openedPhoto.heading).not.toBeNull();
  const compass = page.locator(".pnlm-compass");
  await expect(compass).toBeVisible();
  await expect(page.getByText("Người đóng góp thử nghiệm")).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("m3-compass.png") });
  expect(externalRequests).toEqual([]);

  const forward = page.getByRole("button", {
    name: "Tiến tới ảnh phía trước",
  });
  const backward = page.getByRole("button", {
    name: "Lùi tới ảnh phía sau",
  });
  await expect(forward).toBeVisible();
  await expect(backward).toBeVisible();
  const nextPhoto = (await forward.isEnabled()) ? forward : backward;
  await expect(nextPhoto).toBeEnabled();
  await nextPhoto.click();
  await expect(page).not.toHaveURL(new RegExp(`/photo/${openedPhotoId}`));
  await expect(compass).toBeVisible();

  const initialCompassTransform = await compass.getAttribute("style");
  const panoramaBounds = await page
    .locator(".pnlm-render-container")
    .boundingBox();
  expect(panoramaBounds).not.toBeNull();
  const centerX = panoramaBounds!.x + panoramaBounds!.width / 2;
  const centerY = panoramaBounds!.y + panoramaBounds!.height / 2;
  const touchSession = await page.context().newCDPSession(page);
  await touchSession.send("Input.dispatchTouchEvent", {
    type: "touchStart",
    touchPoints: [{ x: centerX, y: centerY, id: 1 }],
  });
  await touchSession.send("Input.dispatchTouchEvent", {
    type: "touchMove",
    touchPoints: [{ x: centerX + 80, y: centerY, id: 1 }],
  });
  await touchSession.send("Input.dispatchTouchEvent", {
    type: "touchEnd",
    touchPoints: [],
  });
  await touchSession.detach();
  await expect
    .poll(() => compass.getAttribute("style"))
    .not.toBe(initialCompassTransform);

  await page.locator(".pnlm-zoom-in").click();
  await page.locator(".pnlm-zoom-out").click();
  expect(externalRequests).toEqual([]);

  await page.getByRole("button", { name: "Đóng ảnh và quay lại bản đồ" }).click();
  await expect(page).toHaveURL(/\/\?/);
  const returnedView = new URL(page.url()).searchParams;
  for (const parameter of ["lat", "lng", "z"]) {
    expect(returnedView.get(parameter)).toBe(initialView.get(parameter));
  }
  const returnedCluster = page.locator(".photo-cluster");
  await expect(returnedCluster).toBeVisible();
  await returnedCluster.click();
  await expect(page.locator('path[fill="#f59e0b"]')).toBeVisible();
});
