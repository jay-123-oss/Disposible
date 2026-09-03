"""Comprehensive Unit Test Suite for Security Layer Agents (Session 6)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.security import (
    AlgorithmChecker,
    AuthChecker,
    BreachChecker,
    ComplianceChecker,
    CSRFChecker,
    EncryptionValidator,
    GdprChecker,
    HashVerifier,
    HipaaChecker,
    InputSanitizer,
    OutputEncoder,
    ParameterValidator,
    PasswordValidator,
    PermissionAuditor,
    PolicyEnforcer,
    QueryAnalyzer,
    RoleChecker,
    SecurityOrchestrator,
    SQLInjectionScanner,
    StrengthChecker,
    TokenChecker,
    TokenValidator,
    XSSScanner,
    register_all_security_agents,
)
from core.registry import AgentRegistry


class TestSecurityAgents(unittest.TestCase):
    """Test suite covering all 16 Security domain agents and fractal subagent structures."""

    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.registry.clear()

    def test_security_orchestrator_spawns_subsystems(self) -> None:
        """Verify SecurityOrchestrator spawns all 7 L4 security audit coordinators."""
        orch = SecurityOrchestrator(agent_id="TEST_SEC_ORCH", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(orch.auth_checker)
        self.assertIsNotNone(orch.permission_auditor)
        self.assertIsNotNone(orch.sql_scanner)
        self.assertIsNotNone(orch.xss_scanner)
        self.assertIsNotNone(orch.csrf_checker)
        self.assertIsNotNone(orch.encryption_validator)
        self.assertIsNotNone(orch.compliance_checker)

        child_names = [c.name for c in orch.children.values()]
        self.assertIn("AuthChecker", child_names)
        self.assertIn("PermissionAuditor", child_names)
        self.assertIn("SQLInjectionScanner", child_names)
        self.assertIn("XSSScanner", child_names)
        self.assertIn("CSRFChecker", child_names)
        self.assertIn("EncryptionValidator", child_names)
        self.assertIn("ComplianceChecker", child_names)

    def test_auth_checker_spawns_validators(self) -> None:
        """Verify AuthChecker spawns PasswordValidator and TokenValidator."""
        ac = AuthChecker(agent_id="TEST_AC", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(ac.password_validator)
        self.assertIsNotNone(ac.token_validator)

        self.assertIsInstance(ac.password_validator, PasswordValidator)
        self.assertIsInstance(ac.token_validator, TokenValidator)

    def test_password_validator_spawns_atomic_verifiers(self) -> None:
        """Verify PasswordValidator spawns StrengthChecker, HashVerifier, BreachChecker."""
        pv = PasswordValidator(agent_id="TEST_PV")
        self.assertIsNotNone(pv.strength_checker)
        self.assertIsNotNone(pv.hash_verifier)
        self.assertIsNotNone(pv.breach_checker)

        self.assertIsInstance(pv.strength_checker, StrengthChecker)
        self.assertIsInstance(pv.hash_verifier, HashVerifier)
        self.assertIsInstance(pv.breach_checker, BreachChecker)

    def test_permission_auditor_spawns_subsystems(self) -> None:
        """Verify PermissionAuditor spawns RoleChecker and PolicyEnforcer."""
        pa = PermissionAuditor(agent_id="TEST_PA", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(pa.role_checker)
        self.assertIsNotNone(pa.policy_enforcer)

        self.assertIsInstance(pa.role_checker, RoleChecker)
        self.assertIsInstance(pa.policy_enforcer, PolicyEnforcer)

    def test_sql_injection_scanner_spawns_subsystems(self) -> None:
        """Verify SQLInjectionScanner spawns QueryAnalyzer and ParameterValidator."""
        sq = SQLInjectionScanner(agent_id="TEST_SQ", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(sq.query_analyzer)
        self.assertIsNotNone(sq.parameter_validator)

        self.assertIsInstance(sq.query_analyzer, QueryAnalyzer)
        self.assertIsInstance(sq.parameter_validator, ParameterValidator)

    def test_query_analyzer_catches_unparameterized_sql(self) -> None:
        """Verify QueryAnalyzer flags raw SQL string formatting as a vulnerability."""
        qa = QueryAnalyzer(agent_id="TEST_QA")
        dirty_code = ["cursor.execute(f'SELECT * FROM users WHERE email = {email}')"]
        res = qa.analyze_queries(dirty_code)
        self.assertFalse(res["passed"])
        self.assertGreater(len(res["flaws_detected"]), 0)

    def test_xss_scanner_spawns_subsystems(self) -> None:
        """Verify XSSScanner spawns OutputEncoder and InputSanitizer."""
        xs = XSSScanner(agent_id="TEST_XS", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(xs.output_encoder)
        self.assertIsNotNone(xs.input_sanitizer)

        self.assertIsInstance(xs.output_encoder, OutputEncoder)
        self.assertIsInstance(xs.input_sanitizer, InputSanitizer)

    def test_csrf_checker_spawns_subsystems(self) -> None:
        """Verify CSRFChecker spawns TokenChecker and ReferrerValidator."""
        csrf = CSRFChecker(agent_id="TEST_CSRF", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(csrf.token_checker)
        self.assertIsNotNone(csrf.referrer_validator)

        self.assertIsInstance(csrf.token_checker, TokenChecker)

    def test_encryption_validator_spawns_subsystems(self) -> None:
        """Verify EncryptionValidator spawns AlgorithmChecker and KeyManager."""
        ev = EncryptionValidator(agent_id="TEST_EV", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(ev.algo_checker)
        self.assertIsNotNone(ev.key_manager)

        self.assertIsInstance(ev.algo_checker, AlgorithmChecker)

    def test_compliance_checker_spawns_subsystems(self) -> None:
        """Verify ComplianceChecker spawns GdprChecker and HipaaChecker."""
        cc = ComplianceChecker(agent_id="TEST_CC", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(cc.gdpr_checker)
        self.assertIsNotNone(cc.hipaa_checker)

        self.assertIsInstance(cc.gdpr_checker, GdprChecker)
        self.assertIsInstance(cc.hipaa_checker, HipaaChecker)

    def test_security_orchestrator_end_to_end_audit(self) -> None:
        """Verify SecurityOrchestrator executes full audit, aggregates findings, and validates gate."""
        orch = SecurityOrchestrator(agent_id="TEST_SEC_E2E", auto_spawn_subagents=True, max_depth=7)
        envelope = {
            "task_id": "T_SECURITY_E2E",
            "payload": {
                "auth_config": {"min_password_length": 12, "jwt_algorithm": "RS256"},
                "permissions_config": {"enforce_rbac": True, "roles": ["user", "admin"]},
                "code_snippets": ["stmt = select(User).where(User.id == entity_id)"],
                "raw_inputs": ["clean_user_input"],
            },
        }
        result = orch.execute_lifecycle(envelope)

        self.assertEqual(result["status"], "COMPLETED")
        audit_report = result["security_audit_report"]
        self.assertIn("overall_security_score", audit_report)
        self.assertIn("gate_approved", audit_report)
        self.assertTrue(audit_report["gate_approved"])
        self.assertGreaterEqual(audit_report["overall_security_score"], 85.0)
        self.assertIn("vulnerability_counts", audit_report)
        self.assertIn("subsystem_results", audit_report)

    def test_register_all_security_agents(self) -> None:
        """Verify registration helper registers all security agents into AgentRegistry."""
        res = register_all_security_agents(self.registry, max_depth=7)
        total = res["total_registered"]
        self.assertGreaterEqual(total, 16)
        self.assertIsNotNone(self.registry.get_agent("S1_SECURITY_ORCHESTRATOR"))


if __name__ == "__main__":
    unittest.main()
