import { test, expect } from "@playwright/test";

const email = process.env.E2E_EMAIL;
const password = process.env.E2E_PASSWORD;

test.describe("Studio smoke", () => {
  test.skip(!email || !password, "Set E2E_EMAIL and E2E_PASSWORD to run auth E2E");

  test("login and reach app home", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill(email!);
    await page.getByLabel("Password").fill(password!);
    await page.getByRole("button", { name: "Sign in" }).click();
    await page.waitForURL(/\/app/);
    await expect(page.getByText(/Good (morning|afternoon|evening)/)).toBeVisible();
  });

  test("open chats list", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill(email!);
    await page.getByLabel("Password").fill(password!);
    await page.getByRole("button", { name: "Sign in" }).click();
    await page.waitForURL(/\/app/);

    await page.goto("/app/chats");
    await expect(page.getByRole("heading", { name: "Chats" })).toBeVisible();
    await expect(page.getByRole("button", { name: "New chat" })).toBeVisible();
  });
});

test.describe("Studio public routes", () => {
  test("login page renders", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
  });
});
