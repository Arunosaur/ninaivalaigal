# Contributing to ninaivalaigal

**Thank you for your interest in contributing!** 🎉

This guide will help you understand how to contribute to ninaivalaigal effectively.

---

## 📚 Table of Contents

1. [Ways to Contribute](#ways-to-contribute)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Code Standards](#code-standards)
5. [Pull Request Process](#pull-request-process)
6. [Testing Requirements](#testing-requirements)
7. [Documentation Standards](#documentation-standards)
8. [Community Guidelines](#community-guidelines)

---

## 1. Ways to Contribute

### **Code Contributions**
- Fix bugs
- Add new features
- Improve performance
- Refactor code

### **Documentation**
- Improve existing docs
- Add examples
- Fix typos
- Translate docs

### **Testing**
- Write tests
- Report bugs
- Test new features
- Improve test coverage

### **Community**
- Answer questions
- Review PRs
- Share knowledge
- Write blog posts

**All contributions are valued!**

---

## 2. Getting Started

### **Find Something to Work On**

**Good first issues:**
- Look for `good-first-issue` label
- Check `help-wanted` issues
- Review documentation TODOs

**Feature requests:**
- Check existing issues first
- Discuss in issue before starting
- Get approval for large changes

**Bug fixes:**
- Reproduce the bug
- Document steps to reproduce
- Link to issue in PR

---

## 3. Development Setup

### **Prerequisites**
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Git

### **Clone and Setup**

```bash
# Fork the repository on GitHub first

# Clone your fork
git clone https://github.com/YOUR_USERNAME/ninaivalaigal.git
cd ninaivalaigal

# Add upstream remote
git remote add upstream https://github.com/original/ninaivalaigal.git

# Backend setup
conda create -n nina python=3.11
conda activate nina
pip install -r server/requirements.txt

# Frontend setup
cd frontend-nextjs-customer
npm install

# Database setup
createdb ninaivalaigal_dev
cd server
alembic upgrade head
```

### **Running Locally**

```bash
# Backend (terminal 1)
cd server
python run_server.py

# Frontend (terminal 2)
cd frontend-nextjs-customer
npm run dev
```

### **Verify Setup**

```bash
# Backend health check
curl http://localhost:13390/health

# Frontend check
open http://localhost:3000
```

---

## 4. Code Standards

### **Python Standards**

**Style:** Follow PEP 8
- Use Black for formatting
- Line length: 88 characters
- Use type hints
- Write docstrings

```python
def calculate_relevance(query: str, memories: List[Memory]) -> List[float]:
    """
    Calculate relevance scores for memories.

    Args:
        query: Search query string
        memories: List of memory objects

    Returns:
        List of relevance scores (0.0 to 1.0)
    """
    # Implementation here
    pass
```

**Linting:**
```bash
black server/
flake8 server/
mypy server/
```

### **TypeScript/JavaScript Standards**

**Style:** Prettier + ESLint
- Use TypeScript for type safety
- Use functional components (React)
- Use hooks (not class components)

```typescript
interface User {
  id: string;
  email: string;
  name: string;
}

export function UserProfile({ user }: { user: User }) {
  // Implementation here
}
```

**Linting:**
```bash
npm run lint
npm run type-check
```

### **File Organization**

**Backend:**
```
server/
  api/         # API endpoints
  database/    # Models and operations
  services/    # Business logic
  tests/       # Test files
```

**Frontend:**
```
frontend-nextjs-customer/
  app/         # Next.js pages
  components/  # React components
  services/    # API clients
  utils/       # Utilities
```

---

## 5. Pull Request Process

### **Branch Naming**

Use descriptive branch names:
```bash
# Features
feat/add-memory-tags
feat/improve-search

# Bugs
fix/login-redirect
fix/memory-deletion-bug

# Docs
docs/update-api-guide
docs/fix-readme-typo
```

### **Commit Messages**

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Refactoring
- `chore`: Maintenance

**Examples:**
```
feat(auth): add refresh token support

Implements refresh tokens with 30-day expiration.
Includes device tracking and revocation.

Closes #123
```

```
fix(memory): prevent duplicate memory creation

Added uniqueness check before inserting memory.

Fixes #456
```

### **Pull Request Template**

```markdown
## Description
[Brief description of changes]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing complete

## Checklist
- [ ] Code follows style guidelines
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Tests added/updated

## Related Issues
Closes #[issue number]
```

### **Review Process**

1. **Automated checks:** Must pass CI/CD
2. **Code review:** At least 1 approval required
3. **Testing:** All tests must pass
4. **Documentation:** Must be updated if needed
5. **Merge:** Squash and merge (usually)

---

## 6. Testing Requirements

### **Unit Tests**

**Required for:**
- New functions
- Bug fixes
- Refactorings

```bash
# Run unit tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=server --cov-report=html
```

### **Integration Tests**

**Required for:**
- New API endpoints
- Database changes
- Authentication changes

```bash
# Run integration tests
pytest tests/integration/ -v
```

### **Test Coverage**

**Minimum coverage:** 80% for new code
- Critical modules: 100% (auth, RBAC)
- Business logic: 90%
- Utilities: 80%

---

## 7. Documentation Standards

### **Code Comments**

```python
# Good: Explain WHY, not WHAT
# Calculate using cosine similarity because it's scale-invariant
similarity = cosine_similarity(query_vec, memory_vec)

# Bad: Obvious comment
# Calculate similarity
similarity = calculate_similarity(query_vec, memory_vec)
```

### **Docstrings**

**Required for:**
- All public functions
- All classes
- Complex algorithms

```python
def search_memories(
    query: str,
    k: int = 10,
    context_id: Optional[str] = None
) -> List[Memory]:
    """
    Search memories using semantic similarity.

    Args:
        query: Search query string
        k: Number of results to return (default: 10)
        context_id: Optional context filter

    Returns:
        List of Memory objects sorted by relevance

    Raises:
        ValueError: If k < 1 or k > 100
        PermissionError: If user lacks access to context

    Example:
        >>> memories = search_memories("API authentication", k=5)
        >>> print(f"Found {len(memories)} memories")
    """
```

### **README Updates**

**Update README.md when:**
- Adding new features
- Changing setup process
- Updating dependencies
- Changing APIs

### **SPEC Updates**

**Update or create SPECs when:**
- Adding new features
- Changing architecture
- Modifying behavior

See `specs/000-template/` for SPEC template.

---

## 8. Community Guidelines

### **Code of Conduct**

**We are committed to:**
- Welcoming environment
- Respectful communication
- Constructive feedback
- Inclusive community

**Unacceptable:**
- Harassment
- Discrimination
- Trolling
- Spam

**Report violations:** support@ninaivalaigal.com

### **Communication Channels**

- **GitHub Issues:** Bug reports, feature requests
- **GitHub Discussions:** Questions, ideas
- **Discord:** Real-time chat (link in README)
- **Email:** support@ninaivalaigal.com

### **Getting Help**

**Stuck? Ask for help!**
- Comment on your PR
- Ask in Discord
- Open a discussion
- Tag maintainers

**We're here to help!**

### **Recognition**

**Contributors are recognized:**
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Featured in blog posts
- Community badges (coming soon)

---

## Questions?

**Need help?**
- Read [Developer Onboarding](DEVELOPER_ONBOARDING.md)
- Check [API Examples](API_EXAMPLES.md)
- Visit [Testing Guide](TESTING_GUIDE.md)
- Ask in GitHub Discussions

**Thank you for contributing to ninaivalaigal! 🚀**
