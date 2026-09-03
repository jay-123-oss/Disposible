# Technical FAQ

### Why use stigmergy instead of direct agent messaging?
Direct messaging between $N$ agents causes $O(N^2)$ communication bottlenecks. Stigmergy allows agents to coordinate indirectly through blackboard signals, scaling linearly.

### What is the maximum depth?
The global depth is bounded at Level 7, with a two-tier supervisory rule (Parent -> Child -> Grandchild).
