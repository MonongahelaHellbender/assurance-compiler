#!/usr/bin/env python3
"""
ledger_modelcard_demo.py — run a typical open-weights model-card safety argument
through the assurance-compiler and print the ADMIT / REFUSE / NEEDS-RULE ledger.

The claims below are ILLUSTRATIVE — paraphrased from the *kind* of safety and
capability language that appears in open-weights model cards ("evaluated on
benchmark X", "red-teamed", "safe for general use"). They are not quoted from,
or attributed to, any specific model or vendor. The point is not to single out a
card; it is to show what a fail-closed, eval-native checker does with prose
safety claims that ship WITHOUT machine-verified evidence controls attached.

To audit a real, named model card, replace `MODEL_CARD_CLAIMS` with that card's
claims and attach whichever evidence controls the card actually documents. What
is asserted-but-unverified fails closed (REFUSE); what has no rule is honest
about it (NEEDS-RULE); only claims backed by verified evidence ADMIT.

Run:  python3 ledger_modelcard_demo.py
"""
from assurance_compiler import Step, Evidence, compile_case, render

# A typical open-weights model-card safety argument, as prose claims map to
# (evidence-kind, claim-type). Evidence controls default to False (fail-closed):
# a model card that merely *states* a benchmark number attaches no verified
# gradeability / contamination / instrument / elicitation controls, so the
# checker treats each as an unrefuted defeater.
MODEL_CARD_CLAIMS = [
    Step(
        "\"Achieves 78% on a coding benchmark, demonstrating strong general coding capability.\"",
        Evidence("benchmark", source="model card, benchmark table", machine_verified=False),
        "general_capability",
    ),
    Step(
        "\"The model is safe for general-purpose deployment.\"",
        Evidence("benchmark", source="model card, safety section", machine_verified=False),
        "deployment_safety",
    ),
    Step(
        "\"Red-teaming found no capability to assist with dangerous tasks.\" (inability claim)",
        Evidence("benchmark", source="model card, red-team summary", machine_verified=False),
        "lacks_capability",
    ),
    Step(
        "\"The model is well-calibrated and reports uncertainty reliably.\"",
        Evidence("benchmark", source="model card, calibration note", machine_verified=False),
        "well_calibrated",
    ),
    Step(
        "\"Scored 78% on the published coding benchmark.\" (scoped to the benchmark itself)",
        Evidence("benchmark", source="model card, benchmark table", machine_verified=False),
        "benchmark_performance",
    ),
]

# The SAME calibration claim, but backed by a machine-verified honesty-atlas
# fingerprint (all controls asserted + re-verifiable). This is what "licensed
# as worded" actually requires — contrast it with the prose version above.
CALIBRATION_WITH_EVIDENCE = [
    Step(
        "\"Well-calibrated on fresh arithmetic-verification tasks (honesty-atlas fingerprint).\"",
        Evidence(
            "representative_eval",
            source="honesty-atlas fingerprint, fresh-instance oracle-graded",
            machine_verified=True,
            contamination_controlled=True,
            instrument_selftest_passed=True,
            failure_modes_classified=True,
            confidence_definition_stated=True,
        ),
        "well_calibrated",
    ),
]


def main():
    print("=" * 74)
    print("A · Typical open-weights model-card safety argument (prose claims)")
    print("=" * 74)
    print(render(compile_case(MODEL_CARD_CLAIMS)))
    print("\n" + "=" * 74)
    print("B · The same calibration claim, backed by machine-verified evidence")
    print("=" * 74)
    print(render(compile_case(CALIBRATION_WITH_EVIDENCE)))
    print(
        "\nReading: prose safety claims fail closed — not because they are false, but "
        "because\nthe evidence that would license the wording is not attached. Attach "
        "verified\nevidence (argument B) and the same claim is admitted. The verdict is "
        "deterministic\nand every refusal names its rule."
    )


if __name__ == "__main__":
    main()
