# Contributing to Website Uptime Monitor

Thank you for your interest in contributing. This document explains how to get started.

---

## Getting started

1. Fork the repository on GitHub.
2. Clone your fork:

```bash
git clone https://github.com/your-username/website-uptime-monitor.git
cd website-uptime-monitor
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Copy the example environment file:

```bash
cp .env.example .env
```

5. Run the tests to confirm everything works:

```bash
cd website-uptime-monitor
python -m pytest test_main.py -v
```

All 21 tests should pass before you start making changes.

---

## Making changes

- Create a new branch for your change:

```bash
git checkout -b your-branch-name
```

- Make your changes in small, focused commits.
- Run the tests after every change.
- Push your branch and open a pull request against `main`.

---

## Commit message style

Use a short, clear description in the present tense:

```
Add timeout configuration via environment variable
Fix SSL error not recorded as DOWN in history
Update README with new --history flag examples
```

---

## Running tests

```bash
cd website-uptime-monitor
python -m pytest test_main.py -v
```

---

## Reporting bugs

Open a GitHub issue using the bug report template. Include:

- What you expected to happen
- What actually happened
- Steps to reproduce
- Your operating system and Python version

---

## Code style

- Follow PEP 8 for Python code.
- Keep functions small and focused on one task.
- Add a test for any new behaviour you introduce.
- Do not commit `history.json`, `.env`, or any file containing secrets.

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
