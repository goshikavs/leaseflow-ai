import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, test, vi } from "vitest";
import { ReviewPage } from "@/components/ReviewPage";
import { jsonResponse, renderUi, sampleLease } from "./test-utils";

beforeEach(() => {
  vi.restoreAllMocks();
});

function mockLeaseFetch(lease = sampleLease) {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string, init?: RequestInit) => {
      if (url.includes("/audit-timeline")) return Promise.resolve(jsonResponse({ events: [], latest_policy_result: null, approval_source: null }));
      if (url.includes("/audit")) return Promise.resolve(jsonResponse([]));
      if (url.includes("/workflow")) return Promise.resolve(jsonResponse(null));
      if (url.includes("/flags")) {
        return Promise.resolve(
          jsonResponse({
            organization_id: "org-harborpoint",
            property_id: "prop-unassigned",
            config_version: 1,
            flags: { REQUIRE_MANUAL_APPROVAL: false, ENABLE_AUTO_APPROVAL: true },
            restricted: true,
            note: "Read-only",
          }),
        );
      }
      if (url.includes("/mcp/status")) {
        return Promise.resolve(jsonResponse({ transport: "in-process", servers: {} }));
      }
      if (init?.method === "PATCH") {
        return Promise.resolve(
          jsonResponse({
            ...lease,
            property_address: "410 Example Parkway, Denver, CO 80202",
            issues: [],
            version: lease.version + 1,
          }),
        );
      }
      if (url.includes("/approve")) {
        return Promise.resolve(jsonResponse({ ...lease, status: "approved", issues: [], approved_by: "demo-reviewer" }));
      }
      return Promise.resolve(jsonResponse(lease));
    }),
  );
}

test("renders extracted fields, evidence, issues, and disabled approval", async () => {
  mockLeaseFetch();
  renderUi(<ReviewPage leaseId="lease-1" />);
  expect(await screen.findByDisplayValue("Northwind Analytics LLC")).toBeInTheDocument();
  expect(screen.getByText(/Tenant: Northwind Analytics LLC/)).toBeInTheDocument();
  expect(screen.getByText(/Property address is required before approval/)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /approve lease/i })).toBeDisabled();
  expect(screen.getByRole("button", { name: /save corrections/i })).toBeEnabled();
});

test("save operation updates the review form", async () => {
  const user = userEvent.setup();
  mockLeaseFetch();
  renderUi(<ReviewPage leaseId="lease-1" />);
  const address = await screen.findByLabelText(/property address/i);
  await user.clear(address);
  await user.type(address, "410 Example Parkway, Denver, CO 80202");
  await user.click(screen.getByRole("button", { name: /save corrections/i }));
  expect(await screen.findByRole("status")).toHaveTextContent(/corrections saved/i);
});

test("approval is available when there are no blocking issues", async () => {
  const user = userEvent.setup();
  mockLeaseFetch({ ...sampleLease, issues: [] });
  renderUi(<ReviewPage leaseId="lease-1" />);
  const approve = await screen.findByRole("button", { name: /approve lease/i });
  expect(approve).toBeEnabled();
  await user.click(approve);
  await waitFor(() => expect(screen.getByText(/lease approved/i)).toBeInTheDocument());
});

test("export link appears after approval", async () => {
  mockLeaseFetch({ ...sampleLease, status: "approved", issues: [], approved_by: "demo-reviewer" });
  renderUi(<ReviewPage leaseId="lease-1" />);
  expect(await screen.findByRole("link", { name: /view approved export/i })).toHaveAttribute(
    "href",
    "/leases/lease-1/approved",
  );
  expect(screen.getByRole("button", { name: /save corrections/i })).toBeDisabled();
});

test("review fields are keyboard accessible", async () => {
  mockLeaseFetch({ ...sampleLease, issues: [] });
  renderUi(<ReviewPage leaseId="lease-1" />);
  const tenant = await screen.findByLabelText(/tenant name/i);
  tenant.focus();
  expect(tenant).toHaveFocus();
  expect(screen.getByLabelText(/landlord name/i)).toBeInTheDocument();
});
