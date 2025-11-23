# Project Context (Source of Truth)

**⚠️ CRITICAL FOR ALL AGENTS AND DEVELOPERS ⚠️**

This directory contains the **definitive** documentation for the PesuLabs Homelab project. If you find conflicting information elsewhere, **THIS FOLDER WINS.**

## 📚 Core Documentation

| Document | Description |
| :--- | :--- |
| [**ARCHITECTURE.md**](./ARCHITECTURE.md) | **Start Here.** System topology, hardware, software stack, and deployment strategy. |
| [**NETWORKING_STANDARD.md**](./NETWORKING_STANDARD.md) | **The Golden Rules.** How services talk to each other (Internal DNS) and the world (Ingress). |
| [**REPO_STRUCTURE.md**](./REPO_STRUCTURE.md) | Where to find code, manifests, and configs. |
| [**SERVICE_INVENTORY.md**](./SERVICE_INVENTORY.md) | List of all active services, their internal URLs, and ports. |
| [**AUTHENTIK_INTEGRATION.md**](./AUTHENTIK_INTEGRATION.md) | How to protect services with Single Sign-On. |
| [**LLAMACPP_CONFIGURATION.md**](./LLAMACPP_CONFIGURATION.md) | **AI Core.** llama.cpp LLM service with model switching, monitoring, and GPU acceleration. |
| [**SESSION-STATE.md**](./SESSION-STATE.md) | **The Living Memory.** A chronological log of sessions, decisions, and rationale. |

## 🧠 Session State Strategy

The `SESSION-STATE.md` file is our **long-term memory**. It is not just a status report; it is a **decision log**.

**For Agents:**
1.  **Start of Session**: Read the "Current Status" and the last entry in "Session Log" to understand where we left off and *why*.
2.  **During Session**: If you make a significant architectural decision (e.g., "Switching from Ollama to LlamaCpp"), note it down mentally.
3.  **End of Session**: Append a new entry to the "Session Log" using the template below.

**Template:**
```markdown
### [YYYY-MM-DD] [Time] - [Session Title]
**Goal**: [1-line goal]

#### 🧠 Decisions & Rationale
- **[Decision]**: [What changed?]
  - **Why**: [Context/Reasoning]
  - **Alternatives**: [What did we reject?]

#### 🛠️ Changes
- [Service/Component]: [Brief change summary]

#### 📝 Reflections
- [What worked/failed?]
```

If you are an AI agent joining this project, please read:
1.  `ARCHITECTURE.md` to understand the lay of the land.
2.  `NETWORKING_STANDARD.md` to avoid breaking connectivity.
3.  `REPO_STRUCTURE.md` to know where to write code.


