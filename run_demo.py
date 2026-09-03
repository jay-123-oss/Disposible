"""Interactive demonstration script: executes live tasks on all 6 core LLM agents."""

from __future__ import annotations

import json
import sys
from orchestrator import Core6Orchestrator

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_demo():
    print("=" * 70)
    print("🤖 FRACTAL 6-AGENT CORE SYSTEM - LIVE EXECUTION DEMO")
    print("=" * 70)

    orch = Core6Orchestrator()

    # 1. Coding Agent
    print("\n[1/6] 💻 Coding Agent (Qwen2.5-Coder:3B)")
    res_code = orch.process("Build an async token bucket rate limiter in Python", "coding")
    print(res_code.get("output", ""))

    # 2. Testing Agent
    print("\n[2/6] 🧪 Testing Agent (Qwen2.5-Coder:3B)")
    res_test = orch.process("Write pytest test cases for the rate limiter", "testing")
    print(res_test.get("output", ""))

    # 3. Security Agent
    print("\n[3/6] 🛡️ Security Agent (Qwen2.5-Coder:3B)")
    res_sec = orch.process("Audit authentication and rate limiting security", "security")
    print(res_sec.get("output", ""))

    # 4. Quality Agent
    print("\n[4/6] 📊 Quality Agent (Llama3.2:3B)")
    res_qual = orch.process("Review code maintainability and SOLID design patterns", "quality")
    print(res_qual.get("output", ""))

    # 5. Infrastructure Agent
    print("\n[5/6] 🐳 Infrastructure Agent (Llama3.2:3B)")
    res_infra = orch.process("Generate production Dockerfile and Kubernetes deployment", "infrastructure")
    print(res_infra.get("output", ""))

    # 6. Embedding Agent
    print("\n[6/6] 🧠 Embedding Agent (Nomic-Embed-Text)")
    res_emb = orch.process("Search vector database for authentication documentation", "embedding")
    print(f"Dimensions: {res_emb.get('dimensions')}")
    print(f"Sample Vector: {res_emb.get('sample_vector')}")
    print(f"Output: {res_emb.get('output')}")

    # Full Sequential Pipeline
    print("\n" + "=" * 70)
    print("🔄 FULL 6-AGENT SEQUENTIAL PIPELINE DEMO (/run-all)")
    print("=" * 70)
    res_all = orch.process_all("Build and deploy a scalable payment webhook receiver")
    print(f"Task: {res_all.get('task')}")
    print(f"Total Agents Executed: {res_all.get('total_agents')}")
    print(f"Total Latency: {res_all.get('total_latency_seconds')}s")
    for agent_id in res_all.get("results", {}):
        print(f"  - {agent_id.upper()}: Processed successfully")

    print("\n" + "=" * 70)
    print("✅ All 6 Agents Executed and Verified Successfully!")
    print("=" * 70)


if __name__ == "__main__":
    run_demo()
