from pathlib import Path

from pydantic import Field

from career_ai.agent.executor import run_career_agent
from career_ai.evals.graders import EvalCaseResult, grade_case
from career_ai.evals.loader import load_eval_cases
from career_ai.llm.client import LLMClient
from career_ai.models import FrozenModel


class EvalSuiteResult(FrozenModel):
    """Aggregate result for a deterministic career eval suite run."""

    total_cases: int = Field(ge=0)
    passed_cases: int = Field(ge=0)
    failed_cases: int = Field(ge=0)
    case_results: list[EvalCaseResult] = Field(default_factory=list)


def run_eval_suite(
    *,
    case_dir: Path,
    prompt_dir: Path,
    llm_client: LLMClient,
) -> EvalSuiteResult:
    """Run every eval case through the agent harness and deterministic graders."""
    case_results: list[EvalCaseResult] = []
    for case in load_eval_cases(case_dir):
        agent_run = run_career_agent(
            resume_text=case.input.resume_text,
            jd_text=case.input.jd_text,
            prompt_dir=prompt_dir,
            llm_client=llm_client,
        )
        case_results.append(grade_case(case, agent_run.workflow))
    passed_cases = sum(1 for case_result in case_results if case_result.passed)
    total_cases = len(case_results)
    return EvalSuiteResult(
        total_cases=total_cases,
        passed_cases=passed_cases,
        failed_cases=total_cases - passed_cases,
        case_results=case_results,
    )


def collect_failed_check_messages(result: EvalSuiteResult) -> list[str]:
    """Return stable human-readable failed check messages for reports."""
    return [
        f"{case_result.case_id}:{check.name}: {check.message}"
        for case_result in result.case_results
        for check in case_result.checks
        if not check.passed
    ]
