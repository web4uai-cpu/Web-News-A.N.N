import { View, Text, FlatList, Pressable, RefreshControl } from "react-native";
import { useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";

const CAT_COLORS: Record<string, string> = {
  technology: "#3b82f6", business: "#10b981", politics: "#f59e0b",
  finance: "#22d3ee", health: "#ec4899", science: "#a78bfa",
  sports: "#f97316", entertainment: "#e879f9", geopolitics: "#ef4444",
  general: "#6b7280",
};

export default function HomeScreen() {
  const router = useRouter();
  const { data: scripts, isLoading, refetch } = useQuery({
    queryKey: ["scripts"],
    queryFn: () => api.scripts(30),
    refetchInterval: 30000,
  });

  return (
    <View style={{ flex: 1, backgroundColor: "#05050a" }}>
      {/* Header */}
      <View style={{ padding: 16, borderBottomWidth: 1, borderBottomColor: "rgba(255,255,255,0.05)" }}>
        <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
          <View style={{ backgroundColor: "#dc2626", borderRadius: 6, paddingHorizontal: 8, paddingVertical: 4 }}>
            <Text style={{ color: "#fff", fontSize: 10, fontWeight: "900" }}>A.N.N.</Text>
          </View>
          <Text style={{ color: "#f8fafc", fontSize: 18, fontWeight: "bold" }}>AI News Network</Text>
          <View style={{ marginLeft: "auto", flexDirection: "row", alignItems: "center", gap: 4 }}>
            <View style={{ width: 6, height: 6, borderRadius: 3, backgroundColor: "#ef4444" }} />
            <Text style={{ color: "#ef4444", fontSize: 10, fontWeight: "800" }}>LIVE</Text>
          </View>
        </View>
      </View>

      {/* News Feed */}
      <FlatList
        data={scripts || []}
        keyExtractor={(item) => item.id}
        refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} tintColor="#818cf8" />}
        contentContainerStyle={{ padding: 12, gap: 10 }}
        renderItem={({ item }) => (
          <Pressable
            onPress={() => router.push(`/article/${item.id}`)}
            style={{
              backgroundColor: "rgba(255,255,255,0.02)",
              borderRadius: 12,
              borderWidth: 1,
              borderColor: "rgba(255,255,255,0.05)",
              overflow: "hidden",
            }}
          >
            <View style={{ height: 3, backgroundColor: CAT_COLORS[item.category] || "#6b7280" }} />
            <View style={{ padding: 14 }}>
              <Text style={{ color: CAT_COLORS[item.category] || "#6b7280", fontSize: 9, fontWeight: "700", textTransform: "uppercase", letterSpacing: 1 }}>
                {item.category}
              </Text>
              <Text style={{ color: "#f8fafc", fontSize: 14, fontWeight: "600", marginTop: 4, lineHeight: 20 }}>
                {item.headline}
              </Text>
              <Text style={{ color: "#64748b", fontSize: 12, marginTop: 6, lineHeight: 18 }} numberOfLines={2}>
                {item.english_script.replace(/\[PAUSE\]/g, "").substring(0, 150)}
              </Text>
              <View style={{ flexDirection: "row", gap: 12, marginTop: 8 }}>
                <Text style={{ color: "#475569", fontSize: 10 }}>{item.word_count_en} words</Text>
                <Text style={{ color: "#475569", fontSize: 10 }}>~{item.estimated_duration_seconds}s</Text>
              </View>
            </View>
          </Pressable>
        )}
        ListEmptyComponent={
          <View style={{ alignItems: "center", paddingVertical: 60 }}>
            <Text style={{ fontSize: 40 }}>📡</Text>
            <Text style={{ color: "#f8fafc", fontSize: 14, fontWeight: "600", marginTop: 12 }}>AI Newsroom Standing By</Text>
            <Text style={{ color: "#64748b", fontSize: 12, marginTop: 4 }}>Pull to refresh for latest broadcasts</Text>
          </View>
        }
      />
    </View>
  );
}
