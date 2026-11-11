# 🤝 Contributing to IBKR-MCP

Thank you for your interest in contributing to **IBKR-MCP**! We welcome contributions from quant researchers, software engineers, and algorithmic traders.

## 📋 Code of Conduct
We are committed to providing a welcoming, inclusive, and professional environment for all contributors.

## 🛠️ Development Setup
1. **Fork and Clone:**
   ```bash
   git clone https://github.com/<your-username>/IBKR-MCP.git
   cd IBKR-MCP
   ```
2. **Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Branching Model:**
   * Feature branch: `feature/your-feature-name`
   * Bug fix: `fix/issue-description`
   * Performance optimization: `perf/optimization-target`

## 📏 Code Style Guidelines
* Follow **PEP 8** style conventions.
* Provide clear docstrings for all classes and functions.
* Include type annotations (`typing`) where appropriate.
* Ensure code passes flake8 static analysis (`flake8 . --count --select=E9,F63,F7,F82`).

## 🚀 Pull Request Process
1. Verify syntax and static analysis before submitting your PR.
2. Update technical documentation in `README.md` and document changes in `CHANGELOG.md`.
3. Submit PR against `main` with a descriptive summary of changes.
