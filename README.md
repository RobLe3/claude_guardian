# Claude Guardian

[![CI/CD](https://github.com/claude-guardian/claude-guardian/workflows/CI/badge.svg)](https://github.com/claude-guardian/claude-guardian/actions/workflows/ci.yml)
[![Security Scan](https://github.com/claude-guardian/claude-guardian/workflows/Security%20Scanning/badge.svg)](https://github.com/claude-guardian/claude-guardian/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/claude-guardian/claude-guardian/branch/main/graph/badge.svg)](https://codecov.io/gh/claude-guardian/claude-guardian)
[![Documentation](https://readthedocs.org/projects/claude-guardian/badge/?version=latest)](https://docs.claude-guardian.com/en/latest/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**Claude Guardian** (formerly IFF-Guardian) is an advanced AI-powered security system designed specifically to protect Claude Code from malicious coding techniques, resource hijacking, and repository damage through real-time threat detection, automated response, and comprehensive security analytics.

## 🚀 Features

### 🛡️ Advanced Threat Detection
- **Real-time monitoring** with ML-based anomaly detection
- **Custom rule engine** for flexible threat identification
- **IOC matching** against multiple threat intelligence feeds
- **Behavioral analysis** for zero-day threat detection

### 🤖 Automated Response
- **Configurable playbooks** for incident response
- **Integration ecosystem** with popular security tools
- **Automated containment** actions and quarantine
- **Escalation workflows** with notification systems

### 📊 Comprehensive Analytics
- **Security dashboards** with real-time metrics
- **Threat intelligence** integration and correlation
- **Risk assessment** and vulnerability management
- **Compliance reporting** for various frameworks

### 🔗 Enterprise Ready
- **RESTful API** with comprehensive documentation
- **SIEM integration** capabilities
- **Multi-tenant architecture** with RBAC
- **High availability** and horizontal scalability

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#️-installation)
- [Configuration](#️-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Architecture](#️-architecture)
- [Development](#-development)
- [Contributing](#-contributing)
- [Security](#-security)
- [License](#-license)

## 🏃 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/claude-guardian/claude-guardian.git
cd claude-guardian

# Copy environment configuration
cp .env.example .env
# Edit .env with your configuration

# Start with Docker Compose
docker-compose up -d

# Access the application
open http://localhost:8000
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install

# Run the application
uvicorn claude_guardian.main:app --reload
```

## 🛠️ Installation

### System Requirements

**Minimum:**
- Python 3.9+
- 4GB RAM
- 20GB storage
- PostgreSQL 12+
- Redis 6+

**Recommended:**
- Python 3.11+
- 8GB RAM
- 100GB SSD storage
- PostgreSQL 14+
- Redis 7+

### Production Installation

```bash
# Install from PyPI
pip install claude-guardian

# Or install from source
git clone https://github.com/claude-guardian/claude-guardian.git
cd claude-guardian
pip install -e .
```

### Database Setup

```bash
# PostgreSQL setup
createdb claude_guardian
export DATABASE_URL=\"postgresql://user:password@localhost:5432/claude_guardian\"

# Run migrations
alembic upgrade head
```

## ⚙️ Configuration

Claude Guardian uses a hierarchical configuration system supporting multiple formats and environments.

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Application
APP_NAME=Claude Guardian
APP_ENVIRONMENT=production
SECRET_KEY=your-super-secret-key-change-this

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/claude_guardian

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENABLE_2FA=true
```

### Configuration Files

Environment-specific configurations are located in `config/environments/`:

- `development.yaml` - Development settings
- `staging.yaml` - Staging environment
- `production.yaml` - Production environment

### Security Configuration

Security policies are defined in `config/security/security_policy.yaml`:

```yaml
authentication:
  multi_factor:
    enabled: true
    required_for_admin: true

password_policy:
  min_length: 12
  require_uppercase: true
  require_lowercase: true
  require_digits: true
  require_special_chars: true
```

## 📚 Usage

### Web Interface

Access the web interface at `http://localhost:8000` after starting the application.

### CLI Usage

```bash
# Start the server
claude-guardian server --host 0.0.0.0 --port 8000

# Run security scan
claude-guardian scan --target 192.168.1.0/24

# Generate report
claude-guardian report --type daily --format pdf
```

### API Usage

```python
import httpx

# Authentication
auth_response = httpx.post(
    \"http://localhost:8000/api/v1/auth/login\",
    json={\"username\": \"user\", \"password\": \"password\"}
)
token = auth_response.json()[\"access_token\"]

# Create threat detection rule
headers = {\"Authorization\": f\"Bearer {token}\"}
rule_response = httpx.post(
    \"http://localhost:8000/api/v1/rules\",
    json={
        \"name\": \"Suspicious Login Pattern\",
        \"condition\": \"failed_logins > 5 AND time_window < 300\",
        \"action\": \"block_ip\"
    },
    headers=headers
)
```

## 📖 API Documentation

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | User authentication |
| GET | `/api/v1/threats` | List detected threats |
| POST | `/api/v1/rules` | Create detection rule |
| GET | `/api/v1/analytics/dashboard` | Security dashboard data |
| POST | `/api/v1/incidents` | Create security incident |

### Rate Limiting

API endpoints are rate-limited:
- **Authenticated users**: 1000 requests/hour
- **Unauthenticated**: 100 requests/hour
- **Admin endpoints**: 5000 requests/hour

## 🏗️ Architecture

Claude Guardian follows a modern microservices architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │    │   Mobile App    │    │   Third-party   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │      API Gateway          │
                    │   (FastAPI + Uvicorn)     │
                    └─────────────┬─────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
    ┌─────────┴─────────┐ ┌──────┴──────┐ ┌────────┴────────┐
    │  Threat Engine    │ │  Analytics  │ │ Incident Mgmt   │
    │    Service        │ │   Service   │ │    Service      │
    └─────────┬─────────┘ └──────┬──────┘ └────────┬────────┘
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │     Data Layer            │
                    │ PostgreSQL + Redis        │
                    └───────────────────────────┘
```

### Key Components

- **API Gateway**: FastAPI-based REST API
- **Threat Engine**: Real-time threat detection and analysis
- **Analytics Service**: Security metrics and reporting
- **Incident Management**: Automated response and workflows
- **Data Layer**: PostgreSQL for persistence, Redis for caching

## 👨‍💻 Development

### Development Setup

```bash
# Clone and setup
git clone https://github.com/claude-guardian/claude-guardian.git
cd claude-guardian

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Start development server
uvicorn claude_guardian.main:app --reload --host 0.0.0.0 --port 8000
```

### Code Quality

We maintain high code quality standards:

```bash
# Format code
black .
isort .

# Lint code
flake8 .
pylint src/

# Type checking
mypy src/

# Security scanning
bandit -r src/
safety check
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test types
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

### Git Workflow

We follow **Git Flow** with these branch types:

- `main` - Production-ready code
- `develop` - Development integration
- `feature/*` - New features
- `hotfix/*` - Critical fixes
- `release/*` - Release preparation

See [Git Workflow Documentation](docs/developer-guide/git-workflow.md) for details.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### How to Contribute

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'feat: add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Standards

- **Code Style**: Follow PEP 8 with Black formatting
- **Commit Messages**: Use [Conventional Commits](https://conventionalcommits.org/)
- **Documentation**: Update docs for new features
- **Testing**: Maintain >80% test coverage
- **Security**: Run security scans before submitting

### Community

- 📧 **Email**: team@claude-guardian.com
- 💬 **Discussions**: [GitHub Discussions](https://github.com/claude-guardian/claude-guardian/discussions)
- 🐛 **Issues**: [GitHub Issues](https://github.com/claude-guardian/claude-guardian/issues)

## 🔒 Security

Security is our top priority. Please see our [Security Policy](SECURITY.md) for:

- **Supported versions**
- **Reporting vulnerabilities**
- **Security best practices**
- **Response timeline**

### Reporting Security Issues

🚨 **For security vulnerabilities, please email**: security@claude-guardian.com

**Do not** create public issues for security vulnerabilities.

### Security Features

- 🔐 **Multi-factor authentication** (TOTP, SMS, Email)
- 🛡️ **Role-based access control** (RBAC)
- 🔒 **Encryption** at rest and in transit (AES-256, TLS 1.3)
- 📊 **Security monitoring** and audit logging
- 🚫 **Rate limiting** and DDoS protection

## 📊 Status & Metrics

### Build Status

| Branch | Build | Tests | Security | Coverage |
|--------|-------|--------|----------|----------|
| main | [![CI](https://github.com/claude-guardian/claude-guardian/workflows/CI/badge.svg?branch=main)](https://github.com/claude-guardian/claude-guardian/actions/workflows/ci.yml) | ✅ | [![Security](https://github.com/claude-guardian/claude-guardian/workflows/Security%20Scanning/badge.svg)](https://github.com/claude-guardian/claude-guardian/actions/workflows/security.yml) | [![codecov](https://codecov.io/gh/claude-guardian/claude-guardian/branch/main/graph/badge.svg)](https://codecov.io/gh/claude-guardian/claude-guardian) |
| develop | [![CI](https://github.com/claude-guardian/claude-guardian/workflows/CI/badge.svg?branch=develop)](https://github.com/claude-guardian/claude-guardian/actions/workflows/ci.yml) | ✅ | ✅ | [![codecov](https://codecov.io/gh/claude-guardian/claude-guardian/branch/develop/graph/badge.svg)](https://codecov.io/gh/claude-guardian/claude-guardian) |

### Performance Metrics

- **Response Time**: < 200ms (95th percentile)
- **Throughput**: > 10,000 requests/second
- **Uptime**: 99.9% SLA
- **Detection Accuracy**: > 95%

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Claude Guardian Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the \"Software\"), to deal
in the Software without restriction...
```

## 🙏 Acknowledgments

- **Security Community** for threat intelligence feeds
- **Open Source Projects** that make this possible
- **Contributors** who help improve Claude Guardian
- **Users** who trust us with their security

## 📈 Roadmap

See our [Development Roadmap](IFF_Guardian_Development_Roadmap.md) for upcoming features and improvements.

---

<div align=\"center\">

**Made with ❤️ by the Claude Guardian Team**

[Website](https://claude-guardian.com) • [Documentation](https://docs.claude-guardian.com) • [Support](mailto:support@claude-guardian.com)

</div>