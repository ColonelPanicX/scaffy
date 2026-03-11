# Context Build — Paste After First Onboarding

Use this prompt immediately after `00-onboard.md` to seed memory and context
before the first real work session begins.

---

Now that you have oriented to the project structure:

1. Read `.collab/context.md`. Note any fields that are empty or incomplete.

2. Initialize your project memory with the following stable facts (use whatever
   persistent memory mechanism your agent supports):
   - Project name and one-sentence description
   - Tech stack: languages, frameworks, key dependencies
   - Key file paths: entry points, config files, test directories
   - Naming and style conventions
   - Hard constraints or guardrails (e.g., "never commit credentials")

3. Report back to the user:
   - What you saved to memory
   - Which fields in `context.md` are empty and should be filled in before work begins

Do not start any work tasks until this step is complete.
