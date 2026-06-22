import { NewsClient } from "@/components/news/news-client";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "A.N.N. — Live Broadcasts",
  description: "AI-powered news broadcasts in English and Hindi. Breaking news, world events, technology, finance, and more.",
};

export default function NewsPage() {
  return <NewsClient />;
}
