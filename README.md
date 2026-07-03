# assurance-compiler

> A deterministic, fail-closed checker for the **evaluation claims** inside AI safety
> arguments. It reads each "evidence → claim" step and returns **ADMIT / REFUSE /
> NEEDS-RULE** under named, cited rules — with zero LLM in the verdict path.

AI governance has converged on the **safety case**: a structured argument that evidence
justifies a safety claim. But safety cases today are prose, and the evidence behind an eval
claim — "scored 78%, therefore capable"; "red-teamed, therefore safe" — is usually taken on
the author's word. `assurance-compiler` type-checks those steps: a claim is **admitted only
if a named rule licenses the evidence→claim jump AND every applicable eval-native defeater is
refuted by a machine-verifiable fact.** Everything else fails closed.

## See it in 20 seconds

```bash
python3 assurance_compiler.py --selftest      # 18/18 — the checker validates itself first
python3 ledger_modelcard_demo.py              # a typical model-card safety argument, checked
```

A typical open-weights model-card safety argument, run through the checker (claims are
illustrative — paraphrased from the *kind* of language model cards use, not any one vendor's):

```
[REFUSE] "78% on a coding benchmark, demonstrating strong general coding capability."
          type error: success on a fixed benchmark does not establish a general capability
          ✗ gradeability · ✗ contamination · ✗ instrument_validity · ✗ elicitation_gap
[REFUSE] "The model is safe for general-purpose deployment."
          type error: benchmark success does not establish deployment safety
          ✗ gradeability · contamination · instrument_validity · elicitation_gap · threshold_validity · behavioural_limit
[REFUSE] "Red-teaming found no capability to assist with dangerous tasks."   (inability)
          ✗ elicitation_gap · threshold_validity · contamination · behavioural_limit
[REFUSE] "The model is well-calibrated and reports uncertainty reliably."
          ✗ instrument_validity · abstention_semantics · confidence_definition · contamination
[ADMIT ] "Scored 78% on the published coding benchmark."   (scoped to the benchmark itself)
------------------------------------------------------------------------
coverage: 1/5 claims licensed as worded · 4 refused · 0/5 backed by machine-verified evidence
```

The claims aren't *false* — they fail because the evidence that would license the wording isn't
attached. Attach machine-verified evidence and the same claim admits:

```
[ADMIT ] "Well-calibrated on fresh arithmetic-verification tasks (honesty-atlas fingerprint)."
          [machine-verified evidence] — type rule admits and all applicable defeaters refuted
coverage: 1/1 licensed · 1/1 backed by machine-verified evidence
```

## What it checks — "type-checking a claim"

Like a compiler rejecting `int + string`, the engine rejects evidence→claim type errors over a
table of **named, cited rules** (the contestable product; disagreement is about a *rule*, not a
model's opinion):

| step | verdict |
|---|---|
| `benchmark score → "safe to deploy"` | **REFUSE** (a benchmark can't license deployment safety) |
| `held-out eval + all controls met → "general capability"` | **ADMIT** |
| a claim no rule covers | **NEEDS-RULE** (honest: don't guess — author a rule) |

### Eval-native defeaters (the part general assurance tools don't have)

Classical assurance tooling ([CLARISSA / Assurance 2.0](https://www.csl.sri.com/users/rushby/assurance2.0)
— real prior art, credited) checks argument *structure* over evidence a **human vouches for**.
This adds defeaters specific to **AI evaluation**, each of which must be refuted by a
machine-verifiable fact or the claim fails closed:

- **contamination** — were the eval instances possibly in training data?
- **instrument validity** — did the measuring tool pass its own self-test?
- **abstention semantics** — is "abstention" real, or is truncation/refusal being mis-scored as honesty?
- **elicitation gap** — could better prompting/tools beat the eval (sandbagging)?
- **threshold validity** — is the pass/fail line justified or arbitrary?
- **behavioural limit** — is this even a property behavioural evidence can reach?

## Why you can trust the verdict

- **Fail-closed:** an unstated control is an *active defeater*, never assumed met.
- **Zero LLM in the decision path:** the verdict is a table lookup over cited rules.
- **Machine-verifiable evidence:** the intended evidence nodes are outputs of self-validating
  instruments ([honesty-atlas](https://github.com/MonongahelaHellbender/honesty-atlas),
  gradeability-audit, oracle-shield), re-verified when cited — not human say-so.
- **The checker validates itself first:** `--selftest` runs 18 planted cases (including planted
  overclaims that MUST refuse) and the engine refuses to be trusted until they pass.
- **Lean-checked core:** the underlying claim-compiler kernel's soundness properties are proved
  in `claim_core.lean` (no `sorry`).

## What this is — and is not

The claim is the **combination** — eval-native defeaters + machine-verified evidence +
fail-closed coverage — not "the first machine-checkable safety case" (CLARISSA has priority on
machine-checked assurance arguments). The illustrative ledger uses paraphrased, unattributed
claims; auditing a specific named model card is a deliberate, separate step. It is a discipline
for licensing claims, not a truth oracle: it says whether the evidence *licenses the wording*,
not whether the model is safe.

MIT © Melissa Ellison.
