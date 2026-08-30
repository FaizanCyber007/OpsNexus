"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export const DEMO_ORG_ID = "00000000-0000-0000-0000-000000000001";
export const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

interface TenantContextValue {
  organizationIdDraft: string;
  organizationId: string;
  handleOrgChange: (newDraft: string) => void;
  resetTenant: () => void;
}

const TenantContext = createContext<TenantContextValue | null>(null);

export function TenantProvider({ children }: { children: ReactNode }) {
  const [organizationIdDraft, setOrganizationIdDraft] = useState<string>(DEMO_ORG_ID);

  const organizationId = useMemo(() => {
    const trimmed = organizationIdDraft.trim();
    return UUID_PATTERN.test(trimmed) ? trimmed : "";
  }, [organizationIdDraft]);

  const handleOrgChange = useCallback((newDraft: string) => {
    setOrganizationIdDraft(newDraft);
  }, []);

  const resetTenant = useCallback(() => {
    setOrganizationIdDraft(DEMO_ORG_ID);
  }, []);

  const value = useMemo(
    () => ({
      organizationIdDraft,
      organizationId,
      handleOrgChange,
      resetTenant,
    }),
    [organizationIdDraft, organizationId, handleOrgChange, resetTenant]
  );

  return <TenantContext.Provider value={value}>{children}</TenantContext.Provider>;
}

export function useTenant(): TenantContextValue {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error("useTenant must be used within a TenantProvider");
  }
  return context;
}
