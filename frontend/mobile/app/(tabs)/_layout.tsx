import { Tabs } from "expo-router";

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarStyle: { backgroundColor: "#0a0a14", borderTopColor: "rgba(255,255,255,0.05)" },
        tabBarActiveTintColor: "#818cf8",
        tabBarInactiveTintColor: "#64748b",
        headerStyle: { backgroundColor: "#05050a" },
        headerTintColor: "#f8fafc",
      }}
    >
      <Tabs.Screen name="index" options={{ title: "Home", tabBarLabel: "Home" }} />
      <Tabs.Screen name="categories" options={{ title: "Categories", tabBarLabel: "Categories" }} />
      <Tabs.Screen name="video" options={{ title: "Broadcasts", tabBarLabel: "Video" }} />
      <Tabs.Screen name="settings" options={{ title: "Settings", tabBarLabel: "Settings" }} />
    </Tabs>
  );
}
