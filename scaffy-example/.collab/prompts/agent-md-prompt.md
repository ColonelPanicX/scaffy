# Agent Instructions Generator

_Paste this into your AI agent after filling out `.collab/agent-profile.md`._

---

I've filled out `.collab/agent-profile.md` for this project.

Read it carefully and generate an agent instructions file in the project root.
Name it appropriately for the agent you are:

- Claude Code → `CLAUDE.md`
- OpenAI Codex / ChatGPT → `AGENTS.md`
- Gemini → `GEMINI.md`
- Other → use whatever instructions file your agent reads at session start

**Guidelines for the file you generate:**

- Keep it practical and concise — every line should matter in a working session
- Lead with a one-line project summary, then tech stack, then key commands
- Pull conventions and guardrails directly from the profile — don't invent details
- Format for skimmability: short sections, bullets, code blocks for commands
- If the profile is sparse or ambiguous on something important, ask before generating
