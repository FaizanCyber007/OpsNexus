import { render, waitFor, screen, fireEvent } from "@testing-library/react";
import { SettingsGovernanceContent } from "./SettingsGovernanceContent";
import { useTenant } from "@/contexts/TenantContext";
import { apiClient } from "@/lib/apiClient";

jest.mock("@/contexts/TenantContext", () => ({
  useTenant: jest.fn(),
  DEMO_ORG_ID: "demo-org"
}));
jest.mock("@/lib/apiClient", () => ({
  apiClient: {
    getHealthRules: jest.fn(),
    getPlaybooks: jest.fn(),
    getSystemStatus: jest.fn(),
  }
}));
jest.mock("@/contexts/ToastContext", () => ({
  useToast: () => ({ showSuccess: jest.fn(), showError: jest.fn() })
}));

describe("SettingsGovernanceContent", () => {
  it("handles overlapping refreshes ignoring older responses that resolve last", async () => {
    let resolveRules1: (value?: unknown) => void;
    const promiseRules1 = new Promise(r => { resolveRules1 = r; });
    let resolveRules2: (value?: unknown) => void;
    const promiseRules2 = new Promise(r => { resolveRules2 = r; });

    let callCount = 0;
    (apiClient.getHealthRules as jest.Mock).mockImplementation(() => {
      callCount++;
      return callCount === 1 ? promiseRules1 : promiseRules2;
    });
    (apiClient.getPlaybooks as jest.Mock).mockResolvedValue([]);
    (apiClient.getSystemStatus as jest.Mock).mockResolvedValue(null);

    (useTenant as jest.Mock).mockReturnValue({
      organizationId: "org-1",
      handleOrgChange: jest.fn(),
      resetTenant: jest.fn(),
      organizationIdDraft: "org-1"
    });

    render(<SettingsGovernanceContent />);

    // Fast-forward initial loading
    resolveRules1([{ id: "rule-1", name: "Rule 1", metric: "cpu_usage", threshold: 80, is_active: true }]);
    
    // Wait for the UI to update with Rule 1
    // By clicking the tab we can see it
    const alertTab = screen.getByText(/Alert Rules/i);
    fireEvent.click(alertTab);

    await waitFor(() => {
      expect(screen.getByText("Rule 1")).toBeTruthy();
    });

    // Now trigger an overlapping refresh
    let refreshCallCount = 0;
    let resolveRefreshRules1: (value?: unknown) => void;
    const promiseRefreshRules1 = new Promise(r => { resolveRefreshRules1 = r; });
    let resolveRefreshRules2: (value?: unknown) => void;
    const promiseRefreshRules2 = new Promise(r => { resolveRefreshRules2 = r; });

    (apiClient.getHealthRules as jest.Mock).mockImplementation(() => {
      refreshCallCount++;
      return refreshCallCount === 1 ? promiseRefreshRules1 : promiseRefreshRules2;
    });

    const refreshButton = screen.getByText("Refresh").closest("button");
    
    fireEvent.click(refreshButton!);
    fireEvent.click(refreshButton!); // overlapping refresh

    // Resolve Req 2 first
    resolveRefreshRules2([{ id: "rule-3", name: "Rule 3", metric: "cpu_usage", threshold: 80, is_active: true }]);
    
    // Resolve Req 1 (stale) later
    resolveRefreshRules1([{ id: "rule-2", name: "Rule 2", metric: "cpu_usage", threshold: 80, is_active: true }]);

    await waitFor(() => {
      expect(screen.queryByText("Rule 2")).toBeNull();
      expect(screen.getByText("Rule 3")).toBeTruthy();
    });
  });
});
