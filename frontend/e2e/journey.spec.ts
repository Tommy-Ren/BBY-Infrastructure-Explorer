import { test, expect } from "@playwright/test";

test("search, select, radius, reload, and back navigation use real API data", async ({
  page,
}, testInfo) => {
  await page.goto("/");
  await page.getByRole("searchbox", { name: "Find your school" }).fill("Alpha");
  await page.getByRole("button", { name: "Alpha Secondary" }).click();
  await expect(
    page.getByRole("heading", { name: "Alpha Secondary" }),
  ).toBeVisible();
  await expect(page.locator(".metric-value")).toHaveText("24");
  await expect(page.getByText("95.1")).toBeVisible();
  await page.getByRole("radio", { name: "500 m", exact: true }).check();
  await expect(page.locator(".metric-value")).toHaveText("93");
  await expect(page).toHaveURL(/school=sch-.*radius=500/);
  await page.reload();
  await expect(
    page.getByRole("radio", { name: "500 m", exact: true }),
  ).toBeChecked();
  await expect(page.locator(".metric-value")).toHaveText("93");
  await page.getByRole("radio", { name: "100 m", exact: true }).check();
  await expect(page.locator(".metric-value")).toHaveText("1");
  await page.goBack();
  await expect(page.locator(".metric-value")).toHaveText("93");
  await expect(
    page.getByRole("button", { name: "Copy link to this school" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: testInfo.outputPath("school-details.png"),
    fullPage: true,
  });
});

test("school points on the map select a school and load nearby features", async ({
  page,
  request,
}, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await page.getByRole("button", { name: "Alpha Secondary" }).waitFor();
  const response = await request.get("/api/v1/schools?search=Alpha");
  const school = (await response.json()).items[0];
  const canvas = page.locator(".maplibregl-canvas");
  await canvas.scrollIntoViewIfNeeded();
  const bounds = await canvas.boundingBox();
  if (!bounds) throw new Error("Map canvas is missing");
  const world = 512 * 2 ** 11.2;
  const mercatorY = (latitude: number) =>
    (1 -
      Math.log(Math.tan(Math.PI / 4 + (latitude * Math.PI) / 360)) / Math.PI) /
    2;
  const x =
    bounds.width / 2 + ((school.location.longitude + 122.96) / 360) * world;
  const y =
    bounds.height / 2 +
    (mercatorY(school.location.latitude) - mercatorY(49.25)) * world;
  // Wait for the GeoJSON source to finish rendering by retrying a real map click.
  await expect(async () => {
    await canvas.click({ position: { x, y } });
    await expect(
      page.getByRole("heading", { name: "Alpha Secondary" }),
    ).toBeVisible({ timeout: 1500 });
  }).toPass({ timeout: 15000 });
  await expect(page.locator(".metric-value")).toHaveText("24");
  await expect(page.locator(".map-notice")).toHaveCount(0, { timeout: 15000 });
  expect(errors).toEqual([]);
  await page.screenshot({
    path: testInfo.outputPath("map-selected.png"),
    fullPage: true,
  });
});

test("empty search and list recovery work when map tiles fail", async ({
  page,
}) => {
  await page.route("https://tile.openstreetmap.org/**", (route) =>
    route.abort(),
  );
  await page.goto("/");
  const search = page.getByRole("searchbox");
  await search.fill("nothing matches");
  await expect(
    page.getByText("No schools found", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Clear search" }).click();
  await page.getByRole("button", { name: "Armstrong Elementary" }).click();
  await expect(
    page.getByRole("heading", { name: "Armstrong Elementary" }),
  ).toBeVisible();
  await expect(page.locator(".metric-value")).toHaveText("4");
});

test("initial API and detail failures have working retry paths", async ({
  page,
}) => {
  let fail = true;
  await page.route("**/api/v1/schools", (route) =>
    fail ? route.fulfill({ status: 503, body: "{}" }) : route.continue(),
  );
  await page.goto("/");
  await expect(page.getByRole("alert")).toContainText("try again");
  fail = false;
  await page.getByRole("button", { name: "Try again", exact: true }).click();
  await page.getByRole("button", { name: "Alpha Secondary" }).waitFor();
  let failDetail = true;
  await page.route("**/api/v1/schools/sch-*", (route) =>
    failDetail ? route.fulfill({ status: 503, body: "{}" }) : route.continue(),
  );
  await page.getByRole("button", { name: "Alpha Secondary" }).click();
  await expect(page.getByRole("alert")).toContainText("try again");
  failDetail = false;
  await page.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(page.locator(".metric-value")).toHaveText("24");
});

test("unknown shared school and malformed radius are recoverable", async ({
  page,
}) => {
  await page.goto("/?school=missing&radius=oops");
  await expect(page.getByRole("alert")).toContainText(
    "not in the current dataset",
  );
  await page.getByRole("button", { name: "Alpha Secondary" }).click();
  await expect(
    page.getByRole("radio", { name: "250 m", exact: true }),
  ).toBeChecked();
  await expect(page.locator(".metric-value")).toHaveText("24");
});
