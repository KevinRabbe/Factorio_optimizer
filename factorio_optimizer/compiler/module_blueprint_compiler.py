from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from factorio_optimizer.config.generation_config import GenerationConfig
from factorio_optimizer.core.objects import Position
from factorio_optimizer.expansion.module_graph_expander import expand_module_graph_to_blueprint_plan
from factorio_optimizer.export.blueprint_json_exporter import export_plan_to_blueprint_json
from factorio_optimizer.export.blueprint_string_encoder import encode_blueprint_string
from factorio_optimizer.modules.module_factory import create_module_for_recipe
from factorio_optimizer.render.ascii_renderer import render_ascii
from factorio_optimizer.validation.connection_validator import validate_module_connections
from factorio_optimizer.validation.recipe_validator import RecipeValidationSpec, validate_recipe_plan
from factorio_optimizer.validation.structure_validator import validate_plan_structure


@dataclass(frozen=True)
class ModuleBlueprintRequest:
    recipe_name: str
    era: str = "early"
    machine_name: str | None = None
    seed: int = 0


@dataclass(frozen=True)
class ModuleBlueprintReport:
    recipe_name: str
    module_id: str
    module_type: str
    machine_name: str | None
    width: int
    height: int
    structure_valid: bool
    recipe_valid: bool
    connection_valid: bool
    validation_errors: list[str]
    ascii: str
    blueprint_json: dict[str, Any]
    blueprint_string: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "recipe_name": self.recipe_name,
            "module_id": self.module_id,
            "module_type": self.module_type,
            "machine_name": self.machine_name,
            "width": self.width,
            "height": self.height,
            "structure_valid": self.structure_valid,
            "recipe_valid": self.recipe_valid,
            "connection_valid": self.connection_valid,
            "valid": self.structure_valid and self.recipe_valid and self.connection_valid,
            "validation_errors": self.validation_errors,
            "ascii": self.ascii,
            "blueprint_json": self.blueprint_json,
            "blueprint_string": self.blueprint_string,
        }


def compile_module_blueprint(request: ModuleBlueprintRequest) -> ModuleBlueprintReport:
    config = GenerationConfig(seed=request.seed, era=request.era)
    module = create_module_for_recipe(
        recipe_name=request.recipe_name,
        module_id=f"generated_{request.recipe_name}_module",
        origin=Position(0, 0),
        config=config,
        machine_name=request.machine_name,
    )

    width = module.footprint.width if module.footprint is not None else 12
    height = module.footprint.height if module.footprint is not None else 12
    plan = expand_module_graph_to_blueprint_plan(
        module=module,
        plan_id=f"generated_{request.recipe_name}_module_expanded",
        width=width,
        height=height,
    )

    output_item = module.output_rates[0].item if module.output_rates else request.recipe_name
    recipe_spec = RecipeValidationSpec(
        recipe=request.recipe_name,
        input_items=tuple(rate.item for rate in module.input_rates),
        output_item=output_item,
    )
    recipe_validation = validate_recipe_plan(plan, recipe_spec)
    structure_validation = validate_plan_structure(plan)
    connection_validation = validate_module_connections(module)
    validation_errors = [
        *structure_validation.errors,
        *recipe_validation.errors,
        *connection_validation.errors,
    ]

    blueprint_json = export_plan_to_blueprint_json(plan)
    blueprint_string = encode_blueprint_string(blueprint_json)

    return ModuleBlueprintReport(
        recipe_name=request.recipe_name,
        module_id=module.module_id,
        module_type=module.module_type,
        machine_name=module.machine_name,
        width=plan.width,
        height=plan.height,
        structure_valid=structure_validation.passed,
        recipe_valid=recipe_validation.passed,
        connection_valid=connection_validation.passed,
        validation_errors=validation_errors,
        ascii=render_ascii(plan),
        blueprint_json=blueprint_json,
        blueprint_string=blueprint_string,
    )
