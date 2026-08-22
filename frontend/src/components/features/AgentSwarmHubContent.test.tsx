import { render, waitFor } from "@testing-library/react";
import { AgentSwarmHubContent } from "./AgentSwarmHubContent";
import { useTenant } from "@/contexts/TenantContext";
import { apiClient } from "@/lib/apiClient";

jest.mock("@/contexts/TenantContext", () => ({
  useTenant: jest.fn(),
}));
jest.mock("@/lib/apiClient", () => ({
  apiClient: {
    getMcpTools: jest.fn(),
    getAgentRuns: jest.fn(),
  }
}));
jest.mock("@/contexts/ToastContext", () => ({
  useToast: () => ({ showSuccess: jest.fn(), showError: jest.fn() })
}));

describe("AgentSwarmHubContent", () => {
  it("prevents stale asynchronous responses from updating state after tenant changes", async () => {
    let resolveA: (value?: unknown) => void;
    const promiseA = new Promise((r) => { resolveA = r; });
    
    let resolveB: (value?: unknown) => void;
    const promiseB = new Promise((r) => { resolveB = r; });

    let callCount = 0;
    (apiClient.getMcpTools as jest.Mock).mockImplementation(() => {
      callCount++;
      return callCount === 1 ? promiseA : promiseB;
    });
    (apiClient.getAgentRuns as jest.Mock).mockImplementation(() => {
      return callCount === 1 ? promiseA : promiseB;
    });

    (useTenant as jest.Mock).mockReturnValue({ organizationId: "workspace-A" });
    const { rerender } = render(<AgentSwarmHubContent />);

    // Switch to workspace B
    (useTenant as jest.Mock).mockReturnValue({ organizationId: "workspace-B" });
    rerender(<AgentSwarmHubContent />);

    // Resolve B
    resolveB({ tools: [{ name: "tool-b" }] }); // getMcpTools
    resolveB([]); // getAgentRuns
    
    // Resolve A (stale)
    resolveA({ tools: [{ name: "tool-a" }] });
    resolveA([]);

    // Check that tool-a is not rendered, meaning stale response was ignored
    await waitFor(() => {
      expect(apiClient.getMcpTools).toHaveBeenCalledTimes(2);
    });
  });
});
