import nox


@nox.session(name="lint", venv_backend="none")
def lint(session):
    session.run("ruff", "check", ".", *session.posargs)
    session.run("ruff", "format", "--check", ".", *session.posargs)


@nox.session(name="tests", venv_backend="none")
def pytest(session):
    session.run(
        "pytest",
        "-vv",
        "--cov=.",
        "--cov-report=term-missing",
        *session.posargs,
    )
