import threading


def thread_running(name):
    for thread in threading.enumerate():
        if thread.name == name:
            return True
    return False


def get_thread(name):
    for thread in threading.enumerate():
        if thread.name == name:
            return thread
    return None