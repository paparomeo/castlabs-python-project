def s(cmd):
    """Helper function to convert list commands to strings.

    """
    return " ".join(cmd) if isinstance(cmd, list) else cmd


def prun(c, cmd, **kwargs):
    c.run(f"poetry run {cmd}", **kwargs)


def get_app_cmd(host, port, reload=False):
    cmd = ["uvicorn", "--lifespan=off"]
    if host is not None:
        cmd.append(f"--host={host}")
    if port is not None:
        cmd.append(f"--port={port}")
    if reload:
        cmd.append("--reload")
    cmd.append("app.main:app")
    return cmd
