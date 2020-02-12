import psutil
import signal


def kill_child_processes(parent_pid, sig=signal.SIGTERM):
    """
    Thanks @ostrokach - https://stackoverflow.com/questions/42782953/python-concurrent-futures-how-to-make-it-cancelable
    :param parent_pid:
    :param sig:
    :return:
    """
    try:
        parent = psutil.Process(parent_pid)
    except psutil.NoSuchProcess:
        return
    children = parent.children(recursive=True)
    for process in children:
        process.send_signal(sig)
