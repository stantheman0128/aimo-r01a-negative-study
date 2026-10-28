"""Explicitly acquire one pinned official input, or verify/copy a local file.

This stdlib-only step is separate from offline inference and numerical replay.
It neither accepts publisher terms nor handles credentials. Review applicable
publisher terms yourself before choosing to run it. No input is bundled here.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
from queue import Empty, Queue
import tempfile
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

OFFICIAL_URL = (
    "https://huggingface.co/datasets/aimo-interp/train-main-v2/resolve/"
    "fa8af758c6519fc97a9d0bd9017feb6f12232b52/data/train-00000-of-00001.parquet"
)
EXPECTED_BYTES = 11372
EXPECTED_SHA256 = "e18eb44207e7987781ec2ff214793196038442bdc1466fdf5498f3e87ec58285"
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SOCKET_TIMEOUT_SECONDS = 10
STREAM_WALL_SECONDS = 30
NETWORK_WALL_SECONDS = 25


class HTTPSOnlyRedirect(HTTPRedirectHandler):
    """Follow the official endpoint's HTTPS delivery redirects, never downgrade."""

    def redirect_request(self, request, fp, code, message, headers, new_url):
        parsed = urlsplit(new_url)
        if parsed.scheme != "https" or parsed.username or parsed.password:
            raise RuntimeError("Refused a non-HTTPS or credential-bearing redirect")
        return super().redirect_request(request, fp, code, message, headers, new_url)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def fetch_official(started):
    """Bound the whole network transfer without giving its daemon any file access."""
    result = Queue(maxsize=1)

    def fetch():
        try:
            opener = build_opener(HTTPSOnlyRedirect())
            request = Request(OFFICIAL_URL, headers={"Accept-Encoding": "identity"})
            with opener.open(request, timeout=SOCKET_TIMEOUT_SECONDS) as response:
                require(response.status == 200, "Official endpoint did not return HTTP 200")
                require(response.headers.get("Content-Encoding", "identity").lower() == "identity",
                        "Unexpected content encoding")
                length = response.headers.get("Content-Length")
                require(length is None or int(length) == EXPECTED_BYTES, "Official response length mismatch")
                payload = bytearray()
                while True:
                    require(time.monotonic() - started < NETWORK_WALL_SECONDS, "Network wall limit")
                    chunk = response.read1(min(8192, EXPECTED_BYTES + 1 - len(payload)))
                    if not chunk:
                        break
                    payload.extend(chunk)
                    require(len(payload) <= EXPECTED_BYTES, "Official input exceeds pinned byte length")
                result.put((bytes(payload), None))
        except Exception as error:
            result.put((None, error))

    # A timed-out network worker is a daemon with no filesystem side effects;
    # the CLI can exit without waiting for DNS, redirects or a trickling peer.
    threading.Thread(target=fetch, name="pinned-input-fetch", daemon=True).start()
    remaining = NETWORK_WALL_SECONDS - (time.monotonic() - started)
    require(remaining > 0, "Network wall limit")
    try:
        payload, error = result.get(timeout=remaining)
    except Empty as error:
        raise RuntimeError("Network wall limit; no input file was written") from error
    if error is not None:
        raise error
    return io.BytesIO(payload)


def copy_verified(stream, destination, started):
    """Write at most expected length + 1 bytes, verify, then publish without replace.

    A same-directory hard link makes the completed file visible atomically and
    fails if the destination exists. Filesystems without hard-link support fail
    safely; there is no overwrite/rename fallback. The temporary name is removed
    on success or failure. The final destination is never removed by this helper.
    """
    fd, temporary_name = tempfile.mkstemp(prefix="." + destination.name + ".", suffix=".part",
                                          dir=destination.parent)
    temporary = Path(temporary_name)
    try:
        digest = hashlib.sha256()
        count = 0
        with os.fdopen(fd, "wb") as output:
            while True:
                require(time.monotonic() - started < STREAM_WALL_SECONDS, "Acquisition wall limit")
                chunk = stream.read(min(8192, EXPECTED_BYTES + 1 - count))
                if not chunk:
                    break
                count += len(chunk)
                require(count <= EXPECTED_BYTES, "Official input exceeds pinned byte length")
                output.write(chunk)
                digest.update(chunk)
            require(count == EXPECTED_BYTES, "Official input byte length mismatch")
            require(digest.hexdigest() == EXPECTED_SHA256, "Official input SHA256 mismatch")
            output.flush()
            os.fsync(output.fileno())
        require(time.monotonic() - started < STREAM_WALL_SECONDS, "Acquisition wall limit")
        os.link(temporary, destination)
        return {"bytes": count, "sha256": digest.hexdigest()}
    finally:
        temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True,
                        help="New file outside this source package; its parent must exist")
    parser.add_argument("--from-local", type=Path,
                        help="Verify/copy an already obtained pinned file; makes no network request")
    args = parser.parse_args(argv)
    try:
        require(not os.path.lexists(args.destination), "Destination already exists; no overwrite allowed")
        parent = args.destination.parent.resolve(strict=True)
        require(parent.is_dir(), "Destination parent must be an existing directory")
        destination = parent / args.destination.name
        require(not destination.is_relative_to(PACKAGE_ROOT), "Keep acquired data outside the source package")
        require(not os.path.lexists(destination), "Destination already exists; no overwrite allowed")
        started = time.monotonic()
        if args.from_local is not None:
            source = args.from_local.resolve(strict=True)
            require(source.is_file(), "Local source must be a regular file")
            require(source.stat().st_size == EXPECTED_BYTES, "Local source byte length mismatch")
            with source.open("rb") as stream:
                verified = copy_verified(stream, destination, started)
            mode = "verified_local_copy"
        else:
            with fetch_official(started) as stream:
                verified = copy_verified(stream, destination, started)
            mode = "official_pinned_revision"
        print(json.dumps({"status": "VERIFIED_NEW_FILE", "source_mode": mode,
                          "destination": str(destination), **verified}, sort_keys=True))
        return 0
    except (OSError, RuntimeError, ValueError, URLError, HTTPError) as error:
        # No login, token, agreement, alternate revision or mirror is attempted.
        print(json.dumps({"status": "FAILED_NO_FALLBACK", "error": str(error),
                          "action": "Check publisher access and applicable terms directly; an already obtained file may be supplied with --from-local."},
                         sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
