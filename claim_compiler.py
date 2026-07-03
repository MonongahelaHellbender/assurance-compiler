#!/usr/bin/env python3
"""
Claim Compiler v0.1 — a deterministic epistemic typechecker for scientific claims. (PRIVATE build.)

It does NOT determine scientific truth. It checks whether the KIND of evidence on hand licenses the KIND
of claim/wording someone wants to make, under a set of NAMED, explicit bridge rules. The promotion
decision is a pure table lookup — ZERO LLM authority in the path. Disagreement is about a named rule,
not the engine.

  check(evidence_type, claim_type) -> Verdict
    REFUSE      a named rule forbids this evidence→claim jump (a scientific "type error")
    ADMIT       a named rule licenses it (the wording matches what the evidence supports)
    NEEDS_RULE  no rule covers this pair (honest: don't guess — narrow the claim or author a rule)

Each REFUSE carries: reason code · allowed wording · missing bridge · falsifier · next gate.

Honest positioning: this FORMALIZES + ENFORCES known evidence standards (GRADE, Bradford-Hill,
levels-of-evidence, surrogate-endpoint caveats, the benchmark↔deployment gap, prior-art/novelty) as a
cross-domain machine-checkable typechecker. It invents no epistemology and adjudicates no truth.
AI-trust-lane / claim-assurance artifact. Not filed claim language.
"""
from dataclasses import dataclass
from enum import Enum


class V(Enum):
    ADMIT = "ADMIT"
    REFUSE = "REFUSE"
    NEEDS_RULE = "NEEDS-RULE"


@dataclass
class Rule:
    evidence: str
    claim: str
    verdict: V
    reason: str = ""
    allowed: str = ""      # allowed wording (REFUSE)
    bridge: str = ""       # missing bridge
    falsifier: str = ""
    next_gate: str = ""
    via: str = ""          # provenance: which rule fired (point / category X→Y / no-rule)


# ---- the named bridge rules: the product IS this table; explicit + contestable by design ----------
RULES = [
    # materials / chemistry
    Rule("simulation", "synthesizable_material", V.REFUSE,
         "computational evidence cannot establish experimental synthesis",
         "computational candidate for external review",
         "independent synthesis and characterization",
         "failed synthesis or incompatible phase formation",
         "blinded laboratory validation"),
    Rule("predicted_structure", "effective_drug", V.REFUSE,
         "a predicted structure cannot establish therapeutic effect",
         "predicted binder; candidate for assay",
         "in-vitro → in-vivo → clinical evidence",
         "no measurable binding / no efficacy in assay",
         "biochemical binding assay"),
    # biomedicine
    Rule("in_vitro", "patient_benefit", V.REFUSE,
         "a cell assay cannot establish patient benefit",
         "in-vitro activity; preclinical signal only",
         "animal model → clinical trial with patient outcomes",
         "no effect in vivo / no clinical benefit",
         "preclinical in-vivo study"),
    Rule("surrogate_endpoint", "clinical_improvement", V.REFUSE,
         "a surrogate endpoint does not establish clinical improvement",
         "improved surrogate marker",
         "a trial powered on a hard clinical endpoint",
         "surrogate improves but the clinical endpoint does not",
         "outcome trial on the clinical endpoint"),
    Rule("correlation", "causation", V.REFUSE,
         "correlation does not establish causation",
         "association observed",
         "randomization or a valid causal-identification design",
         "association vanishes under control for confounders",
         "randomized or quasi-experimental design"),
    # ML / AI
    Rule("benchmark", "deployment_safety", V.REFUSE,
         "benchmark success does not establish deployment safety",
         "benchmark score under stated conditions",
         "evaluation under distribution shift + adversarial + red-team testing",
         "failure under shift / adversarial / real-world conditions",
         "staged deployment with monitoring + red-team eval"),
    Rule("benchmark", "general_capability", V.REFUSE,
         "success on a fixed benchmark does not establish a general capability",
         "performance on the stated benchmark",
         "evaluation over a representative held-out distribution",
         "fails on held-out / out-of-distribution instances",
         "systematic eval over the target population"),
    Rule("single_example", "general_capability", V.REFUSE,
         "one successful example does not establish a general capability",
         "demonstrated on the shown instance",
         "evaluation over a representative held-out distribution",
         "fails on held-out / out-of-distribution instances",
         "systematic benchmark over a defined population"),
    # scholarship
    Rule("rederivation", "literature_priority", V.REFUSE,
         "re-deriving a known result does not establish literature priority",
         "an independent re-derivation of a known result",
         "a prior-art / novelty search against the literature",
         "the result already exists in prior work",
         "systematic prior-art search"),

    # ---- VALID narrow promotions: the typechecker is not 'refuse everything' ----
    Rule("simulation", "computational_candidate", V.ADMIT),
    Rule("predicted_structure", "predicted_binder", V.ADMIT),
    Rule("in_vitro", "preclinical_signal", V.ADMIT),
    Rule("correlation", "association", V.ADMIT),
    Rule("rct_on_endpoint", "clinical_improvement", V.ADMIT),
    Rule("representative_eval", "general_capability", V.ADMIT),
    Rule("synthesis_characterization", "synthesizable_material", V.ADMIT),
    Rule("benchmark", "benchmark_performance", V.ADMIT),
    Rule("prior_art_search", "literature_priority", V.ADMIT),
]

_INDEX = {(r.evidence, r.claim): r for r in RULES}


# ====================================================================================================
# v0.2 — category lattice: the move from hand-authored POINT rules to a general RULE SYSTEM.
# Specific evidence/claim types roll up into categories; a small set of CATEGORY rules then covers many
# surface pairs by generalization. (Her frontier step: "turning six hand-authored decisions into a
# general rule system.") Uncovered category pairs still return NEEDS_RULE — honest coverage gaps.
# ====================================================================================================
EVIDENCE_CAT = {
    "simulation": "COMPUTATIONAL", "predicted_structure": "COMPUTATIONAL", "dft": "COMPUTATIONAL",
    "md_simulation": "COMPUTATIONAL", "ml_prediction": "COMPUTATIONAL", "in_silico": "COMPUTATIONAL",
    "docking": "COMPUTATIONAL",
    "in_vitro": "IN_VITRO", "cell_assay": "IN_VITRO", "organoid": "IN_VITRO",
    "in_vivo_animal": "ANIMAL", "mouse_model": "ANIMAL", "animal_study": "ANIMAL",
    "correlation": "OBSERVATIONAL", "observational_study": "OBSERVATIONAL",
    "retrospective_cohort": "OBSERVATIONAL", "cross_sectional": "OBSERVATIONAL",
    "epidemiological": "OBSERVATIONAL",
    "surrogate_endpoint": "SURROGATE", "biomarker": "SURROGATE",
    "rct_on_endpoint": "INTERVENTIONAL", "randomized_trial": "INTERVENTIONAL", "rct": "INTERVENTIONAL",
    "benchmark": "BENCHMARK", "leaderboard": "BENCHMARK", "test_set": "BENCHMARK",
    "single_example": "SINGLE_INSTANCE", "anecdote": "SINGLE_INSTANCE", "one_case": "SINGLE_INSTANCE",
    "case_report": "SINGLE_INSTANCE",
    "rederivation": "REDERIVATION", "reimplementation": "REDERIVATION",
    "representative_eval": "REPRESENTATIVE_EVAL", "held_out_eval": "REPRESENTATIVE_EVAL",
    "synthesis_characterization": "EXPERIMENTAL_SYNTHESIS", "prior_art_search": "PRIOR_ART",
}
CLAIM_CAT = {
    "synthesizable_material": "PHYSICAL_REALIZATION", "manufacturable": "PHYSICAL_REALIZATION",
    "stable_compound": "PHYSICAL_REALIZATION", "synthesized": "PHYSICAL_REALIZATION",
    "effective_drug": "THERAPEUTIC_EFFECT", "cures_disease": "THERAPEUTIC_EFFECT",
    "therapeutic": "THERAPEUTIC_EFFECT",
    "patient_benefit": "PATIENT_OUTCOME", "clinical_improvement": "PATIENT_OUTCOME",
    "survival_benefit": "PATIENT_OUTCOME", "improves_outcomes": "PATIENT_OUTCOME",
    "causation": "CAUSAL", "causes": "CAUSAL", "prevents": "CAUSAL", "drives": "CAUSAL",
    "deployment_safety": "DEPLOYMENT_SAFETY", "safe_to_deploy": "DEPLOYMENT_SAFETY",
    "reliable_in_production": "DEPLOYMENT_SAFETY",
    "general_capability": "GENERAL_CAPABILITY", "generally_solves": "GENERAL_CAPABILITY",
    "literature_priority": "PRIORITY", "novel_discovery": "PRIORITY", "first_to_show": "PRIORITY",
    "association": "ASSOCIATION",
    "computational_candidate": "CANDIDATE", "predicted_binder": "CANDIDATE",
    "preclinical_signal": "CANDIDATE",
    "benchmark_performance": "BENCHMARK_RESULT",
}


@dataclass
class CatRule:
    ev_cat: str
    claim_cat: str
    verdict: V
    reason: str = ""
    allowed: str = ""
    bridge: str = ""
    falsifier: str = ""
    next_gate: str = ""


CAT_RULES = [
    CatRule("COMPUTATIONAL", "PHYSICAL_REALIZATION", V.REFUSE,
            "computational evidence cannot establish physical realization (synthesis/manufacture)",
            "computational candidate for experimental review",
            "independent synthesis + characterization",
            "failed synthesis / incompatible phase formation",
            "blinded laboratory validation"),
    CatRule("COMPUTATIONAL", "THERAPEUTIC_EFFECT", V.REFUSE,
            "computational/predicted evidence cannot establish therapeutic effect",
            "computational candidate; predicted activity",
            "binding assay → in-vivo → clinical evidence",
            "no measurable activity in assay",
            "biochemical / cell assay"),
    CatRule("COMPUTATIONAL", "CANDIDATE", V.ADMIT),
    CatRule("IN_VITRO", "PATIENT_OUTCOME", V.REFUSE,
            "a cell assay cannot establish patient outcomes",
            "in-vitro activity; preclinical signal",
            "animal model → clinical trial with patient outcomes",
            "no effect in vivo / no clinical benefit",
            "preclinical in-vivo study"),
    CatRule("IN_VITRO", "CANDIDATE", V.ADMIT),
    CatRule("ANIMAL", "PATIENT_OUTCOME", V.REFUSE,
            "efficacy in an animal model does not establish patient benefit",
            "efficacy in the animal model; preclinical signal",
            "a human clinical trial with patient outcomes",
            "no benefit in the human trial",
            "phase I→III clinical program"),
    CatRule("SURROGATE", "PATIENT_OUTCOME", V.REFUSE,
            "a surrogate endpoint does not establish a hard patient outcome",
            "improved surrogate marker",
            "a trial powered on the clinical endpoint",
            "surrogate improves but the clinical endpoint does not",
            "outcome trial on the clinical endpoint"),
    CatRule("OBSERVATIONAL", "CAUSAL", V.REFUSE,
            "observational association does not establish causation",
            "association observed",
            "randomization or a valid causal-identification design",
            "association vanishes under control for confounders",
            "randomized or quasi-experimental design"),
    CatRule("OBSERVATIONAL", "ASSOCIATION", V.ADMIT),
    CatRule("INTERVENTIONAL", "CAUSAL", V.ADMIT),
    CatRule("INTERVENTIONAL", "PATIENT_OUTCOME", V.ADMIT),
    CatRule("BENCHMARK", "DEPLOYMENT_SAFETY", V.REFUSE,
            "benchmark performance does not establish deployment safety",
            "benchmark score under stated conditions",
            "evaluation under distribution shift + adversarial + red-team testing",
            "failure under shift / adversarial / real-world conditions",
            "staged deployment with monitoring + red-team eval"),
    CatRule("BENCHMARK", "GENERAL_CAPABILITY", V.REFUSE,
            "a fixed benchmark does not establish a general capability",
            "performance on the stated benchmark",
            "evaluation over a representative held-out distribution",
            "fails on out-of-distribution instances",
            "systematic eval over the target population"),
    CatRule("BENCHMARK", "BENCHMARK_RESULT", V.ADMIT),
    CatRule("SINGLE_INSTANCE", "GENERAL_CAPABILITY", V.REFUSE,
            "one example does not establish a general capability",
            "demonstrated on the shown instance",
            "evaluation over a representative held-out distribution",
            "fails on held-out instances",
            "systematic benchmark over a defined population"),
    CatRule("REPRESENTATIVE_EVAL", "GENERAL_CAPABILITY", V.ADMIT),
    CatRule("REDERIVATION", "PRIORITY", V.REFUSE,
            "re-deriving a known result does not establish literature priority",
            "an independent re-derivation of a known result",
            "a prior-art / novelty search against the literature",
            "the result already exists in prior work",
            "systematic prior-art search"),
    CatRule("PRIOR_ART", "PRIORITY", V.ADMIT),
    CatRule("EXPERIMENTAL_SYNTHESIS", "PHYSICAL_REALIZATION", V.ADMIT),
]
_CAT_INDEX = {(r.ev_cat, r.claim_cat): r for r in CAT_RULES}


def check(evidence: str, claim: str) -> Rule:
    """Deterministic resolution: exact point rule → category rule → NEEDS_RULE (never guess)."""
    r = _INDEX.get((evidence, claim))
    if r:
        return Rule(**{**r.__dict__, "via": "point"})

    ec, cc = EVIDENCE_CAT.get(evidence), CLAIM_CAT.get(claim)
    if ec and cc:
        cr = _CAT_INDEX.get((ec, cc))
        if cr:
            return Rule(evidence, claim, cr.verdict, cr.reason, cr.allowed, cr.bridge,
                        cr.falsifier, cr.next_gate, via=f"category {ec}→{cc}")

    # honest coverage gap — distinguish "untyped term" from "typed but no category rule"
    why = []
    if not ec:
        why.append(f"evidence '{evidence}' not in the type vocabulary")
    if not cc:
        why.append(f"claim '{claim}' not in the type vocabulary")
    if ec and cc:
        why.append(f"no category rule for {ec}→{cc}")
    return Rule(evidence, claim, V.NEEDS_RULE,
                reason="; ".join(why) or f"no named rule covers {evidence} → {claim}",
                allowed=f"state only what '{evidence}' supports, or author a bridge rule",
                next_gate="author + name a (category) bridge rule for this pair",
                via="no-rule")


def render(r: Rule) -> str:
    out = [f"Verdict: {r.verdict.value}"]
    if r.verdict is V.REFUSE:
        out += [f"Type error: {r.reason}", f"Allowed wording: {r.allowed}",
                f"Missing bridge: {r.bridge}", f"Falsifier: {r.falsifier}", f"Next gate: {r.next_gate}"]
    elif r.verdict is V.ADMIT:
        out += [f"Licensed: '{r.evidence}' licenses the claim '{r.claim}' as worded"]
    else:
        out += [f"Reason: {r.reason}", f"Note: {r.allowed}", f"Next gate: {r.next_gate}"]
    return "\n".join(out)


# ---- paired evaluation cases: tempting overclaims (REFUSE) + valid promotions (ADMIT) -------------
CASES = [
    ("simulation", "synthesizable_material", V.REFUSE),
    ("predicted_structure", "effective_drug", V.REFUSE),
    ("in_vitro", "patient_benefit", V.REFUSE),
    ("surrogate_endpoint", "clinical_improvement", V.REFUSE),
    ("correlation", "causation", V.REFUSE),
    ("benchmark", "deployment_safety", V.REFUSE),
    ("benchmark", "general_capability", V.REFUSE),
    ("single_example", "general_capability", V.REFUSE),
    ("rederivation", "literature_priority", V.REFUSE),
    ("simulation", "computational_candidate", V.ADMIT),
    ("predicted_structure", "predicted_binder", V.ADMIT),
    ("in_vitro", "preclinical_signal", V.ADMIT),
    ("correlation", "association", V.ADMIT),
    ("rct_on_endpoint", "clinical_improvement", V.ADMIT),
    ("representative_eval", "general_capability", V.ADMIT),
    ("synthesis_characterization", "synthesizable_material", V.ADMIT),
    ("benchmark", "benchmark_performance", V.ADMIT),
    ("prior_art_search", "literature_priority", V.ADMIT),
]


def main():
    print("=== type-error demonstrations ===\n")
    for ev, cl in [("simulation", "synthesizable_material"), ("correlation", "causation"),
                   ("benchmark", "deployment_safety"), ("single_example", "general_capability")]:
        print(render(check(ev, cl)) + "\n")

    fr = sum(1 for ev, cl, exp in CASES if exp is V.ADMIT and check(ev, cl).verdict is V.REFUSE)
    fp = sum(1 for ev, cl, exp in CASES if exp is V.REFUSE and check(ev, cl).verdict is V.ADMIT)
    correct = sum(1 for ev, cl, exp in CASES if check(ev, cl).verdict is exp)
    n_adm = sum(1 for *_, e in CASES if e is V.ADMIT)
    n_ref = sum(1 for *_, e in CASES if e is V.REFUSE)
    print(f"=== evaluation ({len(CASES)} paired cases · {len(RULES)} rules) ===")
    print(f"  correct {correct}/{len(CASES)}  ·  FALSE REFUSALS {fr}/{n_adm} valid promotions  ·  "
          f"FALSE PROMOTIONS {fp}/{n_ref} overclaims")
    print("  (v0.1 rules match these cases by construction; the real test is HELD-OUT adversarial cases —")
    print("   tempting overclaims that look admissible — which is the build-out to the 40-case suite.)")


if __name__ == "__main__":
    main()
