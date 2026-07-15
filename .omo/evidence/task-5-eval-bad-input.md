# Task 5 Evidence - Eval Bad Input Boundary

## Original Failure
Before the fix, a missing case directory returned success with Total cases: 0, and eval-matrix marked ake-default as passed with passed=0 failed=0.

## Fixed CLI Boundary
Command: career-ai-agent eval --case-dir <missing> --prompt-dir prompts

`	ext
Eval case directory does not exist: C:\Users\Sherlock 
Lee\AppData\Local\Temp\career-agent-eval-20260715-1215\missing-cases-after-fix

`

Observed exit code: 2

Command: career-ai-agent eval-matrix --case-dir <missing> --prompt-dir prompts

`	ext
Eval case directory does not exist: C:\Users\Sherlock 
Lee\AppData\Local\Temp\career-agent-eval-20260715-1215\missing-cases-after-fix

`

Observed exit code: 2

## Interpretation
Missing eval inputs now fail loudly and cannot be confused with a successful zero-case run.
