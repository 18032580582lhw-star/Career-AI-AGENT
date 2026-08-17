from pathlib import Path
from typing import Final

from career_ai.models import FrozenModel
from career_ai.workflows.career_fit import run_career_fit_workflow
from career_ai.workflows.models import CareerFitWorkflowResult
from career_ai.workflows.quality import CareerQualityReport, assess_career_quality
from career_ai.workflows.run_record import (
    CareerFitRunRecord,
    RunInputSummary,
    RunQualityCheckRecord,
    new_run_id,
)

OPERATION: Final[str] = "career_fit_analysis"


class CareerFitRunResult(FrozenModel):
    """Typed result shared by CLI and eval callers."""

    workflow: CareerFitWorkflowResult
    quality: CareerQualityReport
    run_record: CareerFitRunRecord

    def for_public_output(self) -> "CareerFitRunResult":
        """Return the complete schema without source-derived free-text bodies."""
        report = self.workflow.report
        public_report = report.model_copy(
            update={
                "jd_analysis": report.jd_analysis.model_copy(update={"requirements": []}),
                "bullet_suggestions": [],
                "cover_letter_draft": "[REDACTED_GENERATED_TEXT]",
                "rewritten_resume": "[REDACTED_GENERATED_TEXT]",
            },
        )
        return self.model_copy(
            update={
                "workflow": self.workflow.model_copy(update={"report": public_report}),
            },
        )


class CareerFitApplicationService:
    """Run the deterministic career-fit use case."""

    def __init__(self, *, prompt_dir: Path) -> None:
        """Bind the prompt strategy directory used by each run."""
        self._prompt_dir: Path = prompt_dir

    def run(self, *, resume_text: str, jd_text: str) -> CareerFitRunResult:
        """Return workflow output, quality findings, and a safe audit record."""
        workflow = run_career_fit_workflow(
            resume_text=resume_text,
            jd_text=jd_text,
            prompt_dir=self._prompt_dir,
        )
        quality = assess_career_quality(
            workflow=workflow,
            resume_text=resume_text,
            jd_text=jd_text,
        )
        checks = [
            RunQualityCheckRecord(
                name=check.name,
                code=check.name,
                status="passed" if check.passed else "failed",
            )
            for check in quality.checks
        ]
        return CareerFitRunResult(
            workflow=workflow,
            quality=quality,
            run_record=CareerFitRunRecord(
                run_id=new_run_id(),
                operation=OPERATION,
                final_status="passed" if quality.passed else "failed-quality",
                input_summary=RunInputSummary.from_inputs(
                    resume_text=resume_text,
                    jd_text=jd_text,
                ),
                step_names=workflow.steps,
                quality_checks=checks,
            ),
        )
