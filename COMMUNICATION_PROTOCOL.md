# COMMUNICATION_PROTOCOL.md: Message Specification, Stigmergy & Artifact Protocols

## 1. Protocol Architecture & Invariants

Communication in this fractal multi-agent system is architected around two core physical principles:
1. **Vertical Determinism (Control Channel):** Direct, synchronous or asynchronous command envelopes between immediate parent and child ($L_k \leftrightarrow L_{k+1}$).
2. **Horizontal Decoupling (Stigmergy Channel):** Peer agents never talk to each other directly. Instead, they interact indirectly by modifying and observing the shared environment (the **Stigmergy Blackboard** and the **Artifact Filesystem**).

### Architectural Invariants:
* **Invariant C1 (No Lateral Cross-Talk):** Any attempt by an agent to send a message directly to a peer at the same level or across unrelated sub-trees is blocked by the runtime router and logged as a security violation.
* **Invariant C2 (Hard Token Envelope Ceiling):** No single message envelope transmitted over IPC, Unix socket, or HTTP may exceed **4,096 tokens** (approximately $16\,\text{KB}$).
* **Invariant C3 (Artifact Pointer Indirection):** Any data payload exceeding **20,000 tokens** (or $8\,\text{KB}$ raw text) must be offloaded to the local filesystem under `/artifacts/`. The message transmits *only* the canonical file URI, SHA-256 digest, and an extractive summary.
* **Invariant C4 (Cryptographic Tracing):** Every message frame must carry a globally unique `trace_id`, a parent `correlation_id`, and a cryptographic checksum of its payload.

---

## 2. Standard Message Format Specification

All control messages, task dispatches, status beacons, and completion receipts conform to the standard **Fractal Agent Message Frame (FAMF)** JSON specification.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "FractalAgentMessageFrame",
  "type": "object",
  "required": [
    "frame_id",
    "trace_id",
    "correlation_id",
    "timestamp_utc",
    "sender_id",
    "recipient_id",
    "message_type",
    "priority",
    "token_budget",
    "payload",
    "payload_checksum"
  ],
  "properties": {
    "frame_id": {
      "type": "string",
      "format": "uuid",
      "description": "Globally unique identifier for this message frame"
    },
    "trace_id": {
      "type": "string",
      "pattern": "^trc_[a-f0-9]{16}$",
      "description": "End-to-end distributed transaction trace identifier"
    },
    "correlation_id": {
      "type": "string",
      "format": "uuid",
      "description": "Frame ID of the initiating request being responded to"
    },
    "timestamp_utc": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 UTC timestamp of frame generation"
    },
    "sender_id": {
      "type": "string",
      "pattern": "^[A-Z0-9_]{3,32}$"
    },
    "recipient_id": {
      "type": "string",
      "pattern": "^[A-Z0-9_]{3,32}$"
    },
    "message_type": {
      "type": "string",
      "enum": [
        "TASK_DELEGATION",
        "PROGRESS_BEACON",
        "EXECUTION_RECEIPT",
        "ERROR_ESCALATION",
        "CIRCUIT_BREAK_ALERT",
        "STIGMERGY_SIGNAL",
        "TERMINATION_ORDER"
      ]
    },
    "priority": {
      "type": "string",
      "enum": ["LOW", "NORMAL", "HIGH", "CRITICAL"]
    },
    "token_budget": {
      "type": "object",
      "required": ["allocated", "consumed", "remaining"],
      "properties": {
        "allocated": { "type": "integer", "maximum": 4096 },
        "consumed": { "type": "integer" },
        "remaining": { "type": "integer" }
      }
    },
    "payload": {
      "type": "object",
      "description": "Message-type specific payload object"
    },
    "payload_checksum": {
      "type": "string",
      "pattern": "^sha256:[a-f0-9]{64}$",
      "description": "SHA-256 hash of canonical serialized payload JSON"
    }
  }
}
```

---

## 3. Agent-to-Agent Communication Protocols

Vertical communication between supervising parents and subordinate children is governed by three primary message frames:

### 3.1 Task Delegation Frame (Parent $\rightarrow$ Child)
Sent by a parent agent ($L_k$) to initiate an atomic or sub-decomposed task on a child ($L_{k+1}$).

```json
{
  "frame_id": "8f3e2b1a-4c9d-4e7a-9a1b-3f2e1d0c9b8a",
  "trace_id": "trc_9a8b7c6d5e4f3a2b",
  "correlation_id": "00000000-0000-0000-0000-000000000000",
  "timestamp_utc": "2026-09-02T18:20:00.120Z",
  "sender_id": "GRT_001",
  "recipient_id": "L7_VAL_01",
  "message_type": "TASK_DELEGATION",
  "priority": "HIGH",
  "token_budget": {
    "allocated": 1024,
    "consumed": 0,
    "remaining": 1024
  },
  "payload": {
    "task_id": "TSK_VAL_USER_GET_01",
    "intent": "Generate Pydantic v2 query validator for user ID",
    "atomic_scope": {
      "target_file": "app/api/validators/user_validator.py",
      "target_symbol": "UserIdQueryValidator",
      "constraints": [
        "Inherit from pydantic.BaseModel",
        "Field user_id must be uuid.UUID",
        "Forbid extra query parameters"
      ]
    },
    "artifact_references": [
      {
        "uri": "file:///workspace/artifacts/specs/user_model_spec.json",
        "sha256": "sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"
      }
    ]
  },
  "payload_checksum": "sha256:3d2891a9f0e1c2b3a4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7"
}
```

### 3.2 Progress Beacon Frame (Child $\rightarrow$ Parent)
Emitted by long-running intermediate agents ($L_1$ to $L_6$) at periodic intervals (default: every 5 seconds) to prevent watchdog timeouts.

```json
{
  "frame_id": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "trace_id": "trc_9a8b7c6d5e4f3a2b",
  "correlation_id": "8f3e2b1a-4c9d-4e7a-9a1b-3f2e1d0c9b8a",
  "timestamp_utc": "2026-09-02T18:20:05.150Z",
  "sender_id": "L7_VAL_01",
  "recipient_id": "GRT_001",
  "message_type": "PROGRESS_BEACON",
  "priority": "NORMAL",
  "token_budget": {
    "allocated": 1024,
    "consumed": 312,
    "remaining": 712
  },
  "payload": {
    "task_id": "TSK_VAL_USER_GET_01",
    "percent_complete": 60,
    "current_step": "AST_VALIDATION",
    "memory_rss_mb": 184
  },
  "payload_checksum": "sha256:e1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2"
}
```

### 3.3 Execution Receipt Frame (Child $\rightarrow$ Parent)
The terminal response emitted when an agent completes its atomic task. Contains verification proofs, hashes, and performance telemetry.

```json
{
  "frame_id": "2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e",
  "trace_id": "trc_9a8b7c6d5e4f3a2b",
  "correlation_id": "8f3e2b1a-4c9d-4e7a-9a1b-3f2e1d0c9b8a",
  "timestamp_utc": "2026-09-02T18:20:07.410Z",
  "sender_id": "L7_VAL_01",
  "recipient_id": "GRT_001",
  "message_type": "EXECUTION_RECEIPT",
  "priority": "HIGH",
  "token_budget": {
    "allocated": 1024,
    "consumed": 418,
    "remaining": 606
  },
  "payload": {
    "task_id": "TSK_VAL_USER_GET_01",
    "status": "COMPLETED",
    "execution_duration_ms": 7290,
    "artifacts_produced": [
      {
        "uri": "file:///workspace/app/api/validators/user_validator.py",
        "sha256": "sha256:9f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
        "byte_size": 432
      }
    ],
    "verification_proof": {
      "ast_syntax_valid": true,
      "linter_exit_code": 0,
      "cyclomatic_complexity": 1
    }
  },
  "payload_checksum": "sha256:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"
}
```

---

## 4. Stigmergy Pattern Implementation

The **Stigmergy Pattern** eliminates the $O(N^2)$ communication bottleneck of traditional multi-agent systems. In biological systems (such as termite mound construction or ant foraging), agents do not broadcast instructions to peers; instead, an agent modifies the local environment (deposits a chemical pheromone), which autonomously stimulates action by subsequent agents.

### 4.1 Theoretical Foundation: Quadratic vs. Linear Scaling
In a conventional conversational multi-agent system with $N$ collaborating agents:
$$\text{Peer-to-Peer Message Count} = \frac{N(N-1)}{2} = O(N^2)$$
If each coordination round exchanges $K$ tokens across $N$ agents, token consumption scales quadratically:
$$\text{Total Tokens}_{\text{conversational}} = O(K \cdot N^2)$$
For $N = 50$ agents and an average conversational context of $K = 2,000$ tokens, a single cycle consumes:
$$\frac{50 \times 49}{2} \times 2,000 = 2,450,000\,\text{tokens}\quad (\text{Catastrophic Token Exhaustion})$$

Under our **Stigmergy Architecture**:
1. An agent writes its output artifact to disk and appends a tiny signal ($\approx 50$ tokens) to `/state/global/blackboard.json`.
2. Dependent agents check the blackboard state filter. Only the specific agent whose precondition is met wakes up.
3. Total message count across the entire pipeline is strictly linear with respect to the number of task steps:
$$\text{Total Tokens}_{\text{stigmergy}} = \sum_{i=1}^{N} \text{Tokens}(\text{Task}_i) + O(S \cdot N) = O(N)$$
Where $S$ is the minuscule blackboard signal size ($\le 100$ bytes). For $N=50$ atomic tasks with average execution prompts of $800$ tokens:
$$\text{Total Tokens}_{\text{stigmergy}} \approx 50 \times 800 + (50 \times 20) = 41,000\,\text{tokens}$$
**Stigmergy achieves a $98.3\%$ reduction in total token overhead.**

---

### 4.2 Stigmergy Mechanics: Traces, Signals, and Decay

```
+----------------------------------------------------------------------------------------------------+
|                                    STIGMERGY BLACKBOARD (/state/global/blackboard.json)            |
|                                                                                                    |
|  +-----------------------------------------------------------------------------------------------+ |
|  | ACTIVE PHEROMONE SIGNALS                                                                      | |
|  |                                                                                               | |
|  |  Signal 1: [BACKEND_SCHEMA_READY]                                                             | |
|  |  - Origin: L7_SCH_01        - Strength: 0.95 (Decays at 0.05/min)                             | |
|  |  - Payload Ref: file:///artifacts/schemas/user.json                                          | |
|  |  - Listeners Awoken: [L7_VAL_01, L7_SQL_01, L7_TST_01]                                          | |
|  |                                                                                               | |
|  |  Signal 2: [ROUTE_AST_ASSEMBLED]                                                              | |
|  |  - Origin: GRT_001          - Strength: 0.88                                                  | |
|  |  - Listeners Awoken: [L7_TST_03, SAST_001]                                                    | |
|  +-----------------------------------------------------------------------------------------------+ |
|                                                  |                                                 |
|  +-----------------------------------------------+-----------------------------------------------+ |
|  | GARBAGE COLLECTION & EVAPORATION ENGINE                                                       | |
|  |   Current Pheromone Evaporation Formula: S(t) = S_0 * e^(-lambda * (t - t_0))                  | |
|  |   Signals with S(t) < 0.10 are automatically evicted from active memory.                      | |
|  +-----------------------------------------------------------------------------------------------+ |
+----------------------------------------------------------------------------------------------------+
```

#### The Pheromone Signal Schema (`/state/global/blackboard.json`)
```json
{
  "signal_id": "sig_usr_schema_001",
  "topic": "DATA_MODEL:USER:CREATED",
  "origin_agent_id": "L7_SCH_01",
  "emitted_at_utc": "2026-09-02T18:22:00.000Z",
  "initial_intensity": 1.0,
  "decay_rate_lambda": 0.02,
  "ttl_seconds": 600,
  "environmental_modifications": [
    {
      "path": "app/models/user.py",
      "action": "CREATED",
      "sha256": "sha256:4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a"
    }
  ],
  "context_pointers": [
    {
      "key": "user_schema_spec",
      "uri": "file:///workspace/artifacts/schemas/user_model.json"
    }
  ],
  "consumed_by": ["L7_VAL_01", "L7_SQL_01"]
}
```

#### Pheromone Decay & Evaporation Mathematics
To prevent the blackboard from accumulating obsolete signals and exhausting local memory, every signal is subjected to exponential mathematical decay:

$$I(t) = I_0 \cdot e^{-\lambda (t - t_0)}$$

Where:
- $I(t)$ is the current pheromone intensity at time $t$.
- $I_0$ is the initial emission intensity ($1.0$).
- $\lambda$ is the decay constant ($\lambda = 0.02\,\text{sec}^{-1}$ for standard task signals; $\lambda = 0.005\,\text{sec}^{-1}$ for foundational architectural contracts).
- $t - t_0$ is elapsed time in seconds.

**Evaporation Rule:** When $I(t) < 0.10$ or $t - t_0 > \text{ttl\_seconds}$, the signal is deemed "evaporated" and permanently pruned by the `MonitoringDomain` (`MON_001`) garbage collection thread.

---

## 5. Artifact-Based Communication & Offloading Protocol

To guarantee that no LLM prompt exceeds the 4,096 token limit, all large context objects are managed through the **Artifact Offload Engine**.

```
[Agent Execution Pipeline]
            |
            v
    { Context Object }
            |
    Is Context Size > 20,000 Tokens? (or > 8 KB raw text)
            |
      +-----+-----+
      |           |
     YES          NO
      |           |
      |           +---> [Inline Directly in Prompt Body]
      v
[Write Immutable File to /artifacts/...]
      |
[Compute SHA-256 Digest]
      |
[Generate 150-Token Extractive Summary]
      |
[Inject Pointer Envelope into Message]
   - URI: file:///workspace/artifacts/...
   - SHA-256: sha256:...
   - Summary: "Pydantic user model with fields id, email..."
```

### Pointer Envelope Schema
When an artifact is passed to an agent, the prompt receives only the pointer block:

```json
{
  "artifact_type": "SOURCE_SPECIFICATION",
  "uri": "file:///workspace/artifacts/openapi_spec_v1.json",
  "byte_size": 48290,
  "token_count_equivalent": 12450,
  "sha256": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "symbol_index": [
    { "symbol": "UserSchema", "offset": 1024, "length": 420 },
    { "symbol": "AuthRequest", "offset": 1444, "length": 310 }
  ],
  "concise_summary": "OpenAPI specification declaring auth, user registration, and profile GET/PUT endpoints with JWT bearer authentication."
}
```

---

## 6. Synchronous vs. Asynchronous Communication Patterns

The communication subsystem maps operational workflows to appropriate synchronization primitives:

| Pattern | Mechanism | Timeout | Fallback Action | Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **Sync RPC** | Blocking IPC Socket / Subprocess Pipe | $30\,\text{seconds}$ | Circuit Trip $\rightarrow$ Escalate to Parent | Leaf agent atomic execution ($L7$ code generation, AST validation). |
| **Async Event** | Blackboard Signal + Ephemeral Poll | $120\,\text{seconds}$ | Emit `TASK_TIMEOUT` $\rightarrow$ Reassign Worker | Cross-domain synchronization ($L2$ Backend waiting for $L2$ Database migration). |
| **Hierarchical Waterfall** | Parent Join Barrier | $180\,\text{seconds}$ | Quality Gate Failure $\rightarrow$ Rollback | Phase transition (Planning complete $\rightarrow$ Development begins). |
| **Broadcast Consensus** | Parallel Fan-out / Fan-in | $15\,\text{seconds}$ | Quorum Evaluation ($\ge 3/4$ Agree) | Security & quality validation quorum. |

---

## 7. Error Handling, Retries, and Dead Letter Protocols

```
[Inbound Message Frame]
            |
            v
   [Validate JSON Schema] ---- INVALID ---> [Reject Frame: SCHEMA_VIOLATION]
            |
            v
  [Verify SHA-256 Checksum] -- MISMATCH --> [Reject Frame: CORRUPTED_PAYLOAD]
            |
            v
   [Check Recipient State] --- BUSY ------> [Enqueue in Local FIFO Queue]
            |
            v
      [Process Task]
            |
      +-----+-----+
      |           |
   SUCCESS     FAILURE
      |           |
      v           v
  [Emit RECEIPT]  [Attempt Count < 2?]
                  |        |
                 YES       NO
                  |        |
                  |        +--> [Trip Circuit Breaker to OPEN]
                  v             [Move Frame to /state/dead_letter/]
          [Exponential Backoff] [Emit ERROR_ESCALATION to Parent]
          [Retry Atomic Task]
```

### Dead Letter Queue (DLQ) Management
- Undeliverable, unparseable, or repeatedly failing message frames are diverted to `/state/dead_letter/{frame_id}.json`.
- The `MonitoringDomain` inspects the DLQ on every tick. If more than 3 messages enter the DLQ within a 60-second window, the system enters `EMERGENCY_FREEZE` mode, pausing active workers and awaiting operator intervention or initiating automated rollback to the last known green checkpoint.
