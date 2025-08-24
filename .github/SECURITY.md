# Security Policy

## Supported Versions

We actively support and provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.1.x   | :white_check_mark: |
| 2.0.x   | :white_check_mark: |
| 1.9.x   | :x:                |
| < 1.9   | :x:                |

## Reporting a Vulnerability

The IFF-Guardian team takes security bugs seriously. We appreciate your efforts to responsibly disclose your findings, and will make every effort to acknowledge your contributions.

### How to Report a Security Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **security@iff-guardian.com**

Include the following information in your report:
- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 48 hours.
- **Assessment**: We will assess the vulnerability and determine its severity within 5 business days.
- **Timeline**: We will provide an expected timeline for addressing the vulnerability.
- **Updates**: We will keep you informed of our progress throughout the remediation process.
- **Credit**: We will publicly acknowledge your responsible disclosure, unless you prefer to remain anonymous.

### Security Response Timeline

- **Critical vulnerabilities**: Patches within 24-48 hours
- **High severity**: Patches within 1 week
- **Medium severity**: Patches within 2 weeks
- **Low severity**: Patches within 1 month

## Security Best Practices for Contributors

### Code Review Requirements
- All code changes require review from at least one maintainer
- Security-sensitive changes require review from a security team member
- Automated security scans must pass before merging

### Dependencies
- Keep dependencies up to date
- Use `safety` to check for known vulnerabilities
- Pin dependency versions in production

### Secrets Management
- Never commit secrets, API keys, or passwords to the repository
- Use environment variables or secure secret management systems
- Rotate credentials regularly

### Authentication & Authorization
- Implement proper authentication for all endpoints
- Use principle of least privilege for access controls
- Validate all input data

### Data Protection
- Encrypt sensitive data at rest and in transit
- Implement proper logging without exposing sensitive information
- Follow GDPR and other applicable privacy regulations

## Security Tools Used

- **Static Analysis**: CodeQL, Bandit
- **Dependency Scanning**: Safety, pip-audit
- **Container Scanning**: Trivy
- **Secrets Detection**: TruffleHog
- **SAST**: SonarCloud
- **Infrastructure Scanning**: Checkov, tfsec

## Contact

For questions about this security policy, contact the security team at security@iff-guardian.com.