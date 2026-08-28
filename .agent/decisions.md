# Architectural Decision Record

---

## ADR-001: Python-only for MVP

**Date**: 2026-08-28  
**Status**: Decided

**Context**: The product must support analyzing codebases. Supporting multiple languages multiplies implementation complexity.

**Decision**: MVP supports Python only.

**Consequences**: Multi-language support deferred. Demo migration must be Python. Blast radius does not work across language boundaries.

---

## ADR-002: Drop Tree-sitter from MVP

**Date**: 2026-08-28  
**Status**: Decided

**Context**: Tree-sitter was proposed for code parsing.

**Decision**: Use Python stdlib `ast` for all parsing in MVP. Tree-sitter is valuable in multi-language contexts but adds FFI complexity for no benefit in a Python-only system.

**Consequences**: Parsing is limited to Python files. `ast` gives full access to Python AST. If multi-language support is added later, Tree-sitter can replace this.

---

## ADR-003: NetworkX + JSON for code graph (no graph database)

**Date**: 2026-08-28  
**Status**: Decided

**Context**: A graph database (Neo4j, etc.) was considered.

**Decision**: NetworkX for in-memory graph operations. Persist graph as JSON using `networkx.node_link_data()` to disk per run. SQLite for run metadata and report blobs.

**Consequences**: No graph query language (Cypher etc.). Graph operations use NetworkX API. Sufficient for MVP demo scale. Does not scale to very large codebases.

---

## ADR-004: SQLite only (no ORM, no hosted database)

**Date**: 2026-08-28  
**Status**: Decided

**Context**: SQLite vs Supabase/Postgres was evaluated.

**Decision**: SQLite using Python stdlib `sqlite3`. No ORM (SQLAlchemy etc.). No hosted database. Single-user local demo.

**Consequences**: No multi-user, no hosted persistence. Fine for hackathon.

---

## ADR-005: Docker sandbox (pre-built image, read-only bind mount)

**Date**: 2026-08-28  
**Status**: Decided

**Context**: Two Docker approaches were evaluated: (A) pre-built image + bind mount, (B) dynamic image build per run.

**Decision**: Option A. Pre-built `migration-verifier-runner:latest` image. Code is bind-mounted read-only per run.

**Consequences**: Faster execution. Less isolation than Option B (code is not baked into an ephemeral image). Sufficient for hackathon threat model.

---

## ADR-006: Google Gemini Flash as LLM

**Date**: 2026-08-28  
**Status**: Decided

**Context**: OpenAI, Gemini, Ollama were evaluated.

**Decision**: Google Gemini Flash. Free tier available. Good quality. Hackathon-friendly.

**Consequences**: Requires `GEMINI_API_KEY` env var. Falls back gracefully (AI section of report is empty) if key is absent.

---

## ADR-007: React Flow for graph visualization

**Date**: 2026-08-28  
**Status**: Decided

**Context**: D3.js, React Flow, static SVG were evaluated.

**Decision**: React Flow. Pre-built, interactive, visually impressive for blast radius visualization.

**Consequences**: Adds `reactflow` npm dependency.

---

## ADR-008: Zip upload for codebase submission

**Date**: 2026-08-28  
**Status**: Decided

**Context**: Text path inputs vs zip upload were evaluated.

**Decision**: Zip file upload. Better UX for demo. Works even if backend is deployed remotely.

**Consequences**: Backend must unzip to a temp directory per run. Temp directories cleaned after run completes.

---

## ADR-009: Purpose-built demo migration

**Date**: 2026-08-28  
**Status**: Decided

**Context**: Real-world migration (requests→httpx) vs purpose-built project were evaluated.

**Decision**: Build a small purpose-built Python project with a controlled regression baked into the migrated version. This ensures the demo always produces a convincing regression_detected result.

**Consequences**: We must build `demo/original/` and `demo/migrated/` as part of M10.

---

## ADR-010: No TypeScript in MVP

**Date**: 2026-08-28  
**Status**: Decided

**Context**: TypeScript was in the original stack proposal.

**Decision**: Use JavaScript for the MVP frontend. TypeScript adds build complexity and type errors that slow down LatentCode.

**Consequences**: No type safety in frontend. Can migrate to TypeScript post-hackathon.

---

## ADR-011: No AI-generated tests

**Date**: 2026-08-28  
**Status**: Decided

**Context**: AI test generation was considered as a feature.

**Decision**: Cut from MVP. LLM-generated tests are unreliable and hard to verify. The demo is more credible with "we ran your existing tests."

**Consequences**: If a codebase has no tests, the classification is "unverified." This is an honest outcome.
