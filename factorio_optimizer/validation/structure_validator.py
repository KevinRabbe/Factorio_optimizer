from __future__ import annotations

from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.validation.blueprint_validator import (
    ValidationResult,
    validate_plan_structure as _validate_plan_structure,
)


def validate_plan_structure(plan: BlueprintPlan, check_placement: bool = True) -> ValidationResult:
    return _validate_plan_structure(plan, check_placement=check_placement)
