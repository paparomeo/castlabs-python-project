from invoke import task

from .helpers import prun
from .test import unit_runner


@task
def run(c):
    """Check code test coverage.

    """
    unit_runner(c, "coverage run -m pytest")


@task(run, default=True)
def report(c):
    """Check code test coverage and display console report.

    """
    prun(c, "coverage report --show-missing")


@task(run)
def html(c):
    """Check code test coverage and open html report.

    """
    prun(c, "coverage html")
    c.run("xdg-open htmlcov/index.html")
