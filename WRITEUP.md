# Type-checking the claims inside AI safety cases

*A fail-closed compiler from evaluation evidence to licensed wording. 2026.*

## The gap

Frontier-AI governance has standardized on the **safety case** — a structured argument that
evidence justifies a safety claim — and regulators increasingly expect one. Yet every safety
case today is a **prose document**, and the field's own position papers concede that behavioural
evaluation cannot support the strongest claims governance now asks for. Meanwhile the evidence
behind an eval claim is usually taken on the author's word: "we scored 78%, so the model is
capable"; "we red-teamed it, so it's safe."

There is a layer missing between "we wrote an argument" and "the argument holds": a **checker**
that reads each step and says, deterministically, whether the evidence licenses the wording.

## What already exists (and what it doesn't do)

[CLARISSA / Assurance 2.0](https://www.csl.sri.com/users/rushby/assurance2.0) (SRI, Adelard,
DARPA-funded) machine-checks assurance-argument **structure** — is the claim tree well-formed,
are defeaters tracked — but by its own design the **evidence is human-asserted**: a person
vouches that a cited artifact means what the node says. It is general-purpose (its worked example
is a light bulb) and proprietary. The frontier-AI safety-case literature (inability templates,
scalable/dynamic safety cases, construction taxonomies) is **prose and frameworks — no checker.**

So the open seam is precise: **nobody checks frontier-AI *evaluation* claims with evidence that
is itself machine-verified, under defeaters specific to how evals fail, fail-closed and open.**

## The contribution (a combination, never a "first")

1. **Eval-native defeaters.** Named, cited threats to an *evaluation* claim — contamination,
   instrument validity, abstention semantics, elicitation gaps, threshold validity, and the
   behavioural-evidence limit — each of which must be refuted by a machine-verifiable fact.
2. **Machine-verified evidence nodes.** The evidence is the output of self-validating instruments
   (honesty-atlas, gradeability-audit, oracle-shield), re-verified at citation time — precisely
   the authenticity step CLARISSA leaves to human judgment.
3. **Fail-closed with a coverage denominator.** An unstated control is an *active* defeater;
   claims refuse by default; the ledger reports "of N claims, k licensed as worded, and how many
   were backed by machine-verified evidence."
4. **Open, deterministic, zero-LLM in the verdict path**, over a Lean-checked kernel.

Vocabulary bridges to Assurance 2.0 so the assurance community can read it: **ADMIT = sustained
claim, REFUSE = active (unrefuted) defeater, NEEDS-RULE = missing warrant.**

## What the checker does to a typical safety argument

Run against paraphrased open-weights model-card claims, four of five refuse — not because the
claims are false, but because the evidence that would license the wording isn't attached. A
benchmark score doesn't license a general-capability or deployment-safety claim (a type error);
an inability claim with no elicitation study fails on the sandbagging defeater; a calibration
claim with no instrument-validity or abstention-semantics control fails closed. The one claim
that admits is the honestly-scoped one ("scored 78% on the benchmark"). Attach a machine-verified
honesty-atlas fingerprint to the calibration claim and it admits — same claim, real evidence.

## The discipline that makes it credible

The checker **validates itself before it validates anything else**: 18 planted self-test cases,
including planted overclaims that must refuse and the invariant that nothing with an active
defeater may ADMIT. It caught its own author's mistakes three times during development. And the
first live run over real evidence **refused a claim the author wanted to make** — an inability
claim about a model's limits that lacked an elicitation study and rested on an arbitrary
threshold. A checker that tells its builder "no" is the strongest evidence it isn't just
confirming what you hoped.

## Limits — read before quoting

- **It checks whether evidence licenses wording, not whether a model is safe.** A REFUSE means
  "the argument as written isn't warranted," not "the model is dangerous."
- **The rules are the contestable product.** They cite their sources; they are meant to be
  argued with and versioned. A wrong rule refused loudly is the mechanism working, not failing.
- **CLARISSA/Assurance 2.0 has priority** on machine-checked assurance arguments; the claim here
  is the eval-native, machine-verified-evidence, open combination.
- The illustrative ledger uses paraphrased, unattributed claims. Auditing a specific named model
  card is a separate, deliberate step.
