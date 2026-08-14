export const STATUS_OPTIONS = ["open", "in_progress", "pending", "resolved", "closed"] as const;
export const PRIORITY_OPTIONS = ["P1", "P2", "P3", "P4"] as const;

export const CATEGORY_OPTIONS = [
  "Access Management",
  "Laptop/Endpoint",
  "Network & VPN",
  "Email & Collaboration",
  "ERP/WMS",
  "Printers & Devices",
  "Security",
  "Telephony",
  "General",
] as const;

export const TEAM_OPTIONS = [
  "identity",
  "endpoint",
  "network",
  "collaboration",
  "erp",
  "hardware",
  "security",
  "telephony",
  "service-desk",
] as const;
