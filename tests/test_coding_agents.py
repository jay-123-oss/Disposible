"""Comprehensive Unit Test Suite for Coding Layer Agents (Session 4)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.coding import (
    APIRouteAgent,
    AlterTable,
    AuthController,
    AuthMiddleware,
    AuthService,
    BackendAgent,
    ControllerAgent,
    CreateTable,
    DatabaseAgent,
    DELETERouteAgent,
    DropTable,
    GETRouteAgent,
    InsertQuery,
    LoggingMiddleware,
    MigrationAgent,
    MiddlewareAgent,
    ModelAgent,
    POSTRouteAgent,
    PUTRouteAgent,
    QueryAgent,
    RateLimiter,
    RouteResponseFormatter,
    RouteServiceCaller,
    RouteValidator,
    SelectQuery,
    ServiceAgent,
    SessionModel,
    UpdateQuery,
    UserController,
    UserModel,
    UserService,
    register_all_coding_agents,
)
from core.registry import AgentRegistry


class TestCodingAgents(unittest.TestCase):
    """Test suite covering all 24 Coding domain agents and fractal subagent structures."""

    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.registry.clear()

    def test_backend_agent_spawns_subsystems(self) -> None:
        """Verify BackendAgent spawns the 5 L4 subsystem coordinators."""
        backend = BackendAgent(agent_id="TEST_BACKEND", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(backend.api_agent)
        self.assertIsNotNone(backend.middleware_agent)
        self.assertIsNotNone(backend.controller_agent)
        self.assertIsNotNone(backend.service_agent)
        self.assertIsNotNone(backend.database_agent)

        # Verify child names in children map
        child_names = [c.name for c in backend.children.values()]
        self.assertIn("APIRouteAgent", child_names)
        self.assertIn("MiddlewareAgent", child_names)
        self.assertIn("ControllerAgent", child_names)
        self.assertIn("ServiceAgent", child_names)
        self.assertIn("DatabaseAgent", child_names)

    def test_api_route_agent_spawns_verbs(self) -> None:
        """Verify APIRouteAgent spawns GET, POST, PUT, DELETE route agents."""
        api = APIRouteAgent(agent_id="TEST_API", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(api.get_agent)
        self.assertIsNotNone(api.post_agent)
        self.assertIsNotNone(api.put_agent)
        self.assertIsNotNone(api.delete_agent)

        self.assertIsInstance(api.get_agent, GETRouteAgent)
        self.assertIsInstance(api.post_agent, POSTRouteAgent)
        self.assertIsInstance(api.put_agent, PUTRouteAgent)
        self.assertIsInstance(api.delete_agent, DELETERouteAgent)

    def test_route_handlers_spawn_triplets(self) -> None:
        """Verify route agents spawn Validator, ServiceCaller, and ResponseFormatter."""
        get_agent = GETRouteAgent()
        self.assertIsNotNone(get_agent.validator)
        self.assertIsNotNone(get_agent.service_caller)
        self.assertIsNotNone(get_agent.response_formatter)

        self.assertIsInstance(get_agent.validator, RouteValidator)
        self.assertIsInstance(get_agent.service_caller, RouteServiceCaller)
        self.assertIsInstance(get_agent.response_formatter, RouteResponseFormatter)

    def test_middleware_agent_spawns_handlers(self) -> None:
        """Verify MiddlewareAgent spawns Auth, Logging, and RateLimiter."""
        mw = MiddlewareAgent(agent_id="TEST_MW", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(mw.auth_agent)
        self.assertIsNotNone(mw.logging_agent)
        self.assertIsNotNone(mw.rate_limiter)

        self.assertIsInstance(mw.auth_agent, AuthMiddleware)
        self.assertIsInstance(mw.logging_agent, LoggingMiddleware)
        self.assertIsInstance(mw.rate_limiter, RateLimiter)

    def test_controller_agent_spawns_controllers(self) -> None:
        """Verify ControllerAgent spawns AuthController and UserController."""
        ctrl = ControllerAgent(agent_id="TEST_CTRL", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(ctrl.auth_controller)
        self.assertIsNotNone(ctrl.user_controller)

        self.assertIsInstance(ctrl.auth_controller, AuthController)
        self.assertIsInstance(ctrl.user_controller, UserController)

    def test_service_agent_spawns_services(self) -> None:
        """Verify ServiceAgent spawns AuthService and UserService."""
        svc = ServiceAgent(agent_id="TEST_SVC", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(svc.auth_service)
        self.assertIsNotNone(svc.user_service)

        self.assertIsInstance(svc.auth_service, AuthService)
        self.assertIsInstance(svc.user_service, UserService)

    def test_database_agent_spawns_database_subsystems(self) -> None:
        """Verify DatabaseAgent spawns ModelAgent, QueryAgent, and MigrationAgent."""
        db = DatabaseAgent(agent_id="TEST_DB", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(db.model_agent)
        self.assertIsNotNone(db.query_agent)
        self.assertIsNotNone(db.migration_agent)

        self.assertIsInstance(db.model_agent, ModelAgent)
        self.assertIsInstance(db.query_agent, QueryAgent)
        self.assertIsInstance(db.migration_agent, MigrationAgent)

    def test_model_agent_spawns_models(self) -> None:
        """Verify ModelAgent spawns UserModel and SessionModel."""
        models = ModelAgent(agent_id="TEST_MODELS", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(models.user_model)
        self.assertIsNotNone(models.session_model)

        self.assertIsInstance(models.user_model, UserModel)
        self.assertIsInstance(models.session_model, SessionModel)

    def test_query_agent_spawns_queries(self) -> None:
        """Verify QueryAgent spawns SelectQuery, InsertQuery, and UpdateQuery."""
        queries = QueryAgent(agent_id="TEST_QUERIES", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(queries.select_query)
        self.assertIsNotNone(queries.insert_query)
        self.assertIsNotNone(queries.update_query)

        self.assertIsInstance(queries.select_query, SelectQuery)
        self.assertIsInstance(queries.insert_query, InsertQuery)
        self.assertIsInstance(queries.update_query, UpdateQuery)

    def test_migration_agent_spawns_ddl_builders(self) -> None:
        """Verify MigrationAgent spawns CreateTable, AlterTable, and DropTable."""
        migrations = MigrationAgent(agent_id="TEST_MIGRATIONS", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(migrations.create_table)
        self.assertIsNotNone(migrations.alter_table)
        self.assertIsNotNone(migrations.drop_table)

        self.assertIsInstance(migrations.create_table, CreateTable)
        self.assertIsInstance(migrations.alter_table, AlterTable)
        self.assertIsInstance(migrations.drop_table, DropTable)

    def test_backend_agent_end_to_end_synthesis(self) -> None:
        """Verify BackendAgent generates complete runnable code bundle."""
        backend = BackendAgent(agent_id="TEST_BACKEND_E2E", auto_spawn_subagents=True, max_depth=7)
        envelope = {"task_id": "T_BACKEND_E2E", "payload": {"entity": "account"}}
        result = backend.execute_lifecycle(envelope)

        self.assertEqual(result["status"], "COMPLETED")
        artifacts = result["backend_artifacts"]
        self.assertIn("main_app_code", artifacts)
        self.assertIn("fastapi", artifacts["main_app_code"].lower())
        self.assertIn("database", artifacts)
        self.assertIn("services", artifacts)
        self.assertIn("controllers", artifacts)
        self.assertIn("middleware", artifacts)
        self.assertIn("api_routes", artifacts)

    def test_register_all_coding_agents(self) -> None:
        """Verify registration helper registers all agents into AgentRegistry."""
        res = register_all_coding_agents(self.registry, max_depth=7)
        total = res["total_registered"]
        self.assertGreaterEqual(total, 24)
        self.assertIsNotNone(self.registry.get_agent("C1_BACKEND_AGENT"))


if __name__ == "__main__":
    unittest.main()
