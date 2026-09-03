# Feature Tour

- **Fractal Spawning**: Every agent can spawn subagents to break down tasks dynamically.
- **Two-Tier Supervisory Bounding**: Agents supervise children and grandchildren only, bounded by a global depth ceiling of 7.
- **Stigmergic Coordination**: Decoupled signaling prevents cross-agent communication bottlenecks.
- **Strict Quality Gates**: Every artifact passes 5 sequential quality gates before acceptance.
- **Process Sandboxing**: Untrusted code runs in isolated environments with memory and syscall caps.
- **Fault Recovery**: Snapshot checkpointing enables instant resumption upon failure.
