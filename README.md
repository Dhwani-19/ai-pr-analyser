# ai-pr-risk-orchestrator

`ai-pr-risk-orchestrator` is a production-style open-source Python project that analyzes GitHub Pull Requests and generates a **PR Risk Intelligence Report** using a **CrewAI multi-agent orchestration model**.

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
```

3. Run analyzer:

```bash
python src/app/github_entry.py
```

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
