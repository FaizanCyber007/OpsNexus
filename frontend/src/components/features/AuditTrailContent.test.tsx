import { render, waitFor, screen, fireEvent } from "@testing-library/react";
import { AuditTrailContent } from "./AuditTrailContent";
import { useTenant } from "@/contexts/TenantContext";
import { apiClient } from "@/lib/apiClient";

jest.mock("@/contexts/TenantContext", () => ({
  useTenant: jest.fn(),
}));
jest.mock("@/lib/apiClient", () => ({
  apiClient: {
    getAuditLogs: jest.fn(),
  }
}));
jest.mock("@/contexts/ToastContext", () => ({
  useToast: () => ({ showSuccess: jest.fn(), showError: jest.fn() })
}));

describe("AuditTrailContent", () => {
  it("prevents obsolete requests from updating logs after organizationId changes", async () => {
    let resolveFirstReq: (value?: unknown) => void = () => {};
    const promiseFirstReq = new Promise(r => { resolveFirstReq = r; });
    
    let resolveSecondReq: (value?: unknown) => void = () => {};
    const promiseSecondReq = new Promise(r => { resolveSecondReq = r; });

    let callCount = 0;
    (apiClient.getAuditLogs as jest.Mock).mockImplementation(() => {
      callCount++;
      return callCount === 1 ? promiseFirstReq : promiseSecondReq;
    });

    (useTenant as jest.Mock).mockReturnValue({ organizationId: "org-1" });
    const { rerender } = render(<AuditTrailContent />);

    // Switch to org-2
    (useTenant as jest.Mock).mockReturnValue({ organizationId: "org-2" });
    rerender(<AuditTrailContent />);

    // Resolve second request
    resolveSecondReq([{ id: "log-2", resource_id: "res-2", resource_type: "doc", action: "CREATE", timestamp: "2023-01-01T00:00:00Z" }]);
    
    // Resolve first request (stale)
    resolveFirstReq([{ id: "log-1", resource_id: "res-1", resource_type: "doc", action: "CREATE", timestamp: "2023-01-01T00:00:00Z" }]);

    await waitFor(() => {
      expect(screen.queryByText("res-1")).toBeNull();
      expect(screen.getByText("res-2")).toBeTruthy();
      expect(apiClient.getAuditLogs).toHaveBeenCalledTimes(2);
    });
  });

  it("handles repeated refreshes ignoring older overlapping responses", async () => {
    let resolveReq1: (value?: unknown) => void = () => {};
    const promiseReq1 = new Promise(r => { resolveReq1 = r; });
    
    let resolveReq2: (value?: unknown) => void = () => {};
    const promiseReq2 = new Promise(r => { resolveReq2 = r; });

    let callCount = 0;
    (apiClient.getAuditLogs as jest.Mock).mockImplementation(() => {
      callCount++;
      return callCount === 1 ? promiseReq1 : promiseReq2;
    });

    (useTenant as jest.Mock).mockReturnValue({ organizationId: "org-1" });
    render(<AuditTrailContent />);

    // Fast-forward initial loading so button is enabled
    resolveReq1([{ id: "log-1", resource_id: "res-1", resource_type: "doc", action: "CREATE", timestamp: "2023-01-01T00:00:00Z" }]);
    await waitFor(() => {
      expect(screen.getByText("res-1")).toBeTruthy();
    });

    // We override getAuditLogs to return the overlapping promises now
    let refreshCallCount = 0;
    let resolveRefresh1: (value?: unknown) => void = () => {};
    const promiseRefresh1 = new Promise(r => { resolveRefresh1 = r; });
    let resolveRefresh2: (value?: unknown) => void = () => {};
    const promiseRefresh2 = new Promise(r => { resolveRefresh2 = r; });

    (apiClient.getAuditLogs as jest.Mock).mockImplementation(() => {
      refreshCallCount++;
      return refreshCallCount === 1 ? promiseRefresh1 : promiseRefresh2;
    });

    const refreshButton = screen.getByText("Refresh").closest("button");
    
    fireEvent.click(refreshButton!);
    fireEvent.click(refreshButton!); // overlapping refresh!

    // Resolve Req 2 first
    resolveRefresh2([{ id: "log-3", resource_id: "res-3", resource_type: "doc", action: "CREATE", timestamp: "2023-01-01T00:00:00Z" }]);
    
    // Resolve Req 1 (stale) later
    resolveRefresh1([{ id: "log-2", resource_id: "res-2", resource_type: "doc", action: "CREATE", timestamp: "2023-01-01T00:00:00Z" }]);

    await waitFor(() => {
      expect(screen.queryByText("res-2")).toBeNull();
      expect(screen.getByText("res-3")).toBeTruthy();
    });
  });
});
