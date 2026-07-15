# F3 Evidence - Real Manual QA

## Fresh GitHub Raw PowerShell Install
- Command: powershell.exe -NoProfile -ExecutionPolicy Bypass -File <raw install-agent.ps1> -RepoUrl https://github.com/18032580582lhw-star/Career-AI-AGENT.git -InstallRoot <temp> -Agent all
- Exit code: 0

### Key stdout
`	ext
Provider: fake
Workspace: PASS
Skill version: PASS
Passed cases: 3
Failed cases: 0
- fake-default: fake/local-fake status=passed passed=3 failed=0
`

### Key stderr
`	ext
powershell.exe : Cloning into 'C:\Users\Sherlock Lee\AppData\Local\Temp\career-agent-f3-raw-ps-20260715-1242\Career-AI-
AGENT'...
At line:10 char:1
+ powershell.exe -NoProfile -ExecutionPolicy Bypass -File $script -Repo ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (Cloning into 'C...er-AI-AGENT'...:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
`

## Streamlit Browser QA
- Evidence reused from this final debug run: .omo/evidence/task-7-streamlit-browser.md and .omo/evidence/task-7-streamlit-teardown.md.
- Playwright completed visible Prepare and Generate with API flow, no traceback, no page errors, no bad non-favicon responses, and port released after teardown.

## Cleanup
- Removed temp install root after writing this evidence.
