# Task 8 Evidence - GitHub Raw Surface

## Scope

Plan: `.omo/plans/debug-stabilization.md`

Task: `8. Packaging Release Debug`

Scenario: raw release surface

## Commands

```powershell
Invoke-WebRequest -Uri <raw-url> -UseBasicParsing -TimeoutSec 30
```

## Results

```text
200 marker=True https://raw.githubusercontent.com/18032580582lhw-star/Career-AI-AGENT/main/docs/agent-install.md
200 marker=True https://raw.githubusercontent.com/18032580582lhw-star/Career-AI-AGENT/main/scripts/install-agent.ps1
200 marker=True https://raw.githubusercontent.com/18032580582lhw-star/Career-AI-AGENT/main/scripts/install-agent.sh
```

Markers checked:

- `docs/agent-install.md`: contains `Career-AI-AGENT`
- `scripts/install-agent.ps1`: contains `Invoke-Native`
- `scripts/install-agent.sh`: contains guarded `if "$candidate" --version >/dev/null 2>&1; then`

## Interpretation

GitHub raw release surface is live and contains the two installer hardening fixes rather than only returning HTTP 200.

## Cleanup

Raw requests created no local persistent artifacts. The temp packaging root was removed:

```text
PKG_ROOT_EXISTS_AFTER_CLEANUP=False
```
