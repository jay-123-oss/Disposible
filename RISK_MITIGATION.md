# RISK_MITIGATION.md: Failure Taxonomy, Defense Systems & Emergency Protocols

## 1. Threat & Failure Model: The Anatomy of Multi-Agent Degradation

Autonomous coding systems deployed on local hardware face unique operational failure modes. When agents are unconstrained, small cognitive slips in 3-billion-parameter models compound exponentially into catastrophic system states.

```
       CONVENTIONAL AGENT DRIFT                         FRACTAL CONTROLLED EXECUTION
     (The "AI Whack-A-Mole" Loop)                     (Deterministic Quality Barrier)

         [Defect in Module A]                             [Atomic Task: Module A]
                  |                                                  |
                  v                                                  v
     [Agent Modifies Whole File]                          [Atomic AST Patch Generated]
                  |                                                  |
                  v                                                  v
     [Introduces Bug in Module B]                         [Quality Gate QG-4 Evaluated]
                  |                                                  |
                  v                                                  |-- FAILED (Regression)
     [Agent Rewrites Interface C]                                    v
                  |                                       [Immediate Git Reset --hard]
                  v                                       [Rollback to Last Green Checkpoint]
     [Breaks System Architecture]                                    |
                  |                                                  v
                  v                                       [Quarantine Agent & Retry Alternative]
         CATASTROPHIC FAILURE                             100% REGRESSION-FREE STABILITY
```

---

## 2. Comprehensive Risk Matrix: The 7 Critical Problems + Edge Risks

| Risk ID | Problem Domain | Risk Description & Failure Impact | Severity | Prevention Strategy | Real-Time Detection Mechanism | Recovery & Fallback Protocol |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RSK-01** | **Infinite Recursion** | Sub-agents spawn child agents recursively without bound, causing stack overflow and process exhaustion. | **CRITICAL** | Hard relative depth bound (`maxDepth = 2`). Hard global ceiling at $L7$. Strict DAG validation. | Task DAG cycle-detector runs on every insertion; recursion token decrement. | Reject spawn request; terminate rogue agent PID; escalate task to parent coordinator. |
| **RSK-02** | **Context Window Pressure** | Full file dumps and conversational logs exceed 4,096 token limit, inducing model hallucinations. | **HIGH** | Strict 4,096 token cap per call; offload payloads $>20\text{K}$ tokens to `/artifacts/`. | Request interceptor counts tokens before calling Ollama REST API. | Reject oversized prompt; trigger 3-tier AST compression and pass file URI pointer. |
| **RSK-03** | **Token Overhead** | Peer-to-peer agent chatter scales quadratically ($O(N^2)$), consuming millions of tokens. | **HIGH** | Stigmergy pattern: agents communicate indirectly via blackboard traces; zero peer messaging. | Token governor monitors running token count against $5,000$ mission budget. | Silence conversational chatter; convert all coordination to linear blackboard signals. |
| **RSK-04** | **Multi-Agent Amplification** | Hallucinated code or flawed assumptions by one agent are accepted as truth by downstream agents. | **CRITICAL** | Zero-trust layered quality gates (QG-1 to QG-7); no unverified code passes boundaries. | Automated AST parsing, typing checks, and unit test execution on every receipt. | Immediate task rejection (RED); trip circuit breaker; rollback to prior clean snapshot. |
| **RSK-05** | **System Memory Exhaustion** | Multiple concurrent agents or model runners exceed 8GB workstation RAM, causing OS kernel panic / OOM. | **CRITICAL** | 512MB RAM hard cgroup/job quota per agent; max 7 concurrent workers in pool. | Background telemetry daemon (`TEL_001`) polls OS process table every $500\,\text{ms}$. | Send `SIGKILL` to highest-RSS non-orchestrator agent; throttle worker pool to 3 slots. |
| **RSK-06** | **Tool State Drift** | Non-idempotent tool calls (partial file writes, environment mutations) corrupt workspace files. | **HIGH** | Sandboxed scoped file I/O; pre/post cryptographic hashing of all modified files. | `WorkingTreeInspector` (`L7_MON_01`) runs `git status --porcelain` on task completion. | `git reset --hard` to last checkpoint commit SHA; execute `git clean -fd`. |
| **RSK-07** | **Sub-Goal Whack-A-Mole** | Fixing a local bug causes unintended regressions in existing functions. | **CRITICAL** | Complete regression suite must run on every commit; 100% pass required. | Quality Gate QG-4 executes full existing pytest test suite before sign-off. | Automated rollback; blacklists the specific code patch; alerts developer. |
| **RSK-08** | **3B Local Model Drift** | Local 3B parameter model produces malformed JSON or deviates from requested format. | **HIGH** | Constrained JSON schema decoding; temperature set to $0.1$; few-shot grammar rules. | Schema validation interceptor parses response; checks all required fields. | Automated feedback iteration (1 retry) with syntax error injected into prompt; fallback to regex. |
| **RSK-09** | **Agent Deadlocks** | Two intermediate agents wait mutually on each other's completion signals on the blackboard. | **MEDIUM** | Strict topological sorting (Kahn's algorithm); cyclic dependencies forbidden at planning. | Watchdog monitor detects tasks in `WAITING` state $>30\,\text{seconds}$. | Cancel dependent task; emit `DEADLOCK_DETECTED`; notify parent orchestrator to re-sequence. |
| **RSK-10** | **Secret / Credential Leak** | Agent inadvertently outputs hardcoded API tokens, private keys, or passwords in source files. | **CRITICAL** | Regex and Shannon entropy detectors scan all diffs before file commit. | QG-5 security scanner inspects diff with automated secret patterns (AWS, JWT, SSH). | Reject code commit; wipe diff; quarantine agent; substitute with environment variable call. |

---

## 3. Deep-Dive Prevention Strategies

### 3.1 Mathematical Anti-Recursion Shield
To guarantee that no execution path recurses infinitely:
1. Every task envelope generated at Level $N$ carries an immutable decrementing **Recursion Gas Budget**:
$$G_{\text{remaining}} = G_{\text{parent}} - 1$$
2. When a task reaches $G_{\text{remaining}} = 0$ (configured to match the level difference to $L7$), the agent runtime physically removes the `spawn_sub_agent` tool from the agent's capability list, forcing the agent to act as a leaf node.
3. If an agent attempts to invoke a sub-agent when `level >= 7` or `gas <= 0`, the tool runner raises an uncatchable `RecursionBudgetExceededException`.

### 3.2 Memory Governor & Process Isolation (8GB Hard Ceiling)
To ensure the system never exceeds 8GB workstation RAM:
```python
import resource
import os

def enforce_agent_memory_limit(max_ram_mb: int = 512):
    """Enforces hard physical memory ceiling using OS kernel primitives."""
    max_bytes = max_ram_mb * 1024 * 1024
    if os.name != "nt":  # POSIX systems
        # RLIMIT_AS controls maximum address space
        resource.setrlimit(resource.RLIMIT_AS, (max_bytes, max_bytes))
    else:
        # Windows systems: Job Object memory limits are bound to the worker PID
        import win32job
        import win32api
        h_job = win32job.CreateJobObject(None, "")
        info = win32job.QueryInformationJobObject(h_job, win32job.JobObjectExtendedLimitInformation)
        info['ProcessMemoryLimit'] = max_bytes
        info['BasicLimitInformation']['LimitFlags'] = win32job.JOB_OBJECT_LIMIT_PROCESS_MEMORY
        win32job.SetInformationJobObject(h_job, win32job.JobObjectExtendedLimitInformation, info)
        win32job.AssignProcessToJobObject(h_job, win32api.GetCurrentProcess())
```

---

## 4. Real-Time Detection Mechanisms

The system employs three active background watchdogs running in low-overhead daemon threads:

```
+----------------------------------------------------------------------------------------------------+
|                                ACTIVE TELEMETRY & INVARIANT WATCHDOGS                              |
|                                                                                                    |
|  +---------------------------+  +---------------------------+  +---------------------------------+ |
|  |     TASK WATCHDOG         |  |      DRIFT MONITOR        |  |        RESOURCE GOVERNOR        | |
|  | - Ticks every 1.0 second. |  | - Runs on tool execution. |  | - Ticks every 500 milliseconds. | |
|  | - Hard 30s timeout cap.   |  | - Git working tree diff.  |  | - Reads system total RSS.       | |
|  | - Identifies deadlocks.   |  | - Computes SHA-256 hashes.|  | - Enforces 8GB global ceiling.  | |
|  +---------------------------+  +---------------------------+  +---------------------------------+ |
+----------------------------------------------------------------------------------------------------+
```

### Invariant Check Rules:
1. **Rule I-1 (Tree Purity):** At the end of every atomic task, the only modified files in the working directory must match the `atomic_scope.target_file` declared in the task delegation envelope. If any other file was modified, drift is flagged immediately.
2. **Rule I-2 (Execution Boundedness):** If an agent execution step takes longer than $30\,\text{seconds}$, the watchdog sends `SIGKILL` to the worker process and marks the task as timed out.
3. **Rule I-3 (Memory Monotonicity):** If total system RAM exceeds $7,600\,\text{MB}$ ($92\%$ of $8\,\text{GB}$), the resource governor freezes worker dispatch and pauses active worker processes until memory is reclaimed.

---

## 5. Recovery Procedures & Deterministic Re-winding

When a failure is detected, the recovery protocol executes deterministically without generative guessing:

```
[Defect / Failure Detected]
             |
             v
   [Identify Scope of Impact]
             |
     +-------+-------+
     |               |
[Atomic Task Failure] [Domain-Level Failure]
     |               |
     v               v
1. Kill worker PID.  1. Kill all domain worker PIDs.
2. Discard uncommitted file changes. 2. Read git commit SHA from last green checkpoint.
3. Increment task retry counter.     3. Execute: git reset --hard <git_commit_sha>
4. If retries < 2: Retry with        4. Execute: git clean -fd
   compiler error feedback.          5. Restore task_dag.json to checkpoint state.
5. If retries >= 2: Trip breaker,    6. Mark domain task FAILED; alert Orchestrator.
   escalate to parent coordinator.
```

---

## 6. Fallback Plans: Graceful Degradation

If the primary neural model (`qwen2.5-coder:3b`) repeatedly fails a specific task due to cognitive limitations:

1. **Fallback Level 1 (Model Switching):** The orchestrator switches the assigned model to `llama3.2:3b`, which possesses different tokenization and instruction-following biases.
2. **Fallback Level 2 (Hyper-Decomposition):** If a Level 6 task fails under both models, the parent agent splits the atomic task into two even smaller micro-tasks (e.g., separating parameter extraction from validation logic).
3. **Fallback Level 3 (Deterministic Code Templates):** For standard, recurring boilerplate (CRUD routes, Dockerfiles, pytest mocks), the system bypasses neural LLM generation entirely and renders verified, pre-tested AST templates populated with the target entity parameters.
4. **Fallback Level 4 (Human-in-the-Loop Escalation):** If all automated fallbacks fail after 2 iterations, the system freezes the workspace, logs full diagnostics, and requests precise human guidance without corrupting any previously validated files.

---

## 7. Emergency Stop Protocols (System Kill Switch)

If an irrecoverable state occurs (e.g., disk full, runaway loop, or memory cascade), the operator or watchdog triggers the **Emergency Kill Switch**.

### 7.1 The Emergency Shutdown Sequence
1. **Signal Emission:** The orchestrator writes `{"status": "EMERGENCY_STOP", "reason": "OPERATOR_KILL"}` to `/state/global/system_state.json`.
2. **Process Termination:** The orchestrator iterates through `active_agent_pids` and dispatches `SIGKILL` to all worker processes, immediately releasing all allocated RAM.
3. **Blackboard Freeze:** The Stigmergy Blackboard lockfile is acquired and sealed; all pending pheromone signals are marked invalid.
4. **Workspace Quarantine:** The current Git working tree is snapshotted to a quarantine branch (`quarantine/emergency-stop-<timestamp>`) for post-mortem forensics.
5. **Clean Restoration:** The primary working branch is hard-reset to the last verified green checkpoint:
   ```bash
   git reset --hard $(cat /state/checkpoints/LATEST/git_commit_sha)
   git clean -fd
   ```
6. **Diagnostic Manifest Generation:** A post-mortem diagnostic dump is generated at `/artifacts/emergency_post_mortem.json` detailing exact token counts, process states, and failure stack traces at the moment of shutdown.
