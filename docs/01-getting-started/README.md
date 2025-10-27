# Getting Started with HAWWA

This section contains everything you need to get started with HAWWA development.

## 📋 Contents

- [**Development Setup**](DEV_SETUP.md) - Complete development environment setup
- [**Contributing Guidelines**](CONTRIBUTING.md) - How to contribute to the project

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.12+
- PostgreSQL 14+
- Redis 7.0+
- Git

### 2. Clone Repository
```bash
git clone git@github.com:essyem/hawwa-staging.git
cd hawwa
```

### 3. Setup Environment
```bash
# Create virtual environment
python3 -m venv env-hawwa
source env-hawwa/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python manage.py migrate
```

### 4. Run Development Server
```bash
python manage.py runserver
```

Visit: http://localhost:8000

## 📚 Next Steps

1. Read the [Development Setup Guide](DEV_SETUP.md) for detailed instructions
2. Review [Contributing Guidelines](CONTRIBUTING.md) before making changes
3. Check [Architecture Documentation](../05-architecture/) to understand the system
4. Look at [Pending Tasks](../07-project-management/Pending_Tasks.md) for current work

## 🆘 Need Help?

- Check existing documentation in `/docs`
- Review code comments and docstrings
- Contact the development team
- Create an issue on GitHub
