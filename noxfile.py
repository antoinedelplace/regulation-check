import nox

# -------------------------
# Lint session
# -------------------------


@nox.session(name="lint", venv_backend="none")
def lint(session):
    """
    Run Ruff linting and formatting checks.
    """
    session.run("ruff", "check", ".", *session.posargs)
    session.run("ruff", "format", "--check", ".", *session.posargs)


# -------------------------
# Test session
# -------------------------


@nox.session(name="tests", venv_backend="none")
def tests(session):
    """
    Run pytest with coverage.
    """
    session.run(
        "pytest",
        "-vv",
        "--cov=src",
        "--cov=scripts",
        "--cov-report=term-missing",
        *session.posargs,
    )


# -------------------------
# CI session
# -------------------------


@nox.session(name="ci", venv_backend="none")
def ci(session):
    """
    Continuous Integration pipeline.

    Runs:
    - lint
    - tests
    """
    session.notify("lint")
    session.notify("tests")
