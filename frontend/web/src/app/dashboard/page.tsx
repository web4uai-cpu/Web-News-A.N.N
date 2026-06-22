import { DashboardClient } from "@/components/dashboard/dashboard-client";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "A.N.N. Control Center",
  description: "Autonomous News Network command dashboard — pipeline control, agent monitoring, and analytics.",
};

export default function DashboardPage() {
  return <DashboardClient />;
}
