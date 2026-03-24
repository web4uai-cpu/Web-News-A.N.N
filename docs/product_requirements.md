# A.N.N. Product Requirements & Client Workflows

## Overview
The AI News Network (A.N.N.) serves two fundamentally different target audiences from a single centralized dashboard (Orbital Portal).

### 1. B2B Enterprise Client (News Aggregators, Developers, Trading Apps)
- **Objective:** Consume A.N.N.'s high-speed, fact-checked API feeds programmatically.
- **Interface Used:**
  - **Command Center:** To monitor heavy API quota limits (e.g., 100k requests/month).
  - **API Architect (Developer Tab):** To generate, view, and cycle secure `ann_sk_...` API keys and view HTTP/WebSocket documentation.
- **Output Generation:** Raw JSON, RSS, and Atom feeds via GET/WebSocket endpoints. No studio generation needed.

### 2. Social Media Creator (Influencers, Automated News Channels)
- **Objective:** Fully automate the creation and distribution of Avatar-based news videos.
- **Interface Used:**
  - **Social Auto-Pilot (Config Tab):** To securely input and link their `Instagram Access_Token`, `Facebook Page_ID`, and `LinkedIn Token`.
  - **Synthesis Engine (Studio Tab):** To input a prompt (e.g., "AI Market Crash").
- **Output Generation:** The system parses the prompt, scrapes news, generates an audio script, renders an MP4 Avatar video, and directly pushes it to their linked social profiles. 
