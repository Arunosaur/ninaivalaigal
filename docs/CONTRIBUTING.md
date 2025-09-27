# Contributing to Ninaivalaigal

**Version**: 2.0
**Last Updated**: September 27, 2024
**Welcome Contributors!** 🎉

Thank you for your interest in contributing to Ninaivalaigal! This guide will help you get started with contributing to our enterprise-grade AI memory management platform.

## 🌟 **Welcome to the Community**

Ninaivalaigal is an open-source AI memory management platform with enterprise-grade capabilities. We welcome contributions from developers, designers, documentation writers, and AI enthusiasts who want to help build the future of intelligent memory systems.

### **What We're Building**
- **Enterprise AI Memory Platform**: Production-ready memory management with advanced sharing and collaboration
- **Foundation SPECs Complete**: 6 of 7 foundation SPECs implemented (86% complete)
- **Comprehensive Testing**: E2E test matrix with chaos testing and 85%+ coverage
- **Multi-Architecture Support**: ARM64 + x86_64 with dual CI/CD validation
- **Graph Intelligence**: Apache AGE integration for advanced memory relationships

## 🚀 **Getting Started**

### **1. Development Environment Setup**

#### **Prerequisites**
- **Python 3.11+**: Primary development language
- **PostgreSQL 15+**: Database with pgvector extension
- **Redis 7+**: Caching and session management
- **Git**: Version control
- **Docker** (optional): For containerized development

#### **Quick Setup**
```bash
# Clone the repository
git clone https://github.com/your-org/ninaivalaigal.git
cd ninaivalaigal

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install

# Copy environment configuration
cp .env.example .env
# Edit .env with your local configuration

# Start development stack
make dev-stack-up

# Verify setup
make health-check
```

#### **Apple Container CLI Setup (Recommended for macOS)**
```bash
# Install Apple Container CLI (if not already installed)
# Follow Apple's installation guide

# Start native ARM64 stack
make start-native-stack

# Verify health
curl http://localhost:13370/health
```

### **2. Repository Structure**

```
ninaivalaigal/
├── server/                     # FastAPI backend application
│   ├── memory/                 # Memory management modules
│   │   ├── provider_registry.py    # SPEC-020: Provider architecture
│   │   ├── sharing_contracts.py    # SPEC-049: Sharing collaboration
│   │   ├── consent_manager.py      # SPEC-049: Consent management
│   │   ├── temporal_access.py      # SPEC-049: Temporal access
│   │   └── audit_logger.py         # SPEC-049: Audit logging
│   ├── routers/                # FastAPI route handlers
│   ├── database/               # Database schemas and migrations
│   └── utils/                  # Utility functions
├── tests/                      # Comprehensive test suite
│   ├── unit/                   # Unit tests (90% coverage target)
│   ├── integration/            # Integration tests (80% coverage)
│   ├── functional/             # Functional tests (70% coverage)
│   ├── e2e/                    # End-to-end test matrix
│   ├── chaos/                  # Chaos testing suite
│   └── coverage/               # Coverage validation tools
├── docs/                       # Documentation
│   ├── ARCHITECTURE_OVERVIEW.md    # System architecture
│   ├── API_DOCUMENTATION.md        # API reference
│   ├── MEMORY_LIFECYCLE.md         # Memory management guide
│   ├── TESTING_GUIDE.md            # Testing documentation
│   └── CONTRIBUTING.md             # This file
├── specs/                      # SPEC documentation
│   ├── 007-unified-context-scope/  # SPEC-007: Context system
│   ├── 020-memory-provider/        # SPEC-020: Provider architecture
│   ├── 049-memory-sharing/         # SPEC-049: Sharing collaboration
│   └── 052-comprehensive-testing/  # SPEC-052: Test coverage
├── .github/                    # GitHub Actions workflows
│   └── workflows/              # CI/CD pipeline definitions
└── containers/                 # Container configurations
```

### **3. Development Workflow**

#### **Branch Strategy**
- **`main`**: Production-ready code, protected branch
- **`develop`**: Integration branch for features
- **`feature/SPEC-XXX-description`**: Feature branches for SPEC implementation
- **`bugfix/issue-description`**: Bug fix branches
- **`hotfix/critical-issue`**: Critical production fixes

#### **Commit Convention**
We use [Conventional Commits](https://www.conventionalcommits.org/) for clear commit messages:

```bash
# Feature commits
feat(memory): implement SPEC-049 temporal access controls
feat(api): add memory sharing endpoints

# Bug fixes
fix(provider): resolve failover race condition
fix(auth): handle expired JWT tokens properly

# Documentation
docs(api): update sharing contract documentation
docs(contributing): add development setup guide

# Tests
test(chaos): add Redis failure simulation tests
test(e2e): implement foundation SPEC validation

# Refactoring
refactor(memory): optimize relevance scoring algorithm
refactor(database): consolidate PostgreSQL + AGE schema

# SPEC implementation
feat(SPEC-049): complete memory sharing collaboration
test(SPEC-052): add comprehensive coverage validation
```

## 🎯 **Contribution Areas**

### **1. Foundation SPECs (High Priority)**

#### **SPEC-058: Documentation Expansion (FINAL FOUNDATION SPEC)**
- **Status**: 🔄 IN PROGRESS (Final step to 100% foundation completion)
- **Areas**: Developer docs, API documentation, user guides, contribution guidelines
- **Impact**: Unlocks external onboarding and public roadmap visibility

#### **Foundation SPEC Testing & Validation**
- **SPEC-007**: Unified Context Scope System validation
- **SPEC-020**: Memory Provider Architecture testing
- **SPEC-049**: Memory Sharing Collaboration workflows
- **SPEC-052**: Test coverage expansion and chaos testing

### **2. Core Development Areas**

#### **Memory Management**
- Memory provider implementations (Redis, Vector DBs)
- Advanced relevance scoring algorithms
- Memory lifecycle automation
- Performance optimization

#### **Sharing & Collaboration**
- Cross-organization sharing features
- Advanced permission systems
- Collaboration workflows
- Real-time sharing notifications

#### **Graph Intelligence**
- Apache AGE integration enhancements
- Graph-based memory relationships
- Intelligent memory discovery
- Graph reasoning algorithms

#### **Testing & Quality Assurance**
- Expand test coverage (current: 85%+ target)
- Chaos testing scenarios
- Performance testing
- Security testing

### **3. Infrastructure & DevOps**

#### **CI/CD Pipeline**
- GitHub Actions workflow optimization
- Multi-architecture build improvements
- Deployment automation
- Quality gate enhancements

#### **Containerization**
- Docker optimization
- Apple Container CLI enhancements
- Production deployment configurations
- Health monitoring improvements

#### **Monitoring & Observability**
- Metrics collection and visualization
- Log aggregation and analysis
- Performance monitoring
- Alert system integration

### **4. Documentation & Community**

#### **Technical Documentation**
- API reference improvements
- Architecture documentation
- Integration guides
- Best practices documentation

#### **User Documentation**
- User guides and tutorials
- Getting started guides
- Use case examples
- Troubleshooting guides

#### **Community Building**
- Contributing guidelines
- Code of conduct
- Issue templates
- Discussion facilitation

## 📋 **Development Guidelines**

### **1. Code Style & Standards**

#### **Python Code Style**
We follow [PEP 8](https://pep8.org/) with some modifications:

```python
# Use Black for formatting
black server/ tests/

# Use flake8 for linting
flake8 server/ tests/

# Use mypy for type checking
mypy server/

# Use isort for import sorting
isort server/ tests/
```

#### **Code Quality Standards**
- **Type Hints**: All functions must have type hints
- **Docstrings**: All public functions must have docstrings
- **Error Handling**: Comprehensive error handling with proper logging
- **Testing**: All new code must have corresponding tests
- **Security**: Follow security best practices, especially for auth and data handling

#### **Example Code Style**
```python
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class MemoryProvider:
    """
    Base class for memory providers.

    Provides interface for storing and retrieving memories
    with comprehensive error handling and logging.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize memory provider.

        Args:
            config: Provider configuration dictionary

        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config
        self._validate_config()

    async def remember(
        self,
        content: str,
        context: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store a memory.

        Args:
            content: Memory content to store
            context: Memory context information
            metadata: Optional metadata dictionary

        Returns:
            Dictionary containing memory information

        Raises:
            MemoryStorageError: If storage operation fails
        """
        try:
            # Implementation here
            logger.info(f"Storing memory in context: {context}")
            return {"memory_id": "generated_id", "status": "stored"}

        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise MemoryStorageError(f"Storage failed: {e}") from e

    def _validate_config(self) -> None:
        """Validate provider configuration."""
        required_keys = ["connection_string", "timeout"]
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required config key: {key}")
```

### **2. Testing Requirements**

#### **Test Coverage Requirements**
- **Unit Tests**: 90% coverage for all new code
- **Integration Tests**: 80% coverage for component interactions
- **Functional Tests**: 70% coverage for end-to-end workflows
- **All new features must include comprehensive tests**

#### **Test Structure**
```python
import pytest
from unittest.mock import Mock, AsyncMock
from your_module import YourClass

class TestYourClass:
    """Test suite for YourClass"""

    @pytest.fixture
    async def mock_dependency(self):
        """Mock external dependency"""
        return AsyncMock()

    @pytest.fixture
    async def your_instance(self, mock_dependency):
        """Create instance for testing"""
        return YourClass(dependency=mock_dependency)

    async def test_successful_operation(self, your_instance):
        """Test successful operation scenario"""
        # Arrange
        expected_result = {"status": "success"}

        # Act
        result = await your_instance.perform_operation()

        # Assert
        assert result == expected_result

    async def test_error_handling(self, your_instance):
        """Test error handling scenario"""
        # Arrange
        your_instance.dependency.side_effect = Exception("Test error")

        # Act & Assert
        with pytest.raises(YourCustomError):
            await your_instance.perform_operation()
```

#### **Running Tests**
```bash
# Run all tests with coverage
make test-all

# Run specific test types
make test-unit
make test-integration
make test-functional

# Run tests for specific module
pytest tests/unit/test_memory_providers.py -v

# Run tests with coverage report
pytest tests/ --cov=server --cov-report=html
```

### **3. Documentation Standards**

#### **Code Documentation**
- **Docstrings**: Use Google-style docstrings
- **Type Hints**: All function parameters and return types
- **Comments**: Explain complex logic and business rules
- **README**: Update relevant README files for new features

#### **API Documentation**
- **OpenAPI/Swagger**: All endpoints must be documented
- **Examples**: Include request/response examples
- **Error Codes**: Document all possible error responses
- **Authentication**: Document authentication requirements

#### **SPEC Documentation**
- **Implementation Notes**: Document how SPECs are implemented
- **Acceptance Criteria**: Verify all criteria are met
- **Testing**: Document test coverage for SPEC features
- **Completion Summary**: Update completion status

## 🔄 **Pull Request Process**

### **1. Before Submitting**

#### **Pre-Submission Checklist**
- [ ] Code follows style guidelines (Black, flake8, mypy pass)
- [ ] All tests pass locally (`make test-all`)
- [ ] Test coverage meets requirements (90%/80%/70%)
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated (if applicable)
- [ ] Commit messages follow conventional commit format
- [ ] Branch is up to date with main/develop

#### **Quality Gates**
```bash
# Run quality checks
make lint          # Code style and linting
make type-check    # Type checking with mypy
make test-all      # All tests with coverage
make security-scan # Security vulnerability scan
```

### **2. Pull Request Template**

```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] SPEC implementation
- [ ] Test coverage improvement

## SPEC Implementation (if applicable)
- **SPEC Number**: SPEC-XXX
- **SPEC Title**: Title of SPEC
- **Implementation Status**: Complete/Partial
- **Acceptance Criteria Met**: Yes/No

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Functional tests added/updated
- [ ] All tests pass
- [ ] Coverage requirements met

## Documentation
- [ ] Code documentation updated
- [ ] API documentation updated
- [ ] User documentation updated
- [ ] SPEC documentation updated

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] No breaking changes (or clearly documented)
- [ ] All quality gates pass
```

### **3. Review Process**

#### **Review Criteria**
- **Code Quality**: Follows standards and best practices
- **Functionality**: Meets requirements and works as expected
- **Testing**: Adequate test coverage and quality
- **Documentation**: Clear and comprehensive documentation
- **Security**: No security vulnerabilities introduced
- **Performance**: No significant performance regressions

#### **Review Timeline**
- **Small PRs** (< 100 lines): 1-2 business days
- **Medium PRs** (100-500 lines): 2-3 business days
- **Large PRs** (> 500 lines): 3-5 business days
- **SPEC Implementation PRs**: 3-7 business days (depending on complexity)

## 🐛 **Bug Reports & Feature Requests**

### **1. Bug Report Template**

```markdown
**Bug Description**
A clear and concise description of the bug.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
A clear description of what you expected to happen.

**Actual Behavior**
A clear description of what actually happened.

**Environment**
- OS: [e.g. macOS 14.0, Ubuntu 22.04]
- Python version: [e.g. 3.11.5]
- Ninaivalaigal version: [e.g. 2.0.0]
- Database: [e.g. PostgreSQL 15.4]
- Redis: [e.g. Redis 7.2]

**Logs**
```
Paste relevant log output here
```

**Additional Context**
Add any other context about the problem here.
```

### **2. Feature Request Template**

```markdown
**Feature Description**
A clear and concise description of the feature you'd like to see.

**Problem Statement**
What problem does this feature solve? What use case does it address?

**Proposed Solution**
Describe the solution you'd like to see implemented.

**Alternative Solutions**
Describe any alternative solutions or features you've considered.

**SPEC Alignment**
Does this align with any existing SPECs? Should a new SPEC be created?

**Implementation Considerations**
- Impact on existing functionality
- Performance considerations
- Security implications
- Testing requirements

**Additional Context**
Add any other context, mockups, or examples about the feature request.
```

## 🏆 **Recognition & Rewards**

### **Contributor Recognition**
- **Contributors List**: All contributors are recognized in our README
- **SPEC Implementation Credits**: Major SPEC contributors get special recognition
- **Community Highlights**: Outstanding contributions featured in community updates
- **Mentorship Opportunities**: Experienced contributors can mentor newcomers

### **Contribution Levels**
- **First-time Contributor**: Welcome package and guidance
- **Regular Contributor**: Access to contributor channels and early feature previews
- **Core Contributor**: Voting rights on major decisions and SPEC priorities
- **Maintainer**: Full repository access and release management responsibilities

## 📞 **Getting Help**

### **Communication Channels**
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and community discussions
- **Discord/Slack**: Real-time chat (link in README)
- **Email**: maintainers@ninaivalaigal.com for sensitive issues

### **Documentation Resources**
- **Architecture Overview**: `docs/ARCHITECTURE_OVERVIEW.md`
- **API Documentation**: `docs/API_DOCUMENTATION.md`
- **Testing Guide**: `docs/TESTING_GUIDE.md`
- **Memory Lifecycle**: `docs/MEMORY_LIFECYCLE.md`

### **Development Resources**
- **SPEC Documentation**: `specs/` directory
- **Example Implementations**: `examples/` directory
- **Test Examples**: `tests/` directory
- **Development Scripts**: `scripts/` directory

## 🎉 **Welcome to the Community!**

We're excited to have you contribute to Ninaivalaigal! Whether you're fixing a small bug, implementing a major feature, or improving documentation, every contribution helps make Ninaivalaigal better for everyone.

**Key Points to Remember:**
- 🎯 **Foundation SPECs**: We're 86% complete - help us reach 100%!
- 🧪 **Quality First**: Comprehensive testing is our priority
- 📚 **Documentation Matters**: Good docs make great software accessible
- 🤝 **Community Driven**: We value collaboration and mutual respect
- 🚀 **Enterprise Ready**: We're building production-grade software

**Ready to contribute?** Check out our [Good First Issues](https://github.com/your-org/ninaivalaigal/labels/good%20first%20issue) or dive into [SPEC-058 Documentation Expansion](https://github.com/your-org/ninaivalaigal/issues/spec-058) to help us achieve 100% foundation completion!

---

**Thank you for helping build the future of AI memory management! 🧠✨**
