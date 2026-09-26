import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import { KnowledgePage } from "@/components/KnowledgePage";
import { jsonResponse, renderUi } from "./test-utils";

test("renders knowledge search and grounded answer", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) => {
      if (url.includes("/rag/search")) {
        return Promise.resolve(
          jsonResponse({
            items: [
              {
                chunk_id: "c1",
                document_id: "d1",
                lease_id: "l1",
                organization_id: "org-harborpoint",
                property_id: "prop-prosper-retail",
                document_version: 1,
                document_type: "lease",
                section_heading: "Rent Schedule",
                start_page: 1,
                end_page: 1,
                source_text: "Monthly Base Rent: 4200.00 USD",
                score: 0.81,
              },
            ],
          }),
        );
      }
      return Promise.resolve(
        jsonResponse({
          answer: "Based only on retrieved lease passages: Monthly Base Rent: 4200.00 USD",
          insufficient_evidence: false,
          citations: [],
          provider: "local-hashing",
          model_name: "local-hashing-1.0",
        }),
      );
    }),
  );
  const user = userEvent.setup();
  renderUi(<KnowledgePage />);
  expect(screen.getByRole("heading", { name: /lease knowledge/i })).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: /search and answer/i }));
  expect((await screen.findAllByText(/4200.00 USD/)).length).toBeGreaterThan(0);
  expect(screen.getByText(/Rent Schedule/)).toBeInTheDocument();
  expect(screen.getByText(/score 0.81/)).toBeInTheDocument();
});
