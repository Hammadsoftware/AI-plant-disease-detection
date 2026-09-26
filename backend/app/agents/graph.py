from dataclasses import dataclass

from langgraph.graph import END, START, StateGraph

from app.agents.nodes import DiseaseAgentNodes
from app.agents.state import PlantDiagnosisState
from app.schemas.diagnosis import Diagnosis, DiseaseExplanation
from app.schemas.research import DiagnosisResearch, ResearchBundle, ResearchStatus


@dataclass(frozen=True)
class AgentOutcome:
    explanation: DiseaseExplanation | None
    research_status: ResearchStatus
    groq_status: str
    research: DiagnosisResearch
    errors: list[str]
    warnings: list[str]


def build_disease_graph(nodes: DiseaseAgentNodes):
    """Compile the fan-out/fan-in evidence workflow."""

    workflow = StateGraph(PlantDiagnosisState)
    workflow.add_node("validate_prediction", nodes.validate_prediction)
    workflow.add_node("extract_crop_and_disease", nodes.extract_crop_and_disease)
    workflow.add_node("disease_research", nodes.disease_research)
    workflow.add_node("treatment_research", nodes.treatment_research)
    workflow.add_node("pesticide_research", nodes.pesticide_research)
    workflow.add_node("evidence_validation", nodes.evidence_validation)
    workflow.add_node("generate_explanation", nodes.generate_explanation)
    workflow.add_node("validate_final_response", nodes.validate_final_response)

    workflow.add_edge(START, "validate_prediction")
    workflow.add_edge("validate_prediction", "extract_crop_and_disease")
    workflow.add_edge("extract_crop_and_disease", "disease_research")
    workflow.add_edge("extract_crop_and_disease", "treatment_research")
    workflow.add_edge("extract_crop_and_disease", "pesticide_research")
    workflow.add_edge(
        ["disease_research", "treatment_research", "pesticide_research"],
        "evidence_validation",
    )
    workflow.add_edge("evidence_validation", "generate_explanation")
    workflow.add_edge("generate_explanation", "validate_final_response")
    workflow.add_edge("validate_final_response", END)
    return workflow.compile()


class DiseaseResearchAgent:
    """Application-facing wrapper around the compiled LangGraph workflow."""

    def __init__(self, nodes: DiseaseAgentNodes) -> None:
        self.graph = build_disease_graph(nodes)

    async def explain(
        self,
        image_id: str | None,
        diagnosis: Diagnosis,
        *,
        include_web_research: bool,
        include_pesticides: bool,
    ) -> AgentOutcome:
        initial_state: PlantDiagnosisState = {
            "image_id": image_id,
            "predicted_disease": diagnosis.disease,
            "raw_class_name": diagnosis.class_name,
            "confidence": diagnosis.confidence,
            "top_predictions": [
                item.model_dump(mode="json") for item in diagnosis.top_predictions
            ],
            "uncertain_prediction": diagnosis.is_uncertain,
            "include_web_research": include_web_research,
            "include_pesticides": include_pesticides,
            "explanation": None,
            "research_status": "disabled",
            "groq_status": "disabled",
            "errors": [],
            "warnings": [],
        }
        result = await self.graph.ainvoke(initial_state)
        disease = result.get("disease_research", _empty_bundle("disease"))
        treatment = result.get("treatment_research", _empty_bundle("treatment"))
        pesticide = result.get("pesticide_research", _empty_bundle("pesticide"))
        evidence = result["evidence"]
        return AgentOutcome(
            explanation=result.get("explanation"),
            research_status=result.get("research_status", "disabled"),
            groq_status=result.get("groq_status", "disabled"),
            research=DiagnosisResearch(
                disease=disease,
                treatment=treatment,
                pesticide=pesticide,
                evidence=evidence,
            ),
            errors=list(dict.fromkeys(result.get("errors", []))),
            warnings=list(dict.fromkeys(result.get("warnings", []))),
        )


def _empty_bundle(topic: str) -> ResearchBundle:
    return ResearchBundle(topic=topic, status="disabled")
