"""KnowledgeBase class storing question templates, tech stacks, architectures, and risks."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional


logger = logging.getLogger("FractalCore.KnowledgeBase")


class KnowledgeBase:
    """In-memory knowledge repository for the planning domain."""

    def __init__(self) -> None:
        self.question_templates: Dict[str, List[str]] = {
            "project_type": [
                "What type of software project are you developing? (Options: API, Web, CLI, Microservice)",
                "Is this a standalone service or integrated into an existing distributed architecture?",
                "What is the primary interface modality? (REST, GraphQL, CLI, Frontend UI)",
            ],
            "tech_stack": [
                "Which primary backend programming language is preferred? (python, node, go, rust, java)",
                "Do you have a specific database engine in mind? (PostgreSQL, SQLite, Redis, MongoDB)",
                "What web framework or routing layer should be targeted?",
            ],
            "features": [
                "What core functional capabilities are essential? (e.g. Authentication, RBAC, File Storage, Webhooks)",
                "Does the application require asynchronous background jobs or real-time event streaming?",
                "What third-party integrations or external APIs are mandatory?",
            ],
            "constraints": [
                "What are your hardware and memory operational boundaries? (e.g., <=8GB RAM, local execution)",
                "Are there strict deployment constraints? (e.g., Docker, bare-metal, serverless)",
                "What is the allowable latency ceiling for critical user requests? (e.g., <200ms)",
            ],
            "success_criteria": [
                "What automated unit/integration test coverage threshold must be achieved? (e.g., >=90%)",
                "What are the target throughput and concurrency expectations?",
                "What zero-defect criteria or compliance checks define a successful delivery?",
            ],
        }

        self.tech_stack_data: Dict[str, Dict[str, Any]] = {
            "python": {
                "frameworks": ["FastAPI", "Django", "Flask"],
                "default_framework": "FastAPI",
                "orm": ["SQLAlchemy", "SQLModel", "Tortoise-ORM"],
                "test_framework": "pytest",
                "libraries": {
                    "auth": ["pyjwt", "passlib", "bcrypt"],
                    "validation": ["pydantic", "marshmallow"],
                    "networking": ["httpx", "aiohttp", "requests"],
                    "async_tasks": ["celery", "arq"],
                },
                "use_cases": ["High-throughput REST APIs", "AI/ML Pipelines", "Rapid Prototyping", "Data Processing"],
                "strengths": ["Rapid development", "Massive ecosystem", "Rich type annotation support in Python 3.10+"],
            },
            "node": {
                "frameworks": ["Express", "NestJS", "Fastify"],
                "default_framework": "Fastify",
                "orm": ["Prisma", "TypeORM", "Drizzle"],
                "test_framework": "jest",
                "libraries": {
                    "auth": ["jsonwebtoken", "passport", "argon2"],
                    "validation": ["zod", "joi"],
                    "networking": ["axios", "undici"],
                    "async_tasks": ["bullmq"],
                },
                "use_cases": ["Real-time applications", "I/O intensive web services", "Full-stack TypeScript"],
                "strengths": ["Event-driven I/O", "Shared frontend/backend language"],
            },
            "go": {
                "frameworks": ["Gin", "Echo", "Fiber", "Standard Library (net/http)"],
                "default_framework": "Gin",
                "orm": ["GORM", "sqlx"],
                "test_framework": "testing",
                "libraries": {
                    "auth": ["golang-jwt/jwt", "bcrypt"],
                    "validation": ["validator/v10"],
                    "networking": ["net/http"],
                },
                "use_cases": ["Microservices", "Cloud infrastructure tooling", "High-concurrency systems"],
                "strengths": ["Extremely low memory footprint", "Fast compilation", "Native concurrency"],
            },
            "rust": {
                "frameworks": ["Actix-web", "Axum", "Rocket"],
                "default_framework": "Axum",
                "orm": ["SeaORM", "Diesel", "sqlx"],
                "test_framework": "cargo test",
                "libraries": {
                    "auth": ["jsonwebtoken", "argon2"],
                    "validation": ["validator"],
                    "networking": ["reqwest", "tokio"],
                },
                "use_cases": ["Mission-critical low-latency systems", "Embedded software", "High-security backends"],
                "strengths": ["Memory safety without garbage collector", "Zero-cost abstractions"],
            },
            "java": {
                "frameworks": ["Spring Boot", "Quarkus", "Micronaut"],
                "default_framework": "Spring Boot",
                "orm": ["Hibernate", "JPA"],
                "test_framework": "JUnit 5",
                "libraries": {
                    "auth": ["Spring Security", "jjwt"],
                    "validation": ["Hibernate Validator"],
                },
                "use_cases": ["Enterprise business applications", "Distributed transactional services"],
                "strengths": ["Robust enterprise ecosystem", "Battle-tested concurrency models"],
            },
        }

        self.architecture_patterns: Dict[str, Dict[str, Any]] = {
            "monolithic": {
                "description": "Unified single codebase containing presentation, business logic, and data access layers.",
                "layers": ["Presentation/Routing", "Service/Business Logic", "Data Access/ORM"],
                "recommended_for": ["MVPs", "Small teams", "Single-purpose applications", "Rapid delivery"],
                "complexity": "LOW",
            },
            "microservices": {
                "description": "Independently deployable bounded contexts communicating over HTTP REST or message brokers.",
                "layers": ["API Gateway", "Domain Service Nodes", "Shared Event Bus", "Dedicated Databases"],
                "recommended_for": ["Large engineering organizations", "Independent autoscaling needs"],
                "complexity": "HIGH",
            },
            "serverless": {
                "description": "Event-driven stateless functions executing within ephemeral cloud runtimes.",
                "layers": ["API Gateway / Event Trigger", "Function Handlers", "Managed Storage"],
                "recommended_for": ["Sporadic traffic", "Low idle cost", "Task-based workloads"],
                "complexity": "MEDIUM",
            },
            "hexagonal": {
                "description": "Ports and Adapters architecture isolating core business domain from external infrastructure.",
                "layers": ["Domain Core", "Application Ports", "Adapters (HTTP, DB, CLI)"],
                "recommended_for": ["High testability", "Complex business rules", "Pluggable dependencies"],
                "complexity": "MEDIUM",
            },
            "clean": {
                "description": "Layered dependency inversion where inner business entities know nothing of outer layers.",
                "layers": ["Entities", "Use Cases", "Interface Adapters", "Frameworks & Drivers"],
                "recommended_for": ["Enterprise longevity", "High maintainability", "Multi-platform delivery"],
                "complexity": "HIGH",
            },
        }

        self.risk_patterns: Dict[str, Dict[str, Any]] = {
            "performance": {
                "description": "Unbounded latency, N+1 query overhead, CPU bottlenecking under concurrency.",
                "mitigation": "Enforce pagination, implement database indexes, connection pooling, and caching.",
            },
            "security": {
                "description": "Injection vulnerabilities (SQLi, XSS), unhashed credentials, broken object-level auth.",
                "mitigation": "Use parameterized queries, Argon2 password hashing, strict Pydantic DTO validation, and SAST scans.",
            },
            "timeline": {
                "description": "Feature creep, ambiguous third-party API dependencies, under-decomposed tasks.",
                "mitigation": "Decompose into atomic tasks (<=15 min each), enforce strict phase quality gates.",
            },
            "technical": {
                "description": "Language version incompatibilities, conflicting library dependencies, unsupported runtime tools.",
                "mitigation": "Pin dependencies with exact hashes, test in isolated local sandboxes.",
            },
            "resource": {
                "description": "Local workstation RAM exhaustion exceeding 8GB limit or local LLM inference timeouts.",
                "mitigation": "Apply 512MB RAM cap per agent process, 30s timeouts, and offload >4096 token context.",
            },
            "external": {
                "description": "Unreachable remote services or external vendor rate limits.",
                "mitigation": "Implement exponential backoff, circuit breakers, and mock fallback fixtures.",
            },
        }

        self.common_requirements: Dict[str, Dict[str, Any]] = {
            "api": {
                "functional": ["HTTP REST endpoints", "JSON serialization", "CRUD operations", "Error status responses"],
                "non_functional": ["Response time < 200ms", "Structured logging", "Zero SQL injections"],
                "technical": ["FastAPI or Express", "Pydantic/Zod DTOs", "SQLAlchemy/Prisma ORM"],
            },
            "web_app": {
                "functional": ["HTML template rendering or SPA bundle", "Session management", "Static asset serving"],
                "non_functional": ["Lighthouse performance >= 90", "Cross-browser compatibility"],
                "technical": ["Jinja2 or React", "Tailwind CSS or Vanilla CSS"],
            },
            "cli_tool": {
                "functional": ["Positional arguments", "Flag parsing", "Colored terminal output", "Exit codes"],
                "non_functional": ["Startup time < 100ms", "Zero external daemon dependencies"],
                "technical": ["argparse or click", "Rich terminal library"],
            },
            "microservice": {
                "functional": ["Health check endpoints (/health, /ready)", "Metric exposition (/metrics)", "Graceful shutdown"],
                "non_functional": ["Containerization via Dockerfile", "Configurable via environment variables"],
                "technical": ["Docker", "Prometheus client", "Structured JSON logger"],
            },
        }

        logger.debug("KnowledgeBase initialized with templates, tech stacks, and risk patterns.")

    def get_templates_for_category(self, category: str) -> List[str]:
        """Fetch predefined question templates for a category."""
        return list(self.question_templates.get(category, []))

    def get_tech_stack_info(self, language: str) -> Optional[Dict[str, Any]]:
        """Fetch language runtime specifications and frameworks."""
        return self.tech_stack_data.get(language.lower())

    def get_architecture_pattern(self, pattern_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve details on a specific architecture pattern."""
        return self.architecture_patterns.get(pattern_name.lower())

    def get_risk_pattern(self, category: str) -> Optional[Dict[str, Any]]:
        """Retrieve risks and standard mitigations for a category."""
        return self.risk_patterns.get(category.lower())

    def get_common_requirements(self, project_type: str) -> Dict[str, Any]:
        """Retrieve standard requirements baseline for a project type."""
        return self.common_requirements.get(project_type.lower(), self.common_requirements["api"])
