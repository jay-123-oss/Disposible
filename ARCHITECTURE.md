# ARCHITECTURE.md: Production-Grade Fractal Multi-Agent Coding System

## 1. Executive Summary & Core Philosophy

Modern autonomous coding agents routinely suffer from the **"AI Whack-A-Mole" problem**: an agent fixing a defect in module $A$ inadvertently introduces regressions in module $B$, attempts to patch $B$ by refactoring shared interface $C$, and triggers an uncontrollable cascade of hallucinations and architectural degradation. This failure mode stems directly from monolithic context concentration, unbounded state spaces, unisolated side effects, and lack of deterministic quality barriers.

This architecture specifies an enterprise-ready, fractal multi-agent coding framework engineered to guarantee a **95%+ first-attempt success rate** on complex software engineering tasks using local, resource-constrained Large Language Models (`qwen2.5-coder:3b` and `llama3.2:3b` via Ollama) within an **8GB system RAM ceiling**.

### The Core Philosophy
> **"Every task gets its own specialized agent. Every agent can spawn sub-agents. The chain continues until the task becomes atomic."**

The architecture solves the Whack-A-Mole phenomenon through six non-negotiable architectural axioms:
1. **Fractal Decomposition:** Large engineering tasks are mathematically recursively decomposed into strictly bounded, context-isolated sub-problems until leaf agents operate purely at the atomic level (e.g., generating a single route handler, writing an AST-validated regex, or verifying a SQL schema).
2. **Context Isolation & Zero Cross-Talk:** Peer agents never exchange unbounded conversational prompts. Communication is strictly vertical (Parent $\leftrightarrow$ Child) or asynchronous through an environmental blackboard using stigmergy ($O(N)$ linear token scaling instead of $O(N^2)$ quadratic peer-to-peer bloat).
3. **Deterministic Quality Gates:** No code, plan, or configuration crosses a domain or layer boundary without satisfying cryptographically verifiable, automated acceptance criteria (static analysis, unit tests, security audits, and regression fences).
4. **Tool State Idempotency:** Environment mutations (file writes, shell executions, git commits) are sandboxed, snapshot-backed, and verified against pre/post-execution hash invariants to eliminate tool state drift.
5. **Strict Depth and Memory Fencing:** Depth is hard-capped (`maxDepth = 2` relative parent-to-grandchild supervision scope; global max level $L7$), and memory is strictly bounded at 512MB RAM per active agent container/process.
6. **Self-Healing through Compensating Transactions:** Failures trigger deterministic rollback mechanisms rather than generative prompt apologies, completely preventing regression loops.

---

## 2. Overall System Architecture Diagram

```
+----------------------------------------------------------------------------------------------------+
|                                      LEVEL 0: META-ORCHESTRATOR                                     |
|                                       [ORCH_001: System Core]                                      |
|                                                                                                    |
|  +------------------------+   +------------------------+   +------------------------------------+  |
|  | Task Reception & Goal  |   | Global State Watchdog  |   | Resource Governor & Memory Monitor |  |
|  | Decomposition Engine   |   |  & Heartbeat Monitor   |   |   (Max 8GB System / 512MB Node)    |  |
|  +------------------------+   +------------------------+   +------------------------------------+  |
+-------------------------------------------------+--------------------------------------------------+
                                                  |
                     +----------------------------+----------------------------+
                     | Top-Down Task Delegation                                | Bottom-Up Consolidated
                     v                                                         | Quality Proofs
+------------------------------------------------------------------------------+---------------------+
|                                LEVEL 1: DOMAIN CONTROLLER AGENTS                                    |
|                                                                                                     |
|  +-----------------+  +-----------------+  +-----------------+  +-----------------+  +------------+ |
|  |  PLANNING_DOM   |  |   CODING_DOM    |  |   TESTING_DOM   |  |  SECURITY_DOM   |  | DEPLOY_DOM | |
|  |   (PLAN_001)    |  |   (DEV_001)     |  |   (TEST_001)    |  |   (SEC_001)     |  | (DEP_001)  | |
|  +--------+--------+  +--------+--------+  +--------+--------+  +--------+--------+  +-----+------+ |
+-----------|--------------------|--------------------|--------------------|-----------------|-------+
            |                    |                    |                    |                 |
            |                    |                    |                    |                 |
+-----------v--------------------v--------------------v--------------------v-----------------v-------+
|                                LEVEL 2: MODULE SPECIALIST AGENTS                                    |
|                                                                                                     |
|  [SpecParser]      [BackendModule]      [UnitTestModule]     [SASTScanner]        [BuildPacker]     |
|  [ArchDesigner]    [FrontendModule]     [IntegrationModule]  [SecretAuditor]      [MigrationRunner] |
|  [TaskDecomposer]  [DatabaseModule]     [MutationModule]     [DependencyChecker]  [ReleaseGate]     |
+-----------+--------------------+--------------------+--------------------+-----------------+-------+
            |                    |                    |                    |                 |
            |                    |                    |                    |                 |
+-----------v--------------------v--------------------v--------------------v-----------------v-------+
|                           LEVEL 3: COMPONENT ORCHESTRATORS & L4-L6 PIPELINES                        |
|                                                                                                     |
|  * API Controllers   * Business Services   * Data Models   * Route Dispatchers   * AST Parsers      |
|  (Each intermediate node strictly supervises at most 2 child levels down to atomic workers)         |
+-------------------------------------------------+--------------------------------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
|                               LEVEL 7: ATOMIC LEAF EXECUTION AGENTS                                 |
|                                                                                                    |
|  +-------------------+  +-------------------+  +-------------------+  +--------------------------+ |
|  |   TOKEN_VERIFIER  |  |  GET_ROUTE_WORKER |  |   SCHEMA_DEFINER  |  |   ASSERTION_EVALUATOR    | |
|  |   (No Children)   |  |   (No Children)   |  |   (No Children)   |  |      (No Children)       | |
|  +---------+---------+  +---------+---------+  +---------+---------+  +------------+-------------+ |
+------------|----------------------|----------------------|-------------------------|---------------+
             |                      |                      |                         |
             v                      v                      v                         v
+----------------------------------------------------------------------------------------------------+
|                               ENVIRONMENTAL RUNTIME & SHARED BLACKBOARD                            |
|                                                                                                    |
|  +-----------------------------------------------------------------------------------------------+ |
|  |                               STIGMERGY BLACKBOARD (/state/global/)                            | |
|  |   - Artifact Registry       - Digital Pheromone Signals    - Pheromone Decay & TTL GC         | |
|  |   - Task Dependency DAG     - Idempotency State Log        - Dynamic Quality Status Map       | |
|  +-----------------------------------------------------------------------------------------------+ |
|                                                  |                                                 |
|  +-----------------------------------------------+-----------------------------------------------+ |
|  |                                TOOL EXECUTION ENGINE (Sandboxed)                              | |
|  |   - Pre/Post Execution Hashing          - Git Snapshot & Fast Rollback Engine                 | |
|  |   - File System Driver (Scoped I/O)     - Subprocess Runner (Resource Capped: 512MB RAM)      | |
|  |   - Ollama Inference Pool (Local qwen2.5-coder:3b / llama3.2:3b via HTTP REST API)            | |
|  +-----------------------------------------------------------------------------------------------+ |
+----------------------------------------------------------------------------------------------------+
```

---

## 3. Layered Architecture (Level 0 to Level N)

The system enforces a 8-tier hierarchy ($L0$ through $L7$) where agents become progressively more specialized as the level number increases.

| Level | Designation | Authority & Scope | Sub-Agent Capability | Typical Execution Latency |
| :--- | :--- | :--- | :--- | :--- |
| **L0** | **Meta-Orchestrator** | Global mission lifecycle, system resources, user interface, domain dispatch, global abort/commit. | Spawns L1 Domains | Continuous |
| **L1** | **Domain Controllers** | Strategic governance over specific engineering pillars (Planning, Dev, Testing, Security, Deploy). | Spawns L2 Modules | 10s - 30s |
| **L2** | **Module Agents** | Architectural units (e.g., Backend, Database, Frontend, Static Analysis). Formulates execution DAG. | Spawns L3 Components | 5s - 15s |
| **L3** | **Component Agents** | Component-level coordinators (e.g., Auth Component, User Profile Component, Migration Controller). | Spawns L4 Sub-components | 3s - 10s |
| **L4** | **Sub-System Agents** | Service-level or Route-level coordinators (e.g., Service Layer, API Router Layer). | Spawns L5 Operation Agents | 2s - 8s |
| **L5** | **Operation Agents** | Action grouping (e.g., HTTP Route handler group, Query Builder, Middleware Stack). | Spawns L6 Task Agents | 1s - 5s |
| **L6** | **Task Agents** | Focused task managers (e.g., `GET_ROUTE_AGENT`, `REGISTER_SERVICE`). | Spawns L7 Atomic Workers | 1s - 3s |
| **L7** | **Leaf / Atomic Workers**| **Pure execution units.** Direct tool users (AST edit, file write, regex parse). **Zero sub-agents.** | **None (Leaf Node)** | <1s - 3s |

### Structural Constraints on Layering:
1. **Strict Downward Delegation:** An agent at Level $N$ may only instantiate and assign tasks to agents at Level $N+1$.
2. **Strict Upward Reporting:** An agent at Level $N+1$ reports execution tokens, gate artifacts, and terminal states exclusively to its direct parent at Level $N$.
3. **No Horizontal Linkage:** Agents at the same level (e.g., $L2$ `BackendModule` and $L2$ `FrontendModule`) cannot invoke each other directly or exchange execution prompts. All cross-domain alignment occurs asynchronously via the **Stigmergy Blackboard** or synchronously via their common ancestor.
4. **Leaf Purity:** Level 7 agents are strictly forbidden from spawning any sub-agents. Their prompt templates are single-shot, tool-bound, deterministic execution loops with strict output schemas.

---

## 4. Data Flow Between Layers

Data flow across the system operates along three distinct vectors: **Vertical Control**, **Upward Verification**, and **Stigmergic Coordination**.

```
    DOWNWARD CONTROL FLOW                         UPWARD VERIFICATION FLOW
 (Decomposition & Delegation)                   (Artifacts & Quality Proofs)

      [Parent Agent (L_k)]                           [Parent Agent (L_k)]
              |                                               ^
              | 1. Task Envelope (JSON)                       | 4. Verified Gate Proof
              |    - Task ID, Intent, Input Ref               |    - Artifact URI, Checksum
              |    - Token & RAM Budget                       |    - Test/Lint Verification
              v                                               |
     [Child Agent (L_k+1)]                          [Child Agent (L_k+1)]
              |                                               ^
              | 2. Atomic Subtask Delegation                  | 3. Execution Result
              v                                               |
     [Atomic Leaf (L_7)] ---------------------------> [Atomic Leaf (L_7)]
                             TOOL EXECUTION & MUTATION
                                      |
                                      v
                      +-------------------------------+
                      | Stigmergy Blackboard / Disk   |
                      |  - Writes Code Artifact       |
                      |  - Emits Trace Signal         |
                      |  - Updates Pheromone Map      |
                      +-------------------------------+
                                      |
       HORIZONTAL COORDINATION (Implicit Stigmergic Observation)
                                      v
                          [Other Domain Observer]
```

### 1. Downward Control Flow (Intent Decomposition)
- The user's prompt enters at $L0$. The $L0$ Meta-Orchestrator generates a structured `MissionSpecification` artifact, deposits it into the artifact registry, and passes an immutable `TaskEnvelope` to $L1$ Planning.
- Once $L1$ Planning completes the execution DAG, $L0$ dispatches phase envelopes to the respective $L1$ Domain Controllers.
- Each descending layer decomposes the task description into a narrower, domain-specialized context. By the time the task reaches $L7$, the context is reduced to an atomic instruction (e.g., `"Generate a Pydantic v2 schema for UserRegistration with fields: username (str), email (EmailStr), password (SecretStr)"`).

### 2. Upward Verification Flow (Artifact & Proof Synthesis)
- Atomic workers do not return conversational text to their parents. They return a **Structured Execution Receipt**:
  ```json
  {
    "task_id": "TSK_L7_0042",
    "status": "COMPLETED",
    "artifacts_produced": ["file:///workspace/app/schemas/user.py"],
    "checksum": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "quality_metrics": { "syntax_valid": true, "tokens_used": 284, "execution_ms": 740 }
  }
  ```
- The parent aggregates the receipts of all its children, runs its own layer-level verification, and propagates a synthesized quality proof upward.

### 3. Horizontal Coordination (Stigmergy Blackboard)
- Peer agents communicate implicitly through environmental modifications. When $L2$ `BackendModule` writes an OpenAPI specification to `/artifacts/api/openapi.json`, it writes a **Stigmergic Trace** to `/state/global/blackboard.json`.
- The $L2$ `FrontendModule` and $L2$ `UnitTestModule` listen for filesystem signals and trace updates. When the trace condition `openapi.ready` is detected, their execution triggers automatically without any peer-to-peer coupling.

---

## 5. Communication Protocols

All communications conform to the strict JSON protocols specified in [COMMUNICATION_PROTOCOL.md](file:///c:/Users/jayde/OneDrive/Desktop/disposible/COMMUNICATION_PROTOCOL.md).

### Protocol Summary Matrix
| Communication Type | Channel | Pattern | Payload Type | Typical Overhead |
| :--- | :--- | :--- | :--- | :--- |
| **Parent $\rightarrow$ Child** | Unix Domain Socket / IPC Pipe | Synchronous Dispatch | `TaskEnvelope` (Metadata + Pointer) | < 1 KB |
| **Child $\rightarrow$ Parent** | Unix Domain Socket / IPC Pipe | Event Response | `ExecutionReceipt` (Status + Metrics) | < 2 KB |
| **Agent $\rightarrow$ Environment** | POSIX File I/O + Git CLI | Transactional Write | Source Code, Diffs, Test Reports | Variable (Disk backed) |
| **Agent $\rightarrow$ Blackboard** | Atomic JSON File Updates | Stigmergic Signal | `PheromoneTrace` (Event, State, TTL) | < 500 Bytes |
| **Agent $\rightarrow$ LLM** | Ollama HTTP REST API | Stateless POST | Minimal System + User Prompt ($\le$4096 tok) | $\le$ 4096 Tokens |

### Core Invariant: Pointer-Based Context Passing
In order to prevent context bloat:
- Payloads exceeding **20,000 tokens** (or larger than 8KB raw text) are **strictly forbidden** from being transmitted in message bodies.
- Large contexts are written to the filesystem as immutable artifacts (`/artifacts/...`). The message payload conveys only the URI, byte-range, and SHA-256 checksum of the artifact.

---

## 6. State Management Strategy

The system eliminates external database dependencies (e.g., PostgreSQL, Redis, MongoDB) in favor of a **lightweight, deterministic, file-based JSON state system** backed by Git snapshots. Full details are codified in [STATE_MANAGEMENT.md](file:///c:/Users/jayde/OneDrive/Desktop/disposible/STATE_MANAGEMENT.md).

```
/state/
├── global/
│   ├── system_state.json        # Global mission status, active agents, resource allocations
│   ├── blackboard.json          # Stigmergic signals, pheromone traces, decay timestamps
│   └── lockfile.lock            # Process-safe file locking for concurrency control
├── tasks/
│   ├── task_dag.json            # Full hierarchical task execution graph with dependencies
│   └── active/                  # Ephemeral task state envelopes
│       ├── TSK_001.json
│       └── TSK_002.json
├── checkpoints/
│   ├── CHK_001_initial/         # Git tree SHA + state snapshot
│   ├── CHK_002_planned/
│   └── CHK_003_backend_pass/
└── agents/
    ├── AGENT_001_Orchestrator/  # Agent-local scratchpad and execution memory
    │   └── local_state.json
    └── AGENT_042_GetRoute/
        └── local_state.json
```

### State Guarantees:
1. **ACID File Operations:** All JSON state updates use the **Atomic Write-and-Rename** pattern (`open(temp_path) -> write -> flush -> os.replace(temp_path, final_path)`) protected by file-level mutex locks (`fcntl` / `msvcrt`).
2. **Isolated Agent-Local State:** Each agent possesses a private, ephemeral directory (`/state/agents/{agent_id}/`) containing its local scratchpad and context metrics. When an agent terminates, its local state is archived or purged, eliminating memory leakage.
3. **Deterministic Checkpoint Engine:** At the completion of each quality gate, the state engine captures an atomic snapshot combining:
   - A complete Git tree commit SHA.
   - A frozen copy of `task_dag.json` and `system_state.json`.
   - The cryptographic checksum of all produced artifacts.

---

## 7. Scaling & Resource Strategy (Local Hardware Capped at 8GB RAM)

The architecture is explicitly tuned to operate on consumer workstations or single-node virtual machines with **8GB total RAM** hosting local 3B parameter models via Ollama.

### Memory & Process Budget
$$\text{Total System RAM} = 8192\,\text{MB}$$
- **Ollama Runner (`qwen2.5-coder:3b` / `llama3.2:3b` in Q4_K_M quantization):** $2200\,\text{MB}$ reserved.
- **Operating System & Tooling (Python, Git, Node, Linters):** $1800\,\text{MB}$ reserved.
- **Agent Concurrency Pool:** $4000\,\text{MB}$ available.
- **Per-Agent Process Limit:** $512\,\text{MB}$ maximum RSS (Resident Set Size).
- **Maximum Concurrent Active Agents:** $\lfloor 4000 / 512 \rfloor = 7\text{ concurrent worker processes}$.

```
+-------------------------------------------------------------------------+
|                    8192 MB TOTAL SYSTEM RAM ALLOCATION                   |
|                                                                         |
|  +--------------------+  +--------------------+  +--------------------+  |
|  |   Ollama Runtime   |  |   OS, Git, Node,   |  | Agent Execution    |  |
|  | (3B Q4 Model Pool) |  |   Python Runtime   |  | Process Pool       |  |
|  |      2200 MB       |  |      1800 MB       |  | 4000 MB (Max 7 PIDs|  |
|  |                    |  |                    |  |   @ 512 MB each)   |  |
|  +--------------------+  +--------------------+  +--------------------+  |
+-------------------------------------------------------------------------+
```

### Execution Pooling & Worker Queues
- While the agent hierarchy contains 50+ specialized agent specifications, they **do not run as 50 simultaneous OS processes**.
- Agents are instantiated as lightweight Python task definitions and executed via a **Priority-Bounded Worker Pool** (capped at 4-7 parallel threads/processes depending on current RSS).
- Inactive agents exist purely as serialized JSON registry entries in `/state/agents/`. When a task reaches their queue, they are dynamically loaded into an available pool slot, execute their atomic step, emit their receipt, and unload.

---

## 8. Fault Tolerance & Resilience Mechanisms

To eliminate unhandled exceptions and infinite error spirals, the architecture implements enterprise-grade resilience patterns:

```
[Agent Task Invocation]
        |
        v
+-----------------------+      Tripped
|    Circuit Breaker    |-------------------> [Quarantine Agent & Fallback to Parent]
+-----------------------+
        | Normal (Closed)
        v
+-----------------------+      Health Check Timeout
|    Sandbox Watchdog   |-------------------> [Process SIGKILL & Spawn Fresh Worker]
+-----------------------+
        | OK
        v
+-----------------------+      Hash Mismatch
| Idempotency Inspector |-------------------> [Git Reset --hard to Last Checkpoint]
+-----------------------+
        | Valid
        v
[Execution Success & State Commit]
```

1. **Three-State Circuit Breakers (`Closed`, `Open`, `Half-Open`):**
   - Each agent registry entry tracks consecutive failures.
   - If an agent fails 2 consecutive execution attempts, its circuit trips to `Open`.
   - The task is immediately escalated to the parent agent to select an alternative decomposition strategy or fall back to a rule-based deterministic template.
2. **Process Watchdogs & Hard Resource Quotas:**
   - Every worker process is wrapped by an execution watchdog thread with a hard wall-clock timeout ($30\text{ seconds}$ per atomic task).
   - Python `resource` limits (or OS job objects on Windows) enforce the 512MB RAM ceiling. If an agent exceeds 512MB, it is terminated with an out-of-memory signal (`SIGKILL`), its state is discarded, and the task is rescheduled.
3. **Idempotency Verification & Tool State Drift Shield:**
   - Before any atomic tool runs, the system records the working directory Git tree hash and modified timestamp index.
   - Upon task completion, if side effects outside the declared file scope are detected (e.g., unintended edits to existing files), the entire transaction is rolled back via `git checkout -- .` and the offending agent is penalized.
4. **Supervisory Tree Restarts:**
   - Adopting Erlang/OTP supervisory tree principles: parent agents supervise child agents with configurable restart strategies (`One-For-One`, `Rest-For-One`). When a leaf node crashes unexpectedly, its parent decides whether to retry the atomic worker, respawn with fresh context, or bubble the failure upward.

---

## 9. Comprehensive Mapping of the 7 Critical Problems to Architectural Solutions

The table below demonstrates how this architecture systematically eradicates the seven core failure modes of multi-agent coding systems:

| # | Critical Problem | Root Cause in Conventional Systems | Architectural Solution in this System | File Reference |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Infinite Recursion** | Agents spawn child agents indefinitely when encountering ambiguous errors, losing control of depth and task scope. | **Strict Depth Fencing:** Global depth capped at $L7$. Relative depth per agent capped at `maxDepth = 2` (parent $\rightarrow$ child $\rightarrow$ grandchild). Cycle-detection via Task Dependency Graph DAG invariants. Hard recursion budget token. | `ARCHITECTURE.md`, `AGENT_HIERARCHY.md` |
| **2** | **Context Window Pressure** | Whole-file concatenations, growing chat histories, and large compiler logs exhaust the model's token limits, causing hallucinations. | **Automated Context Offloading:** Hard cap of 4096 tokens per LLM call. Artifact offloading for any payload $>20\text{K}$ tokens. AST-based diff extraction, symbol extraction, and semantic compression pipeline. | `STATE_MANAGEMENT.md`, `COMMUNICATION_PROTOCOL.md` |
| **3** | **Token Overhead** | Peer-to-peer agent chatter scales quadratically ($O(N^2)$), consuming millions of tokens in repetitive coordination prompts. | **Stigmergy Blackboard Architecture:** Replaces $O(N^2)$ conversational chatter with $O(N)$ linear environmental coordination via shared blackboard traces, artifact pointers, and signal decay mechanisms. | `COMMUNICATION_PROTOCOL.md`, `STATE_MANAGEMENT.md` |
| **4** | **Multi-Agent Error Amplification** | Hallucinations or faulty code generated by one agent are treated as ground truth by subsequent agents, compounding errors. | **Zero-Trust Layered Quality Gates:** Seven automated quality checkpoints (QG-1 through QG-7). Code cannot progress between agents without passing AST parsing, unit testing, SAST scans, and idempotency checks. | `QUALITY_GATES.md` |
| **5** | **Fault Tolerance & Crashes** | Memory leaks, model crashes, or process deadlocks bring down the entire orchestration pipeline. | **Sandboxed Worker Pooling & Circuit Breakers:** 512MB RAM hard cgroups/process limit, 30s execution timeouts, Erlang-style supervisory trees, and three-state circuit breakers with graceful degradation. | `ARCHITECTURE.md`, `RISK_MITIGATION.md` |
| **6** | **Tool State Drift** | Non-idempotent tool calls (e.g., partial file writes, broken dependencies) corrupt the development workspace. | **Pre/Post-Execution Cryptographic Hashing:** Git snapshot rollback engine, atomic file replacement, strict filesystem sandbox scoping, and automated regression restoration. | `STATE_MANAGEMENT.md`, `QUALITY_GATES.md` |
| **7** | **Evaluation & Whack-A-Mole** | Single-dimensional "does it run" checks miss subtle interface breaks, security vulnerabilities, or performance degradation. | **Multi-Dimensional Quality Evaluation:** Quantitative scoring across 4 dimensions: Correctness ($\ge 90\%$), Security ($\ge 95\%$), Performance ($\ge 85\%$), and Maintainability ($\ge 90\%$) with automated regression barriers. | `QUALITY_GATES.md`, `RISK_MITIGATION.md` |

---

## 10. Architectural Invariants & Execution Guarantees

Every implementation module in this system must strictly satisfy these formal invariants:
- **Invariant 1 (Acyclic Decomposition):** The task delegation graph must always be a Directed Acyclic Graph (DAG). No agent may be assigned a task that depends on its own output or the output of its descendants.
- **Invariant 2 (Zero Monolithic Prompts):** No LLM request may exceed 4096 tokens under any circumstances. Payloads violating this are immediately rejected by the Tool Execution Engine.
- **Invariant 3 (Atomic Workmanship):** Real code is written *only* by Level 7 leaf agents. Parent agents ($L0$ through $L6$) are strictly coordinators, validators, and synthesizers; they never generate production code directly.
- **Invariant 4 (Commit on Green Only):** Git commits and state checkpoints are created *only* when all unit tests, linters, and quality gates pass with a 100% clean bill of health.
- **Invariant 5 (Deterministic Rollback):** If an atomic change fails testing after 2 iterations, the workspace is automatically rolled back to the prior checkpoint via `git reset --hard`, entirely preventing cumulative error drift.
