# Import custom modules
from src.raphael.chemistry.models import CastingCluster, ChemistryReport
from src.raphael.agentry.casting_director.models import CastingReport
from src.raphael.agentry.risk_management.models import RiskAssessment, RiskLevel, RiskReport
from src.raphael.recommendation.models import ClusterRecommendation, RecommendationReport
from src.raphael.roster.models import Roster


class RecommendationEngine:
    """
    Final step of the pipeline: joins a ChemistryReport's ranked clusters
    with a RiskReport's per-actor assessments into a RecommendationReport --
    each cluster annotated with its own actors' top risks.

    Purely a deterministic join + rank over already-computed data (no LLM
    call), same shape as ChemistryEngine.
    """

    # Walk order for the severity-band floor in _top_risks.
    _BAND_ORDER = (RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW)

    def invoke(self, chemistry_report: ChemistryReport, risk_report: RiskReport, casting_report: CastingReport) -> RecommendationReport:
        """
        Builds a RecommendationReport from a ChemistryReport and the
        RiskReport covering its candidates. `casting_report` is the same
        (dossier-enriched) report ChemistryEngine built its graph from --
        every character's full candidate shortlist, not just the actors each
        cluster happened to pick -- carried through as `roster` so a swap
        can be scored later without re-running the pipeline.
        """
        assessments_by_name = {assessment.name: assessment for assessment in risk_report.assessments}

        return RecommendationReport(
            title=chemistry_report.title,
            recommendations=[
                ClusterRecommendation(
                    cluster=cluster,
                    top_risks=self._top_risks(cluster, assessments_by_name),
                )
                for cluster in chemistry_report.clusters
            ],
            roster=Roster(
                title=casting_report.title,
                casting_report=casting_report,
                risk_assessments=risk_report.assessments,
            ),
        )

    def build_single(self, cluster: CastingCluster, risk_assessments: list[RiskAssessment]) -> ClusterRecommendation:
        """
        Wraps a single already-scored CastingCluster (e.g. from
        ChemistryEngine.score_selection) into a ClusterRecommendation, same
        shape as one entry of invoke()'s output -- used by the /swap
        endpoint so a swap's response mirrors /recommend's.
        """
        assessments_by_name = {assessment.name: assessment for assessment in risk_assessments}
        return ClusterRecommendation(cluster=cluster, top_risks=self._top_risks(cluster, assessments_by_name))

    def _top_risks(self, cluster: CastingCluster, assessments_by_name: dict[str, RiskAssessment]) -> list[RiskAssessment]:
        """
        Severity-band floor: walks high -> medium -> low, always pulling in
        a whole band at a time, stopping once the running total reaches >=
        3. A floor, not a hard cap -- e.g. 5 high-risk actors all appear
        rather than arbitrarily dropping 2 to hit an exact count of 3.
        """
        assessments = [
            assessments_by_name[selection.candidate.name]
            for selection in cluster.selections
            if selection.candidate.name in assessments_by_name
        ]

        top_risks: list[RiskAssessment] = []
        for level in self._BAND_ORDER:
            if len(top_risks) >= 3:
                break
            top_risks.extend(assessment for assessment in assessments if assessment.risk_level == level)

        return top_risks
