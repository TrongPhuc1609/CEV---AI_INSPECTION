# AI Agent Start Here

This is an existing multi-AI project.

## Mandatory
Read `PROJECT_CONTEXT.md` before coding.

Then inspect relevant source, tests, `docs/REAL_WORLD_VALIDATION_PLAN.md` and `data/physical_trial/README.md` before adding abstractions.

At the start of a task, identify:
- current baseline
- completed work
- current next task
- files likely to change
- acceptance criteria
- evidence class required: S (software), R (real-image replay), C (camera), M (motion/timing), or P (PLC/physical reject)

Workflow:
1. Create/use a feature branch.
2. Implement the smallest coherent change.
3. Add/update tests.
4. Run the test suite.
5. Update `PROJECT_CONTEXT.md` when project status/decisions change.
6. Commit with a meaningful message.
7. Push and open a Pull Request.

Never claim completion without a verified test/build result.
Never claim physical validation from software/CI evidence alone.
Never treat a real camera frame as production inspection evidence until it has ground truth and is evaluated through the acceptance process.
Never bypass Vision Adapter -> Observation -> Rule Engine -> Orchestrator.
Never hard-code product-specific rules.
