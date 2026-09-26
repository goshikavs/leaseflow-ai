import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import { AgentSettingsPage } from "@/components/AgentSettingsPage";
import { jsonResponse, renderUi } from "./test-utils";

const catalog = {
  lease_types: [
    {
      lease_type: "commercial",
      label: "Commercial",
      description: "Office, retail, and industrial leases.",
      flags: { ENABLE_FINANCE_AGENT: true, ENABLE_INSURANCE_AGENT: false },
    },
    {
      lease_type: "residential",
      label: "Residential",
      description: "Residential leases.",
      flags: { ENABLE_FINANCE_AGENT: true, ENABLE_INSURANCE_AGENT: true },
    },
  ],
  agents: [
    {
      key: "ENABLE_FINANCE_AGENT",
      agent_name: "finance",
      label: "Finance",
      mandatory: true,
      description: "Checks tenant financial status.",
    },
    {
      key: "ENABLE_INSURANCE_AGENT",
      agent_name: "insurance",
      label: "Insurance",
      mandatory: false,
      description: "Optional insurance specialist.",
    },
  ],
  note: "Lease-type settings cannot turn on an agent that the organization disabled.",
};

test("saves residential agent toggles", async () => {
  const user = userEvent.setup();
  const fetchMock = vi.fn((url: string, init?: RequestInit) => {
    if (url.includes("/flags/lease-types/residential") && init?.method === "POST") {
      return Promise.resolve(
        jsonResponse({
          lease_type: "residential",
          flags: { ENABLE_FINANCE_AGENT: false, ENABLE_INSURANCE_AGENT: true },
          note: catalog.note,
        }),
      );
    }
    return Promise.resolve(jsonResponse(catalog));
  });
  vi.stubGlobal("fetch", fetchMock);
  renderUi(<AgentSettingsPage />);
  expect(await screen.findByRole("heading", { name: /agent settings/i })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: /commercial leases/i })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: /residential leases/i })).toBeInTheDocument();
  const finance = screen.getAllByLabelText(/finance agent/i)[1];
  await user.click(finance);
  await user.click(screen.getByRole("button", { name: /save residential settings/i }));
  await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent(/residential agent settings saved/i));
  const putCall = fetchMock.mock.calls.find((call) => String(call[0]).includes("/residential"));
  expect(putCall?.[1]).toMatchObject({ method: "POST" });
});
