import { render, waitFor, screen } from "@testing-library/react";
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
    let resolveMcpA: (value?: unknown) => void;
    const promiseMcpA = new Promise((r) => { resolveMcpA = r; });
    let resolveMcpB: (value?: unknown) => void;
    const promiseMcpB = new Promise((r) => { resolveMcpB = r; });

    let resolveRunsA: (value?: unknown) => void;
    const promiseRunsA = new Promise((r) => { resolveRunsA = r; });
    let resolveRunsB: (value?: unknown) => void;
    const promiseRunsB = new Promise((r) => { resolveRunsB = r; });

    let mcpCallCount = 0;
    (apiClient.getMcpTools as jest.Mock).mockImplementation(() => {
      mcpCallCount++;
      return mcpCallCount === 1 ? promiseMcpA : promiseMcpB;
    });
    let runsCallCount = 0;
    (apiClient.getAgentRuns as jest.Mock).mockImplementation(() => {
      runsCallCount++;
      return runsCallCount === 1 ? promiseRunsA : promiseRunsB;
    });

    (useTenant as jest.Mock).mockReturnValue({ organizationId: "workspace-A" });
    const { rerender } = render(<AgentSwarmHubContent />);

    // Switch to workspace B
    (useTenant as jest.Mock).mockReturnValue({ organizationId: "workspace-B" });
    rerender(<AgentSwarmHubContent />);

    // Resolve B
    resolveMcpB({ tools: [{ name: "tool-b" }] }); // getMcpTools
    resolveRunsB([]); // getAgentRuns
    
    // Resolve A (stale)
    resolveMcpA({ tools: [{ name: "tool-a" }] });
    resolveRunsA([]);

    // Check that tool-a is not rendered, meaning stale response was ignored
    await waitFor(() => {
      expect(screen.queryByText("tool-a")).toBeNull();
      expect(screen.getByText("tool-b")).toBeTruthy();
      expect(apiClient.getMcpTools).toHaveBeenCalledTimes(2);
      expect(apiClient.getAgentRuns).toHaveBeenCalledTimes(2);
    });
  });
});
