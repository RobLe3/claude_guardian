# IFF-Guardian Documentation

Welcome to the IFF-Guardian documentation! This directory contains comprehensive documentation for the IFF-Guardian threat detection and response system.

## Documentation Structure

### User Documentation
- **[User Guide](user-guide/)** - End-user documentation for using IFF-Guardian
  - Getting started
  - Web interface usage
  - API usage examples
  - Troubleshooting

### API Documentation
- **[API Reference](api/)** - Complete API documentation
  - REST API endpoints
  - Authentication
  - Request/response schemas
  - Code examples

### Developer Documentation
- **[Developer Guide](developer-guide/)** - Documentation for contributors and developers
  - Development setup
  - Architecture overview
  - Contributing guidelines
  - Code conventions

### Architecture Documentation
- **[Architecture](architecture/)** - System architecture and design decisions
  - High-level architecture
  - Database design
  - Security architecture
  - Deployment architecture

## Building Documentation

### Prerequisites
```bash
pip install -r requirements-dev.txt
```

### Build HTML Documentation
```bash
cd docs
make html
```

### Build PDF Documentation
```bash
cd docs
make latexpdf
```

### Live Reload During Development
```bash
sphinx-autobuild . _build/html
```

## Documentation Standards

### Writing Guidelines
1. Use clear, concise language
2. Include code examples where applicable
3. Follow the Google style guide for Python docstrings
4. Use consistent formatting and structure

### File Organization
- Use meaningful file names
- Group related documentation together
- Include README files in each subdirectory
- Use consistent heading levels

### Links and References
- Use relative links for internal documentation
- Always test links before committing
- Include version information where relevant

## Contributing to Documentation

1. Follow the existing structure and style
2. Update relevant sections when making code changes
3. Test documentation builds locally before submitting PR
4. Include screenshots and diagrams where helpful

## Documentation Tools

- **Sphinx** - Documentation generator
- **MyST Parser** - Markdown support for Sphinx
- **Read the Docs Theme** - Professional documentation theme
- **Autodoc** - Automatic API documentation generation

## Need Help?

- Check existing documentation first
- Create an issue for documentation bugs or improvements
- Join our developer discussions for questions

## Version Information

This documentation is automatically versioned with the main application. Each release includes updated documentation available at:

- **Latest**: https://docs.iff-guardian.com/latest/
- **Stable**: https://docs.iff-guardian.com/stable/
- **Versioned**: https://docs.iff-guardian.com/v{version}/