# Git Workflow and Branching Strategy

This document outlines the Git workflow and branching strategy for the IFF-Guardian project.

## Branching Strategy

We follow a **Git Flow** inspired branching strategy with some modifications for modern CI/CD practices.

### Branch Types

#### Main Branches

##### `main` Branch
- **Purpose**: Production-ready code
- **Protection**: Highly protected, no direct pushes
- **Merge Requirements**: 
  - Pull request with at least 2 approvals
  - All CI checks must pass
  - No merge conflicts
  - Up-to-date with target branch

##### `develop` Branch  
- **Purpose**: Integration branch for features
- **Protection**: Protected, no direct pushes
- **Merge Requirements**:
  - Pull request with at least 1 approval
  - All CI checks must pass
  - No merge conflicts

#### Supporting Branches

##### Feature Branches (`feature/*`)
- **Naming**: `feature/IFF-123-add-user-authentication`
- **Purpose**: New features and enhancements
- **Source**: Branch from `develop`
- **Merge**: Back to `develop` via Pull Request
- **Lifetime**: Short-lived (1-2 weeks max)

```bash
# Create feature branch
git checkout develop
git pull origin develop
git checkout -b feature/IFF-123-add-user-authentication

# Work on feature
git add .
git commit -m "feat: add user authentication endpoints"
git push origin feature/IFF-123-add-user-authentication

# Create PR to develop
```

##### Hotfix Branches (`hotfix/*`)
- **Naming**: `hotfix/IFF-456-critical-security-fix`
- **Purpose**: Critical fixes for production issues
- **Source**: Branch from `main`
- **Merge**: To both `main` and `develop`
- **Lifetime**: Very short-lived (hours to 1 day)

```bash
# Create hotfix branch
git checkout main
git pull origin main
git checkout -b hotfix/IFF-456-critical-security-fix

# Apply fix
git add .
git commit -m "fix: resolve critical authentication vulnerability"
git push origin hotfix/IFF-456-critical-security-fix

# Create PRs to both main and develop
```

##### Release Branches (`release/*`)
- **Naming**: `release/v2.1.0`
- **Purpose**: Prepare new production releases
- **Source**: Branch from `develop`
- **Merge**: To both `main` and `develop`
- **Lifetime**: Short-lived (few days to 1 week)

```bash
# Create release branch
git checkout develop
git pull origin develop
git checkout -b release/v2.1.0

# Prepare release (version bump, changelog, etc.)
git add .
git commit -m "chore: prepare release v2.1.0"
git push origin release/v2.1.0

# Create PRs to main and develop
```

##### Bug Fix Branches (`bugfix/*`)
- **Naming**: `bugfix/IFF-789-fix-memory-leak`
- **Purpose**: Non-critical bug fixes
- **Source**: Branch from `develop`
- **Merge**: Back to `develop` via Pull Request
- **Lifetime**: Short-lived (few days to 1 week)

## Commit Message Convention

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types
- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect code meaning (white-space, formatting, etc.)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **chore**: Changes to build process or auxiliary tools
- **ci**: Changes to CI configuration files and scripts
- **build**: Changes that affect the build system or dependencies
- **revert**: Reverts a previous commit

### Examples
```bash
feat(auth): add OAuth2 authentication support
fix(api): resolve memory leak in request processing
docs(readme): update installation instructions
test(auth): add unit tests for login functionality
chore(deps): update FastAPI to v0.104.1
```

### Breaking Changes
```bash
feat(api)!: change user authentication endpoint structure

BREAKING CHANGE: The /auth/login endpoint now returns different response format
```

## Pull Request Workflow

### 1. Before Creating a PR

```bash
# Ensure your branch is up to date
git checkout develop
git pull origin develop
git checkout your-feature-branch
git rebase develop

# Run tests locally
pytest
black .
flake8 .
mypy src/

# Run security checks
bandit -r src/
safety check
```

### 2. Creating a Pull Request

1. **Push your branch**:
   ```bash
   git push origin your-branch-name
   ```

2. **Create PR via GitHub UI**
3. **Fill out PR template completely**
4. **Add appropriate labels**
5. **Request reviews from team members**
6. **Link to related issues**

### 3. PR Review Process

#### Reviewer Responsibilities
- Review code quality and architecture
- Check for security vulnerabilities  
- Verify test coverage
- Ensure documentation is updated
- Test the changes locally if needed

#### Author Responsibilities
- Respond to feedback promptly
- Make requested changes
- Keep PR up to date with target branch
- Ensure CI checks pass

### 4. Merging Strategy

#### Feature/Bug Fix PRs to `develop`
- **Strategy**: Squash and merge
- **Rationale**: Keeps develop history clean

#### Release PRs to `main`
- **Strategy**: Create a merge commit
- **Rationale**: Preserves release history

#### Hotfix PRs
- **Strategy**: Squash and merge
- **Rationale**: Quick integration of critical fixes

## Release Process

### 1. Prepare Release Branch
```bash
git checkout develop
git pull origin develop
git checkout -b release/v2.1.0
```

### 2. Version Bump and Changelog
```bash
# Update version in pyproject.toml and __init__.py
bump2version minor

# Update CHANGELOG.md
# Generate changelog from commits
git log --oneline --pretty=format:"- %s" v2.0.0..HEAD > temp_changelog.txt
```

### 3. Create Release PR
- Create PR from `release/v2.1.0` to `main`
- Include changelog and version updates
- Get required approvals
- Merge to `main`

### 4. Tag Release
```bash
git checkout main
git pull origin main
git tag -a v2.1.0 -m "Release version 2.1.0"
git push origin v2.1.0
```

### 5. Merge Back to Develop
- Create PR from `main` to `develop`
- Merge to keep develop up to date

## Git Hooks

We use pre-commit hooks to maintain code quality:

### Setup Pre-commit
```bash
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
```

### Hook Configuration
The `.pre-commit-config.yaml` includes:
- Code formatting (Black, isort)
- Linting (flake8, pylint, mypy)
- Security scanning (bandit, safety)
- Documentation checks
- Commit message validation

## Branch Protection Rules

### `main` Branch
- Require pull request reviews (2 required)
- Require status checks to pass
- Require conversation resolution
- Require signed commits
- Include administrators in restrictions
- Allow force pushes: ❌
- Allow deletions: ❌

### `develop` Branch  
- Require pull request reviews (1 required)
- Require status checks to pass
- Require up-to-date branches
- Allow force pushes: ❌
- Allow deletions: ❌

## Git Configuration

### Recommended Git Configuration
```bash
# Set up user information
git config user.name "Your Name"
git config user.email "your.email@company.com"

# Enable GPG signing (recommended)
git config user.signingkey YOUR_GPG_KEY
git config commit.gpgsign true

# Set up useful aliases
git config alias.co checkout
git config alias.br branch
git config alias.ci commit
git config alias.st status
git config alias.unstage 'reset HEAD --'
git config alias.last 'log -1 HEAD'
git config alias.visual '!gitk'

# Set default branch name
git config init.defaultBranch main

# Set merge strategy
git config merge.ours.driver true
```

## Troubleshooting Common Issues

### Merge Conflicts
```bash
# When rebasing
git rebase develop
# Resolve conflicts in editor
git add .
git rebase --continue

# When merging
git merge develop
# Resolve conflicts in editor  
git add .
git commit
```

### Undoing Changes
```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Revert a commit (creates new commit)
git revert <commit-hash>
```

### Cleaning Up
```bash
# Delete merged branches
git branch --merged | grep -v "\*\|main\|develop" | xargs -n 1 git branch -d

# Clean up remote tracking branches
git remote prune origin
```

## Best Practices

### General
1. **Keep commits small and focused**
2. **Write descriptive commit messages**
3. **Test before pushing**
4. **Rebase instead of merge for feature branches**
5. **Use meaningful branch names**

### Security
1. **Never commit secrets or credentials**
2. **Use signed commits for main branches**
3. **Review all changes before merging**
4. **Keep branches up to date**

### Collaboration
1. **Communicate changes in team channels**
2. **Request reviews from appropriate team members**
3. **Be responsive to PR feedback**
4. **Help others with their PRs**

This workflow ensures code quality, security, and team collaboration while maintaining a clean and traceable Git history.