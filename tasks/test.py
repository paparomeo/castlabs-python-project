from invoke import task

from .helpers import prun, s


def unit_runner(
    c, command, capture="fd", verbosity=0, match=None,
):
    cmd = [command, f"--capture={capture}", f"--verbosity={verbosity}"]
    if match is not None:
        cmd.extend(["-k", match])
    prun(c, s(cmd), pty=True)


@task(default=True)
def unit(
    c, command="pytest", capture="fd", verbosity=0, match=None,
):
    """Run the unit tests.

    """
    unit_runner(c, command, capture, verbosity, match)
