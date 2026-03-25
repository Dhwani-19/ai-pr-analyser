# ai-pr-risk-orchestrator

`ai-pr-risk-orchestrator` is a production-style open-source Python project that analyzes GitHub Pull Requests and generates a **PR Risk Intelligence Report** using a **CrewAI multi-agent orchestration model** with an **OpenAI-backed manager/agent runtime**.

## Problem Statement

AI-assisted coding tools increase PR volume, but review bandwidth does not scale at the same pace. Traditional PR bots often create noisy comments instead of actionable risk context.

This project focuses on **risk intelligence**, not comment spam:
- It analyzes PR metadata and diff content.
- It extracts structural and heuristic risk signals.
- It computes a normalized risk score.
- It outputs a report that helps teams prioritize human review.

## Architecture

```text
GitHub Pull Request Event
        |
        v
+---------------------------+
|      Flow Controller      |
|  (app/flow.py)            |
| - fetch PR metadata/diff  |
| - detect languages        |
| - parse diff chunks       |
| - execute crew            |
+---------------------------+
        |
        v
+---------------------------+
|      CrewAI Crew          |
|  (crews/pr_risk_crew.py)  |
|  Hierarchical process     |
|  Manager: Risk Aggregator |
+---------------------------+
        |
        v
+---------------------------+
|        Agents             |
| - Repo Context            |
| - Python Analyzer         |
| - TypeScript Analyzer     |
| - AI Pattern Detection    |
| - Risk Aggregator         |
+---------------------------+
        |
        v
+---------------------------+
|      Analysis Tools       |
|  AST + heuristics + score |
+---------------------------+
        |
        v
PR Risk Intelligence Report
```

## Project Structure

```text
ai-pr-risk-orchestrator/
├── src/
│   ├── app/
│   │   ├── flow.py
│   │   └── github_entry.py
│   ├── crews/
│   │   └── pr_risk_crew.py
│   ├── agents/
│   │   ├── repo_context_agent.py
│   │   ├── python_analyzer_agent.py
│   │   ├── typescript_analyzer_agent.py
│   │   ├── ai_pattern_agent.py
│   │   └── risk_manager_agent.py
│   ├── tools/
│   │   ├── github_tools.py
│   │   ├── diff_tools.py
│   │   ├── language_detector.py
│   │   ├── python_analysis_tools.py
│   │   ├── typescript_analysis_tools.py
│   │   ├── complexity_tools.py
│   │   └── risk_scoring_tool.py
│   └── models/
│       ├── pr_models.py
│       ├── signal_models.py
│       └── report_models.py
├── .github/workflows/pr_risk.yml
├── requirements.txt
└── README.md
```

## Local Run

1. Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Export runtime context:

```bash
export GITHUB_REPOSITORY="owner/repo"
export PR_NUMBER="123"
export GITHUB_TOKEN="<token>"
export ENABLE_CREWAI="true"
export OPENAI_API_KEY="<openai-api-key>"
export OPENAI_MODEL_NAME="gpt-5-mini"
```

3. Run analyzer:

```bash
python src/app/github_entry.py
```

4. Run web UI (GitHub App flow):

```bash
uvicorn src.app.web_entry:app --host 0.0.0.0 --port 8000
```

Then open `http://127.0.0.1:8000`, connect GitHub, choose an installation, select a repository, and analyze a pull request.

The web UI now lets the user choose:
- LLM provider: OpenAI or Anthropic
- model name
- provider API key

Those values are used for the CrewAI summary during the analysis request.

Additional environment required for the web flow:

```bash
export SESSION_SECRET="<long-random-secret>"
export GITHUB_APP_ID="<github-app-id>"
export GITHUB_CLIENT_ID="<github-app-client-id>"
export GITHUB_CLIENT_SECRET="<github-app-client-secret>"
export GITHUB_APP_PRIVATE_KEY="<github-app-private-key-with-\\n-escapes>"
export GITHUB_APP_NAME="<github-app-slug>"
```

If `ENABLE_CREWAI=true`, the app now creates real CrewAI `Agent` objects, injects a configured `crewai.LLM`, and executes `crew.kickoff(...)`. If the OpenAI configuration is missing while CrewAI is enabled, the run fails fast instead of silently falling back.

## Public Beta Notes

Before opening the web app to other users:
- Rotate any API keys that were ever committed or exposed in `.env`.
- Set `SESSION_HTTPS_ONLY=true` on the hosted deployment.
- Prefer `ALLOW_USER_SUPPLIED_LLM_KEYS=false` for a public beta, and configure provider keys on the server instead of asking users to paste their own keys.
- If you disable user-supplied keys, provide `OPENAI_API_KEY` and/or `ANTHROPIC_API_KEY` on the server.
- Change the GitHub App installation setting from `Only on this account` to `Any account` if external users need to install it.

## Docker Run

Build the image:

```bash
docker build -t pr-risk-analyzer .
```

Run locally:

```bash
docker run --rm -p 8000:8000 --env-file .env pr-risk-analyzer
```

## Koyeb Deployment

Recommended free-first setup:
- Deploy from GitHub using the included `Dockerfile`
- Service type: Web Service
- Instance: Free
- Expose port `8000` via `$PORT`

Koyeb environment variables to set:

```bash
SESSION_SECRET=<long-random-secret>
SESSION_HTTPS_ONLY=true
ALLOW_USER_SUPPLIED_LLM_KEYS=false
GITHUB_APP_ID=<github-app-id>
GITHUB_CLIENT_ID=<github-app-client-id>
GITHUB_CLIENT_SECRET=<github-app-client-secret>
GITHUB_APP_PRIVATE_KEY=<github-app-private-key-with-\n-escapes>
GITHUB_APP_NAME=<github-app-slug>
ENABLE_CREWAI=true
OPENAI_API_KEY=<optional-if-using-openai>
ANTHROPIC_API_KEY=<optional-if-using-anthropic>
```

After Koyeb gives you a public URL:
1. Update the GitHub App callback URL to `https://<your-koyeb-url>/auth/github/callback`
2. Verify the GitHub App can be installed by other users if needed
3. Test the full flow with a non-owner GitHub account before sharing the link

## GitHub Action Setup

The workflow is defined in `.github/workflows/pr_risk.yml` and triggers on PR `opened` and `synchronize` events.

Ensure repository Actions permissions allow PR read access and `GITHUB_TOKEN` is available (default in GitHub-hosted runners).

## Risk Scoring Formula

```text
risk_score =
  0.3  * security_score +
  0.25 * complexity_score +
  0.25 * ai_pattern_score +
  0.2  * architectural_score
```

Thresholds:
- `0-30`: LOW
- `31-70`: MEDIUM
- `71-100`: HIGH

## Extensibility Notes

The codebase is designed for easy extension with:
- GitHub App integration (webhook + auth layer)
- policy engine for team-specific gates
- cross-repo analytics pipeline
- enterprise plugin architecture

## Roadmap

- Add persisted signal store for longitudinal trend analysis.
- Add optional FastAPI service mode for GitHub App ingestion.
- Add richer semantic analysis prompts for manager agent.
- Add language packs for Java, Go, and Kotlin.
- Add test suite and benchmark fixtures for calibration.
