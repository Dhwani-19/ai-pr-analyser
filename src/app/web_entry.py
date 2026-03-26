"""FastAPI web UI for PR risk analysis with GitHub App auth."""

from __future__ import annotations

import html
import os
import sys
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware

# Ensure `src` is on path when executed from repository root.
CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app.flow import PRRiskFlow  # noqa: E402
from app.auth.github_app import (  # noqa: E402
    build_user_oauth_url,
    create_installation_token,
    create_oauth_state,
    exchange_code_for_user_token,
    fetch_authenticated_user,
    list_installation_repositories,
    list_repository_pull_requests,
    list_user_installations,
)
from app.auth.session import (  # noqa: E402
    SESSION_LLM_API_KEY,
    SESSION_LLM_MODEL,
    SESSION_LLM_PROVIDER,
    SESSION_SELECTED_INSTALLATION,
    SESSION_USER_LOGIN,
    SESSION_USER_TOKEN,
    clear_auth_session,
    get_session_value,
    set_session_value,
)
from app.config import load_settings  # noqa: E402
from models.llm_models import LLMConfig  # noqa: E402

load_dotenv()

settings = load_settings()

app = FastAPI(title="PR Risk Analyzer UI")
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    same_site="lax",
    https_only=settings.session_https_only,
)

PROVIDER_MODEL_OPTIONS: dict[str, list[str]] = {
    "openai": [
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-5-mini",
        "gpt-5",
    ],
    "anthropic": [
        "claude-3-5-haiku-latest",
        "claude-3-5-sonnet-latest",
        "claude-3-7-sonnet-latest",
    ],
}


HTML_BASE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>PR Risk Analyzer</title>
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <style>
      :root {
        --bg: #f3f6f9;
        --ink: #101828;
        --muted: #667085;
        --surface: rgba(255, 255, 255, 0.92);
        --surface-strong: #ffffff;
        --line: #d8e0e7;
        --line-strong: #c3ced8;
        --primary: #0a6c5b;
        --primary-hover: #085646;
        --accent: #b7791f;
        --error: #9b2c2c;
        --ok: #1f7a4f;
        --shadow: 0 18px 42px rgba(16, 24, 40, 0.08);
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
        background:
          linear-gradient(180deg, rgba(10, 108, 91, 0.04), transparent 220px),
          linear-gradient(180deg, #f8fafc 0%, #f3f6f9 100%),
          var(--bg);
        color: var(--ink);
      }
      .app-shell {
        max-width: 1120px;
        margin: 0 auto;
        padding: 20px 20px 44px;
      }
      .topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 16px;
        margin-bottom: 16px;
        padding: 0 2px;
      }
      .brand {
        display: flex;
        align-items: center;
        gap: 14px;
      }
      .brand-mark {
        width: 40px;
        height: 40px;
        display: grid;
        place-items: center;
        border-radius: 12px;
        background: linear-gradient(135deg, #0a6c5b, #0d5a71);
        color: #f7fbfa;
        font-weight: 700;
        letter-spacing: 0.06em;
        box-shadow: 0 10px 20px rgba(10, 108, 91, 0.18);
      }
      .brand-copy h1 {
        margin: 0;
        font-size: 18px;
        font-weight: 700;
        letter-spacing: -0.02em;
      }
      .brand-copy p {
        margin: 4px 0 0;
        color: var(--muted);
        font-size: 13px;
      }
      .status-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        border: 1px solid var(--line-strong);
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.88);
        color: var(--muted);
        font-size: 12px;
        font-weight: 600;
      }
      .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: var(--ok);
      }
      .workspace {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 28px;
        box-shadow: var(--shadow);
      }
      h1 {
        margin: 0 0 10px;
        font-size: clamp(28px, 4vw, 38px);
        line-height: 1.05;
        letter-spacing: -0.04em;
      }
      h2 {
        margin: 0 0 10px;
        font-size: 24px;
        letter-spacing: -0.03em;
      }
      p.sub {
        max-width: 760px;
        margin: 0 0 24px;
        color: var(--muted);
        font-size: 16px;
        line-height: 1.6;
      }
      form {
        display: grid;
        gap: 14px;
      }
      .actions {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 18px;
      }
      label {
        font-size: 14px;
        color: var(--muted);
        font-weight: 600;
        display: block;
        margin-bottom: 8px;
      }
      input, select {
        width: 100%;
        border: 1px solid var(--line);
        border-radius: 14px;
        font-size: 15px;
        padding: 13px 14px;
        background: #fff;
        color: var(--ink);
      }
      input:focus, select:focus {
        outline: none;
        border-color: rgba(12, 107, 88, 0.42);
        box-shadow: 0 0 0 4px rgba(12, 107, 88, 0.1);
      }
      .form-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 16px;
      }
      button, .button {
        display: inline-block;
        border: none;
        border-radius: 999px;
        background: var(--primary);
        color: #fff;
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 0.01em;
        padding: 13px 18px;
        cursor: pointer;
        width: fit-content;
        text-decoration: none;
        box-shadow: 0 14px 28px rgba(12, 107, 88, 0.18);
        transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
      }
      button:hover, .button:hover {
        background: var(--primary-hover);
        transform: translateY(-1px);
        box-shadow: 0 18px 36px rgba(12, 107, 88, 0.22);
      }
      button[disabled] {
        opacity: 0.75;
        cursor: progress;
      }
      .button.secondary {
        background: #fff;
        color: var(--ink);
        border: 1px solid var(--line);
        box-shadow: none;
      }
      .status {
        margin-top: 18px;
        padding: 15px 16px;
        border-radius: 16px;
        font-size: 14px;
        line-height: 1.5;
      }
      .status.error {
        background: rgba(143, 45, 45, 0.08);
        color: var(--error);
        border: 1px solid rgba(143, 45, 45, 0.16);
      }
      .status.ok {
        background: rgba(27, 107, 70, 0.08);
        color: var(--ok);
        border: 1px solid rgba(27, 107, 70, 0.16);
      }
      .status.warning {
        background: rgba(183, 121, 31, 0.1);
        color: #8a5a16;
        border: 1px solid rgba(183, 121, 31, 0.24);
      }
      .loading-overlay {
        position: fixed;
        inset: 0;
        display: none;
        align-items: center;
        justify-content: center;
        background: rgba(12, 18, 24, 0.45);
        backdrop-filter: blur(4px);
        z-index: 999;
      }
      .loading-overlay.visible {
        display: flex;
      }
      .loading-panel {
        min-width: 280px;
        padding: 22px 24px;
        border-radius: 22px;
        background: #101820;
        color: #f8fafc;
        box-shadow: 0 18px 48px rgba(15, 23, 42, 0.35);
      }
      .loading-panel h2 {
        margin: 0 0 8px;
        font-size: 20px;
      }
      .loading-panel p {
        margin: 0;
        color: #cbd5e1;
      }
      .spinner {
        width: 42px;
        height: 42px;
        margin-bottom: 14px;
        border-radius: 999px;
        border: 4px solid rgba(255, 255, 255, 0.18);
        border-top-color: #f59e0b;
        animation: spin 0.8s linear infinite;
      }
      @keyframes spin {
        to { transform: rotate(360deg); }
      }
      .grid {
        margin-top: 18px;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 12px;
      }
      .metric {
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 16px;
        background: #fbfcfd;
      }
      .metric .label {
        font-size: 12px;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
      }
      .metric .value {
        margin-top: 8px;
        font-size: 28px;
        font-weight: 700;
        letter-spacing: -0.04em;
      }
      .section-title {
        margin-top: 24px;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        color: var(--muted);
      }
      .list {
        margin-top: 18px;
        display: grid;
        gap: 12px;
      }
      .list-item {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 18px;
        padding: 18px;
        border: 1px solid var(--line);
        border-radius: 16px;
        background: #fff;
      }
      .list-item.column {
        display: block;
      }
      .list-item h3 {
        margin: 0 0 6px;
        font-size: 20px;
        letter-spacing: -0.03em;
      }
      .meta {
        color: var(--muted);
        font-size: 14px;
        line-height: 1.55;
      }
      .hero {
        position: relative;
        padding: 0 0 10px;
      }
      .eyebrow {
        display: inline-block;
        margin-bottom: 16px;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(12, 107, 88, 0.1);
        color: var(--primary-hover);
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.14em;
      }
      .stats-row {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 220px));
        gap: 14px;
        margin-top: 18px;
      }
      .stat-card {
        padding: 16px;
        border: 1px solid var(--line);
        border-radius: 16px;
        background: #fbfcfd;
      }
      .stat-card strong {
        display: block;
        margin-bottom: 6px;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--muted);
      }
      .stat-card span {
        display: block;
        font-size: 26px;
        font-weight: 700;
        letter-spacing: -0.05em;
      }
      .summary-panel {
        margin-top: 24px;
        padding: 20px;
        border: 1px solid var(--line);
        border-radius: 16px;
        background: #fbfcfd;
      }
      .toolbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 14px;
        margin-bottom: 22px;
        padding-bottom: 18px;
        border-bottom: 1px solid var(--line);
      }
      .toolbar-title {
        min-width: 0;
      }
      .toolbar-title p {
        margin: 4px 0 0;
        color: var(--muted);
        font-size: 14px;
      }
      .context-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 12px;
        margin-bottom: 22px;
      }
      .context-card {
        padding: 16px;
        border: 1px solid var(--line);
        border-radius: 16px;
        background: #fbfcfd;
      }
      .context-card strong {
        display: block;
        margin-bottom: 6px;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--muted);
      }
      .context-card span {
        font-size: 15px;
        line-height: 1.55;
        color: var(--ink);
      }
      pre {
        margin: 10px 0 0;
        background: #fff;
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 14px 16px;
        white-space: pre-wrap;
        color: var(--ink);
        font-size: 14px;
        line-height: 1.65;
      }
      @media (max-width: 860px) {
        .app-shell {
          padding: 18px 14px 36px;
        }
        .workspace {
          padding: 22px 18px;
          border-radius: 22px;
        }
        .stats-row {
          grid-template-columns: 1fr;
        }
        .topbar {
          flex-direction: column;
          align-items: flex-start;
        }
        .list-item {
          flex-direction: column;
        }
      }
    </style>
  </head>
  <body>
    <div id="loading-overlay" class="loading-overlay" aria-hidden="true">
      <div class="loading-panel">
        <div class="spinner"></div>
        <h2>Analyzing PR</h2>
        <p>Fetching code, running analyzers, and generating the report.</p>
      </div>
    </div>
    <div class="app-shell">
      <div class="topbar">
        <div class="brand">
          <div class="brand-mark">PR</div>
          <div class="brand-copy">
            <h1>PR Risk Analyzer</h1>
            <p>Repository intelligence for high-signal pull request review.</p>
          </div>
        </div>
        <div class="status-chip">
          <span class="status-dot"></span>
          GitHub App Connected Workflow
        </div>
      </div>
      <main class="workspace">
        __BODY__
        __CONTENT__
      </main>
    </div>
    <script>
      const loadingOverlay = document.getElementById('loading-overlay');

      document.querySelectorAll('form[data-llm-config="true"]').forEach((form) => {
        const providerSelect = form.querySelector('select[name="provider"]');
        const modelSelect = form.querySelector('select[name="model"]');

        const modelOptions = {
          openai: ["gpt-4o-mini", "gpt-4o", "gpt-5-mini", "gpt-5"],
          anthropic: [
            "claude-3-5-haiku-latest",
            "claude-3-5-sonnet-latest",
            "claude-3-7-sonnet-latest"
          ]
        };

        const syncModelOptions = () => {
          if (!providerSelect || !modelSelect) return;
          const provider = providerSelect.value;
          const options = modelOptions[provider] || [];
          const previous = modelSelect.value;
          modelSelect.innerHTML = "";

          options.forEach((model) => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            if (model === previous) {
              option.selected = true;
            }
            modelSelect.appendChild(option);
          });

          if (!options.includes(previous) && options.length > 0) {
            modelSelect.value = options[0];
          }
        };

        if (providerSelect && modelSelect) {
          providerSelect.addEventListener('change', syncModelOptions);
          syncModelOptions();
        }

        form.addEventListener('submit', () => {
          const activeButton = form.querySelector('button[type="submit"]');
          if (activeButton) {
            activeButton.disabled = true;
            activeButton.textContent = 'Saving...';
          }
        });
      });

      document.querySelectorAll('form[action="/analyze"]').forEach((form) => {
        form.addEventListener('submit', () => {
          const activeButton = form.querySelector('button[type="submit"]');
          if (activeButton) {
            activeButton.disabled = true;
            activeButton.textContent = 'Analyzing...';
          }
          if (loadingOverlay) {
            loadingOverlay.classList.add('visible');
            loadingOverlay.setAttribute('aria-hidden', 'false');
          }
        });
      });
    </script>
  </body>
</html>
"""


FAVICON_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#8ad7d2" />
      <stop offset="100%" stop-color="#4aa7ac" />
    </linearGradient>
  </defs>
  <rect width="64" height="64" rx="16" fill="url(#bg)" />
  <circle cx="21" cy="22" r="11" fill="#ffffff" fill-opacity="0.92" />
  <path
    d="M18 15.5c-3.7 1.2-6.2 4.6-6.2 8.5 0 4.8 3.9 8.7 8.7 8.7 3.6 0 6.8-2.2 8.1-5.4h-4.1c-.9 1.1-2.3 1.8-4 1.8-2.8 0-5.1-2.3-5.1-5.1 0-2.2 1.4-4.1 3.4-4.8l-.8-3.7z"
    fill="#7b8794"
  />
  <path
    d="M24.1 14.7c2 .9 3.6 2.5 4.4 4.6h-4c-.5-.7-1.3-1.1-2.2-1.4l1.8-3.2z"
    fill="#7b8794"
  />
  <text
    x="40"
    y="38"
    text-anchor="middle"
    font-family="IBM Plex Sans, Segoe UI, sans-serif"
    font-size="24"
    font-weight="700"
    fill="#10232d"
  >PR</text>
</svg>
""".strip()


def _render_page(
    body: str,
    content: str = "",
) -> str:
    return (
        HTML_BASE.replace("__BODY__", body)
        .replace("__CONTENT__", content)
    )


def _landing_body() -> str:
    return f"""
    <div class="hero">
      <div class="eyebrow">Production Review Console</div>
      <h1>Risk-Focused Pull Request Analysis</h1>
      <p class="sub">Connect GitHub, set the analysis model once, and review pull requests through a cleaner operational workflow built around repository selection, PR triage, and report output.</p>
      <div class="actions">
        <a class="button" href="/auth/github/start">Connect GitHub</a>
        <a class="button secondary" href="{html.escape(settings.github_app_install_url, quote=True)}">Install GitHub App</a>
      </div>
      <div class="stats-row">
        <div class="stat-card">
          <strong>Signals</strong>
          <span>4</span>
        </div>
        <div class="stat-card">
          <strong>Access</strong>
          <span>Scoped</span>
        </div>
        <div class="stat-card">
          <strong>Mode</strong>
          <span>Review</span>
        </div>
      </div>
    </div>
    <div class="context-grid">
      <div class="context-card">
        <strong>Authentication</strong>
        <span>GitHub App OAuth with installation-scoped repository access.</span>
      </div>
      <div class="context-card">
        <strong>Output</strong>
        <span>Single report with score, review summary, and recommendation.</span>
      </div>
      <div class="context-card">
        <strong>Use Case</strong>
        <span>Pre-merge triage for higher-risk pull requests and busy review queues.</span>
      </div>
    </div>
    <div class="summary-panel">
      <div class="section-title">Required Access</div>
      <pre>Request read-only GitHub App permissions for Pull requests, Contents, and Metadata. The web flow is intended for scoped repository access and controlled rollout.</pre>
    </div>
    """


def _installations_body(user_login: str, installations_html: str) -> str:
    return f"""
    <div class="toolbar">
      <div class="toolbar-title">
        <div class="eyebrow">Step 1</div>
        <h2>Select Installation</h2>
        <p>Connected as {html.escape(user_login)}. Choose the installation that should grant repository visibility to this workspace.</p>
      </div>
    </div>
    <div class="actions">
      <a class="button secondary" href="{html.escape(settings.github_app_install_url, quote=True)}">Install On Another Repo</a>
      <a class="button secondary" href="/logout">Disconnect</a>
    </div>
    <div class="list">{installations_html}</div>
    """


def _llm_settings_body(
    user_login: str,
    *,
    provider: str,
    model: str,
    api_key: str,
) -> str:
    provider = provider if provider in PROVIDER_MODEL_OPTIONS else "openai"
    options = "".join(
        f'<option value="{html.escape(item, quote=True)}"{(" selected" if item == model else "")}>{html.escape(item)}</option>'
        for item in PROVIDER_MODEL_OPTIONS[provider]
    )
    api_key_field = (
        f"""
      <div>
        <label for="api_key">API Key</label>
        <input id="api_key" name="api_key" type="password" required value="{html.escape(api_key, quote=True)}" placeholder="Provider API key" />
      </div>
        """
        if settings.allow_user_supplied_llm_keys
        else """
      <div class="summary-panel">
        <div class="section-title">Credential Mode</div>
        <pre>Server-managed provider credentials are active for this hosted deployment. End users do not need to enter their own API keys.</pre>
      </div>
        """
    )
    return f"""
    <div class="toolbar">
      <div class="toolbar-title">
        <div class="eyebrow">Step 2</div>
        <h2>Configure Analysis Model</h2>
        <p>Connected as {html.escape(user_login)}. Set the model stack once for this session. That configuration stays active as you browse repositories and analyze pull requests.</p>
      </div>
    </div>
    <form method="post" action="/llm-settings" data-llm-config="true">
      <div class="form-grid">
        <div>
          <label for="provider">LLM Provider</label>
          <select id="provider" name="provider">
            <option value="openai"{(" selected" if provider == "openai" else "")}>OpenAI</option>
            <option value="anthropic"{(" selected" if provider == "anthropic" else "")}>Anthropic</option>
          </select>
        </div>
        <div>
          <label for="model">Model</label>
          <select id="model" name="model">
            {options}
          </select>
        </div>
      </div>
      {api_key_field}
      <div class="actions">
        <button type="submit">Continue To Repositories</button>
        <a class="button secondary" href="/installations">Back To Installations</a>
      </div>
    </form>
    """


def _repos_body(user_login: str, llm_summary: str, repos_html: str) -> str:
    return f"""
    <div class="toolbar">
      <div class="toolbar-title">
        <div class="eyebrow">Step 3</div>
        <h2>Select Repository</h2>
        <p>Signed in as {html.escape(user_login)}. Choose the repository you want to inspect with the current analysis configuration.</p>
      </div>
    </div>
    <div class="section-title">Active LLM</div>
    <pre>{html.escape(llm_summary)}</pre>
    <div class="actions">
      <a class="button secondary" href="/llm-settings">Change LLM</a>
      <a class="button secondary" href="/installations">Change Installation</a>
      <a class="button secondary" href="/logout">Disconnect</a>
    </div>
    <div class="list">{repos_html}</div>
    """


def _pulls_body(owner: str, repo: str, llm_summary: str, pulls_html: str) -> str:
    return f"""
    <div class="toolbar">
      <div class="toolbar-title">
        <div class="eyebrow">Review Queue</div>
        <h2>Choose Pull Request</h2>
        <p>Showing open pull requests for {html.escape(owner)}/{html.escape(repo)}. Select one to run the full risk analysis and generate a review summary.</p>
      </div>
    </div>
    <div class="section-title">Active LLM</div>
    <pre>{html.escape(llm_summary)}</pre>
    <div class="actions">
      <a class="button secondary" href="/llm-settings">Change LLM</a>
      <a class="button secondary" href="/repos">Back To Repositories</a>
    </div>
    <div class="list">{pulls_html}</div>
    """


def _installation_card(installation_id: int, account_login: str, account_type: str) -> str:
    return f"""
    <div class="list-item">
      <div>
        <h3>{html.escape(account_login)}</h3>
        <div class="meta">{html.escape(account_type)} installation available to this operator session.</div>
      </div>
      <form method="post" action="/installations/select">
        <input type="hidden" name="installation_id" value="{installation_id}" />
        <button type="submit">Use Installation</button>
      </form>
    </div>
    """


def _repo_card(full_name: str, private: bool) -> str:
    owner, repo = full_name.split("/", 1)
    visibility = "Private" if private else "Public"
    return f"""
    <div class="list-item">
      <div>
        <h3>{html.escape(full_name)}</h3>
        <div class="meta">{visibility} repository visible to the selected GitHub App installation.</div>
      </div>
      <a class="button" href="/repos/{html.escape(owner)}/{html.escape(repo)}">View Pull Requests</a>
    </div>
    """


def _pull_card(owner: str, repo: str, number: int, title: str, author: str, head_ref: str, updated_at: str) -> str:
    return f"""
    <div class="list-item">
      <div>
        <h3>#{number} {html.escape(title)}</h3>
        <div class="meta">Author: {html.escape(author)} | Branch: {html.escape(head_ref)} | Updated: {html.escape(updated_at)}</div>
      </div>
      <form method="post" action="/analyze">
        <input type="hidden" name="owner" value="{html.escape(owner, quote=True)}" />
        <input type="hidden" name="repo" value="{html.escape(repo, quote=True)}" />
        <input type="hidden" name="pr_number" value="{number}" />
        <button type="submit">Analyze</button>
      </form>
    </div>
    """


def _require_user_session(request) -> tuple[str, str]:
    user_token = get_session_value(request, SESSION_USER_TOKEN)
    user_login = get_session_value(request, SESSION_USER_LOGIN)
    if not user_token or not user_login:
        raise RuntimeError("GitHub session not found. Connect GitHub again.")
    return user_token, user_login


def _require_installation_id(request) -> int:
    installation_id = get_session_value(request, SESSION_SELECTED_INSTALLATION)
    if not installation_id:
        raise RuntimeError("Choose a GitHub App installation first.")
    return int(installation_id)


def _get_saved_llm_config(request: Request) -> LLMConfig | None:
    provider = get_session_value(request, SESSION_LLM_PROVIDER)
    model = get_session_value(request, SESSION_LLM_MODEL)
    api_key = get_session_value(request, SESSION_LLM_API_KEY)
    if not provider or not model or not api_key:
        return None
    return LLMConfig(provider=provider, model=model, api_key=api_key)


def _backend_api_key_for_provider(provider: str) -> str:
    if provider == "openai":
        return os.getenv("OPENAI_API_KEY", "").strip()
    if provider == "anthropic":
        return os.getenv("ANTHROPIC_API_KEY", "").strip()
    return ""


def _require_saved_llm_config(request: Request) -> LLMConfig:
    config = _get_saved_llm_config(request)
    if config is None:
        raise RuntimeError("Choose the LLM provider and model before selecting a repository.")
    return config


def _llm_summary_text(config: LLMConfig) -> str:
    return f"Provider: {config.provider.title()}\nModel: {config.model}\nSession scope: Active for repository and PR analysis"


def _report_summary_text(report) -> str:
    if report.llm_summary:
        return report.llm_summary
    return report.summary


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    return HTMLResponse(_render_page(_landing_body()))


@app.get("/favicon.svg")
def favicon_svg() -> Response:
    return Response(content=FAVICON_SVG, media_type="image/svg+xml")


@app.get("/favicon.ico")
def favicon_ico() -> RedirectResponse:
    return RedirectResponse("/favicon.svg", status_code=307)


@app.get("/healthz", response_class=HTMLResponse)
def healthz() -> HTMLResponse:
    return HTMLResponse("ok")


@app.get("/auth/github/start")
def auth_github_start(request: Request) -> RedirectResponse:
    state = create_oauth_state()
    set_session_value(request, "github_oauth_state", state)
    return RedirectResponse(build_user_oauth_url(settings, state), status_code=302)


@app.get("/auth/github/callback")
def auth_github_callback(request: Request, code: str, state: str) -> RedirectResponse:
    try:
        expected_state = get_session_value(request, "github_oauth_state")
        if not expected_state or state != expected_state:
            raise RuntimeError("GitHub login state mismatch. Start the sign-in flow again.")

        user_token = exchange_code_for_user_token(settings, code)
        user_login = fetch_authenticated_user(settings, user_token)
        installations = list_user_installations(settings, user_token)

        set_session_value(request, SESSION_USER_TOKEN, user_token)
        set_session_value(request, SESSION_USER_LOGIN, user_login)
        request.session.pop("github_oauth_state", None)

        if len(installations) == 1:
            set_session_value(request, SESSION_SELECTED_INSTALLATION, installations[0].installation_id)
            return RedirectResponse("/llm-settings", status_code=302)

        return RedirectResponse("/installations", status_code=302)
    except Exception as exc:
        return RedirectResponse(f"/installations?error={html.escape(str(exc), quote=True)}", status_code=302)


@app.get("/logout")
def logout(request: Request) -> RedirectResponse:
    clear_auth_session(request)
    return RedirectResponse("/", status_code=302)


@app.get("/installations", response_class=HTMLResponse)
def installations(request: Request, error: str = "") -> HTMLResponse:
    content = ""
    try:
        user_token, user_login = _require_user_session(request)
        installations = list_user_installations(settings, user_token)
        if not installations:
            content = (
                '<div class="status error">No GitHub App installations are available yet. '
                f'Install the app first: <a href="{html.escape(settings.github_app_install_url, quote=True)}">install app</a>.</div>'
            )
        elif error:
            content = f'<div class="status error">{html.escape(error)}</div>'

        installations_html = "".join(
            _installation_card(
                installation.installation_id,
                installation.account_login,
                installation.account_type,
            )
            for installation in installations
        )
        return HTMLResponse(_render_page(_installations_body(user_login, installations_html), content))
    except Exception as exc:
        return HTMLResponse(_render_page(_landing_body(), f'<div class="status error">{html.escape(str(exc))}</div>'), status_code=400)


@app.post("/installations/select")
def select_installation(request: Request, installation_id: int = Form(...)) -> RedirectResponse:
    set_session_value(request, SESSION_SELECTED_INSTALLATION, installation_id)
    return RedirectResponse("/llm-settings", status_code=302)


@app.get("/llm-settings", response_class=HTMLResponse)
def llm_settings(request: Request) -> HTMLResponse:
    try:
        _, user_login = _require_user_session(request)
        _require_installation_id(request)
        saved_config = _get_saved_llm_config(request)
        provider = saved_config.provider if saved_config else "openai"
        model = saved_config.model if saved_config else PROVIDER_MODEL_OPTIONS["openai"][0]
        api_key = saved_config.api_key if saved_config else ""
        if not settings.allow_user_supplied_llm_keys:
            api_key = ""
        return HTMLResponse(_render_page(_llm_settings_body(user_login, provider=provider, model=model, api_key=api_key)))
    except Exception as exc:
        return HTMLResponse(_render_page(_landing_body(), f'<div class="status error">{html.escape(str(exc))}</div>'), status_code=400)


@app.post("/llm-settings")
def save_llm_settings(
    request: Request,
    provider: str = Form(...),
    model: str = Form(...),
    api_key: str = Form(""),
) -> Response:
    try:
        resolved_api_key = api_key.strip()
        if not settings.allow_user_supplied_llm_keys:
            resolved_api_key = _backend_api_key_for_provider(provider)
            if not resolved_api_key:
                raise RuntimeError(
                    f"Missing backend API key for provider '{provider}'. Set the server environment first."
                )

        llm_config = LLMConfig(provider=provider, model=model, api_key=resolved_api_key)
        set_session_value(request, SESSION_LLM_PROVIDER, llm_config.provider)
        set_session_value(request, SESSION_LLM_MODEL, llm_config.model)
        set_session_value(request, SESSION_LLM_API_KEY, llm_config.api_key)
        return RedirectResponse("/repos", status_code=302)
    except Exception as exc:
        _, user_login = _require_user_session(request)
        return HTMLResponse(
            _render_page(
                _llm_settings_body(
                    user_login,
                    provider=provider,
                    model=model,
                    api_key="" if not settings.allow_user_supplied_llm_keys else api_key,
                ),
                f'<div class="status error">{html.escape(str(exc))}</div>',
            ),
            status_code=400,
        )


@app.get("/repos", response_class=HTMLResponse)
def repos(request: Request) -> HTMLResponse:
    try:
        _, user_login = _require_user_session(request)
        installation_id = _require_installation_id(request)
        llm_config = _require_saved_llm_config(request)
        installation_token = create_installation_token(settings, installation_id)
        repos = list_installation_repositories(settings, installation_token)
        repos_html = "".join(_repo_card(repo.full_name, repo.private) for repo in repos)
        return HTMLResponse(_render_page(_repos_body(user_login, _llm_summary_text(llm_config), repos_html)))
    except Exception as exc:
        return HTMLResponse(_render_page(_landing_body(), f'<div class="status error">{html.escape(str(exc))}</div>'), status_code=400)


@app.get("/repos/{owner}/{repo}", response_class=HTMLResponse)
def repo_pulls(request: Request, owner: str, repo: str) -> HTMLResponse:
    try:
        installation_id = _require_installation_id(request)
        llm_config = _require_saved_llm_config(request)
        installation_token = create_installation_token(settings, installation_id)
        pulls = list_repository_pull_requests(settings, installation_token, owner, repo)
        pulls_html = "".join(
            _pull_card(owner, repo, pull.number, pull.title, pull.author_login, pull.head_ref, pull.updated_at)
            for pull in pulls
        )
        if not pulls_html:
            pulls_html = '<div class="status ok">No open pull requests found for this repository.</div>'
        return HTMLResponse(_render_page(_pulls_body(owner, repo, _llm_summary_text(llm_config), pulls_html)))
    except Exception as exc:
        return HTMLResponse(_render_page(_landing_body(), f'<div class="status error">{html.escape(str(exc))}</div>'), status_code=400)


@app.post("/analyze", response_class=HTMLResponse)
def analyze(
    request: Request,
    owner: str = Form(...),
    repo: str = Form(...),
    pr_number: int = Form(...),
) -> HTMLResponse:
    try:
        installation_id = _require_installation_id(request)
        llm_config = _require_saved_llm_config(request)
        installation_token = create_installation_token(settings, installation_id)
        flow = PRRiskFlow()
        report = flow.run(
            repo=repo,
            owner=owner,
            pr_number=pr_number,
            github_token=installation_token,
            llm_config=llm_config,
        )

        body = _pulls_body(owner, repo, _llm_summary_text(llm_config), "")
        timeout_warning_html = (
            '<div class="status warning">Model-assisted analysis exceeded the time limit and was stopped. '
            "This result was completed using the deterministic analyzers.</div>"
            if report.llm_timed_out
            else ""
        )
        result_html = f"""
        <div class="status ok">Analysis completed for {html.escape(owner)}/{html.escape(repo)} PR #{pr_number}.</div>
        {timeout_warning_html}
        <div class="grid">
          <div class="metric"><div class="label">Overall Risk</div><div class="value">{report.overall_score} ({html.escape(report.risk_level)})</div></div>
          <div class="metric"><div class="label">Security</div><div class="value">{report.security_score:.2f}</div></div>
          <div class="metric"><div class="label">Complexity</div><div class="value">{report.complexity_score:.2f}</div></div>
          <div class="metric"><div class="label">AI Pattern</div><div class="value">{report.ai_pattern_score:.2f}</div></div>
          <div class="metric"><div class="label">Architectural</div><div class="value">{report.architectural_score:.2f}</div></div>
        </div>
        <div class="section-title">Summary</div>
        <pre>{html.escape(_report_summary_text(report))}</pre>
        <div class="section-title">Recommendation</div>
        <pre>{html.escape(report.recommendation)}</pre>
        """
        return HTMLResponse(_render_page(body, result_html))
    except Exception as exc:
        summary = ""
        saved = _get_saved_llm_config(request)
        if saved:
            summary = _llm_summary_text(saved)
        body = _pulls_body(owner, repo, summary, "")
        return HTMLResponse(_render_page(body, f'<div class="status error">{html.escape(str(exc))}</div>'), status_code=400)
