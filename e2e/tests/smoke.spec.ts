import { test, expect } from "@playwright/test";

test("smoke test", async ({ page }) => {
  await page.goto("data:text/html,<html><title>KMap smoke</title><body>KMap smoke</body></html>");
  await expect(page).toHaveTitle(/KMap smoke/i);
  await expect(page.getByText("KMap smoke")).toBeVisible();
});
