import { expect, test } from "@playwright/test";

test("valid sample can be approved and exported", async ({ page }) => {
  await page.goto("/upload");
  await page.getByRole("button", { name: /complete valid lease/i }).click();
  await expect(page.getByRole("heading", { name: /lease review/i })).toBeVisible({ timeout: 30_000 });
  await expect(page.getByLabel(/tenant name/i)).toHaveValue("Northwind Analytics LLC");
  await page.getByRole("button", { name: /approve lease/i }).click();
  await expect(page.getByRole("status")).toHaveText(/lease approved/i);
  await page.getByRole("link", { name: /view approved export/i }).click();
  const payload = page.locator("pre");
  await expect(payload).toContainText('"schema_version": "1.0"');
  await expect(payload).toContainText("Northwind Analytics LLC");
});

test("blocking issues prevent approval until corrected", async ({ page }) => {
  await page.goto("/upload");
  await page.getByRole("button", { name: /missing fields lease/i }).click();
  await expect(page.getByRole("heading", { name: /lease review/i })).toBeVisible({ timeout: 30_000 });
  await expect(page.getByRole("button", { name: /approve lease/i })).toBeDisabled();
  await page.getByLabel(/property address/i).fill("410 Example Parkway, Denver, CO 80202");
  await page.getByLabel(/landlord name/i).fill("Westbridge Capital LLC");
  await page.getByLabel(/monthly base rent/i).fill("9600.00");
  await page.getByLabel(/currency/i).fill("USD");
  await page.getByRole("button", { name: /save corrections/i }).click();
  await expect(page.getByText(/corrections saved/i)).toBeVisible();
  await expect(page.getByRole("button", { name: /approve lease/i })).toBeEnabled();
});
