# Factorio Optimizer

Object-flow based Factorio blueprint optimizer prototype.

## Current milestone

This repository starts with the smallest useful production challenge:

```text
iron plate input -> iron gear assembler -> iron gear output
```

The first implementation intentionally avoids random tile spam. It models a factory as objects and flows first, then validates, renders, scores, and exports the best plan as a Factorio blueprint string.

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

## Milestones

- 1A: Object-flow planner
- 1B: Static validator
- 1C: ASCII renderer
- 1D: Object-level mutations
- 1E: Basic fitness scoring
- 2A: Factorio blueprint string export

## Design principle

Do not optimize from chaos. Start with ugly-but-working factory plans and evolve them through meaningful object-level changes.
