/-
Claim Compiler — formally verified decision core.  (core Lean 4 + `omega`, no Mathlib import.)

This models `check_order`'s promotion rule: on the claim's axis, a claim whose wording DEMANDS rung `d`
is ADMITted by evidence at rung `e` iff `d ≤ e`. Rungs/demands are naturals (positions in a ladder).

Scope of the proof (stated honestly): the LADDERS are DATA and are NOT proved — they are the contestable,
cited content (see LADDER_PROVENANCE.md). Only the ENGINE — this one comparison — is proved here. This is
deliberately NOT a claim of "formally verified epistemology": it is a verified, monotone, decidable core.
-/

namespace ClaimCore

/-- The promotion decision: ADMIT (`true`) iff the evidence rung `e` meets the demanded rung `d`. -/
def admits (e d : Nat) : Bool := decide (d ≤ e)

/-- ADMIT holds exactly when demand ≤ evidence. -/
theorem admits_iff (e d : Nat) : admits e d = true ↔ d ≤ e := by
  simp [admits]

/-- REFUSE holds exactly when the evidence falls short of the demand — soundness of a refusal. -/
theorem refuse_iff (e d : Nat) : admits e d = false ↔ e < d := by
  simp only [admits, decide_eq_false_iff_not]
  omega

/-- Monotone in evidence: stronger evidence never loses a license. -/
theorem admits_mono_evidence {e e' d : Nat} (h : e ≤ e') :
    admits e d = true → admits e' d = true := by
  simp only [admits_iff]; intro hd; omega

/-- Antitone in demand: a weaker claim is licensed whenever a stronger one is (monotone wording). -/
theorem admits_anti_demand {e d d' : Nat} (h : d' ≤ d) :
    admits e d = true → admits e d' = true := by
  simp only [admits_iff]; intro hd; omega

/-- Totality: every case is decided — there is never an undecided gap inside the core. -/
theorem admits_total (e d : Nat) : admits e d = true ∨ admits e d = false := by
  cases admits e d
  · exact Or.inr rfl
  · exact Or.inl rfl

/-- A refusal is never also an admission (the verdict is unambiguous). -/
theorem not_admit_and_refuse (e d : Nat) : ¬ (admits e d = true ∧ admits e d = false) := by
  intro ⟨h1, h2⟩; rw [h1] at h2; exact Bool.noConfusion h2

end ClaimCore

-- the core depends on no `sorry`; these print only standard axioms.
#print axioms ClaimCore.admits_mono_evidence
#print axioms ClaimCore.admits_anti_demand
#print axioms ClaimCore.refuse_iff
#print axioms ClaimCore.admits_total
