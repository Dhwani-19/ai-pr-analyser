# PR Test Playbook

Use these files to open multiple test PRs and validate different risk outcomes.

## Baseline files

- `pr_test_pack/python/orders_service.py`
- `pr_test_pack/python/user_profile.py`
- `pr_test_pack/typescript/api_routes.ts`
- `pr_test_pack/typescript/formatters.ts`

## Case 1: Low-risk PR

Edit:
- Rename a variable for clarity in `user_profile.py`.
- Add a docstring line in `orders_service.py`.

Expected:
- LOW risk.
- Near-zero security and complexity changes.

## Case 2: Python security signals

Edit in `orders_service.py`:
- Add `import subprocess`.
- Add one helper that uses `subprocess.run(..., shell=True)`.

Expected:
- Higher Python `security_score`.
- Notes should mention suspicious imports and shell usage pattern.

## Case 3: Python complexity spike

Edit in `orders_service.py`:
- Add one large function with many nested `if` / `for` branches.

Expected:
- Higher Python `complexity_delta`.
- Usually MEDIUM risk or above when combined with other signals.

## Case 4: TypeScript unsafe patterns

Edit in `formatters.ts`:
- Introduce `as any`.
- Add an `eval(` usage (even in utility code).

Expected:
- Higher TypeScript `security_score`.
- Notes should mention unsafe TypeScript constructs.

## Case 5: TypeScript architecture impact

Edit in `api_routes.ts`:
- Add multiple route handlers: `app.post`, `app.put`, `app.delete`, `app.patch`.

Expected:
- Higher `architectural_impact` from route changes.
- Medium-to-high final score depending on other edits.

## Case 6: AI-pattern detection

Edit any file with a large diff:
- Use many generic names (`data`, `temp`, `value`, `result`, `item`).
- Add a very long comment line (more than 90 chars).
- Add repetitive blocks with repeated `if (...) { ... }`.
- Keep diff length large and avoid words like `None`, `null`, `undefined`, `except`, `catch`.

Expected:
- Higher `ai_pattern_score`.
- Note may include missing edge-case penalty.

## Case 7: High-risk combined PR

Single PR with all of:
- Python `shell=True` + suspicious import.
- Complex Python function.
- TypeScript `eval(` + `as any`.
- 3 to 5 new API routes.
- AI-style generic naming in a long diff.

Expected:
- HIGH risk likely.
- Strong signals across security, complexity, architecture, and AI pattern.

## Suggested PR sequence

1. PR-A: Case 1 only (control baseline).
2. PR-B: Case 2 only (security isolated).
3. PR-C: Case 5 only (architecture isolated).
4. PR-D: Case 6 only (AI-pattern isolated).
5. PR-E: Case 7 combined (stress test).
