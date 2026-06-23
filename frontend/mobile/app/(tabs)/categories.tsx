import { View, Text, Pressable, ScrollView } from "react-native";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";

const CATEGORIES = [
  { key: "all", label: "All", emoji: "📰" },
  { key: "technology", label: "Tech", emoji: "💻" },
  { key: "business", label: "Business", emoji: "💼" },
  { key: "politics", label: "Politics", emoji: "🏛️" },
  { key: "finance", label: "Finance", emoji: "📈" },
  { key: "health", label: "Health", emoji: "🏥" },
  { key: "science", label: "Science", emoji: "🔬" },
  { key: "sports", label: "Sports", emoji: "⚽" },
  { key: "entertainment", label: "Fun", emoji: "🎬" },
  { key: "geopolitics", label: "World", emoji: "🌍" },
];

export default function CategoriesScreen() {
  const [active, setActive] = useState("all");
  const { data: scripts } = useQuery({
    queryKey: ["scripts"],
    queryFn: () => api.scripts(50),
  });

  const filtered = active === "all"
    ? scripts || []
    : (scripts || []).filter((s: any) => s.category === active);

  return (
    <View style={{ flex: 1, backgroundColor: "#05050a" }}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ maxHeight: 50, borderBottomWidth: 1, borderBottomColor: "rgba(255,255,255,0.05)" }} contentContainerStyle={{ paddingHorizontal: 12, gap: 6, alignItems: "center" }}>
        {CATEGORIES.map((cat) => (
          <Pressable
            key={cat.key}
            onPress={() => setActive(cat.key)}
            style={{
              paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20,
              backgroundColor: active === cat.key ? "rgba(129,140,248,0.15)" : "transparent",
            }}
          >
            <Text style={{ color: active === cat.key ? "#818cf8" : "#64748b", fontSize: 12, fontWeight: "600" }}>
              {cat.emoji} {cat.label}
            </Text>
          </Pressable>
        ))}
      </ScrollView>

      <ScrollView contentContainerStyle={{ padding: 12, gap: 8 }}>
        {filtered.map((s: any) => (
          <View key={s.id} style={{ backgroundColor: "rgba(255,255,255,0.02)", borderRadius: 10, padding: 12, borderWidth: 1, borderColor: "rgba(255,255,255,0.05)" }}>
            <Text style={{ color: "#818cf8", fontSize: 9, fontWeight: "700", textTransform: "uppercase" }}>{s.category}</Text>
            <Text style={{ color: "#f8fafc", fontSize: 13, fontWeight: "600", marginTop: 3 }}>{s.headline}</Text>
            <Text style={{ color: "#475569", fontSize: 10, marginTop: 4 }}>{s.word_count_en} words · ~{s.estimated_duration_seconds}s</Text>
          </View>
        ))}
        {filtered.length === 0 && (
          <Text style={{ color: "#64748b", textAlign: "center", marginTop: 40, fontSize: 13 }}>No stories in this category</Text>
        )}
      </ScrollView>
    </View>
  );
}
