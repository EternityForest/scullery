# SPDX-FileCopyrightText: Copyright Daniel Dunn
# SPDX-License-Identifier: LGPL-2.1-or-later


import sys
import os
import weakref
import types
from typing import TypeVar
# Credit to Jay of stack overflow for this function


def which(program):
    "Check if a program is installed like you would do with UNIX's which command."

    # Because in windows, the actual executable name has .exe while the command name does not.
    if sys.platform == "win32" and not program.endswith(".exe"):
        program += ".exe"

    # Find out if path represents a file that the current user can execute.
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    # If the input was a direct path to an executable, return it
    if fpath:
        if is_exe(program):
            return program

    # Else search the path for the file.
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    # If we got this far in execution, we assume the file is not there and return None
    return None


T = TypeVar("T")


def universal_weakref(f: T, cb=None) -> weakref.ref[T]:
    "Return a weakref or weakmethod as appropriate for f"
    if isinstance(f, types.MethodType):
        # TODO why doesn't linter know this is safe?
        return weakref.WeakMethod(f, cb)  # type: ignore
    else:
        return weakref.ref(f, cb)


def search_paths(fn: str, paths: list[str]) -> str | None:
    for i in paths:
        if os.path.exists(os.path.join(i, fn)):
            return os.path.join(i, fn)
