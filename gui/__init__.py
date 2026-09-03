"""Web-Based GUI Dashboard Layer Package.

Exports all 14 agents, 52 widgets, exceptions, and registration helper.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from core.registry import AgentRegistry
from gui.exceptions import (
    AgentVisualizationError,
    APITesterError,
    CodeEditorError,
    DashboardError,
    GUIError,
    HelpDocsError,
    LogViewerError,
    PerformanceDashboardError,
    ReportViewerError,
    SecurityDashboardError,
    SettingsError,
    TaskTrackingError,
    TestRunnerError,
    UserManagementError,
)
from gui.gui_orchestrator import (
    # L3 Orchestrator
    GUIOrchestrator,
    # L4 Coordinators
    DashboardRenderer,
    AgentVisualizer,
    TaskTrackerUI,
    CodeEditorUI,
    TestRunnerUI,
    SecurityDashboard,
    PerformanceDashboard,
    LogViewerUI,
    SettingsUI,
    UserManagementUI,
    ReportViewerUI,
    APITesterUI,
    HelpDocsUI,
    # L5 Subagent Widgets
    SystemStatusWidget,
    AgentStatusWidget,
    TaskSummaryWidget,
    MetricsWidget,
    AgentTreeRenderer,
    AgentDetailViewer,
    AgentHealthIndicator,
    AgentControlPanel,
    TaskListViewer,
    TaskDetailViewer,
    TaskCreatorUI,
    TaskHistoryViewer,
    CodeEditor,
    FileBrowser,
    SyntaxHighlighter,
    AutoCompleteUI,
    TestSelector,
    TestExecutorUI,
    TestResultsViewer,
    CoverageViewer,
    AuthStatusViewer,
    VulnerabilityViewer,
    ComplianceViewer,
    SecurityScoreViewer,
    ResponseTimeGraph,
    ThroughputGraph,
    ResourceUsageGraph,
    LatencyGraph,
    LogFilter,
    LogSearcher,
    LogDetailViewer,
    LogExporter,
    SystemSettings,
    AgentSettings,
    ModelSettings,
    UserSettings,
    UserListViewer,
    UserCreatorUI,
    RoleManagerUI,
    PermissionViewer,
    ReportListViewer,
    ReportDetailViewer,
    ReportExporter,
    ReportSchedulerUI,
    APIEndpointSelector,
    APIRequestBuilder,
    APIResponseViewer,
    APIHistoryViewer,
    DocumentationViewer,
    SearchHelper,
    FAQViewer,
    TutorialViewer,
)

logger = logging.getLogger("FractalCore.GUI")

__all__ = [
    "GUIOrchestrator",
    "DashboardRenderer",
    "AgentVisualizer",
    "TaskTrackerUI",
    "CodeEditorUI",
    "TestRunnerUI",
    "SecurityDashboard",
    "PerformanceDashboard",
    "LogViewerUI",
    "SettingsUI",
    "UserManagementUI",
    "ReportViewerUI",
    "APITesterUI",
    "HelpDocsUI",
    "SystemStatusWidget",
    "AgentStatusWidget",
    "TaskSummaryWidget",
    "MetricsWidget",
    "AgentTreeRenderer",
    "AgentDetailViewer",
    "AgentHealthIndicator",
    "AgentControlPanel",
    "TaskListViewer",
    "TaskDetailViewer",
    "TaskCreatorUI",
    "TaskHistoryViewer",
    "CodeEditor",
    "FileBrowser",
    "SyntaxHighlighter",
    "AutoCompleteUI",
    "TestSelector",
    "TestExecutorUI",
    "TestResultsViewer",
    "CoverageViewer",
    "AuthStatusViewer",
    "VulnerabilityViewer",
    "ComplianceViewer",
    "SecurityScoreViewer",
    "ResponseTimeGraph",
    "ThroughputGraph",
    "ResourceUsageGraph",
    "LatencyGraph",
    "LogFilter",
    "LogSearcher",
    "LogDetailViewer",
    "LogExporter",
    "SystemSettings",
    "AgentSettings",
    "ModelSettings",
    "UserSettings",
    "UserListViewer",
    "UserCreatorUI",
    "RoleManagerUI",
    "PermissionViewer",
    "ReportListViewer",
    "ReportDetailViewer",
    "ReportExporter",
    "ReportSchedulerUI",
    "APIEndpointSelector",
    "APIRequestBuilder",
    "APIResponseViewer",
    "APIHistoryViewer",
    "DocumentationViewer",
    "SearchHelper",
    "FAQViewer",
    "TutorialViewer",
    "GUIError",
    "DashboardError",
    "AgentVisualizationError",
    "TaskTrackingError",
    "CodeEditorError",
    "TestRunnerError",
    "SecurityDashboardError",
    "PerformanceDashboardError",
    "LogViewerError",
    "SettingsError",
    "UserManagementError",
    "ReportViewerError",
    "APITesterError",
    "HelpDocsError",
    "register_all_gui_agents",
]


def register_all_gui_agents(
    registry: AgentRegistry,
    parent_orchestrator: Optional[GUIOrchestrator] = None,
    max_depth: int = 7,
) -> Dict[str, Any]:
    """Instantiate and register all 14 GUI agents and 52 widgets into registry."""
    orch = parent_orchestrator or GUIOrchestrator(
        agent_id="G1_GUI_ORCHESTRATOR",
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

    logger.info("Successfully registered %d GUI domain agents into registry.", registered_count)
    return {
        "gui_orchestrator": orch,
        "total_registered": registered_count,
    }
