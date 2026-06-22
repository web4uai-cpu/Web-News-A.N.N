import type { Metadata } from "next";
import { PortalClient } from "@/components/portal/portal-client";

export const metadata: Metadata = {
  title: "A.N.N. Orbital | Enterprise Portal",
  description: "Premium enterprise portal for A.N.N. API access, social media configuration, and video synthesis.",
};

export default function PortalPage() {
  return <PortalClient />;
}
