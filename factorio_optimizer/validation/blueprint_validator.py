from __future__ import annotations

from dataclasses import dataclass

from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.core.objects import Direction, FactoryObject, Position
from factorio_optimizer.data.entities import EntitySpec, entity_center, get_entity_spec
from factorio_optimizer.data.recipes import get_recipe


@dataclass(frozen=True)
class RecipeValidationSpec:
    recipe: str
    input_items: tuple[str, ...]
    output_item: str


class ValidationResult:
    def __init__(self) -> None:
        self.errors: list[str] = []

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def extend(self, other: "ValidationResult") -> None:
        self.errors.extend(other.errors)


@dataclass(frozen=True)
class ValidationConfidence:
    structure: ValidationResult
    placement: ValidationResult
    game_practical: ValidationResult

    @property
    def passed(self) -> bool:
        return self.structure.passed and self.placement.passed and self.game_practical.passed

    @property
    def errors(self) -> list[str]:
        return [
            *self.structure.errors,
            *self.placement.errors,
            *self.game_practical.errors,
        ]

    def to_dict(self) -> dict[str, object]:
        return {
            "structure": {
                "passed": self.structure.passed,
                "errors": self.structure.errors,
            },
            "placement": {
                "passed": self.placement.passed,
                "errors": self.placement.errors,
            },
            "game_practical": {
                "passed": self.game_practical.passed,
                "errors": self.game_practical.errors,
            },
            "passed": self.passed,
        }


_INTERFACE_TYPES = {"input_interface", "output_interface"}
_PHYSICAL_TYPES = {"assembler", "belt", "furnace", "inserter", "splitter", "pipe", "chemical_plant", "refinery", "lab"}
_PRODUCER_TYPES = {"assembler", "furnace", "chemical_plant", "refinery"}
_ENTITY_NAMES = {
    "belt": "transport-belt",
    "inserter": "inserter",
    "assembler": "assembling-machine-1",
    "furnace": "stone-furnace",
    "splitter": "splitter",
    "electric_pole": "small-electric-pole",
    "pipe": "pipe",
    "chemical_plant": "chemical-plant",
    "refinery": "oil-refinery",
    "lab": "lab",
}
_DIRECTION_DELTAS: dict[Direction, tuple[int, int]] = {
    "north": (0, -1),
    "east": (1, 0),
    "south": (0, 1),
    "west": (-1, 0),
}
_INSERTER_PICKUP_DELTAS: dict[Direction, tuple[int, int]] = {
    "north": (0, 1),
    "east": (-1, 0),
    "south": (0, -1),
    "west": (1, 0),
}
_INSERTER_DROPOFF_DELTAS: dict[Direction, tuple[int, int]] = {
    "north": (0, -1),
    "east": (1, 0),
    "south": (0, 1),
    "west": (-1, 0),
}


def validate_blueprint_plan(
    plan: BlueprintPlan,
    recipe_spec: RecipeValidationSpec | None = None,
    check_placement: bool = True,
) -> ValidationResult:
    confidence = validate_blueprint_confidence(plan, recipe_spec=recipe_spec)
    result = ValidationResult()
    result.extend(confidence.structure)
    if check_placement:
        result.extend(confidence.placement)
        result.extend(confidence.game_practical)
    return result


def validate_blueprint_confidence(
    plan: BlueprintPlan,
    recipe_spec: RecipeValidationSpec | None = None,
) -> ValidationConfidence:
    structure = ValidationResult()
    placement = ValidationResult()
    game_practical = ValidationResult()

    _validate_unique_object_ids(plan, structure)
    _validate_entity_metadata(plan, structure)
    _validate_bounds(plan, structure)
    _validate_overlaps(plan, structure)
    _validate_flows(plan, structure)
    if recipe_spec is not None:
        _validate_recipe(plan, recipe_spec, structure)
    _validate_belt_continuity(plan, placement)
    _validate_pipe_continuity(plan, placement)
    _validate_inserter_adjacency(plan, placement)
    _validate_power_coverage(plan, game_practical)
    return ValidationConfidence(
        structure=structure,
        placement=placement,
        game_practical=game_practical,
    )


def validate_plan_structure(plan: BlueprintPlan, check_placement: bool = True) -> ValidationResult:
    return validate_blueprint_plan(plan, check_placement=check_placement)


def validate_recipe_plan(plan: BlueprintPlan, spec: RecipeValidationSpec) -> ValidationResult:
    return validate_blueprint_plan(plan, recipe_spec=spec, check_placement=False)


def _validate_unique_object_ids(plan: BlueprintPlan, result: ValidationResult) -> None:
    seen: set[str] = set()
    for obj in plan.objects:
        if obj.object_id in seen:
            result.add_error(f"Duplicate object id: {obj.object_id}.")
        seen.add(obj.object_id)


def _validate_entity_metadata(plan: BlueprintPlan, result: ValidationResult) -> None:
    for obj in plan.objects:
        if obj.width < 1 or obj.height < 1:
            result.add_error(f"Object {obj.object_id} has invalid dimensions {obj.width}x{obj.height}.")
            continue
        entity_name = _entity_name_for_object(obj)
        if entity_name is None:
            continue
        try:
            spec = get_entity_spec(entity_name)
        except ValueError as exc:
            result.add_error(str(exc))
            continue
        if (obj.width, obj.height) != (spec.width, spec.height):
            result.add_error(
                f"Object {obj.object_id} footprint {obj.width}x{obj.height} "
                f"does not match {entity_name} footprint {spec.width}x{spec.height}."
            )
        if obj.recipe is not None and not spec.supports_recipe:
            result.add_error(f"Object {obj.object_id} cannot have recipe {obj.recipe}.")
            continue
        if obj.recipe is not None and spec.recipe_categories:
            try:
                recipe = get_recipe(obj.recipe)
            except ValueError as exc:
                result.add_error(str(exc))
                continue
            if recipe.category not in spec.recipe_categories:
                result.add_error(
                    f"Object {obj.object_id} cannot craft {obj.recipe} "
                    f"category {recipe.category}; {entity_name} supports {', '.join(spec.recipe_categories)}."
                )


def _validate_bounds(plan: BlueprintPlan, result: ValidationResult) -> None:
    for obj in plan.objects:
        for tile in obj.occupied_tiles():
            if tile.x < 0 or tile.y < 0 or tile.x >= plan.width or tile.y >= plan.height:
                result.add_error(
                    f"Object {obj.object_id} is outside grid at ({tile.x}, {tile.y})."
                )


def _validate_overlaps(plan: BlueprintPlan, result: ValidationResult) -> None:
    occupied: dict[Position, str] = {}
    for obj in plan.objects:
        if obj.object_type in _INTERFACE_TYPES:
            continue
        for tile in obj.occupied_tiles():
            if tile in occupied:
                result.add_error(
                    f"Overlap at ({tile.x}, {tile.y}): {occupied[tile]} and {obj.object_id}."
                )
            else:
                occupied[tile] = obj.object_id


def _validate_flows(plan: BlueprintPlan, result: ValidationResult) -> None:
    object_ids = {obj.object_id for obj in plan.objects}
    for flow in plan.flows:
        if flow.source_id not in object_ids:
            result.add_error(f"Flow {flow.flow_id} has unknown source {flow.source_id}.")
        if flow.target_id not in object_ids:
            result.add_error(f"Flow {flow.flow_id} has unknown target {flow.target_id}.")
        if not flow.path:
            result.add_error(f"Flow {flow.flow_id} has empty path.")
        for pos in flow.path:
            if pos.x < 0 or pos.y < 0 or pos.x >= plan.width or pos.y >= plan.height:
                result.add_error(f"Flow {flow.flow_id} path leaves grid at ({pos.x}, {pos.y}).")


def _validate_recipe(plan: BlueprintPlan, spec: RecipeValidationSpec, result: ValidationResult) -> None:
    if not any(obj.object_type in _PRODUCER_TYPES and obj.recipe == spec.recipe for obj in plan.objects):
        result.add_error(f"Missing producer with recipe {spec.recipe}.")
    for item in spec.input_items:
        if not any(obj.object_type == "input_interface" and obj.item == item for obj in plan.objects):
            result.add_error(f"Missing input interface for {item}.")
    if not any(obj.object_type == "output_interface" and obj.item == spec.output_item for obj in plan.objects):
        result.add_error(f"Missing output interface for {spec.output_item}.")
    flow_items = {flow.item for flow in plan.flows}
    for item in spec.input_items:
        if item not in flow_items:
            result.add_error(f"Missing flow for input item {item}.")
    if spec.output_item not in flow_items:
        result.add_error(f"Missing flow for output item {spec.output_item}.")


def _validate_belt_continuity(plan: BlueprintPlan, result: ValidationResult) -> None:
    belts = [obj for obj in plan.objects if obj.object_type == "belt"]
    belt_positions = {obj.position for obj in belts}
    for belt in belts:
        if belt.role in {"input_lane_endpoint", "output_lane_endpoint"}:
            continue
        dx, dy = _DIRECTION_DELTAS[belt.direction]
        next_position = Position(belt.position.x + dx, belt.position.y + dy)
        if _has_same_item_belt_at(belts, next_position, belt.item):
            continue
        if _has_physical_object_at(plan.objects, next_position, allowed_types={"inserter", "splitter", "assembler", "furnace", "chemical_plant", "refinery", "lab"}):
            continue
        if _is_at_plan_edge(belt.position, belt.direction, plan):
            continue
        if _has_any_flow_endpoint_near(plan, belt.position):
            continue
        if next_position not in belt_positions:
            result.add_error(
                f"Belt {belt.object_id} has no forward continuation or receiver at ({next_position.x}, {next_position.y})."
            )


def _validate_pipe_continuity(plan: BlueprintPlan, result: ValidationResult) -> None:
    pipes = [obj for obj in plan.objects if obj.object_type == "pipe"]
    pipe_positions = {obj.position for obj in pipes}
    for pipe in pipes:
        neighbor_positions = [
            Position(pipe.position.x + dx, pipe.position.y + dy)
            for dx, dy in _DIRECTION_DELTAS.values()
        ]
        if any(neighbor in pipe_positions for neighbor in neighbor_positions):
            continue
        if any(
            _has_physical_object_at(
                plan.objects,
                neighbor,
                allowed_types={"chemical_plant", "refinery", "assembler"},
            )
            for neighbor in neighbor_positions
        ):
            continue
        if _is_at_any_plan_edge(pipe.position, plan):
            continue
        result.add_error(f"Pipe {pipe.object_id} has no adjacent pipe, fluid machine, or blueprint edge.")


def _validate_inserter_adjacency(plan: BlueprintPlan, result: ValidationResult) -> None:
    physical_objects = [obj for obj in plan.objects if obj.object_type in _PHYSICAL_TYPES and obj.object_type != "inserter"]
    for inserter in [obj for obj in plan.objects if obj.object_type == "inserter"]:
        pickup = _offset(inserter.position, _INSERTER_PICKUP_DELTAS[inserter.direction])
        dropoff = _offset(inserter.position, _INSERTER_DROPOFF_DELTAS[inserter.direction])
        if not _has_physical_object_covering(physical_objects, pickup) and not _has_flow_path_at(plan, pickup, inserter.item):
            result.add_error(f"Inserter {inserter.object_id} has no pickup target at ({pickup.x}, {pickup.y}).")
        if not _has_physical_object_covering(physical_objects, dropoff) and not _has_flow_path_at(plan, dropoff, inserter.item):
            result.add_error(f"Inserter {inserter.object_id} has no dropoff target at ({dropoff.x}, {dropoff.y}).")


def _validate_power_coverage(plan: BlueprintPlan, result: ValidationResult) -> None:
    poles = [
        (obj, get_entity_spec(_entity_name_for_object(obj) or "small-electric-pole"))
        for obj in plan.objects
        if obj.object_type == "electric_pole"
    ]
    for obj in plan.objects:
        entity_name = _entity_name_for_object(obj)
        if entity_name is None:
            continue
        try:
            spec = get_entity_spec(entity_name)
        except ValueError:
            continue
        if not spec.requires_power or obj.object_type not in _PRODUCER_TYPES | {"lab"}:
            continue
        if not _is_powered_by_any_pole(obj, poles):
            result.add_error(f"Object {obj.object_id} requires power but is not covered by an electric pole.")


def _has_same_item_belt_at(belts: list[FactoryObject], position: Position, item: str | None) -> bool:
    return any(belt.position == position and belt.item == item for belt in belts)


def _has_physical_object_at(
    objects: list[FactoryObject],
    position: Position,
    allowed_types: set[str],
) -> bool:
    return any(obj.object_type in allowed_types and position in obj.occupied_tiles() for obj in objects)


def _has_physical_object_covering(objects: list[FactoryObject], position: Position) -> bool:
    return any(position in obj.occupied_tiles() for obj in objects)


def _has_any_flow_endpoint_near(plan: BlueprintPlan, position: Position) -> bool:
    endpoint_ids = {flow.source_id for flow in plan.flows} | {flow.target_id for flow in plan.flows}
    for obj in plan.objects:
        if obj.object_id in endpoint_ids and _is_adjacent_or_same(position, obj):
            return True
    return False


def _has_flow_path_at(plan: BlueprintPlan, position: Position, item: str | None) -> bool:
    return any(flow.item == item and position in flow.path for flow in plan.flows)


def _is_adjacent_or_same(position: Position, obj: FactoryObject) -> bool:
    for tile in obj.occupied_tiles():
        if abs(tile.x - position.x) + abs(tile.y - position.y) <= 1:
            return True
    return False


def _is_at_plan_edge(position: Position, direction: Direction, plan: BlueprintPlan) -> bool:
    return (
        direction == "north" and position.y == 0
        or direction == "east" and position.x == plan.width - 1
        or direction == "south" and position.y == plan.height - 1
        or direction == "west" and position.x == 0
    )


def _is_at_any_plan_edge(position: Position, plan: BlueprintPlan) -> bool:
    return position.x in {0, plan.width - 1} or position.y in {0, plan.height - 1}


def _offset(position: Position, delta: tuple[int, int]) -> Position:
    return Position(position.x + delta[0], position.y + delta[1])


def _entity_name_for_object(obj: FactoryObject) -> str | None:
    if obj.object_type in _INTERFACE_TYPES:
        return None
    return obj.entity_name or _ENTITY_NAMES.get(obj.object_type)


def _is_powered_by_any_pole(
    obj: FactoryObject,
    poles: list[tuple[FactoryObject, EntitySpec]],
) -> bool:
    obj_center_x, obj_center_y = entity_center(obj.position.x, obj.position.y, obj.width, obj.height)
    for pole, spec in poles:
        pole_center_x, pole_center_y = entity_center(
            pole.position.x,
            pole.position.y,
            pole.width,
            pole.height,
        )
        if (
            abs(obj_center_x - pole_center_x) <= spec.supply_area_distance
            and abs(obj_center_y - pole_center_y) <= spec.supply_area_distance
        ):
            return True
    return False
