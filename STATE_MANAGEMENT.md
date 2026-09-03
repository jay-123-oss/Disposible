# STATE_MANAGEMENT.md: Storage Architecture, Checkpointing & Context Compression

## 1. State Architecture Overview

To maintain zero external runtime dependencies (eliminating PostgreSQL, Redis, MongoDB, and daemon databases), the state engine is built entirely on a **deterministic, transactional file-based JSON architecture** coupled with Git version control.

### Core Architectural Axioms:
1. **Zero Database Footprint:** State is stored strictly as normalized, schema-validated JSON files inside the `/state/` filesystem tree.
2. **ACID File Guarantees:** All write operations employ an **atomic write-flush-rename** sequence protected by POSIX/Windows file locks, preventing corruption during abrupt power loss or process termination.
3. **Partitioned Scoping:** Strict physical boundary between **Global System State** (accessible read-only to workers, read-write to orchestrator) and **Agent-Local State** (private to each individual agent instance).
4. **Git-Backed Checkpointing:** State snapshots capture not only JSON metadata, but the exact commit SHA of the code repository, ensuring instantaneous, bit-level rollbacks.

```
/state/
├── global/
│   ├── system_state.json        # Global mission status, agent registry, system-wide metrics
│   ├── blackboard.json          # Stigmergic pheromones, active environmental signals
│   └── lockfile.lock            # Concurrency mutex lockfile
├── tasks/
│   ├── task_dag.json            # Hierarchical execution graph with complete dependency edges
│   ├── active/                  # Ephemeral in-flight task instances
│   │   ├── TSK_001.json
│   │   └── TSK_042.json
│   └── completed/               # Terminal task receipts with full cryptographic audit trails
│       └── TSK_000_SPEC.json
├── checkpoints/
│   ├── CHK_000_INIT/            # Baseline commit + initial system snapshot
│   ├── CHK_001_SPEC_PASSED/     # Post-planning phase verification
│   └── CHK_002_BACKEND_GREEN/   # Code generation + unit test pass
├── agents/
│   ├── ORCH_001/
│   │   ├── local_state.json     # Private execution memory, step history, scratchpad
│   │   └── context_cache.json   # Compressed AST symbol index
│   └── L7_VAL_01/
│       └── local_state.json
└── dead_letter/                 # Unparseable, rejected, or permanently failed message frames
    └── frame_corrupted_01.json
```

---

## 2. Global State vs. Agent-Local State

| Dimension | Global System State (`/state/global/`) | Agent-Local State (`/state/agents/{id}/`) |
| :--- | :--- | :--- |
| **Authority** | Meta-Orchestrator (`ORCH_001`) only. | The designated Agent process only. |
| **Accessibility** | Read-Only to workers; Read-Write to Orchestrator. | Strictly Private to that agent PID. |
| **Lifetime** | Persists across the entire user mission lifecycle. | Ephemeral; purged upon task completion receipt. |
| **Typical Size** | $50\,\text{KB} - 500\,\text{KB}$. | $2\,\text{KB} - 16\,\text{KB}$. |
| **Content** | Mission status, task DAG, active worker pids, token tally. | Scratchpad, localized step counter, AST symbol index. |
| **Concurrency** | Protected by global file lock (`lockfile.lock`). | Lock-free (single writer process per directory). |

### 2.1 Global System State Schema (`/state/global/system_state.json`)
```json
{
  "mission_id": "MIS_20260902_001",
  "status": "EXECUTING",
  "started_at_utc": "2026-09-02T18:20:00.000Z",
  "last_checkpoint_id": "CHK_001_SPEC_PASSED",
  "total_tokens_consumed": 1842,
  "token_ceiling": 5000,
  "system_memory_rss_mb": 4320,
  "max_memory_rss_mb": 8192,
  "active_agent_pids": {
    "ORCH_001": 10452,
    "GRT_001": 10844,
    "L7_VAL_01": 11020
  },
  "circuit_breakers": {
    "L7_VAL_01": "CLOSED",
    "L7_SVC_01": "CLOSED"
  },
  "quality_gate_status": {
    "QG_1_SPEC": "PASSED",
    "QG_2_ARCH": "PASSED",
    "QG_3_SYNTAX": "EVALUATING",
    "QG_4_TEST": "PENDING"
  }
}
```

### 2.2 Agent-Local State Schema (`/state/agents/{agent_id}/local_state.json`)
```json
{
  "agent_id": "L7_VAL_01",
  "assigned_task_id": "TSK_VAL_USER_GET_01",
  "step_index": 2,
  "max_steps": 3,
  "scratchpad": {
    "target_symbol": "UserIdQueryValidator",
    "parsed_constraints": ["UUIDv4", "strict=True"],
    "ast_generation_attempts": 1
  },
  "token_usage_local": {
    "prompt_tokens": 284,
    "completion_tokens": 98,
    "total_tokens": 382
  },
  "last_error": null
}
```

---

## 3. Task Store Design & DAG Representation

Tasks are modeled as a Directed Acyclic Graph (DAG) residing in `/state/tasks/task_dag.json`. Dependencies are strictly resolved using Kahn's topological sorting algorithm before any child agent is launched.

```
+----------------------------------------------------------------------------------------------------+
|                                    TASK DEPENDENCY DAG (task_dag.json)                             |
|                                                                                                    |
|    [TSK_001: Spec Analysis] (Completed)                                                           |
|                 |                                                                                  |
|                 v                                                                                  |
|    [TSK_002: DB Schema Definition] (Completed)                                                    |
|            /          \                                                                            |
|           /            \                                                                           |
|          v              v                                                                          |
|   [TSK_003: User ORM]  [TSK_004: Migration DDL]                                                    |
|          \              /                                                                          |
|           \            /                                                                           |
|            v          v                                                                            |
|     [TSK_005: Auth Service Logic] (In Execution)                                                   |
|                 |                                                                                  |
|                 v                                                                                  |
|     [TSK_006: Route Handlers] (Blocked on TSK_005)                                                 |
|                 |                                                                                  |
|                 v                                                                                  |
|     [TSK_007: Integration Tests] (Blocked on TSK_006)                                              |
+----------------------------------------------------------------------------------------------------+
```

### Task Definition Schema (`/state/tasks/task_dag.json`)
```json
{
  "dag_version": "1.0.0",
  "mission_id": "MIS_20260902_001",
  "nodes": {
    "TSK_005": {
      "task_id": "TSK_005",
      "task_name": "ImplementAuthService",
      "domain": "DEVELOPMENT",
      "level": 4,
      "assigned_agent": "ASVC_001",
      "dependencies": ["TSK_003", "TSK_004"],
      "status": "EXECUTING",
      "retry_count": 0,
      "max_retries": 2,
      "input_artifacts": [
        "file:///workspace/app/models/user.py",
        "file:///workspace/migrations/versions/001_user.py"
      ],
      "output_artifacts_expected": [
        "file:///workspace/app/services/auth_service.py"
      ],
      "token_allocation": 1200
    }
  }
}
```

### Atomic File Write Pattern (ACID Invariant)
Every mutation to `system_state.json` or `task_dag.json` strictly adheres to this transactional pattern:
```python
import os
import json
import tempfile

def atomic_state_commit(target_filepath: str, state_dict: dict) -> None:
    dir_name = os.path.dirname(target_filepath)
    prefix = ".tmp_" + os.path.basename(target_filepath)
    with tempfile.NamedTemporaryFile("w", dir=dir_name, prefix=prefix, delete=False) as tf:
        json.dump(state_dict, tf, indent=2, sort_keys=True)
        tf.flush()
        os.fsync(tf.fileno())  # Force OS buffer write to physical storage
        temp_name = tf.name
    # Atomic replace is guaranteed by POSIX and modern Windows NTFS
    os.replace(temp_name, target_filepath)
```

---

## 4. Checkpoint System & Git Snapshot Engine

To eliminate the "AI Whack-A-Mole" problem, the state engine maintains an immutable sequence of checkpoints. If any agent introduces a bug, causes a test regression, or produces unparseable syntax, the system rewinds the entire workspace to the prior checkpoint.

### Checkpoint Directory Structure
```
/state/checkpoints/CHK_002_BACKEND_GREEN/
├── metadata.json          # Checkpoint identifier, git commit sha, gate approval proof
├── system_state_snap.json # Complete freeze of global state at commit moment
├── task_dag_snap.json     # Complete freeze of task progress graph
└── artifacts_manifest.json# Checksums of all files in /artifacts/ and /workspace/
```

### Checkpoint Metadata Schema (`metadata.json`)
```json
{
  "checkpoint_id": "CHK_002_BACKEND_GREEN",
  "created_at_utc": "2026-09-02T18:24:15.000Z",
  "triggering_gate": "QG_4_TEST",
  "git_commit_sha": "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1f",
  "git_branch": "agent-run/MIS_20260902_001",
  "quality_score": 98.4,
  "test_pass_ratio": "24/24",
  "security_findings_count": 0,
  "workspace_tree_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

---

## 5. Recovery Mechanisms: Crash & Replay Engine

When an unhandled exception, process termination, or hardware failure occurs, the system initiates deterministic recovery:

```
[System Startup / Crash Recovery Hook]
                  |
                  v
       [Check /state/global/lockfile.lock]
                  |
         Is Lock Held by Dead PID?
                  |
            +-----+-----+
            |           |
           YES          NO
            |           |
            |           +--> [Normal Clean Startup]
            v
 [Read /state/checkpoints/ Latest metadata.json]
            |
            v
 [Execute: git reset --hard <git_commit_sha>]
            |
 [Execute: git clean -fd] (Purges dirty untracked files)
            |
            v
 [Restore system_state.json from Checkpoint Snapshot]
            |
 [Restore task_dag.json from Checkpoint Snapshot]
            |
            v
 [Re-queue Any Tasks That Were "EXECUTING" at Crash Moment]
            |
            v
 [Resume Execution with Fresh Worker Pool]
```

### Compensating Actions:
- If a task crashed while performing a multi-step refactoring, the recovery engine does not attempt to "guess" where it left off.
- The Git working tree is hard-reset to the exact SHA recorded in the last green checkpoint.
- The crashed task's retry counter is incremented. If retries $\ge 2$, it is routed to an alternative decomposition agent.

---

## 6. Context Compression & Offloading Strategy

To ensure high accuracy on local 3B parameter models (`qwen2.5-coder:3b` and `llama3.2:3b`), the context window is rigorously shielded from token saturation.

### 6.1 Token Thresholds & Triggers
* **Request Ceiling:** $4,096\,\text{tokens}$ hard limit per single LLM call.
* **Auto-Offload Ceiling:** $>20,000\,\text{tokens}$ (or raw text $>8\,\text{KB}$) automatically triggers artifact disk offloading.
* **Prompt Working Target:** $\le 1,200\,\text{tokens}$ for atomic leaf workers.

### 6.2 The Three-Tier Compression Pipeline
When code or documentation must be supplied to an agent, it passes through three lossless/semantic compression tiers:

```
[Raw File Content: 15,000 Tokens]
                 |
                 v
   +-----------------------------+
   | TIER 1: AST Structural Strip| -> Removes full function bodies; retains function signatures,
   | (Python ast / treesitter)   |    type annotations, and class definitions. (Compression: ~70%)
   +-----------------------------+
                 |
                 v (Reduced to 4,500 Tokens)
   +-----------------------------+
   | TIER 2: Symbol Extract & Map| -> Extracts only the specific symbols relevant to the target task
   | (Dependency Sub-Graph)      |    (e.g., only 'User' model and 'AuthToken' schema). (Compression: ~60%)
   +-----------------------------+
                 |
                 v (Reduced to 1,200 Tokens)
   +-----------------------------+
   | TIER 3: Semantic Embed Ref  | -> If still > 2,000 tokens, writes full payload to /artifacts/
   | (Pointer Envelope Injection)|    and supplies only 150-token extractive summary + URI.
   +-----------------------------+
                 |
                 v
      [Prompt Delivery: < 800 Tokens]
```

---

## 7. Token Management Strategy & Budgeting

The system enforces a **strict total budget of $\le 5,000\,\text{tokens}$ per end-to-end task execution**. To guarantee compliance, token allocations are partitioned across the hierarchy:

| Level | Agent Category | Max Token Budget / Request | Max Completion Tokens | Typical Total Consumption |
| :--- | :--- | :--- | :--- | :--- |
| **L0** | Meta-Orchestrator | 1,000 | 250 | 500 |
| **L1** | Domain Controllers | 800 | 200 | 400 |
| **L2** | Module Specialists | 600 | 200 | 350 |
| **L3 - L6** | Component / Task Leads | 400 | 150 | 250 |
| **L7** | Atomic Leaf Workers | 300 | 250 | 250 |

### Token Exhaustion Circuit Breaker:
If `total_tokens_consumed` across all sub-agents for a specific mission reaches **4,500 tokens** ($90\%$ of the $5,000$ ceiling):
1. All discretionary exploration and documentation synthesis agents are immediately silenced.
2. The orchestrator dispatches deterministic, template-based leaf fallbacks for remaining atomic steps.
3. The mission completes before token exhaustion can induce hallucinatory degradation.
