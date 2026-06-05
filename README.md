# Factorio Optimizer

Object-flow based Factorio blueprint optimizer prototype.

## Current milestone

This repository starts with the smallest useful production challenge:

```text
iron plate input -> iron gear assembler -> iron gear output
```

The first implementation intentionally avoids random tile spam. It models a factory as objects and flows first, then validates, renders, scores, and exports the best plan as a Factorio blueprint string.

## Setup

```bash
python -m pip install -e ".[dev]"
```

This installs the web runtime dependency (`Flask`) and the development test
dependency (`pytest`).

## Run

```bash
python main.py
```

Expected behavior:

1. Build an iron gear seed plan.
2. Generate object-level layout variants.
3. Validate each variant.
4. Render variants as ASCII.
5. Score variants.
6. Print the best pasteable Factorio blueprint string.

To run the web UI:

```bash
python server.py
```

Then open <http://127.0.0.1:5000>.

To use a different port:

```bash
python server.py --port 8080
```

## Test

```bash
python -m pytest
```

The legacy smoke scripts remain available under
`factorio_optimizer/dev_tests/`, but the automated suite lives in `tests/`.

## Milestones

- 1A: Object-flow planner
- 1B: Static validator
- 1C: ASCII renderer
- 1D: Object-level mutations
- 1E: Basic fitness scoring
- 2A: Factorio blueprint string export
- 3A: Pasteable green circuit block
- 3B: Pasteable red science block
- 4A: Vanilla mid-tier connected slices

## Design principle

Do not optimize from chaos. Start with ugly-but-working factory plans and evolve them through meaningful object-level changes.

## Pasteable blueprint generators

The web API includes practical blueprint generators with a consistent response
shape: `valid`, `validation_errors`, `validation_confidence`,
`blueprint_string`, `blueprint_json`, `ascii`, `summary`, `build_list`, and
`diagnostics`.

Available routes:

- `POST /api/generate-green-circuit-block`
- `POST /api/generate-red-science-block`
- `POST /api/generate-early-science-slice`
- `POST /api/generate-mid-block`
- `POST /api/generate-blue-science-slice`
- `POST /api/generate-mid-tier-slice`

The mid-tier roadmap targets vanilla Factorio through chemical science and
related mid-game intermediates. It intentionally excludes assembler 3, express
belts, beacons/modules, purple/yellow science, rockets, Space Age, and full oil
refinery planning. Fluid recipes currently use labeled external fluid inputs.
The mid-tier slice route chooses the best available shape: connected blue
science slice, connected early science slice, or a single reusable mid block.
