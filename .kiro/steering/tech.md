# Technology Stack

## Framework & Platform
- **Frappe Framework**: Python-based web application framework (v15.0.0+)
- **Python**: Minimum version 3.10
- **Database**: MariaDB/MySQL (via Frappe)
- **Frontend**: JavaScript, HTML, CSS with Frappe's client-side framework

## Build System & Package Management
- **Build Backend**: `flit_core` for Python packaging
- **Dependency Management**: Managed by Frappe Bench
- **Installation**: Via Frappe Bench CLI

## Code Quality & Formatting Tools
- **Ruff**: Python linting and formatting (replaces Black, isort, flake8)
- **ESLint**: JavaScript linting
- **Prettier**: JavaScript/CSS code formatting
- **Pre-commit**: Automated code quality checks

## Development Standards
- **Line Length**: 110 characters (Python), 99 characters (JS/CSS)
- **Indentation**: Tabs (4 spaces equivalent) for Python/JS, 2 spaces for JSON
- **Python Target**: Python 3.10+
- **Encoding**: UTF-8 with LF line endings

## Common Commands

### Installation & Setup
```bash
# Install the app
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app electricity_meter_management

# Setup pre-commit hooks
cd apps/electricity_meter_management
pre-commit install
```

### Development
```bash
# Start development server
bench start

# Run migrations
bench migrate

# Clear cache
bench clear-cache

# Restart services
bench restart
```

### Code Quality
```bash
# Run pre-commit checks manually
pre-commit run --all-files

# Run specific tools
ruff check .
ruff format .
prettier --write "**/*.js"
eslint "**/*.js"
```

### Testing
```bash
# Run unit tests
bench run-tests --app electricity_meter_management

# Run specific test
bench run-tests --app electricity_meter_management --module test_meter_movement
```

## Configuration Files
- `pyproject.toml`: Python project configuration and tool settings
- `.editorconfig`: Editor formatting rules
- `.pre-commit-config.yaml`: Pre-commit hook configuration
- `.eslintrc`: ESLint configuration