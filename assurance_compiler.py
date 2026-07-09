#!/usr/bin/env python3
"""
Assurance Compiler v0.1 (Lane 3) — a deterministic, fail-closed checker for frontier-AI
EVALUATION claims inside safety-case arguments. (PRIVATE build.)

Positioning (see LANE3_POSITIONING.md): CLARISSA/Assurance 2.0 already machine-check assurance-
argument STRUCTURE over HUMAN-ASSERTED evidence. This tool is the open, eval-native descendant:
it checks whether each argument step's CLAIM is licensed by its EVIDENCE, where evidence nodes can
be MACHINE-VERIFIED (outputs of self-validating instruments), under named EVAL-NATIVE DEFEATERS
that traditional assurance tools have no vocabulary for. Fail-closed; zero LLM in the verdict path.
NOT "the first machine-checkable safety case" — CLARISSA has that priority. The contribution is the
combination: eval-native defeaters + machine-verified evidence + coverage denominator + open/det.

Vocabulary bridge to Assurance 2.0:  ADMIT = sustained claim · REFUSE = active (unrefuted)
defeater · NEEDS_RULE = unsupported / missing warrant.

Prior art & differentiation (cite before publishing):
  * "Toward Pre-Deployment Assurance for Enterprise AI Agents" (arXiv:2606.04037) issues a Trust
    Certificate with GRADUATED verdicts (Approved / Conditional / Rejected) for agent deployment.
    Structurally adjacent to this tool's verdict spine, but the axis differs: it grades an agent's
    deployment readiness; this grades whether an EVALUATION CLAIM is licensed by its evidence. Ours
    is one-directional & fail-closed (NEEDS_RULE default; a defeater must be AFFIRMATIVELY refuted,
    never assumed), eval-native (defeaters specific to evaluation evidence), over machine-verified
    evidence nodes, with a declared coverage denominator. Not a competitor — a different unit of
    assurance (the claim, not the agent).
  * Disclosure & currency defeaters below operationalize STREAM (arXiv:2508.09853, reporting
    transparency) and dynamic safety cases (arXiv:2412.17618, continual re-validation).

Layers:
  1. reuse claim_compiler.check for the generic evidence→claim type rules (benchmark→deployment, …)
  2. add EVAL-NATIVE DEFEATERS: named threats specific to *evaluation evidence* — a claim is
     REFUSED if any attached defeater is active (unrefuted), even if its evidence→claim type is ok.
  3. an ARGUMENT is a list of STEPS; compile() returns a per-step ledger + a COVERAGE DENOMINATOR.

Run:  python3 assurance_compiler.py --selftest      # fail-closed gate (must pass before trust)
      python3 assurance_compiler.py --demo          # worked example ledger
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field

import claim_compiler as cc


# ============================================================================================
# EVAL-NATIVE DEFEATERS — the contestable product. Each is a named threat to an EVALUATION
# claim; it is either refuted (by a stated condition being met) or ACTIVE (claim fails closed).
# Sources cited so the rules are contestable data, not the engine's opinion.
# ============================================================================================
@dataclass
class Defeater:
    id: str
    question: str          # the doubt this defeater raises
    refuted_when: str      # the condition (a fact the argument must assert) that refutes it
    source: str            # where the threat is documented
    refutes_field: str     # the evidence-node field whose truthiness refutes this defeater


DEFEATERS = {
    "gradeability": Defeater(
        "gradeability",
        "Is the benchmark actually gradeable — are its gold labels correct and its items well-posed?",
        "evidence.gradeability_verified is True (a deterministic gradeability audit passed)",
        "gradeability-audit (trust-denominator: fraction of a benchmark that is soundly gradeable)",
        "gradeability_verified"),
    "contamination": Defeater(
        "contamination",
        "Could the eval instances be in the model's training data (memorized, not solved)?",
        "evidence.contamination_controlled is True (fresh/held-out/generated-at-runtime instances)",
        "honesty-atlas fresh-instance generation; contamination literature",
        "contamination_controlled"),
    "instrument_validity": Defeater(
        "instrument_validity",
        "Is the measuring instrument itself valid — does it distinguish the states it claims to?",
        "evidence.instrument_selftest_passed is True (a fail-closed harness selftest passed)",
        "honesty-atlas 14/14 selftest; 'Screen Before You Interpret' arXiv:2604.17714",
        "instrument_selftest_passed"),
    "abstention_semantics": Defeater(
        "abstention_semantics",
        "Is 'abstention' real, or is silence (truncation / refusal / error) being scored as honesty?",
        "evidence.failure_modes_classified is True (OK/ABSTAIN/BUDGET_EXCEEDED/REFUSAL distinguished)",
        "honesty-atlas classified-failure design (structural vs verbal abstention, 2026-07-02)",
        "failure_modes_classified"),
    "confidence_definition": Defeater(
        "confidence_definition",
        "Does the 'confidence' measured match the confidence the claim is about (verbalized vs "
        "self-consistency vs logit)?",
        "evidence.confidence_definition_stated is True (the confidence signal is named + matched)",
        "honesty-atlas confidence-definition caveat; calibration literature",
        "confidence_definition_stated"),
    "elicitation_gap": Defeater(
        "elicitation_gap",
        "Was capability properly elicited — could better prompting/tools/fine-tuning beat the eval "
        "(sandbagging / under-elicitation)?",
        "evidence.elicitation_documented is True (elicitation protocol + adversarial fine-tuning "
        "stated)",
        "GovAI cyber-inability template (2411.08088); scheming-eval safety-case work (2411.03336)",
        "elicitation_documented"),
    "threshold_validity": Defeater(
        "threshold_validity",
        "Is the pass/fail threshold justified, or is it an arbitrary line?",
        "evidence.threshold_justified is True (the capability threshold is derived, not asserted)",
        "GovAI cyber-inability template (2411.08088)",
        "threshold_justified"),
    "behavioural_limit": Defeater(
        "behavioural_limit",
        "Is this a property behavioural evidence CAN reach at all (not a latent/long-horizon "
        "property like hidden objectives or loss-of-control)?",
        "evidence.property_is_behavioural is True (the claim is about observable behaviour, not "
        "latent structure)",
        "'Behavioural Assurance Cannot Verify...' arXiv:2605.15164 (the audit gap)",
        "property_is_behavioural"),
    "stream_disclosure": Defeater(
        "stream_disclosure",
        "Does the report DISCLOSE the methodology a reader needs to trust the number — elicitation, "
        "prompts/scaffold, sample size + statistical treatment, contamination controls?",
        "evidence.stream_fields_disclosed is True (the STREAM-required reporting fields are present)",
        "STREAM: Standard for Transparently Reporting Evaluations in AI Model Reports (arXiv:2508.09853)",
        "stream_fields_disclosed"),
    "evidence_staleness": Defeater(
        "evidence_staleness",
        "Is the evidence CURRENT for the deployed model/version, or does it predate the checkpoint or "
        "context it is being used to assure (a safety case must be continually re-validated)?",
        "evidence.current_for_deployed_version is True (the eval targets the deployed artifact, within "
        "a stated staleness horizon)",
        "Dynamic safety cases for frontier AI (arXiv:2412.17618)",
        "current_for_deployed_version"),
    "baseline_comparison": Defeater(
        "baseline_comparison",
        "Is a marginal-capability claim measured against NAMED baselines (weaker models / existing "
        "tools), or asserted in the abstract?",
        "evidence.baseline_named is True (specific baseline models or tools are named + tested)",
        "Anthropic jailbreak-severity framework (capability-gain-over-baseline); the "
        "coverage-denominator discipline",
        "baseline_named"),
    "external_validation": Defeater(
        "external_validation",
        "Was the claim independently validated by a NAMED third party, or only self-asserted?",
        "evidence.externally_validated is True (a named independent evaluator tested it)",
        "third-party AI audit literature (Stanford HAI); CAISI-style external red-team",
        "externally_validated"),
    "scope_discipline": Defeater(
        "scope_discipline",
        "Is a negative/absence claim properly SCOPED (e.g. 'none FOUND, as of DATE, under TESTS X'), "
        "or overstated as 'none exist'?",
        "evidence.scope_stated is True (the claim names its time bound and test scope, and claims "
        "absence-of-evidence not proof-of-absence)",
        "safety-case absence-argument discipline; AbstentionBench 2506.09038",
        "scope_stated"),
}

# which defeaters MUST be addressed for a given claim category (fail-closed: unlisted-but-attached
# defeaters still fire; these are the MINIMUM set the checker demands for the category).
REQUIRED_DEFEATERS = {
    "GENERAL_CAPABILITY": ["gradeability", "contamination", "instrument_validity", "elicitation_gap",
                           "stream_disclosure"],
    "DEPLOYMENT_SAFETY": ["gradeability", "contamination", "instrument_validity", "elicitation_gap",
                          "threshold_validity", "behavioural_limit", "stream_disclosure",
                          "evidence_staleness"],
    "CALIBRATION": ["instrument_validity", "abstention_semantics", "confidence_definition",
                    "contamination"],
    "INABILITY": ["elicitation_gap", "threshold_validity", "contamination", "behavioural_limit",
                  "stream_disclosure", "evidence_staleness"],
    # safety-announcement / system-card rule pack: each credits a specific careful discipline
    # marginal-capability / uplift claims: the defining disciplines are a NAMED baseline + proper
    # elicitation. contamination is a fixed-BENCHMARK concern, not a blanket requirement here — raise
    # it as an extra_defeater when the capability claim rests on a memorizable benchmark.
    "CAPABILITY_GAIN": ["baseline_comparison", "elicitation_gap"],
    "EXTERNAL_VALIDATION": ["external_validation", "threshold_validity"],
    "SAFEGUARD_EFFICACY": ["instrument_validity", "contamination", "threshold_validity"],
    "SCOPED_NEGATIVE": ["scope_discipline", "elicitation_gap"],
}
# claim-type → category, for eval-native claims not in claim_compiler's CLAIM_CAT
EVAL_CLAIM_CAT = {
    "well_calibrated": "CALIBRATION", "honest": "CALIBRATION", "knows_what_it_doesnt_know": "CALIBRATION",
    "lacks_capability": "INABILITY", "cannot_do_X": "INABILITY", "safe_incapable": "INABILITY",
    "general_capability": "GENERAL_CAPABILITY", "deployment_safety": "DEPLOYMENT_SAFETY",
    # safety-announcement / system-card claim types
    "no_unique_capability": "CAPABILITY_GAIN", "capability_bounded_by_baseline": "CAPABILITY_GAIN",
    "independently_validated": "EXTERNAL_VALIDATION", "safeguards_validated": "EXTERNAL_VALIDATION",
    "safeguard_blocks_technique": "SAFEGUARD_EFFICACY", "safeguard_efficacy": "SAFEGUARD_EFFICACY",
    "no_universal_jailbreak_found": "SCOPED_NEGATIVE", "none_found_in_scope": "SCOPED_NEGATIVE",
}
# type-level rules for the eval-native claim categories the base engine doesn't know
# (well_calibrated / lacks_capability). Defeaters do the substantive work; this only checks the
# evidence is the right KIND of thing (a measurement, not a simulation or a single anecdote).
EVAL_TYPE_RULES = {
    ("REPRESENTATIVE_EVAL", "CALIBRATION"): cc.V.ADMIT,
    ("BENCHMARK", "CALIBRATION"): cc.V.ADMIT,
    ("REPRESENTATIVE_EVAL", "INABILITY"): cc.V.ADMIT,
    ("BENCHMARK", "INABILITY"): cc.V.ADMIT,
    ("SINGLE_INSTANCE", "CALIBRATION"): cc.V.REFUSE,
    ("SINGLE_INSTANCE", "INABILITY"): cc.V.REFUSE,
    ("COMPUTATIONAL", "CALIBRATION"): cc.V.REFUSE,
    ("COMPUTATIONAL", "INABILITY"): cc.V.REFUSE,
    # safety-announcement / system-card rule pack — a report/eval is the right KIND of thing;
    # the defeaters (named baselines, external validation, scope discipline, threshold) do the work
    ("BENCHMARK", "CAPABILITY_GAIN"): cc.V.ADMIT,
    ("REPRESENTATIVE_EVAL", "CAPABILITY_GAIN"): cc.V.ADMIT,
    ("SINGLE_INSTANCE", "CAPABILITY_GAIN"): cc.V.REFUSE,
    ("BENCHMARK", "EXTERNAL_VALIDATION"): cc.V.ADMIT,
    ("REPRESENTATIVE_EVAL", "EXTERNAL_VALIDATION"): cc.V.ADMIT,
    ("BENCHMARK", "SAFEGUARD_EFFICACY"): cc.V.ADMIT,
    ("REPRESENTATIVE_EVAL", "SAFEGUARD_EFFICACY"): cc.V.ADMIT,
    ("COMPUTATIONAL", "SAFEGUARD_EFFICACY"): cc.V.REFUSE,
    ("BENCHMARK", "SCOPED_NEGATIVE"): cc.V.ADMIT,
    ("REPRESENTATIVE_EVAL", "SCOPED_NEGATIVE"): cc.V.ADMIT,
    ("SINGLE_INSTANCE", "SCOPED_NEGATIVE"): cc.V.REFUSE,
}


def _type_check(kind: str, claim: str):
    """Return (verdict, reason). Eval-native claims use EVAL_TYPE_RULES; everything else defers to
    the base claim_compiler engine (which owns benchmark→deployment, single_example→general, …)."""
    if claim in EVAL_CLAIM_CAT and claim not in cc.CLAIM_CAT:
        ec = cc.EVIDENCE_CAT.get(kind)
        ccat = EVAL_CLAIM_CAT[claim]
        v = EVAL_TYPE_RULES.get((ec, ccat))
        if v:
            return v, f"eval-type rule {ec}->{ccat}"
        return cc.V.NEEDS_RULE, (f"no eval-type rule for {ec or ('untyped evidence ' + kind)}->{ccat}")
    r = cc.check(kind, claim)
    return r.verdict, r.reason


@dataclass
class Evidence:
    """A machine-verifiable evidence node. Booleans default False = fail-closed: an unstated
    control is treated as an ACTIVE defeater, never assumed satisfied."""
    kind: str                                   # claim_compiler evidence type, e.g. "benchmark"
    source: str = ""                            # human-readable provenance
    machine_verified: bool = False              # is this the output of a self-validating instrument?
    gradeability_verified: bool = False
    contamination_controlled: bool = False
    instrument_selftest_passed: bool = False
    failure_modes_classified: bool = False
    confidence_definition_stated: bool = False
    elicitation_documented: bool = False
    threshold_justified: bool = False
    property_is_behavioural: bool = False
    stream_fields_disclosed: bool = False       # STREAM reporting fields present (arXiv:2508.09853)
    current_for_deployed_version: bool = False  # eval targets the deployed artifact (dynamic safety case)
    baseline_named: bool = False                # marginal-capability claim names its baselines
    externally_validated: bool = False          # a named third party independently tested it
    scope_stated: bool = False                  # a negative claim names its time/test bound


@dataclass
class Step:
    name: str
    evidence: Evidence
    claim: str                                  # claim_compiler / eval claim type
    extra_defeaters: list = field(default_factory=list)   # explicitly-raised additional doubts


@dataclass
class StepResult:
    step: str
    verdict: cc.V
    type_verdict: cc.V
    active_defeaters: list
    reason: str
    machine_verified: bool


def _claim_cat(claim: str) -> str | None:
    return EVAL_CLAIM_CAT.get(claim) or cc.CLAIM_CAT.get(claim)


def check_step(step: Step) -> StepResult:
    """Fail-closed: REFUSE if the evidence→claim type rule refuses OR any required/raised defeater
    is active. ADMIT only if the type rule admits AND every applicable defeater is refuted."""
    tv, treason = _type_check(step.evidence.kind, step.claim)
    cat = _claim_cat(step.claim)
    required = list(REQUIRED_DEFEATERS.get(cat, []))
    for d in step.extra_defeaters:                        # explicitly-raised doubts always apply
        if d not in required:
            required.append(d)

    active = []
    for did in required:
        d = DEFEATERS.get(did)
        if d is None:
            active.append((did, "unknown defeater id — cannot be refuted"))
            continue
        if not getattr(step.evidence, d.refutes_field, False):
            active.append((did, d.question))

    # resolution (fail-closed: a type error OR any active defeater ⇒ REFUSE)
    if tv is cc.V.REFUSE:
        return StepResult(step.name, cc.V.REFUSE, tv, active,
                          f"type error: {treason}", step.evidence.machine_verified)
    if active:
        note = f"{len(active)} active defeater(s): " + "; ".join(a[0] for a in active)
        if tv is cc.V.NEEDS_RULE:
            note += f" (type coverage also incomplete: {treason})"
        return StepResult(step.name, cc.V.REFUSE, tv, active, note,
                          step.evidence.machine_verified)
    if tv is cc.V.NEEDS_RULE:
        return StepResult(step.name, cc.V.NEEDS_RULE, tv, [],
                          treason, step.evidence.machine_verified)
    return StepResult(step.name, cc.V.ADMIT, tv, [],
                      "type rule admits and all applicable defeaters refuted",
                      step.evidence.machine_verified)


@dataclass
class Ledger:
    results: list
    def counts(self):
        c = {v: 0 for v in cc.V}
        for r in self.results:
            c[r.verdict] += 1
        return c
    def coverage(self):
        n = len(self.results)
        mv = sum(1 for r in self.results if r.machine_verified)
        admitted = sum(1 for r in self.results if r.verdict is cc.V.ADMIT)
        return dict(total=n, admitted=admitted, machine_verified_evidence=mv,
                    refused=sum(1 for r in self.results if r.verdict is cc.V.REFUSE),
                    needs_rule=sum(1 for r in self.results if r.verdict is cc.V.NEEDS_RULE))


def compile_case(steps: list) -> Ledger:
    return Ledger([check_step(s) for s in steps])


def render(ledger: Ledger) -> str:
    out = ["ASSURANCE LEDGER", "=" * 72]
    icon = {cc.V.ADMIT: "ADMIT ", cc.V.REFUSE: "REFUSE", cc.V.NEEDS_RULE: "NEEDS "}
    for r in ledger.results:
        mv = " [machine-verified evidence]" if r.machine_verified else " [human-asserted]"
        out.append(f"[{icon[r.verdict]}] {r.step}{mv}")
        out.append(f"          {r.reason}")
        for did, q in r.active_defeaters:
            out.append(f"          ✗ defeater ACTIVE: {did} — {q}")
    cov = ledger.coverage()
    out += ["-" * 72,
            f"coverage: {cov['admitted']}/{cov['total']} claims licensed as worded · "
            f"{cov['refused']} refused · {cov['needs_rule']} needs-rule · "
            f"{cov['machine_verified_evidence']}/{cov['total']} backed by machine-verified evidence"]
    return "\n".join(out)


# ============================================================================================
# FAIL-CLOSED SELFTEST — the instrument must prove itself before any real case is trusted.
# Gold cases: each MUST land on the stated verdict, incl. planted overclaims that MUST refuse.
# ============================================================================================
def _ev(**kw):
    return Evidence(kw.pop("kind", "benchmark"), **kw)


def _all_controls(kind="benchmark"):
    return Evidence(kind, machine_verified=True, gradeability_verified=True,
                    contamination_controlled=True, instrument_selftest_passed=True,
                    failure_modes_classified=True, confidence_definition_stated=True,
                    elicitation_documented=True, threshold_justified=True,
                    property_is_behavioural=True, stream_fields_disclosed=True,
                    current_for_deployed_version=True, baseline_named=True,
                    externally_validated=True, scope_stated=True)


GOLD = [
    # (name, Step, expected verdict)
    ("benchmark→deployment_safety is a type error (always refuse)",
     Step("s", _all_controls(), "deployment_safety"), cc.V.REFUSE),  # type rule refuses regardless
    ("benchmark→general_capability is a type error even with all controls (refuse)",
     Step("s", _all_controls(), "general_capability"), cc.V.REFUSE),
    ("representative_eval→general_capability with ALL controls met → admit",
     Step("s", _all_controls("representative_eval"), "general_capability"), cc.V.ADMIT),
    ("capability claim, gradeability NOT verified → refuse (active defeater)",
     Step("s", Evidence("representative_eval", machine_verified=True, contamination_controlled=True,
                        instrument_selftest_passed=True, elicitation_documented=True),
          "general_capability"), cc.V.REFUSE),
    ("calibration claim, all controls → admit",
     Step("s", Evidence("representative_eval", machine_verified=True, contamination_controlled=True,
                        instrument_selftest_passed=True, failure_modes_classified=True,
                        confidence_definition_stated=True), "well_calibrated"), cc.V.ADMIT),
    ("calibration claim, abstention NOT classified → refuse (the June-2026 trap)",
     Step("s", Evidence("representative_eval", machine_verified=True, contamination_controlled=True,
                        instrument_selftest_passed=True, confidence_definition_stated=True),
          "well_calibrated"), cc.V.REFUSE),
    ("inability claim, elicitation NOT documented → refuse (sandbagging risk)",
     Step("s", Evidence("benchmark", contamination_controlled=True, threshold_justified=True,
                        property_is_behavioural=True), "lacks_capability"), cc.V.REFUSE),
    ("inability claim about a LATENT property (behavioural_limit active) → refuse",
     Step("s", Evidence("benchmark", contamination_controlled=True, threshold_justified=True,
                        elicitation_documented=True, property_is_behavioural=False),
          "lacks_capability"), cc.V.REFUSE),
    ("single_example→general_capability type error → refuse",
     Step("s", _all_controls("single_example"), "general_capability"), cc.V.REFUSE),
    ("uncovered claim type → needs-rule (honest gap, no controls needed)",
     Step("s", Evidence("benchmark"), "wins_a_nobel_prize"), cc.V.NEEDS_RULE),
    ("calibration claim, confidence definition NOT stated → refuse",
     Step("s", Evidence("representative_eval", contamination_controlled=True,
                        instrument_selftest_passed=True, failure_modes_classified=True),
          "well_calibrated"), cc.V.REFUSE),
    ("calibration claim, contamination NOT controlled → refuse",
     Step("s", Evidence("representative_eval", instrument_selftest_passed=True,
                        failure_modes_classified=True, confidence_definition_stated=True),
          "well_calibrated"), cc.V.REFUSE),
    ("explicitly-raised extra defeater applies even when not category-required → refuse",
     Step("s", Evidence("benchmark"), "benchmark_performance",
          extra_defeaters=["contamination"]), cc.V.REFUSE),
    ("scoped benchmark-performance claim with no raised doubts → admit (contestable rule, documented)",
     Step("s", Evidence("benchmark"), "benchmark_performance"), cc.V.ADMIT),
    ("untyped evidence + unrefuted defeaters → REFUSE dominates needs-rule (fail-closed)",
     Step("s", Evidence("vibes"), "well_calibrated"), cc.V.REFUSE),
    ("untyped evidence with ALL controls met → needs-rule surfaces (vocabulary gap, honest)",
     Step("s", _all_controls("vibes"), "well_calibrated"), cc.V.NEEDS_RULE),
    ("computational evidence cannot back an inability claim → refuse (eval-type rule)",
     Step("s", _all_controls("simulation"), "lacks_capability"), cc.V.REFUSE),
    ("capability claim, STREAM methodology NOT disclosed → refuse (undisclosed = defeated)",
     Step("s", Evidence("representative_eval", machine_verified=True, gradeability_verified=True,
                        contamination_controlled=True, instrument_selftest_passed=True,
                        elicitation_documented=True, current_for_deployed_version=True),
          "general_capability"), cc.V.REFUSE),
    ("inability claim, all controls incl. STREAM + currency → admit",
     Step("s", _all_controls("representative_eval"), "lacks_capability"), cc.V.ADMIT),
    ("inability claim, evidence STALE for the deployed version → refuse (dynamic safety case)",
     Step("s", Evidence("representative_eval", machine_verified=True, contamination_controlled=True,
                        threshold_justified=True, property_is_behavioural=True,
                        elicitation_documented=True, stream_fields_disclosed=True),
          "lacks_capability"), cc.V.REFUSE),
    ("capability-gain claim WITH named baselines + elicitation + contamination → admit",
     Step("s", Evidence("benchmark", baseline_named=True, elicitation_documented=True,
                        contamination_controlled=True), "no_unique_capability"), cc.V.ADMIT),
    ("capability-gain claim WITHOUT named baselines → refuse (abstract superiority claim)",
     Step("s", Evidence("benchmark", elicitation_documented=True, contamination_controlled=True),
          "no_unique_capability"), cc.V.REFUSE),
    ("external-validation claim: independently tested AND bar defined → admit",
     Step("s", Evidence("benchmark", externally_validated=True, threshold_justified=True),
          "independently_validated"), cc.V.ADMIT),
    ("external-validation claim: CAISI-tested but superlative 'strong' (no bar) → refuse (threshold)",
     Step("s", Evidence("benchmark", externally_validated=True), "independently_validated"),
     cc.V.REFUSE),
    ("scoped-negative: 'none found, at time of writing, under tests X' + elicitation → admit",
     Step("s", Evidence("benchmark", scope_stated=True, elicitation_documented=True),
          "no_universal_jailbreak_found"), cc.V.ADMIT),
    ("scoped-negative overstated as 'none exist' (scope NOT stated) → refuse",
     Step("s", Evidence("benchmark", elicitation_documented=True),
          "no_universal_jailbreak_found"), cc.V.REFUSE),
    ("safeguard-efficacy with machine-verified eval + all controls → admit",
     Step("s", _all_controls("representative_eval"), "safeguard_blocks_technique"), cc.V.ADMIT),
    ("safeguard-efficacy '>99% blocked' with NO validated instrument → refuse",
     Step("s", Evidence("benchmark", threshold_justified=True, contamination_controlled=True),
          "safeguard_blocks_technique"), cc.V.REFUSE),
]


def selftest(verbose=True):
    fails = []
    for name, step, expected in GOLD:
        got = check_step(step).verdict
        ok = got is expected
        if verbose:
            print(f"  [{'ok' if ok else 'FAIL'}] {name}  (want {expected.value}, got {got.value})")
        if not ok:
            fails.append(name)
    # invariant: no evidence with a missing required control may ever ADMIT (the overclaim gate)
    holes = 0
    for _, step, _ in GOLD:
        r = check_step(step)
        if r.verdict is cc.V.ADMIT and r.active_defeaters:
            holes += 1
    if verbose:
        print(f"  [{'ok' if holes == 0 else 'FAIL'}] invariant: no ADMIT with an active defeater "
              f"({holes} violation(s))")
    if holes:
        fails.append("overclaim-invariant")
    ok = not fails
    if verbose:
        print(f"  => INSTRUMENT {'VALID' if ok else 'INVALID — refusing to run'} "
              f"({len(GOLD) + 1 - len(fails)}/{len(GOLD) + 1})")
    return ok


def demo():
    """A worked frontier-AI safety argument: an under-evidenced version vs a fully-controlled one."""
    print("=== Argument A — a typical under-evidenced eval claim ===")
    a = [
        Step("Model scores 92% on CyberBench, so it is safe to deploy",
             Evidence("benchmark", source="CyberBench v3", machine_verified=False),
             "deployment_safety"),
        Step("Model answers 88% of held-out tasks, so it has general coding capability",
             Evidence("representative_eval", source="internal eval", machine_verified=False,
                      gradeability_verified=False, contamination_controlled=False),
             "general_capability"),
    ]
    print(render(compile_case(a)))
    print("\n=== Argument B — the same claims, fully controlled + machine-verified evidence ===")
    b = [
        Step("Model is well-calibrated on fresh arithmetic (honesty-atlas fingerprint)",
             Evidence("representative_eval", source="honesty-atlas 2026-07-02", machine_verified=True,
                      contamination_controlled=True, instrument_selftest_passed=True,
                      failure_modes_classified=True, confidence_definition_stated=True),
             "well_calibrated"),
        Step("Model has general capability on task family T (representative held-out eval)",
             Evidence("representative_eval", source="gradeability-audited suite", machine_verified=True,
                      gradeability_verified=True, contamination_controlled=True,
                      instrument_selftest_passed=True, elicitation_documented=True),
             "general_capability"),
    ]
    print(render(compile_case(b)))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Assurance Compiler v0.1 (Lane 3)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if a.demo:
        demo()
        return
    ap.print_help()


if __name__ == "__main__":
    main()
