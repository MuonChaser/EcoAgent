#!/usr/bin/env python
"""
Full Research Pipeline - From natural language input to complete report
Usage: python run_research.py
"""
# Must load environment variables before all other imports!
from dotenv import load_dotenv
load_dotenv()

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from orchestrator import ResearchOrchestrator
from loguru import logger
from config.logging_config import setup_logger

# Configure logging
LOG_FILE = setup_logger("run_research")


def main():
    """Run the full research pipeline"""

    # User input
    user_input = "I want to study the impact of digital transformation on firm innovation performance"

    logger.info("=" * 80)
    logger.info("Starting Economics Research: AI for Econometrics")
    logger.info("=" * 80)
    logger.info(f"\nResearch Question: {user_input}\n")

    # Initialize orchestrator
    orchestrator = ResearchOrchestrator(output_dir="output/research")

    try:
        # Run full pipeline
        logger.info("Launching multi-agent research pipeline...\n")

        result = orchestrator.run_full_pipeline(
            user_input=user_input,
            enable_steps=[
                "input_parse",    # 0. Input parsing
                "literature",     # 1. Literature collection
                "variable",       # 2. Variable design
                "theory",         # 3. Theory design
                "model",          # 4. Model design
                # "analysis",     # 5. Data analysis (requires real data)
                # "report",       # 6. Report writing
            ],
            min_papers=8,         # Collect at least 8 papers
            enable_review=False,  # Review not enabled for now
        )

        # Output result summary
        logger.info("\n" + "=" * 80)
        logger.info("Research pipeline complete!")
        logger.info("=" * 80)

        logger.info(f"\nResearch Topic: {result.get('research_topic')}")

        if "input_parsed_data" in result:
            parsed = result["input_parsed_data"]
            logger.info(f"\nCore Variables:")
            logger.info(f"  - Explanatory Variable (X): {parsed.get('variable_x', {}).get('name')}")
            logger.info(f"  - Dependent Variable (Y): {parsed.get('variable_y', {}).get('name')}")

        if "literature_list" in result:
            lit_count = len(result["literature_list"])
            logger.info(f"\nLiterature Collection: {lit_count} core papers")

            if lit_count > 0:
                logger.info("\nFirst 3 papers:")
                for i, lit in enumerate(result["literature_list"][:3], 1):
                    logger.info(f"  {i}. {lit.get('title', 'N/A')}")
                    logger.info(f"     Authors: {lit.get('authors', 'N/A')} ({lit.get('year', 'N/A')})")
                    logger.info(f"     Journal: {lit.get('journal', 'N/A')}\n")

        if "variable_system_data" in result:
            var_data = result["variable_system_data"]
            logger.info("Variable System Design Complete:")

            core_vars = var_data.get("core_variables", {})
            x_vars = core_vars.get("explanatory_variable_x", [])
            y_vars = core_vars.get("dependent_variable_y", [])
            control_vars = var_data.get("control_variables", [])

            logger.info(f"  - Explanatory variables: {len(x_vars)}")
            logger.info(f"  - Dependent variables: {len(y_vars)}")
            logger.info(f"  - Control variables: {len(control_vars)}")

        if "theory_framework_data" in result:
            theory_data = result["theory_framework_data"]
            theories = theory_data.get("theoretical_framework", [])
            hypotheses = theory_data.get("research_hypotheses", [])

            logger.info(f"\nTheoretical Framework:")
            logger.info(f"  - Theories: {len(theories)}")
            logger.info(f"  - Hypotheses: {len(hypotheses)}")

            if hypotheses:
                logger.info("\nHypothesis examples:")
                for i, hyp in enumerate(hypotheses[:2], 1):
                    logger.info(f"  H{i}: {hyp.get('hypothesis_content', 'N/A')}")

        if "model_design_data" in result:
            model_data = result["model_design_data"]
            logger.info(f"\nEconometric Models:")

            baseline = model_data.get("baseline_model", {})
            logger.info(f"  - Baseline model: {baseline.get('model_type', 'N/A')}")

            mechanism = model_data.get("mechanism_models", [])
            heterogeneity = model_data.get("heterogeneity_models", [])
            robustness = model_data.get("robustness_checks", [])

            logger.info(f"  - Mechanism tests: {len(mechanism)} models")
            logger.info(f"  - Heterogeneity analysis: {len(heterogeneity)} dimensions")
            logger.info(f"  - Robustness checks: {len(robustness)} methods")

        # Output file locations
        logger.info("\n" + "=" * 80)
        logger.info("Output Files:")
        logger.info("=" * 80)
        logger.info("  - Full report: output/research/report_*.md")
        logger.info("  - JSON data: output/research/report_*.json")
        logger.info("  - Stage results: output/research/stages/*.json")

        logger.success("\nResearch pipeline completed successfully!")

        return result

    except Exception as e:
        logger.error(f"\nResearch pipeline error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
