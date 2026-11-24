---
name: repository-intelligence
description: Repository analysis, architecture detection, and technology identification
---

# Repository Intelligence Skill

Provides comprehensive repository analysis capabilities for Phantom Engine.

## Capabilities

1. **Structure Analysis**
   - Directory tree mapping
   - Entry point identification
   - Module/graph visualization

2. **Technology Detection**
   - Language detection (Python, TypeScript, Go, Rust, etc.)
   - Framework identification (React, Django, FastAPI, Next.js, etc.)
   - Build tool detection (webpack, vite, cargo, gradle, etc.)
   - Package manager detection (npm, pnpm, yarn, pip, uv, poetry, cargo, go mod)

3. **Dependency Analysis**
   - Dependency graph construction
   - Version conflict detection
   - Outdated dependency identification
   - License compliance checking

4. **Architecture Pattern Recognition**
   - Layered architecture
   - Microservices
   - Modular monolith
   - Clean architecture
   - Hexagonal architecture
   - Event-driven patterns

5. **Code Quality Metrics**
   - Lines of code
   - Cyclomatic complexity
   - Cognitive complexity
   - Code duplication
   - Test coverage

## Usage

```python
from skills.repository_intelligence import RepositoryAnalyzer

analyzer = RepositoryAnalyzer(repo_path)
report = analyzer.analyze()
```

## Output

- `.phantom/scan-report.md` - Human-readable report
- `.phantom/architecture.md` - Architecture documentation
- `.phantom/tech-stack.json` - Structured technology data