from invoke import Collection, task

from . import coverage, test
from .helpers import get_app_cmd, prun, s

coverage = Collection.from_module(coverage)
test = Collection.from_module(test)


@task
def install(c):
    """Install the project dependencies.

    """
    c.run("poetry install", pty=True)


@task
def lint(c):
    """Run linters (pycodestyle, pylint and mypy) on the code.

    """
    prun(c, "flake8 app")
    prun(c, "pylint app")
    prun(c, "mypy app")


@task(default=True)
def run(c, host=None, port=None, reload=False):
    """Run the app server process.

    """

    cmd = s(get_app_cmd(host, port or c.port, reload))
    prun(c, cmd, pty=True)


collection = Collection("app", coverage, install, lint, run, test)
