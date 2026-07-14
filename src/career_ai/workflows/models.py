from career_ai.models import CareerFitReport, FrozenModel, PromptHarnessResult


class CareerFitWorkflowResult(FrozenModel):
    """Complete deterministic career-fit workflow output."""

    report: CareerFitReport
    prompt_result: PromptHarnessResult
    steps: list[str]
