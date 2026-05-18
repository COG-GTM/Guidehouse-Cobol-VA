# Devin Workflow

## Current Repo/Indexing State

- GitHub repository: `https://github.com/COG-GTM/Guidehouse-Cobol`
- Visibility: private
- Default branch: `main`
- Devin organization: `US Federal`
- Devin org id: `org-ebb0d579bbc740c2908d0ddaaca049cb`
- Repository indexed in Devin: `COG-GTM/Guidehouse-Cobol`
- Search index and Wiki index completed after initial push.

## Local Devin For Terminal

Use local Devin when you want the agent to operate on the checked-out repo on this machine.

```bash
cd ~/CascadeProjects/windsurf-project-3

devin auth status

devin -- "Review this repo and summarize the COBOL modernization demo story. Do not edit files."
```

Useful modes once inside the REPL:

```text
/plan          # planning mode; no edits until approved
/ask <prompt>  # one-off question
/model         # change model
/mode          # show current permission mode
```

For a single non-interactive response:

```bash
cd ~/CascadeProjects/windsurf-project-3
devin -p -- "List the highest-value next tasks for the Guidehouse COBOL demo."
```

## Cloud Devin / Remote Tasking

Local Devin for Terminal is the local CLI agent. Full cloud Devin sessions are launched through the Devin app or Devin API.

### Option A: Use The Devin App

1. Open `https://app.devin.ai`.
2. Switch to the `US Federal` org if needed.
3. Confirm `COG-GTM/Guidehouse-Cobol` appears under indexed repositories / Ask Devin / DeepWiki.
4. Start a new Devin session and reference `COG-GTM/Guidehouse-Cobol` in the prompt.
5. Use the starter prompts in `prompts/`.

### Option B: Use The Devin API From Terminal

Your current local environment has a legacy personal API key (`DEVIN_API_KEY`) scoped for the `US Federal` org. Use API v1 for user-attributed sessions with this key.

```bash
cd ~/CascadeProjects/windsurf-project-3
python3 scripts/create_devin_session.py prompts/initial-remote-analysis.md
```

The script prints the cloud Devin session id and URL. To add follow-up messages in the UI, open the URL and continue the conversation there.

If you later switch to a v3 service-user key (`cog_...`), use `DEVIN_ORG_ID=org-ebb0d579bbc740c2908d0ddaaca049cb` with the v3 sessions endpoint.

## DRS / Environment Blueprint

This repo includes `environment.yaml` as a repo-level Devin environment blueprint. The repo has no runtime install, so the blueprint mainly gives Devin persistent knowledge about the source layout, analysis commands, and demo constraints.

Verify DRS org context:

```bash
devin cloud drs whoami
```

Create or update the repo-scoped blueprint from this file:

```bash
devin cloud drs blueprint-create --repo COG-GTM/Guidehouse-Cobol --from-file environment.yaml
```

If the blueprint already exists, use the listed blueprint id:

```bash
devin cloud drs blueprint-list | grep -A3 Guidehouse-Cobol
devin cloud drs blueprint-write --blueprint-id <blueprint-id> --from-file environment.yaml
```

For sandbox setup testing:

```bash
devin cloud drs sandbox-create --repo COG-GTM/Guidehouse-Cobol --prompt "Validate repo setup for the Guidehouse COBOL modernization demo. Do not modify files."

devin cloud drs run --devin-id <devin-id> --command "find . -maxdepth 3 -type f | sort | head -80"
```

## Good First Remote Tasks

1. Ask Devin to refine `business-requirements/initial-requirements.md` with source line citations.
2. Ask Devin to generate `analysis/field-lineage.md` from `LABD20.pco` into table columns.
3. Ask Devin to produce a Python conversion sketch in `converted-code/python/` plus tests.
4. Ask Devin to extract parameterized SQL into `converted-code/sql/`.
5. Ask Devin to create a customer-facing demo script from `docs/demo-plan.md` and `docs/guidehouse-open-questions.md`.
