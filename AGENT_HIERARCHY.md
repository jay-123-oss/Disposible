# AGENT_HIERARCHY.md: Complete Fractal Agent Tree & Registry Catalog

## 1. Fractal Agent Design Principles

The agent hierarchy is governed by six immutable mathematical axioms designed to prevent coordination bloat, infinite loops, and context exhaustion:

* **Rule 1 (Universal Branching):** Every non-leaf agent ($L0$ through $L6$) possesses the capability to spawn specialized child sub-agents to partition its assigned problem space.
* **Rule 2 (Atomic Termination):** The sub-agent decomposition chain continues recursively until the assigned sub-task satisfies the definition of an **Atomic Unit of Work** (a single AST modification, schema definition, pure function, or validation rule).
* **Rule 3 (Strict Specialization):** Each descending sub-agent is strictly more specialized than its parent. Context scope narrows by at least $50\%$ at each descending tier.
* **Rule 4 (No Horizontal Lateral Cross-Talk):** Agents at the same level of the tree cannot directly communicate, pass messages, or invoke each other. All lateral coordination must occur asynchronously via the Stigmergy Blackboard or vertically through their common supervising parent.
* **Rule 5 (Relative Depth Bound - `maxDepth = 2`):** Within any given agent's immediate supervisory lifecycle, it may only instantiate and manage up to two tiers down: Parent $\rightarrow$ Child $\rightarrow$ Grandchild. An agent cannot directly supervise beyond its grandchildren. Overall global depth is bounded at Level 7.
* **Rule 6 (Leaf Execution Exclusivity):** Leaf agents ($L7$) execute the actual mutations (file writes, test executions, AST modifications). Parent agents are pure coordinators, evaluators, and synthesizers; they never write code directly to disk.

---

## 2. Agent Registry Schema

Every agent registered in the system is defined by a strictly validated JSON structure conforming to the following schema:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AgentRegistryEntry",
  "type": "object",
  "required": [
    "agent_id",
    "agent_name",
    "level",
    "parent_id",
    "children_ids",
    "capabilities",
    "tools",
    "max_depth",
    "state",
    "resource_requirements"
  ],
  "properties": {
    "agent_id": {
      "type": "string",
      "pattern": "^[A-Z0-9_]{3,32}$",
      "description": "Unique deterministic agent identifier"
    },
    "agent_name": {
      "type": "string",
      "description": "Descriptive PascalCase agent role name"
    },
    "level": {
      "type": "integer",
      "minimum": 0,
      "maximum": 7,
      "description": "Hierarchical level in the fractal tree"
    },
    "parent_id": {
      "type": ["string", "null"],
      "description": "Agent ID of the direct supervising parent"
    },
    "children_ids": {
      "type": "array",
      "items": { "type": "string" },
      "description": "List of subordinate agent IDs"
    },
    "capabilities": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Declared functional capabilities of this agent"
    },
    "tools": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Specific tool functions permitted for invocation"
    },
    "max_depth": {
      "type": "integer",
      "maximum": 2,
      "description": "Maximum relative depth of sub-agents permitted (Rule 5)"
    },
    "state": {
      "type": "string",
      "enum": ["idle", "working", "waiting", "completed", "failed"],
      "description": "Current lifecycle status"
    },
    "resource_requirements": {
      "type": "object",
      "required": ["ram_mb", "model"],
      "properties": {
        "ram_mb": { "type": "integer", "maximum": 512 },
        "model": { 
          "type": "string", 
          "enum": ["qwen2.5-coder:3b", "llama3.2:3b", "deterministic-rules"] 
        }
      }
    }
  }
}
```

---

## 3. High-Level Hierarchical Tree Overview

```
L0: META_ORCHESTRATOR (ORCH_001)
├── L1: PLANNING_DOMAIN (PLAN_001)
│   ├── L2: SPEC_PARSER_MODULE (SPEC_001)
│   ├── L2: ARCH_DESIGNER_MODULE (ARCH_001)
│   └── L2: TASK_DECOMPOSER_MODULE (DEC_001)
│
├── L1: DEVELOPMENT_DOMAIN (DEV_001)
│   ├── L2: BACKEND_MODULE (BACK_001)
│   │   ├── L3: API_COMPONENT (API_001)
│   │   │   ├── L4: ROUTE_CONTROLLER (RTE_001)
│   │   │   │   ├── L5: GET_ROUTE_OP (GROP_001)
│   │   │   │   │   ├── L6: GET_ROUTE_TASK (GRT_001)
│   │   │   │   │   │   ├── L7: GET_VALIDATOR (L7_VAL_01) [ATOMIC]
│   │   │   │   │   │   ├── L7: GET_SERVICE_CALLER (L7_SVC_01) [ATOMIC]
│   │   │   │   │   │   └── L7: GET_RESPONSE_FORMATTER (L7_FMT_01) [ATOMIC]
│   │   │   │   │   └── L6: POST_ROUTE_TASK (PRT_001)
│   │   │   │   │       ├── L7: POST_VALIDATOR (L7_VAL_02) [ATOMIC]
│   │   │   │   │       ├── L7: POST_SERVICE_CALLER (L7_SVC_02) [ATOMIC]
│   │   │   │   │       └── L7: POST_RESPONSE_FORMATTER (L7_FMT_02) [ATOMIC]
│   │   │   │   └── L5: PUT_ROUTE_OP (PROP_001)
│   │   │   │       └── L6: PUT_ROUTE_TASK (PURT_001)
│   │   │   │           ├── L7: PUT_VALIDATOR (L7_VAL_03) [ATOMIC]
│   │   │   │           ├── L7: PUT_SERVICE_CALLER (L7_SVC_03) [ATOMIC]
│   │   │   │           └── L7: PUT_RESPONSE_FORMATTER (L7_FMT_03) [ATOMIC]
│   │   │   ├── L4: MIDDLEWARE_CONTROLLER (MID_001)
│   │   │   │   ├── L5: AUTH_MIDDLEWARE_OP (AMID_001)
│   │   │   │   │   └── L6: TOKEN_VERIFIER_TASK (TVT_001)
│   │   │   │   │       ├── L7: JWT_PARSER (L7_JWT_01) [ATOMIC]
│   │   │   │   │       ├── L7: USER_EXTRACTOR (L7_USR_01) [ATOMIC]
│   │   │   │   │       └── L7: PERMISSION_CHECKER (L7_PRM_01) [ATOMIC]
│   │   │   │   └── L5: LOGGING_MIDDLEWARE_OP (LMID_001)
│   │   │   │       └── L6: LOG_FORMATTER_TASK (LFT_001)
│   │   │   │           ├── L7: REQUEST_LOGGER (L7_LOG_01) [ATOMIC]
│   │   │   │           └── L7: RESPONSE_LOGGER (L7_LOG_02) [ATOMIC]
│   │   │   └── L4: CONTROLLER_ORCHESTRATOR (CTRL_001)
│   │   │       ├── L5: AUTH_CONTROLLER_OP (ACTR_001)
│   │   │       │   └── L6: AUTH_HANDLER_TASK (AHT_001)
│   │   │       │       ├── L7: REGISTER_HANDLER (L7_HND_01) [ATOMIC]
│   │   │       │       ├── L7: LOGIN_HANDLER (L7_HND_02) [ATOMIC]
│   │   │       │       └── L7: LOGOUT_HANDLER (L7_HND_03) [ATOMIC]
│   │   │       └── L5: USER_CONTROLLER_OP (UCTR_001)
│   │   │           └── L6: USER_HANDLER_TASK (UHT_001)
│   │   │               ├── L7: GET_PROFILE_WORKER (L7_HND_04) [ATOMIC]
│   │   │               ├── L7: UPDATE_PROFILE_WORKER (L7_HND_05) [ATOMIC]
│   │   │               └── L7: DELETE_USER_WORKER (L7_HND_06) [ATOMIC]
│   │   ├── L3: SERVICE_COMPONENT (SVC_001)
│   │   │   ├── L4: AUTH_SERVICE_ORCH (ASVC_001)
│   │   │   │   ├── L5: REGISTER_SERVICE_OP (RSVC_001)
│   │   │   │   │   └── L6: REGISTRATION_PIPELINE (RPL_001)
│   │   │   │   │       ├── L7: PASSWORD_HASHER (L7_SEC_01) [ATOMIC]
│   │   │   │   │       ├── L7: USER_RECORD_CREATOR (L7_DB_01) [ATOMIC]
│   │   │   │   │       └── L7: TOKEN_GENERATOR (L7_SEC_02) [ATOMIC]
│   │   │   │   └── L5: LOGIN_SERVICE_OP (LSVC_001)
│   │   │   │       └── L6: LOGIN_PIPELINE (LPL_001)
│   │   │   │           ├── L7: USER_RECORD_FINDER (L7_DB_02) [ATOMIC]
│   │   │   │           └── L7: PASSWORD_VERIFIER (L7_SEC_03) [ATOMIC]
│   │   │   └── L4: USER_SERVICE_ORCH (USVC_001)
│   │   │       └── L5: USER_OP (UOP_001)
│   │   │           └── L6: USER_MANAGEMENT_TASK (UMT_001)
│   │   │               ├── L7: PROFILE_GETTER (L7_USR_02) [ATOMIC]
│   │   │               ├── L7: PROFILE_UPDATER (L7_USR_03) [ATOMIC]
│   │   │               └── L7: USER_DELETER (L7_USR_04) [ATOMIC]
│   │   └── L3: DATABASE_COMPONENT (DB_001)
│   │       ├── L4: MODEL_ORCHESTRATOR (MDL_001)
│   │       │   ├── L5: USER_MODEL_OP (UMDL_001)
│   │       │   │   └── L6: USER_SCHEMA_TASK (UST_001)
│   │       │   │       ├── L7: USER_SCHEMA_DEFINER (L7_SCH_01) [ATOMIC]
│   │       │   │       └── L7: USER_FIELD_VALIDATOR (L7_SCH_02) [ATOMIC]
│   │       │   └── L5: SESSION_MODEL_OP (SMDL_001)
│   │       │       └── L6: SESSION_SCHEMA_TASK (SST_001)
│   │       │           ├── L7: SESSION_SCHEMA_DEFINER (L7_SCH_03) [ATOMIC]
│   │       │           └── L7: EXPIRY_HANDLER (L7_SCH_04) [ATOMIC]
│   │       ├── L4: QUERY_ORCHESTRATOR (QRY_001)
│   │       │   ├── L5: SELECT_QUERY_OP (SEL_001)
│   │       │   │   └── L6: SELECT_BUILDER_TASK (SBT_001)
│   │       │   │       ├── L7: WHERE_CLAUSE_BUILDER (L7_SQL_01) [ATOMIC]
│   │       │   │       └── L7: JOIN_CLAUSE_BUILDER (L7_SQL_02) [ATOMIC]
│   │       │   └── L5: INSERT_QUERY_OP (INS_001)
│   │       │       └── L6: INSERT_BUILDER_TASK (IBT_001)
│   │       │           ├── L7: VALUE_BUILDER (L7_SQL_03) [ATOMIC]
│   │       │           └── L7: RETURNING_BUILDER (L7_SQL_04) [ATOMIC]
│   │       └── L4: MIGRATION_ORCHESTRATOR (MIG_001)
│   │           └── L5: DDL_OP (DDL_001)
│   │               └── L6: DDL_TASK (DTK_001)
│   │                   ├── L7: CREATE_TABLE_BUILDER (L7_DDL_01) [ATOMIC]
│   │                   ├── L7: ALTER_TABLE_BUILDER (L7_DDL_02) [ATOMIC]
│   │                   └── L7: DROP_TABLE_BUILDER (L7_DDL_03) [ATOMIC]
│   └── L2: FRONTEND_MODULE (FRONT_001)
│       └── L3: UI_COMPONENT_ORCH (UIC_001)
│           ├── L7: COMPONENT_TEMPLATE_GEN (L7_FE_01) [ATOMIC]
│           └── L7: STATE_BINDER (L7_FE_02) [ATOMIC]
│
├── L1: TESTING_DOMAIN (TEST_001)
│   ├── L2: UNIT_TEST_MODULE (UTEST_001)
│   │   ├── L7: TEST_CASE_GENERATOR (L7_TST_01) [ATOMIC]
│   │   ├── L7: MOCK_OBJECT_FACTORY (L7_TST_02) [ATOMIC]
│   │   └── L7: TEST_RUNNER_EXECUTOR (L7_TST_03) [ATOMIC]
│   ├── L2: INTEGRATION_TEST_MODULE (ITEST_001)
│   │   ├── L7: API_TEST_CLIENT_RUNNER (L7_TST_04) [ATOMIC]
│   │   └── L7: DB_FIXTURE_ISOLATOR (L7_TST_05) [ATOMIC]
│   └── L2: REGRESSION_TEST_MODULE (RTEST_001)
│       ├── L7: AST_DIFF_VERIFIER (L7_TST_06) [ATOMIC]
│       └── L7: COVERAGE_ANALYZER (L7_TST_07) [ATOMIC]
│
├── L1: SECURITY_DOMAIN (SEC_001)
│   ├── L2: STATIC_ANALYSIS_MODULE (SAST_001)
│   │   ├── L7: VULN_PATTERN_SCANNER (L7_SEC_04) [ATOMIC]
│   │   └── L7: SECRET_LEAK_DETECTOR (L7_SEC_05) [ATOMIC]
│   └── L2: DEPENDENCY_AUDIT_MODULE (DEPAUD_001)
│       ├── L7: CVE_DATABASE_MATCHER (L7_SEC_06) [ATOMIC]
│       └── L7: LICENSE_COMPLIANCE_CHECK (L7_SEC_07) [ATOMIC]
│
├── L1: DEPLOYMENT_DOMAIN (DEP_001)
│   ├── L2: BUILD_PACKAGE_MODULE (BLD_001)
│   │   ├── L7: DOCKERFILE_GENERATOR (L7_DEP_01) [ATOMIC]
│   │   └── L7: CONTAINER_LINTER (L7_DEP_02) [ATOMIC]
│   └── L2: MIGRATION_DEPLOY_MODULE (MDEP_001)
│       └── L7: MIGRATION_APPLY_WORKER (L7_DEP_03) [ATOMIC]
│
└── L1: MONITORING_DOMAIN (MON_001)
    ├── L2: DRIFT_DETECTOR_MODULE (DRF_001)
    │   ├── L7: WORKING_TREE_INSPECTOR (L7_MON_01) [ATOMIC]
    │   └── L7: IDEMPOTENCY_VERIFIER (L7_MON_02) [ATOMIC]
    └── L2: TELEMETRY_MODULE (TEL_001)
        ├── L7: TOKEN_USAGE_CALCULATOR (L7_MON_03) [ATOMIC]
        └── L7: RAM_PRESSURE_MONITOR (L7_MON_04) [ATOMIC]
```

---

## 4. Complete Catalog of All 56 Specialized Agents

The system defines 56 fully-specified, distinct agent roles partitioned across all operational domains.

### 4.1 Orchestration & Planning Domains (Agents 1 - 7)

| Agent ID | Agent Name | Level | Direct Parent | Children IDs | Responsibility | Assigned Tools | Model / RAM |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ORCH_001` | `MetaOrchestrator` | 0 | `None` | `PLAN_001`, `DEV_001`, `TEST_001`, `SEC_001`, `DEP_001`, `MON_001` | System boot, lifecycle management, user input intake, global quality approval, final sign-off. | `task_queue_read`, `state_commit`, `abort_session`, `write_manifest` | `qwen2.5-coder:3b`<br>512MB |
| `PLAN_001` | `PlanningDomain` | 1 | `ORCH_001` | `SPEC_001`, `ARCH_001`, `DEC_001` | Coordinates requirements analysis, architectural synthesis, and execution graph compilation. | `read_spec`, `publish_plan`, `validate_dag` | `qwen2.5-coder:3b`<br>512MB |
| `SPEC_001` | `SpecParserModule` | 2 | `PLAN_001` | `None` (Calls tools) | Parses natural language user prompt into typed input/output specifications and constraints. | `parse_user_intent`, `extract_entities`, `write_artifact` | `llama3.2:3b`<br>512MB |
| `ARCH_001` | `ArchDesignerModule`| 2 | `PLAN_001` | `None` (Calls tools) | Selects system design patterns, defines folder structures, and designs interface contracts. | `pattern_matcher`, `tree_template_gen`, `write_artifact` | `qwen2.5-coder:3b`<br>512MB |
| `DEC_001` | `TaskDecomposerModule`| 2 | `PLAN_001` | `None` (Calls tools) | Compiles the target architecture into a formal Directed Acyclic Graph (DAG) with dependencies. | `dag_builder`, `dependency_sorter`, `write_task_store` | `qwen2.5-coder:3b`<br>512MB |
| `MON_001` | `MonitoringDomain` | 1 | `ORCH_001` | `DRF_001`, `TEL_001` | Supervises system runtime invariants, resource quotas, and tool state drift detection. | `read_telemetry`, `emit_alert`, `trigger_gc` | `deterministic-rules`<br>256MB |
| `TEL_001` | `TelemetryModule` | 2 | `MON_001` | `L7_MON_03`, `L7_MON_04` | Tracks token usage, latency metrics, and hardware RAM consumption across workers. | `proc_status`, `token_counter`, `aggregate_metrics` | `deterministic-rules`<br>256MB |

### 4.2 Development Domain: Backend Sub-Tree (Agents 8 - 36)

| Agent ID | Agent Name | Level | Direct Parent | Children IDs | Responsibility | Assigned Tools | Model / RAM |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `DEV_001` | `DevelopmentDomain` | 1 | `ORCH_001` | `BACK_001`, `FRONT_001` | Controls code synthesis pipelines and ensures all atomic patches pass local compilation. | `read_task_dag`, `dispatch_module`, `verify_syntax` | `qwen2.5-coder:3b`<br>512MB |
| `BACK_001` | `BackendModule` | 2 | `DEV_001` | `API_001`, `SVC_001`, `DB_001` | Supervises API routes, business logic layer, and database ORM layer. | `inspect_backend_tree`, `coordinate_subsystems` | `qwen2.5-coder:3b`<br>512MB |
| `API_001` | `ApiComponent` | 3 | `BACK_001` | `RTE_001`, `MID_001`, `CTRL_001` | Oversees REST routing, HTTP middleware stack, and controller dispatch. | `check_openapi_spec`, `verify_endpoint_map` | `qwen2.5-coder:3b`<br>512MB |
| `RTE_001` | `RouteController` | 4 | `API_001` | `GROP_001`, `PROP_001` | Manages HTTP route declarations and URL path binding. | `ast_route_map`, `split_http_verbs` | `qwen2.5-coder:3b`<br>512MB |
| `GROP_001` | `GetRouteOp` | 5 | `RTE_001` | `GRT_001` | Operations group for HTTP GET route handling. | `route_spec_read`, `task_split` | `qwen2.5-coder:3b`<br>512MB |
| `GRT_001` | `GetRouteTask` | 6 | `GROP_001` | `L7_VAL_01`, `L7_SVC_01`, `L7_FMT_01` | Supervises code generation for a single atomic GET route. | `assemble_route_block`, `ast_insert` | `qwen2.5-coder:3b`<br>512MB |
| `L7_VAL_01`| `GetValidator` | 7 | `GRT_001` | `None` [ATOMIC] | Generates query param & path validation logic (Pydantic / type constraints). | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `L7_SVC_01`| `GetServiceCaller` | 7 | `GRT_001` | `None` [ATOMIC] | Generates service invocation call with error handling within the route handler. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `L7_FMT_01`| `GetResponseFormatter`| 7 | `GRT_001` | `None` [ATOMIC] | Generates HTTP JSON serialization and status code return block. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `PRT_001` | `PostRouteTask` | 6 | `GROP_001` | `L7_VAL_02`, `L7_SVC_02`, `L7_FMT_02` | Supervises code generation for a single atomic POST route. | `assemble_route_block`, `ast_insert` | `qwen2.5-coder:3b`<br>512MB |
| `L7_VAL_02`| `PostValidator` | 7 | `PRT_001` | `None` [ATOMIC] | Generates request body validation schema and deserialization checks. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `L7_SVC_02`| `PostServiceCaller` | 7 | `PRT_001` | `None` [ATOMIC] | Generates atomic mutation service call with transaction boundaries. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `L7_FMT_02`| `PostResponseFormatter`| 7 | `PRT_001` | `None` [ATOMIC] | Generates HTTP 201 Created response formatting with resource location headers. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `PROP_001` | `PutRouteOp` | 5 | `RTE_001` | `PURT_001` | Operations group for HTTP PUT/PATCH updates. | `route_spec_read`, `task_split` | `qwen2.5-coder:3b`<br>512MB |
| `PURT_001` | `PutRouteTask` | 6 | `PROP_001` | `L7_VAL_03`, `L7_SVC_03`, `L7_FMT_03` | Supervises code generation for atomic PUT/PATCH updates. | `assemble_route_block`, `ast_insert` | `qwen2.5-coder:3b`<br>512MB |
| `L7_VAL_03`| `PutValidator` | 7 | `PURT_001` | `None` [ATOMIC] | Generates partial update schema validation and ID checking. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `L7_SVC_03`| `PutServiceCaller` | 7 | `PURT_001` | `None` [ATOMIC] | Generates update service caller with optimistic concurrency / version checks. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `L7_FMT_03`| `PutResponseFormatter`| 7 | `PURT_001` | `None` [ATOMIC] | Generates HTTP 200 OK / 204 No Content response block. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `MID_001` | `MiddlewareController`| 4 | `API_001` | `AMID_001`, `LMID_001` | Oversees request/response middleware pipelines. | `inspect_middleware_stack` | `qwen2.5-coder:3b`<br>512MB |
| `AMID_001` | `AuthMiddlewareOp` | 5 | `MID_001` | `TVT_001` | Authentication middleware coordination. | `read_security_spec` | `qwen2.5-coder:3b`<br>512MB |
| `TVT_001` | `TokenVerifierTask` | 6 | `AMID_001` | `L7_JWT_01`, `L7_USR_01`, `L7_PRM_01` | Supervises construction of JWT security verification logic. | `combine_auth_steps` | `qwen2.5-coder:3b`<br>512MB |
| `L7_JWT_01`| `JwtParser` | 7 | `TVT_001` | `None` [ATOMIC] | Writes token decoding, signature verification, and expiration checks. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `L7_USR_01`| `UserExtractor` | 7 | `TVT_001` | `None` [ATOMIC] | Extracts user identity & roles from claims into request context. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `L7_PRM_01`| `PermissionChecker`| 7 | `TVT_001` | `None` [ATOMIC] | Generates RBAC/ABAC role evaluation checks. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `LMID_001` | `LoggingMiddlewareOp`| 5 | `MID_001` | `LFT_001` | Request correlation and audit logging pipeline. | `read_logging_spec` | `deterministic-rules`<br>256MB |
| `LFT_001` | `LogFormatterTask` | 6 | `LMID_001` | `L7_LOG_01`, `L7_LOG_02` | Supervises structured JSON request/response logging code. | `combine_logging_steps` | `deterministic-rules`<br>256MB |
| `L7_LOG_01`| `RequestLogger` | 7 | `LFT_001` | `None` [ATOMIC] | Generates inbound request logging (method, path, masked headers, IP). | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `L7_LOG_02`| `ResponseLogger` | 7 | `LFT_001` | `None` [ATOMIC] | Generates response logging (status code, duration in ms, error payload). | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `CTRL_001` | `ControllerOrchestrator`| 4 | `API_001` | `ACTR_001`, `UCTR_001` | Organizes domain business logic handlers and controller classes. | `inspect_controller_tree` | `qwen2.5-coder:3b`<br>512MB |
| `ACTR_001` | `AuthControllerOp` | 5 | `CTRL_001` | `AHT_001` | Grouping for authentication controller endpoints. | `read_auth_flow_spec` | `qwen2.5-coder:3b`<br>512MB |
| `AHT_001` | `AuthHandlerTask` | 6 | `ACTR_001` | `L7_HND_01`, `L7_HND_02`, `L7_HND_03` | Coordinates handler methods for registration, login, logout. | `combine_handlers` | `qwen2.5-coder:3b`<br>512MB |
| `L7_HND_01`| `RegisterHandler` | 7 | `AHT_001` | `None` [ATOMIC] | Writes `handle_register` method connecting input dto to auth service. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `L7_HND_02`| `LoginHandler` | 7 | `AHT_001` | `None` [ATOMIC] | Writes `handle_login` method generating session/token upon credential match. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `L7_HND_03`| `LogoutHandler` | 7 | `AHT_001` | `None` [ATOMIC] | Writes `handle_logout` method invalidating active tokens/cookies. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `UCTR_001` | `UserControllerOp` | 5 | `CTRL_001` | `UHT_001` | Grouping for user profile controller endpoints. | `read_user_flow_spec` | `qwen2.5-coder:3b`<br>512MB |
| `UHT_001` | `UserHandlerTask` | 6 | `UCTR_001` | `L7_HND_04`, `L7_HND_05`, `L7_HND_06` | Coordinates user profile CRUD operations. | `combine_handlers` | `qwen2.5-coder:3b`<br>512MB |
| `L7_HND_04`| `GetProfileWorker` | 7 | `UHT_001` | `None` [ATOMIC] | Writes controller method to fetch current authenticated user profile. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `L7_HND_05`| `UpdateProfileWorker`| 7 | `UHT_001` | `None` [ATOMIC] | Writes controller method to sanitize and update user details. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `L7_HND_06`| `DeleteUserWorker` | 7 | `UHT_001` | `None` [ATOMIC] | Writes controller method to perform soft/hard delete of user accounts. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |

### 4.3 Development Domain: Service & Database Sub-Tree (Agents 37 - 45)

| Agent ID | Agent Name | Level | Direct Parent | Children IDs | Responsibility | Assigned Tools | Model / RAM |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `SVC_001` | `ServiceComponent` | 3 | `BACK_001` | `ASVC_001`, `USVC_001` | Supervises pure business logic, transactional boundaries, and external APIs. | `inspect_service_layer` | `qwen2.5-coder:3b`<br>512MB |
| `ASVC_001` | `AuthServiceOrch` | 4 | `SVC_001` | `RSVC_001`, `LSVC_001` | Directs credential hashing, token generation, and password verification. | `crypto_policy_read` | `qwen2.5-coder:3b`<br>512MB |
| `RSVC_001` | `RegisterServiceOp`| 5 | `ASVC_001` | `RPL_001` | User registration workflow management. | `step_sequencer` | `qwen2.5-coder:3b`<br>512MB |
| `RPL_001` | `RegistrationPipeline`| 6 | `RSVC_001` | `L7_SEC_01`, `L7_DB_01`, `L7_SEC_02` | Sequences password hashing, user DB insertion, and JWT token issue. | `chain_steps` | `qwen2.5-coder:3b`<br>512MB |
| `L7_SEC_01`| `PasswordHasher` | 7 | `RPL_001` | `None` [ATOMIC] | Implements Argon2id / bcrypt password hashing with salt generation. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `L7_DB_01` | `UserRecordCreator`| 7 | `RPL_001` | `None` [ATOMIC] | Generates repository/ORM call to insert user record. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `L7_SEC_02`| `TokenGenerator` | 7 | `RPL_001` | `None` [ATOMIC] | Writes token factory generating signed HMAC-SHA256 JWT tokens. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `LSVC_001` | `LoginServiceOp` | 5 | `ASVC_001` | `LPL_001` | Credential evaluation and login workflow management. | `step_sequencer` | `qwen2.5-coder:3b`<br>512MB |
| `LPL_001` | `LoginPipeline` | 6 | `LSVC_001` | `L7_DB_02`, `L7_SEC_03` | Sequences database user lookup and constant-time password check. | `chain_steps` | `qwen2.5-coder:3b`<br>512MB |
| `L7_DB_02` | `UserRecordFinder` | 7 | `LPL_001` | `None` [ATOMIC] | Writes repository query searching user by normalized email/username. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `L7_SEC_03`| `PasswordVerifier` | 7 | `LPL_001` | `None` [ATOMIC] | Implements timing-attack resistant password verification method. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `DB_001` | `DatabaseComponent`| 3 | `BACK_001` | `MDL_001`, `QRY_001`, `MIG_001` | Supervises schemas, SQL queries, migrations, and database connection pools. | `inspect_db_schema` | `qwen2.5-coder:3b`<br>512MB |
| `MDL_001` | `ModelOrchestrator`| 4 | `DB_001` | `UMDL_001`, `SMDL_001` | Directs ORM model class generation and relational mapping. | `schema_catalog_read` | `qwen2.5-coder:3b`<br>512MB |
| `UMDL_001` | `UserModelOp` | 5 | `MDL_001` | `UST_001` | Manages user table ORM definitions and integrity constraints. | `table_spec_read` | `qwen2.5-coder:3b`<br>512MB |
| `UST_001` | `UserSchemaTask` | 6 | `UMDL_001` | `L7_SCH_01`, `L7_SCH_02` | Builds user table schema and field validation decorators. | `combine_schema_elements` | `qwen2.5-coder:3b`<br>512MB |
| `L7_SCH_01`| `UserSchemaDefiner`| 7 | `UST_001` | `None` [ATOMIC] | Writes SQLAlchemy/SQLModel class definition for User entity. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `L7_SCH_02`| `UserFieldValidator`| 7 | `UST_001` | `None` [ATOMIC] | Writes column-level validators (email format, password length, uniqueness).| `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `QRY_001` | `QueryOrchestrator`| 4 | `DB_001` | `SEL_001`, `INS_001` | Ensures queries are parameterized, indexed, and free from SQL injection. | `sql_ast_parser` | `qwen2.5-coder:3b`<br>512MB |
| `SEL_001` | `SelectQueryOp` | 5 | `QRY_001` | `SBT_001` | SELECT query construction management. | `query_spec_read` | `qwen2.5-coder:3b`<br>512MB |
| `SBT_001` | `SelectBuilderTask`| 6 | `SEL_001` | `L7_SQL_01`, `L7_SQL_02` | Assembles type-safe select queries with joined relations. | `assemble_sql` | `qwen2.5-coder:3b`<br>512MB |
| `L7_SQL_01`| `WhereClauseBuilder`| 7 | `SBT_001` | `None` [ATOMIC] | Writes parameterized WHERE clause predicates preventing injection. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `L7_SQL_02`| `JoinClauseBuilder` | 7 | `SBT_001` | `None` [ATOMIC] | Writes optimized INNER/LEFT JOIN statements with explicit keys. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `MIG_001` | `MigrationOrchestrator`| 4 | `DB_001` | `DDL_001` | Manages database migration scripts (Alembic / raw DDL). | `migration_tree_read` | `qwen2.5-coder:3b`<br>512MB |
| `DDL_001` | `DdlOp` | 5 | `MIG_001` | `DTK_001` | DDL revision generation. | `ddl_spec_read` | `qwen2.5-coder:3b`<br>512MB |
| `DTK_001` | `DdlTask` | 6 | `DDL_001` | `L7_DDL_01`, `L7_DDL_02`, `L7_DDL_03`| Assembles reversible migration step (upgrade & downgrade). | `assemble_migration` | `qwen2.5-coder:3b`<br>512MB |
| `L7_DDL_01`| `CreateTableBuilder`| 7 | `DTK_001` | `None` [ATOMIC] | Writes `op.create_table` DDL statement with primary & foreign keys. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `L7_DDL_02`| `AlterTableBuilder` | 7 | `DTK_001` | `None` [ATOMIC] | Writes safe non-locking column alter / index creation statements. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `L7_DDL_03`| `DropTableBuilder` | 7 | `DTK_001` | `None` [ATOMIC] | Writes reversible downgrade drop table methods. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |

### 4.4 Testing, Security, Deployment & Monitoring Domains (Agents 46 - 56)

| Agent ID | Agent Name | Level | Direct Parent | Children IDs | Responsibility | Assigned Tools | Model / RAM |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TEST_001` | `TestingDomain` | 1 | `ORCH_001` | `UTEST_001`, `ITEST_001`, `RTEST_001` | Controls test generation, test execution sandboxes, and coverage verification. | `pytest_runner`, `coverage_evaluator` | `qwen2.5-coder:3b`<br>512MB |
| `UTEST_001`| `UnitTestModule` | 2 | `TEST_001` | `L7_TST_01`, `L7_TST_02`, `L7_TST_03` | Directs unit test synthesis and fixture isolation. | `inspect_unit_specs` | `qwen2.5-coder:3b`<br>512MB |
| `L7_TST_01`| `TestCaseGenerator`| 7 | `UTEST_001` | `None` [ATOMIC] | Writes isolated pytest functions targeting single unit functions. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `L7_TST_02`| `MockObjectFactory`| 7 | `UTEST_001` | `None` [ATOMIC] | Generates deterministic unittest.mock objects and stubs. | `write_code_snippet`, `ast_validate` | `qwen2.5-coder:3b`<br>512MB |
| `L7_TST_03`| `TestRunnerExecutor`| 7 | `UTEST_001` | `None` [ATOMIC] | Executes pytest in subprocess with capture, parses exit code and XML results. | `run_test_proc`, `parse_junit_xml` | `deterministic-rules`<br>256MB |
| `SEC_001` | `SecurityDomain` | 1 | `ORCH_001` | `SAST_001`, `DEPAUD_001` | Manages vulnerability scanning, secret detection, and OWASP compliance gates. | `read_security_rules`, `audit_report` | `deterministic-rules`<br>256MB |
| `SAST_001` | `SastScannerModule` | 2 | `SEC_001` | `L7_SEC_04`, `L7_SEC_05` | Runs static AST pattern matchers to detect injections, insecure deserialization. | `bandit_runner`, `semgrep_eval` | `deterministic-rules`<br>256MB |
| `L7_SEC_04`| `VulnPatternScanner`| 7 | `SAST_001` | `None` [ATOMIC] | Scans code diffs for CWE-89 (SQLi), CWE-79 (XSS), and insecure randoms. | `regex_ast_scan`, `report_finding` | `deterministic-rules`<br>256MB |
| `L7_SEC_05`| `SecretLeakDetector`| 7 | `SAST_001` | `None` [ATOMIC] | Scans diffs for API tokens, private keys, and hardcoded passwords. | `entropy_scanner`, `regex_leak_scan` | `deterministic-rules`<br>256MB |
| `DEP_001` | `DeploymentDomain` | 1 | `ORCH_001` | `BLD_001`, `MDEP_001` | Supervises packaging, container configuration, and migration execution. | `docker_cli`, `verify_artifacts` | `deterministic-rules`<br>256MB |
| `BLD_001` | `BuildPackageModule`| 2 | `DEP_001` | `L7_DEP_01`, `L7_DEP_02` | Generates container configurations and builds packages. | `dockerfile_inspect` | `deterministic-rules`<br>256MB |
| `L7_DEP_01`| `DockerfileGenerator`| 7 | `BLD_001` | `None` [ATOMIC] | Writes multi-stage, rootless, minimal Dockerfile with pinned hashes. | `write_code_snippet`, `hadolint_scan` | `qwen2.5-coder:3b`<br>512MB |
| `DRF_001` | `DriftDetectorModule`| 2 | `MON_001` | `L7_MON_01`, `L7_MON_02` | Verifies git state hygiene, working tree purity, and environment side effects. | `git_status`, `fs_hash_compare` | `deterministic-rules`<br>256MB |
| `L7_MON_01`| `WorkingTreeInspector`| 7 | `DRF_001`| `None` [ATOMIC] | Verifies no untracked file modifications occurred outside declared scope. | `git_diff_tree`, `hash_directory` | `deterministic-rules`<br>256MB |
| `L7_MON_02`| `IdempotencyVerifier`| 7 | `DRF_001` | `None` [ATOMIC] | Executes secondary test run to verify repeated execution yields identical hash. | `run_idempotence_check` | `deterministic-rules`<br>256MB |

---

## 5. Exemplary JSON Agent Registry Entries

To demonstrate exact conformance with the registry schema, here are three complete, production-ready JSON registry files stored under `/state/agents/`:

### 5.1 Orchestrator Registry (`/state/agents/ORCH_001/registry.json`)
```json
{
  "agent_id": "ORCH_001",
  "agent_name": "MetaOrchestrator",
  "level": 0,
  "parent_id": null,
  "children_ids": ["PLAN_001", "DEV_001", "TEST_001", "SEC_001", "DEP_001", "MON_001"],
  "capabilities": [
    "mission_lifecycle_management",
    "global_state_coordination",
    "quality_gate_approval",
    "resource_governance"
  ],
  "tools": [
    "task_queue_read",
    "state_commit",
    "abort_session",
    "write_manifest"
  ],
  "max_depth": 2,
  "state": "working",
  "resource_requirements": {
    "ram_mb": 512,
    "model": "qwen2.5-coder:3b"
  }
}
```

### 5.2 Intermediate Task Coordinator (`/state/agents/GRT_001/registry.json`)
```json
{
  "agent_id": "GRT_001",
  "agent_name": "GetRouteTask",
  "level": 6,
  "parent_id": "GROP_001",
  "children_ids": ["L7_VAL_01", "L7_SVC_01", "L7_FMT_01"],
  "capabilities": [
    "route_block_assembly",
    "ast_insertion",
    "subtask_validation"
  ],
  "tools": [
    "assemble_route_block",
    "ast_insert"
  ],
  "max_depth": 1,
  "state": "idle",
  "resource_requirements": {
    "ram_mb": 512,
    "model": "qwen2.5-coder:3b"
  }
}
```

### 5.3 Atomic Leaf Worker (`/state/agents/L7_VAL_01/registry.json`)
```json
{
  "agent_id": "L7_VAL_01",
  "agent_name": "GetValidator",
  "level": 7,
  "parent_id": "GRT_001",
  "children_ids": [],
  "capabilities": [
    "pydantic_query_validation",
    "type_constraint_generation",
    "ast_syntax_verification"
  ],
  "tools": [
    "write_code_snippet",
    "ast_validate"
  ],
  "max_depth": 0,
  "state": "idle",
  "resource_requirements": {
    "ram_mb": 512,
    "model": "qwen2.5-coder:3b"
  }
}
```

---

## 6. Execution Lifecycle of an Atomic Sub-Agent Chain

To illustrate the complete fractal descent in action, consider how a high-level user request (`"Add an authenticated GET /api/v1/users/{id} endpoint"`) traverses the tree:

1. **Reception at $L0$ (`ORCH_001`):** Emits mission spec to `/artifacts/spec.json` and invokes $L1$ (`PLAN_001`).
2. **Decomposition at $L1$ (`PLAN_001`):** $L2$ (`DEC_001`) parses spec, determines backend modifications needed, and inserts tasks into `task_dag.json`.
3. **Dispatch to $L1$ (`DEV_001`) $\rightarrow$ $L2$ (`BACK_001`):** $L2$ detects API routing need and passes envelope to $L3$ (`API_001`).
4. **Descent to $L4$ (`RTE_001`) $\rightarrow$ $L5$ (`GROP_001`) $\rightarrow$ $L6$ (`GRT_001`):** The task is narrowed until $L6$ defines the three atomic components of the route: parameter validation, service invocation, and response formatting.
5. **Atomic Execution at $L7$:**
   - `L7_VAL_01` writes the path parameter validator `class UserPathParams(BaseModel): user_id: UUID`.
   - `L7_SVC_01` writes the service call `user = await user_service.get_by_id(user_id)`.
   - `L7_FMT_01` writes the serialized return `return UserResponse.model_validate(user)`.
6. **Synthesis at $L6$ (`GRT_001`):** Assembles the three atomic AST blocks into a single route function:
   ```python
   @router.get("/users/{user_id}", response_model=UserResponse)
   async def get_user_by_id(user_id: UUID, current_user: User = Depends(get_current_user)):
       user = await user_service.get_by_id(user_id)
       return UserResponse.model_validate(user)
   ```
7. **Verification & Quality Gate Passage:** The assembled route is validated via AST parser, written to disk, tested by $L7$ (`L7_TST_01`), scanned by $L7$ (`L7_SEC_04`), and its completion receipt is transmitted upward. At no point did any agent hold the entire application codebase in its context window.
