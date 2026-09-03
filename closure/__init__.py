"""Final Documentation & Project Closure Layer Package.

Exports all 14 closure coordinators, 52 atomic subagents, domain exceptions, and registry helper.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from core.registry import AgentRegistry
from closure.archive_manager import (
    ArchiveManager,
    ArtifactCollector,
    ArtifactOrganizer,
    ArtifactRetriever,
    ArtifactStorer,
)
from closure.celebration_planner import (
    AchievementRecognizer,
    CelebrationPlanner,
    EventPlanner,
    SuccessCommunicator,
    TeamAppreciator,
)
from closure.compliance_auditor import (
    ComplianceAuditor,
    GdprAuditor,
    HipaaAuditor,
    PciAuditor,
    SoxAuditor,
)
from closure.documentation_reviewer import (
    ApiReviewer,
    ArchitectureReviewer,
    DeploymentGuideReviewer,
    DocumentationReviewer,
    UserGuideReviewer,
)
from closure.exceptions import (
    ArchiveError,
    CelebrationError,
    ClosureError,
    ComplianceAuditError,
    DocumentationReviewError,
    FinalReviewError,
    KnowledgeTransferError,
    LessonsLearnedError,
    PerformanceAuditError,
    QualityAuditError,
    ReportGenerationError,
    RoadmapPlanningError,
    SecurityAuditError,
    SignoffError,
)
from closure.final_closure_orchestrator import FinalClosureOrchestrator
from closure.final_review_board import (
    ActionItemTracker,
    FinalReviewBoard,
    ReviewDocumenter,
    ReviewExecutor,
    ReviewPreparer,
)
from closure.future_roadmap_planner import (
    EnhancementPlanner,
    FeaturePlanner,
    FutureRoadmapPlanner,
    ResourcePlanner,
    TimelinePlanner,
)
from closure.knowledge_transfer_manager import (
    DocumentationPreparer,
    HandoverCoordinator,
    KnowledgeBaseUpdater,
    KnowledgeTransferManager,
    TrainingSessionPlanner,
)
from closure.lessons_learned_collector import (
    ImprovementAreasCollector,
    LessonsLearnedCollector,
    StakeholderFeedbackCollector,
    SuccessStoriesCollector,
    TeamFeedbackCollector,
)
from closure.performance_auditor import (
    PerformanceAuditor,
    ResourceUsageAuditor,
    ResponseTimeAuditor,
    ScalabilityAuditor,
    ThroughputAuditor,
)
from closure.project_closure_report_generator import (
    DetailedReportGenerator,
    ExecutiveSummaryGenerator,
    MetricsReportGenerator,
    ProjectClosureReportGenerator,
    RecommendationsGenerator,
)
from closure.quality_auditor import (
    CodeQualityAuditor,
    OutcomeQualityAuditor,
    ProcessQualityAuditor,
    QualityAuditor,
    TestQualityAuditor,
)
from closure.security_auditor import (
    AuthAuditor,
    DataProtectionAuditor,
    SecurityAuditor,
    SecurityComplianceAuditor,
    VulnerabilityAuditor,
)
from closure.signoff_coordinator import (
    SignoffArchiver,
    SignoffCollector,
    SignoffCoordinator,
    SignoffPreparer,
    SignoffValidator,
)

logger = logging.getLogger("FractalCore.Closure")

__all__ = [
    # Master Orchestrator (L3)
    "FinalClosureOrchestrator",
    # Coordinators (L4)
    "DocumentationReviewer",
    "QualityAuditor",
    "PerformanceAuditor",
    "SecurityAuditor",
    "ComplianceAuditor",
    "LessonsLearnedCollector",
    "ProjectClosureReportGenerator",
    "FutureRoadmapPlanner",
    "KnowledgeTransferManager",
    "FinalReviewBoard",
    "SignoffCoordinator",
    "ArchiveManager",
    "CelebrationPlanner",
    # Atomic Workers (L5)
    "ArchitectureReviewer",
    "ApiReviewer",
    "UserGuideReviewer",
    "DeploymentGuideReviewer",
    "CodeQualityAuditor",
    "TestQualityAuditor",
    "ProcessQualityAuditor",
    "OutcomeQualityAuditor",
    "ResponseTimeAuditor",
    "ThroughputAuditor",
    "ResourceUsageAuditor",
    "ScalabilityAuditor",
    "AuthAuditor",
    "DataProtectionAuditor",
    "VulnerabilityAuditor",
    "SecurityComplianceAuditor",
    "GdprAuditor",
    "HipaaAuditor",
    "PciAuditor",
    "SoxAuditor",
    "TeamFeedbackCollector",
    "StakeholderFeedbackCollector",
    "SuccessStoriesCollector",
    "ImprovementAreasCollector",
    "ExecutiveSummaryGenerator",
    "DetailedReportGenerator",
    "MetricsReportGenerator",
    "RecommendationsGenerator",
    "FeaturePlanner",
    "EnhancementPlanner",
    "TimelinePlanner",
    "ResourcePlanner",
    "DocumentationPreparer",
    "TrainingSessionPlanner",
    "HandoverCoordinator",
    "KnowledgeBaseUpdater",
    "ReviewPreparer",
    "ReviewExecutor",
    "ReviewDocumenter",
    "ActionItemTracker",
    "SignoffPreparer",
    "SignoffCollector",
    "SignoffValidator",
    "SignoffArchiver",
    "ArtifactCollector",
    "ArtifactOrganizer",
    "ArtifactStorer",
    "ArtifactRetriever",
    "EventPlanner",
    "AchievementRecognizer",
    "TeamAppreciator",
    "SuccessCommunicator",
    # Exceptions
    "ClosureError",
    "DocumentationReviewError",
    "QualityAuditError",
    "PerformanceAuditError",
    "SecurityAuditError",
    "ComplianceAuditError",
    "LessonsLearnedError",
    "ReportGenerationError",
    "RoadmapPlanningError",
    "KnowledgeTransferError",
    "FinalReviewError",
    "SignoffError",
    "ArchiveError",
    "CelebrationError",
    # Registry Helper
    "register_all_closure_agents",
]


def register_all_closure_agents(
    registry: AgentRegistry,
    parent_orchestrator: Optional[FinalClosureOrchestrator] = None,
    max_depth: int = 7,
) -> Dict[str, Any]:
    """Instantiate and register all 14 Closure coordinators and 52 subagents into registry."""
    orch = parent_orchestrator or FinalClosureOrchestrator(
        agent_id="FC1_FINAL_CLOSURE_ORCHESTRATOR",
        max_depth=max_depth,
        auto_spawn_subagents=True,
    )
    registry.register_agent(orch)
    registered_count = 1

    def _register_children(agent: Any) -> None:
        nonlocal registered_count
        for child_id, child in agent.children.items():
            registry.register_agent(child)
            registered_count += 1
            _register_children(child)

    _register_children(orch)

    logger.info("Successfully registered %d Closure domain agents into registry.", registered_count)
    return {
        "final_closure_orchestrator": orch,
        "total_registered": registered_count,
    }
