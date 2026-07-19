# Related work — every conjunct has an owner

Written 2026-07-19 after a problem-shaped prior-art audit: searching by the *failure modes* this
tool guards against, rather than by tools that resemble it. It retired the combination claim.

**No novelty is claimed.** This is an open, zero-dependency, eval-domain instantiation of
established assurance-case practice.

## What was claimed, and what killed it

The claim was the *combination*: eval-native defeaters + machine-verified evidence + fail-closed
coverage + zero LLM in the verdict path. A conjunction of owned parts is not a contribution, and
every part is owned:

### Machine-verified evidence nodes
**SRI Evidential Tool Bus** — Rushby (2005); Cruanes, Hamon, Owre, Shankar (VMCAI 2013); applied to
assurance cases in arXiv 2403.01918. ETB represents claims, rules and evidence in Datalog; a claim
holds only if it is *derivable* from evidence produced by actually executing verification tools,
with provenance for each link and automatic re-derivation when inputs change. This is the same
research group as CLARISSA. The earlier framing — machine-verifiable evidence "rather than human
attestation," drawn as a distinction from CLARISSA — was false against that group's own portfolio.

### The coverage denominator / fail-closed defeaters
**Eliminative argumentation and Baconian confidence** — Goodenough, Weinstock & Klein (SEI,
2012–2015); formalized in Bloomfield & Rushby, *Confidence in Assurance 2.0 Cases* (arXiv
2409.10665). Baconian confidence *is* n/N — defeaters eliminated over defeaters identified — and a
claim is only as strong as the doubts discharged against it. An unresolved defeater blocks the
claim. That is this tool's fail-closed coverage rule, published first.

### Typed, named rules that downgrade whether evidence licenses a conclusion
**GRADE** (2004–; Cochrane, WHO, NICE, 110+ organizations). *Indirectness* is precisely the
benchmark-does-not-measure-the-claimed-construct defeater; *imprecision* is the threshold defeater.
Named triggers, citable, validated at enormous scale.

### Evidence must exist before the claim is made
**FTC advertising substantiation doctrine** (1983 Policy Statement) and the establishment-claim
doctrine: a reasonable basis must exist *prior to dissemination*, and a claim alluding to a
specific level of evidence requires that level. This is the v0.2 safety-announcement rule pack, as
regulatory doctrine, four decades old.

### Unstated control = active defeater
**Reiter**, closed-world assumption / negation as failure (1978) — and the operational semantics
ETB already inherits by being Datalog-based.

### Machine-checked assurance arguments
**CLARISSA / Assurance 2.0** (Bloomfield & Rushby, arXiv 2004.10474, 2405.15800) has priority. This
was already stated in the README before the audit and remains true.

## What is actually here

An open, zero-dependency, LLM-free implementation of these conventions specialized to *evaluation
claims about AI systems*, with a self-test that refuses to run until planted overclaims are caught,
and a Lean-checked kernel. Engineering and pedagogy in a specific domain — not a new mechanism.

## Method note

Earlier passes searched by architecture (tools resembling this one) and left the combination claim
standing. The pass that searched by failure mode — who else refuses a claim whose supporting
control was never stated, who else counts discharged doubts — retired it in one attempt. Negatives
here are search-shaped and weaker than the positives; couldn't-find is not doesn't-exist.
