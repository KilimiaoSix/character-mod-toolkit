#!/usr/bin/env python3
"""Get pinned upstream dependencies into a local workspace, without executing them."""
import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

LOCK = json.loads(Path(__file__).with_name("dependencies.json").read_text(encoding="utf-8"))
STAMP = ".character-mod-toolkit-source.json"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def unpack(archive, destination, spec):
    prefix = spec["extract_root"]
    include = spec.get("include")
    with zipfile.ZipFile(archive) as contents:
        entries = contents.infolist()
        if len(entries) > 3000 or sum(item.file_size for item in entries) > 256 << 20:
            raise ValueError("Unexpected release archive size")
        for entry in entries:
            path = PurePosixPath(entry.filename)
            if (not path.parts or path.parts[0] != prefix or path.is_absolute()
                    or ".." in path.parts or "\\" in entry.filename
                    or any(":" in part for part in path.parts)
                    or stat.S_ISLNK(entry.external_attr >> 16)):
                raise ValueError(f"Unexpected release archive entry: {entry.filename}")
            relative = path.parts[1:]
            if not relative or (include and relative[0] not in include):
                continue
            target = destination.joinpath(*relative)
            if entry.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with contents.open(entry) as source, target.open("xb") as output:
                    shutil.copyfileobj(source, output)
    for required in include or ("AGENTS.md", "package.json", "server.mjs"):
        if not (destination / required).exists():
            raise ValueError(f"Archive has no {required}")


def download(spec, archive, cache):
    url = urlsplit(spec["source"])
    filename = spec.get("filename", Path(url.path).name)
    local = cache / filename if cache else None
    if local and local.is_file():
        shutil.copyfile(local, archive)
    else:
        gh = shutil.which("gh")
        obtained = False
        if gh:
            try:
                if url.netloc == "api.github.com":
                    with archive.open("wb") as output:
                        subprocess.run([gh, "api", url.path.lstrip("/")], stdout=output,
                                       check=True, timeout=120)
                else:
                    repository = "/".join(url.path.strip("/").split("/")[:2])
                    subprocess.run([gh, "release", "download", spec["revision"], "--repo", repository,
                                    "--pattern", filename, "--output", str(archive)],
                                   check=True, timeout=120)
                obtained = True
            except (OSError, subprocess.SubprocessError):
                archive.unlink(missing_ok=True)
        if not obtained:
            curl = shutil.which("curl.exe" if os.name == "nt" else "curl")
            if not curl:
                raise RuntimeError("Use GitHub CLI, curl, or --archive-dir for GitHub release downloads")
            subprocess.run([curl, "--fail", "--location", "--silent", "--show-error",
                            "--connect-timeout", "10", "--max-time", "120",
                            "--proto", "=https", "--output", str(archive), spec["source"]], check=True)
    if sha256(archive) != spec["sha256"]:
        raise ValueError(f"SHA-256 mismatch: {filename}")


def fetch(name, deps, cache):
    spec = LOCK[name]
    destination = deps / spec["destination"]
    metadata = {key: spec[key] for key in ("source", "revision", "sha256")}
    if destination.is_symlink():
        raise ValueError(f"Dependency destination is a symbolic link: {destination}")
    if destination.exists():
        stamp = destination / STAMP
        already = (sha256(destination) == spec["sha256"] if spec["kind"] == "file"
                   and destination.is_file() else stamp.is_file() and json.loads(stamp.read_text()) == metadata)
        if already:
            print(f"{name}: existing {destination}")
            return
        raise FileExistsError(f"Choose a different workspace or move the existing {destination}")
    with tempfile.TemporaryDirectory(prefix=".fetch-", dir=deps) as directory:
        tmp = Path(directory)
        stage = tmp / "output"
        archive = tmp / "download.zip"
        download(spec, archive, cache)
        if spec["kind"] == "file":
            archive.rename(stage)
        else:
            stage.mkdir()
            unpack(archive, stage, spec)
        if stage.is_dir():
            (stage / STAMP).write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        stage.rename(destination)
    print(f"{name}: ready {destination}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--archive-dir", type=Path, help="optional cache with upstream release filenames")
    parser.add_argument("dependencies", nargs="+", choices=LOCK)
    args = parser.parse_args()
    deps = args.workspace.resolve() / "deps"
    deps.mkdir(parents=True, exist_ok=True)
    for name in dict.fromkeys(args.dependencies):
        fetch(name, deps, args.archive_dir)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, zipfile.BadZipFile) as error:
        print(f"Dependency setup failed: {error}", file=sys.stderr)
        sys.exit(1)
