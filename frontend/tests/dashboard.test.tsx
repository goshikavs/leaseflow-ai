import { screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";
import { DashboardPage } from "@/components/DashboardPage";
import { emptyStats, jsonResponse, renderUi } from "./test-utils";

beforeEach(() => {
  vi.restoreAllMocks();
});

test("renders dashboard empty state", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) => {
      if (url.includes("/stats")) return Promise.resolve(jsonResponse(emptyStats));
      return Promise.resolve(jsonResponse({ items: [], page: 1, page_size: 20, total: 0 }));
    }),
  );
  renderUi(<DashboardPage />);
  expect(await screen.findByRole("heading", { name: /lease review dashboard/i })).toBeInTheDocument();
  expect(await screen.findByText(/no lease records yet/i)).toBeInTheDocument();
  expect(screen.getByText("Total documents")).toBeInTheDocument();
});

test("renders recent leases and api errors", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) => {
      if (url.includes("/stats")) {
        return Promise.resolve(
          jsonResponse({ total_documents: 1, awaiting_review: 1, approved_leases: 0, processing_errors: 0 }),
        );
      }
      return Promise.resolve(
        jsonResponse({
          items: [
            {
              id: "lease-1",
              document_id: "doc-1",
              original_filename: "sample_lease.pdf",
              tenant_name: "Northwind Analytics LLC",
              landlord_name: "Harborpoint",
              property_address: "Dallas",
              status: "awaiting_review",
              version: 1,
              created_at: "2026-04-20T12:00:00Z",
              updated_at: "2026-04-20T12:00:00Z",
              blocking_issue_count: 0,
            },
          ],
          page: 1,
          page_size: 20,
          total: 1,
        }),
      );
    }),
  );
  renderUi(<DashboardPage />);
  expect(await screen.findByText("Northwind Analytics LLC")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /open review/i })).toHaveAttribute("href", "/leases/lease-1");
});

test("displays dashboard api error", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve(
        jsonResponse({ error: { code: "INTERNAL_ERROR", message: "Unable to reach API", details: [] } }, 500),
      ),
    ),
  );
  renderUi(<DashboardPage />);
  await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Unable to reach API"));
});
