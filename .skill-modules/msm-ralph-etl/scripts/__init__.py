"""Ralph ETL Coordinator — evidence-based ontology expansion pipeline."""

__version__ = "0.1.0"


def _register_all_steps() -> None:
    """Register all step handlers with the coordinator (lazy import)."""
    from ralph.coordinator import register_step
    from ralph.common import StepName

    from ralph.step_intake import run_intake
    from ralph.step_crawl import run_crawl
    from ralph.step_preprocess import run_preprocess
    from ralph.step_parse import run_parse
    from ralph.step_concept_map import run_concept_map
    from ralph.step_deduplicate import run_deduplicate
    from ralph.step_validate import run_validate
    from ralph.step_placement import run_placement as run_place
    from ralph.step_seal import run_seal

    register_step(StepName.A_INTAKE, run_intake)
    register_step(StepName.B_CRAWL, run_crawl)
    register_step(StepName.C_PREPROCESS, run_preprocess)
    register_step(StepName.D_PARSE, run_parse)
    # v0.1 new steps
    register_step(StepName.E_CONCEPT_MAP, run_concept_map)
    register_step(StepName.F_DEDUPLICATE, run_deduplicate)
    register_step(StepName.G_VALIDATE, run_validate)
    register_step(StepName.H_PLACE, run_place)
    register_step(StepName.I_SEAL, run_seal)
    # legacy aliases
    register_step(StepName.E_PLACE, run_place)
    register_step(StepName.F_SEAL, run_seal)
