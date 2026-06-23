import { View, Text, ScrollView, Pressable } from "react-native";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";

export default function VideoScreen() {
  const { data: scripts } = useQuery({
    queryKey: ["scripts"],
    queryFn: () => api.scripts(20),
  });

  return (
    <View style={{ flex: 1, backgroundColor: "#05050a" }}>
      <View style={{ padding: 16, borderBottomWidth: 1, borderBottomColor: "rgba(255,255,255,0.05)" }}>
        <Text style={{ color: "#f8fafc", fontSize: 18, fontWeight: "bold" }}>AI Broadcasts</Text>
        <Text style={{ color: "#64748b", fontSize: 12, marginTop: 2 }}>AI-generated anchor video news</Text>
      </View>

      <ScrollView contentContainerStyle={{ padding: 12, gap: 12 }}>
        {(scripts || []).map((s: any) => (
          <View key={s.id} style={{ borderRadius: 16, overflow: "hidden", borderWidth: 1, borderColor: "rgba(255,255,255,0.05)" }}>
            {/* Video Thumbnail */}
            <View style={{ height: 180, backgroundColor: "#0f0f1e", justifyContent: "center", alignItems: "center" }}>
              <Text style={{ fontSize: 40, opacity: 0.2 }}>🤖</Text>
              <View style={{ position: "absolute", top: 8, left: 8, backgroundColor: "rgba(220,38,38,0.8)", borderRadius: 4, paddingHorizontal: 6, paddingVertical: 2 }}>
                <Text style={{ color: "#fff", fontSize: 8, fontWeight: "900" }}>AI BROADCAST</Text>
              </View>
              <View style={{ position: "absolute", bottom: 8, right: 8, backgroundColor: "rgba(0,0,0,0.6)", borderRadius: 4, paddingHorizontal: 6, paddingVertical: 2 }}>
                <Text style={{ color: "#94a3b8", fontSize: 9 }}>~{s.estimated_duration_seconds}s</Text>
              </View>
              {/* Play button overlay */}
              <View style={{ position: "absolute", width: 48, height: 48, borderRadius: 24, backgroundColor: "rgba(255,255,255,0.15)", justifyContent: "center", alignItems: "center" }}>
                <Text style={{ fontSize: 20 }}>▶</Text>
              </View>
            </View>

            {/* Info */}
            <View style={{ padding: 12, backgroundColor: "rgba(255,255,255,0.02)" }}>
              <Text style={{ color: "#f8fafc", fontSize: 13, fontWeight: "600", lineHeight: 18 }}>{s.headline}</Text>
              <View style={{ flexDirection: "row", gap: 8, marginTop: 6 }}>
                <Text style={{ color: "#818cf8", fontSize: 9, fontWeight: "700", textTransform: "uppercase" }}>{s.category}</Text>
                <Text style={{ color: "#475569", fontSize: 9 }}>{s.word_count_en} words</Text>
                <Text style={{ color: "#475569", fontSize: 9 }}>5 languages</Text>
              </View>
            </View>
          </View>
        ))}
      </ScrollView>
    </View>
  );
}
