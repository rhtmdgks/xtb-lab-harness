from __future__ import annotations

from xtb_lab_harness.agents.base import SpecialistAgent
from xtb_lab_harness.agents.candidate_material import review_candidate_material
from xtb_lab_harness.agents.electrostatic import ElectrostaticAgent
from xtb_lab_harness.agents.safety import SafetyAgent
from xtb_lab_harness.agents.schemas import AgentReview, CandidateSpec
from xtb_lab_harness.agents.structural_stability import StructuralStabilityAgent
from xtb_lab_harness.agents.variable_control import VariableControlAgent
from xtb_lab_harness.agents.vdw_dispersion import VdwDispersionAgent
from xtb_lab_harness.xtb.schemas import CandidateResult

CANDIDATE_MATERIAL = "Candidate Material Agent"
ELECTROSTATIC = "Electrostatic Interaction Agent"
VDW = "van der Waals / Dispersion Interpretation Agent"
STRUCTURAL = "Structural Stability Agent"
SAFETY = "Safety Reasoning Agent"
VARIABLE_CONTROL = "Variable Control Agent"
CRITIC = "Critic Agent"
CRITIC = "Critic Agent"

ALL_SPECIALIST_AGENTS = [
    CANDIDATE_MATERIAL,
    ELECTROSTATIC,
    VDW,
    STRUCTURAL,
    SAFETY,
    VARIABLE_CONTROL,
]


class CandidateMaterialRunner:
    name = CANDIDATE_MATERIAL

    def review(
        self,
        candidate: CandidateSpec,
        result: CandidateResult,
        *,
        experiment_objective: str,
    ) -> AgentReview:
        return review_candidate_material(candidate, result, experiment_objective=experiment_objective)


def build_specialist_agents() -> dict[str, SpecialistAgent | CandidateMaterialRunner]:
    return {
        CANDIDATE_MATERIAL: CandidateMaterialRunner(),
        ELECTROSTATIC: ElectrostaticAgent(),
        VDW: VdwDispersionAgent(),
        STRUCTURAL: StructuralStabilityAgent(),
        SAFETY: SafetyAgent(),
        VARIABLE_CONTROL: VariableControlAgent(),
    }
