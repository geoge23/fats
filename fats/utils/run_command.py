import asyncio
from asyncio.subprocess import Process

from .logger import log


async def _post_handler(proc: Process, steal_and_print_output: bool):
    if steal_and_print_output:
        if proc.stdout is None:
            log(f"No stdout to read from for process {proc.pid}")
        else:
            async for line in proc.stdout:
                log(line.decode().rstrip())
    await proc.wait()
    log(f"Process {proc.pid} finished with return code {proc.returncode}")


async def run(prog: str, *args: str, steal_and_print_output: bool = False) -> Process:
    """
    Docstring for run

    :param prog: Description
    :type prog: Program to run. Should be direct path or in PATH.
    :param args: Args to pass to the program, separated as necessary since they will be passed as separate arguments.
    :type args: str
    :param steal_and_print_output: Whether to steal and print the output of the process for logging. WILL CONSUME STDOUT.
    :type steal_and_print_output: bool
    :return: Description
    :rtype: Process
    """
    process = await asyncio.create_subprocess_exec(
        prog,
        *args,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    asyncio.create_task(_post_handler(process, steal_and_print_output))
    return process
