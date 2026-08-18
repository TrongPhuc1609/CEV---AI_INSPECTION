# Contributing

## Mandatory first step
Read `PROJECT_CONTEXT.md`.

## Workflow
1. `git pull --rebase`
2. Read project context and inspect source/tests.
3. Create `feature/<short-description>`.
4. Make a small coherent change.
5. Add/update tests.
6. Run tests.
7. Update project context if status/decisions changed.
8. Commit and push.
9. Open a Pull Request.
10. Review before merge.

## Commit format
`<area>: <change>`

Examples: `rules: add Rule.cmd v1 parser`, `orchestrator: consume InspectionPlan`, `vision: add RT-DETR adapter`.

## Architecture protection
Do not bypass Vision Adapter -> Observation -> Rule Engine -> Region Result -> Orchestrator.
Do not hard-code product-specific inspection rules.
Major architecture changes require a decision record in `PROJECT_CONTEXT.md`.
