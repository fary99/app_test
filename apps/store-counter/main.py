"""Minimal counter for app-store seed."""

from m20app import on_ready, run, ui

n = 0


def _show():
    ui.set("count", text=str(n))


def inc():
    global n
    n += 1
    _show()


def reset():
    global n
    n = 0
    _show()


@on_ready
def init():
    _show()


run()
