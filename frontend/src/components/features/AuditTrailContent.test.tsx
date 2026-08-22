import { render, waitFor } from "@testing-library/react";
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
    let resolveFirstReq: any;
    const promiseFirstReq = new Promise(r => { resolveFirstReq = r; });
    
    let resolveSecondReq: any;
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
    resolveSecondReq([{ id: "log-2", resource_id: "res-2", resource_type: "doc", action: "CREATE" }]);
    
    // Resolve first request (stale)
    resolveFirstReq([{ id: "log-1", resource_id: "res-1", resource_type: "doc", action: "CREATE" }]);

    await waitFor(() => {
      expect(apiClient.getAuditLogs).toHaveBeenCalledTimes(2);
    });
  });
});
