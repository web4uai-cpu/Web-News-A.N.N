import { View, Text, Switch, Pressable } from "react-native";
import { useState } from "react";

export default function SettingsScreen() {
  const [pushEnabled, setPushEnabled] = useState(true);
  const [breakingAlerts, setBreakingAlerts] = useState(true);
  const [language, setLanguage] = useState("en");
  const [darkMode, setDarkMode] = useState(true);

  const languages = [
    { code: "en", label: "English" },
    { code: "hi", label: "हिन्दी" },
    { code: "es", label: "Español" },
    { code: "fr", label: "Français" },
    { code: "ar", label: "العربية" },
  ];

  return (
    <View style={{ flex: 1, backgroundColor: "#05050a", padding: 16 }}>
      <Text style={{ color: "#f8fafc", fontSize: 18, fontWeight: "bold", marginBottom: 20 }}>Settings</Text>

      {/* Notifications */}
      <Text style={{ color: "#818cf8", fontSize: 10, fontWeight: "800", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 12 }}>Notifications</Text>

      <SettingRow label="Push Notifications" value={pushEnabled} onToggle={setPushEnabled} />
      <SettingRow label="Breaking News Alerts" value={breakingAlerts} onToggle={setBreakingAlerts} />

      {/* Language */}
      <Text style={{ color: "#818cf8", fontSize: 10, fontWeight: "800", textTransform: "uppercase", letterSpacing: 1.5, marginTop: 24, marginBottom: 12 }}>Language</Text>

      <View style={{ gap: 6 }}>
        {languages.map((lang) => (
          <Pressable
            key={lang.code}
            onPress={() => setLanguage(lang.code)}
            style={{
              flexDirection: "row", justifyContent: "space-between", alignItems: "center",
              padding: 14, borderRadius: 10, borderWidth: 1,
              borderColor: language === lang.code ? "#818cf8" : "rgba(255,255,255,0.05)",
              backgroundColor: language === lang.code ? "rgba(129,140,248,0.1)" : "rgba(255,255,255,0.02)",
            }}
          >
            <Text style={{ color: "#f8fafc", fontSize: 14 }}>{lang.label}</Text>
            {language === lang.code && <Text style={{ color: "#818cf8", fontSize: 12 }}>✓</Text>}
          </Pressable>
        ))}
      </View>

      {/* App Info */}
      <Text style={{ color: "#818cf8", fontSize: 10, fontWeight: "800", textTransform: "uppercase", letterSpacing: 1.5, marginTop: 24, marginBottom: 12 }}>About</Text>

      <View style={{ backgroundColor: "rgba(255,255,255,0.02)", borderRadius: 10, padding: 14, borderWidth: 1, borderColor: "rgba(255,255,255,0.05)" }}>
        <Text style={{ color: "#f8fafc", fontSize: 14, fontWeight: "600" }}>A.N.N. — AI News Network</Text>
        <Text style={{ color: "#64748b", fontSize: 11, marginTop: 4 }}>Version 1.0.0</Text>
        <Text style={{ color: "#64748b", fontSize: 11, marginTop: 2 }}>10 AI Agents · Zero Humans · 24/7</Text>
      </View>
    </View>
  );
}

function SettingRow({ label, value, onToggle }: { label: string; value: boolean; onToggle: (v: boolean) => void }) {
  return (
    <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: "rgba(255,255,255,0.03)" }}>
      <Text style={{ color: "#f8fafc", fontSize: 14 }}>{label}</Text>
      <Switch value={value} onValueChange={onToggle} trackColor={{ true: "#818cf8", false: "#334155" }} thumbColor="#f8fafc" />
    </View>
  );
}
