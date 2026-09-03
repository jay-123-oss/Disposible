"""User Acceptance Testing (UAT) Layer Package.

Exports all 14 UAT agents, 52 atomic subagents, domain exceptions, and registry helper.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from core.registry import AgentRegistry
from uat.acceptance_criteria_checker import (
    AcceptanceCriteriaChecker,
    FunctionalCriteria,
    NonFunctionalCriteria,
    PerformanceCriteria,
    UiCriteria,
)
from uat.business_flow_tester import (
    BusinessFlowTester,
    NotificationFlow,
    OrderProcessingFlow,
    PaymentProcessingFlow,
    ReportingFlow,
)
from uat.data_integrity_checker import (
    DataAccuracyChecker,
    DataCompletenessChecker,
    DataConsistencyChecker,
    DataIntegrityChecker,
    DataValidityChecker,
)
from uat.end_to_end_tester import (
    AdminOperationsFlow,
    EndToEndTester,
    LoginProtectedFlow,
    RegisterLoginFlow,
    UserCrudFlow,
)
from uat.exceptions import (
    AcceptanceCriteriaError,
    BusinessFlowError,
    DataIntegrityError,
    EndToEndError,
    FeedbackCollectionError,
    IntegrationError,
    PerformanceValidationError,
    RoleBasedError,
    SecurityValidationError,
    UATError,
    UIError,
    UseCaseError,
    UserScenarioError,
    WorkflowError,
)
from uat.integration_validator import (
    ApiIntegration,
    DatabaseIntegration,
    EventIntegration,
    ExternalServiceIntegration,
    IntegrationValidator,
)
from uat.performance_validator import (
    PerformanceValidator,
    ResourceUsageValidator,
    ResponseTimeValidator,
    ScalabilityValidator,
    ThroughputValidator,
)
from uat.role_based_tester import (
    AdminRoleTester,
    GuestRoleTester,
    ManagerRoleTester,
    RoleBasedTester,
    UserRoleTester,
)
from uat.security_validator import (
    AuthValidator,
    AuthorizationValidator,
    ComplianceValidator,
    DataProtectionValidator,
    SecurityValidator,
)
from uat.uat_orchestrator import UATOrchestrator
from uat.use_case_validator import (
    EdgeUseCases,
    ExceptionalUseCases,
    PrimaryUseCases,
    SecondaryUseCases,
    UseCaseValidator,
)
from uat.user_feedback_collector import (
    FeedbackAnalyzer,
    ImprovementSuggester,
    SatisfactionTracker,
    SurveyGenerator,
    UserFeedbackCollector,
)
from uat.user_interface_tester import (
    AccessibilityTester,
    NavigationTester,
    ResponsivenessTester,
    UsabilityTester,
    UserInterfaceTester,
)
from uat.user_scenario_tester import (
    AdminUserScenario,
    ExistingUserScenario,
    GuestUserScenario,
    NewUserScenario,
    UserScenarioTester,
)
from uat.workflow_validator import (
    ApprovalWorkflow,
    ArchiveWorkflow,
    PublishWorkflow,
    ReviewWorkflow,
    WorkflowValidator,
)

logger = logging.getLogger("FractalCore.UAT")

__all__ = [
    # Master Orchestrator (L3)
    "UATOrchestrator",
    # Coordinators (L4)
    "EndToEndTester",
    "UserScenarioTester",
    "BusinessFlowTester",
    "RoleBasedTester",
    "UseCaseValidator",
    "AcceptanceCriteriaChecker",
    "UserInterfaceTester",
    "WorkflowValidator",
    "IntegrationValidator",
    "DataIntegrityChecker",
    "SecurityValidator",
    "PerformanceValidator",
    "UserFeedbackCollector",
    # Atomic Workers (L5)
    "RegisterLoginFlow",
    "LoginProtectedFlow",
    "UserCrudFlow",
    "AdminOperationsFlow",
    "NewUserScenario",
    "ExistingUserScenario",
    "AdminUserScenario",
    "GuestUserScenario",
    "OrderProcessingFlow",
    "PaymentProcessingFlow",
    "NotificationFlow",
    "ReportingFlow",
    "AdminRoleTester",
    "UserRoleTester",
    "ManagerRoleTester",
    "GuestRoleTester",
    "PrimaryUseCases",
    "SecondaryUseCases",
    "EdgeUseCases",
    "ExceptionalUseCases",
    "FunctionalCriteria",
    "NonFunctionalCriteria",
    "UiCriteria",
    "PerformanceCriteria",
    "NavigationTester",
    "ResponsivenessTester",
    "AccessibilityTester",
    "UsabilityTester",
    "ApprovalWorkflow",
    "ReviewWorkflow",
    "PublishWorkflow",
    "ArchiveWorkflow",
    "ApiIntegration",
    "DatabaseIntegration",
    "ExternalServiceIntegration",
    "EventIntegration",
    "DataConsistencyChecker",
    "DataAccuracyChecker",
    "DataCompletenessChecker",
    "DataValidityChecker",
    "AuthValidator",
    "AuthorizationValidator",
    "DataProtectionValidator",
    "ComplianceValidator",
    "ResponseTimeValidator",
    "ThroughputValidator",
    "ResourceUsageValidator",
    "ScalabilityValidator",
    "SurveyGenerator",
    "FeedbackAnalyzer",
    "SatisfactionTracker",
    "ImprovementSuggester",
    # Exceptions
    "UATError",
    "EndToEndError",
    "UserScenarioError",
    "BusinessFlowError",
    "RoleBasedError",
    "UseCaseError",
    "AcceptanceCriteriaError",
    "UIError",
    "WorkflowError",
    "IntegrationError",
    "DataIntegrityError",
    "SecurityValidationError",
    "PerformanceValidationError",
    "FeedbackCollectionError",
    # Helper
    "register_all_uat_agents",
]


def register_all_uat_agents(
    registry: AgentRegistry,
    parent_orchestrator: Optional[UATOrchestrator] = None,
    max_depth: int = 7,
) -> Dict[str, Any]:
    """Instantiate and register all 14 UAT coordinators and 52 subagents into registry."""
    orch = parent_orchestrator or UATOrchestrator(
        agent_id="UA1_UAT_ORCHESTRATOR",
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

    logger.info("Successfully registered %d UAT domain agents into registry.", registered_count)
    return {
        "uat_orchestrator": orch,
        "total_registered": registered_count,
    }
