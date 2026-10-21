"""Private local tutorial saves; JSON data only, never executable snapshots."""

import fcntl
import json
import os
from pathlib import Path
import re
import stat
import uuid


MAX_SAVE_BYTES = 2 * 1024 * 1024


class SaveError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def strict_json(raw):
    """Reject duplicate keys and non-standard floating-point constants."""
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result

    def constant(_):
        raise ValueError("non-finite constant")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


class TutorialStore:
    """An exclusive local writer with atomic 0600 saves in a 0700 directory.

    The digest in the application document detects accidental change; it is not
    a signature against an attacker who can already edit the owner's files.
    No credentials or provider configuration are accepted by this store.
    """

    filename = "tutorial-v1.json"

    def __init__(self, directory):
        self.directory = Path(directory)
        self._dir_fd = None
        self._lock_fd = None
        try:
            self.directory.mkdir(parents=True, mode=0o700, exist_ok=True)
            self._dir_fd = os.open(
                str(self.directory), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            )
            info = os.fstat(self._dir_fd)
            if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
                raise SaveError("UNSAFE_SAVE_DIRECTORY")
            self._lock_fd = os.open(
                ".tutorial.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW,
                0o600, dir_fd=self._dir_fd,
            )
            lock_info = os.fstat(self._lock_fd)
            if not stat.S_ISREG(lock_info.st_mode) or lock_info.st_uid != os.getuid():
                raise SaveError("UNSAFE_SAVE_DIRECTORY")
            try:
                fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise SaveError("SAVE_IN_USE") from None
        except SaveError:
            self.close()
            raise
        except OSError:
            self.close()
            raise SaveError("SAVE_UNAVAILABLE") from None

    def read(self):
        fd = None
        try:
            fd = os.open(self.filename, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=self._dir_fd)
            info = os.fstat(fd)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                    or stat.S_IMODE(info.st_mode) & 0o077
                    or info.st_size > MAX_SAVE_BYTES):
                raise SaveError("INVALID_SAVE")
            with os.fdopen(fd, "rb") as source:
                fd = None
                raw = source.read(MAX_SAVE_BYTES + 1)
            if len(raw) > MAX_SAVE_BYTES:
                raise SaveError("INVALID_SAVE")
            return strict_json(raw)
        except FileNotFoundError:
            return None
        except (OSError, UnicodeError, ValueError, RecursionError):
            raise SaveError("INVALID_SAVE") from None
        finally:
            if fd is not None:
                os.close(fd)

    def write(self, document):
        try:
            raw = json.dumps(document, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode("utf-8")
        except (ValueError, TypeError, RecursionError):
            raise SaveError("INVALID_SAVE") from None
        if len(raw) > MAX_SAVE_BYTES:
            raise SaveError("SAVE_TOO_LARGE")
        temporary = ".tutorial-" + uuid.uuid4().hex + ".tmp"
        fd = None
        try:
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=self._dir_fd)
            with os.fdopen(fd, "wb") as target:
                fd = None
                target.write(raw)
                target.flush()
                os.fsync(target.fileno())
            os.replace(temporary, self.filename,
                       src_dir_fd=self._dir_fd, dst_dir_fd=self._dir_fd)
            os.fsync(self._dir_fd)
        except OSError:
            raise SaveError("SAVE_UNAVAILABLE") from None
        finally:
            if fd is not None:
                os.close(fd)
            try:
                os.unlink(temporary, dir_fd=self._dir_fd)
            except FileNotFoundError:
                pass

    def delete(self):
        try:
            # A crash between fsync and replace may leave a private staging file.
            # Explicit deletion also removes only this store's exact temp names.
            names = [self.filename] + [
                name for name in os.listdir(self._dir_fd)
                if re.fullmatch(r"\.tutorial-[0-9a-f]{32}\.tmp", name)
            ]
            for name in names:
                try:
                    os.unlink(name, dir_fd=self._dir_fd)
                except FileNotFoundError:
                    pass
            os.fsync(self._dir_fd)
        except OSError:
            raise SaveError("SAVE_UNAVAILABLE") from None

    def close(self):
        if self._lock_fd is not None:
            os.close(self._lock_fd)
            self._lock_fd = None
        if self._dir_fd is not None:
            os.close(self._dir_fd)
            self._dir_fd = None
