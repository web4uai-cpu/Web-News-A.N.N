import { HomepageClient } from "@/components/home/homepage-client";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "A.N.N. — AI News Network | Live",
  description: "The world's first autonomous AI news network. Breaking news, AI anchor broadcasts, and real-time market intelligence — powered by 10 AI agents.",
};

export default function HomePage() {
  return <HomepageClient />;
}
