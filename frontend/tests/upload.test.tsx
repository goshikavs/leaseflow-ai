import { fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, test, vi } from "vitest";
import { UploadPage } from "@/components/UploadPage";
import { jsonResponse, renderUi } from "./test-utils";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

beforeEach(() => {
  push.mockReset();
  vi.restoreAllMocks();
});

test("rejects non-pdf files before upload", async () => {
  renderUi(<UploadPage />);
  const input = screen.getByLabelText(/lease pdf/i);
  const file = new File(["hello"], "notes.txt", { type: "text/plain" });
  fireEvent.change(input, { target: { files: [file] } });
  expect(await screen.findByRole("alert")).toHaveTextContent("Only PDF files are accepted.");
});

test("shows processing indicator and navigates after sample upload", async () => {
  const user = userEvent.setup();
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string, init?: RequestInit) => {
      if (url.includes("/demo/samples") && init?.method === "POST") {
        return Promise.resolve(
          jsonResponse({
            id: "doc-1",
            original_filename: "sample_lease.pdf",
            content_hash: "abc",
            uploaded_at: "2026-04-20T12:00:00Z",
            processing_status: "uploaded",
            processing_error: null,
            lease_id: null,
          }),
        );
      }
      if (url.includes("/process")) {
        return Promise.resolve(
          jsonResponse({
            document: { id: "doc-1" },
            lease_id: "lease-1",
            extraction_id: "ext-1",
            validation_issue_count: 0,
            blocking_issue_count: 0,
            provider: "fixture",
            fixture_mode: true,
          }),
        );
      }
      return Promise.resolve(jsonResponse({}, 404));
    }),
  );
  renderUi(<UploadPage />);
  await user.click(screen.getByRole("button", { name: /complete valid lease/i }));
  expect(await screen.findByRole("status")).toHaveTextContent(/uploading|extracting|opening/i);
  await waitFor(() => expect(push).toHaveBeenCalledWith("/leases/lease-1"));
});

test("shows upload api error", async () => {
  const user = userEvent.setup();
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve(jsonResponse({ error: { code: "INVALID_FILE_TYPE", message: "Only PDF files are accepted.", details: [] } }, 422)),
    ),
  );
  renderUi(<UploadPage />);
  await user.click(screen.getByRole("button", { name: /missing fields lease/i }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Only PDF files are accepted.");
});
