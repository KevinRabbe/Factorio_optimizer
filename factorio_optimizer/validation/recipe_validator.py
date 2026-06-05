from __future__ import annotations

from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.validation.blueprint_validator import (
    RecipeValidationSpec,
    ValidationResult,
    validate_recipe_plan as _validate_recipe_plan,
)


def validate_recipe_plan(plan: BlueprintPlan, spec: RecipeValidationSpec) -> ValidationResult:
    return _validate_recipe_plan(plan, spec)
