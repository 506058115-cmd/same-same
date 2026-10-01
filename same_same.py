#!/usr/bin/env python3
"""Find same-sized files with matching SHA-256 hashes; never modify them."""

import argparse
import hashlib
import os
from pathlib import Path
import stat
import sys
from collections import defaultdict


CHUNK_SIZE = 1024 * 1024


def terminal_safe(value):
    return "".join(
        char if char.isprintable() else char.encode("unicode_escape").decode("ascii")
        for char in value
    )


def is_linklike(path):
    if path.is_symlink():
        return True
    is_junction = getattr(os.path, "isjunction", None)
    if is_junction is not None:
        return is_junction(path)
    if os.name == "nt":
        try:
            tag = path.lstat().st_reparse_tag
        except (AttributeError, OSError):
            return False
        mount_point = getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", None)
        return mount_point is not None and tag == mount_point
    return False


def warn(message, warning_count):
    warning_count[0] += 1
    print(f"same-same: {terminal_safe(message)}", file=sys.stderr)


def walk_files(roots, warning_count):
    seen = set()

    def visit(path):
        key = os.path.normcase(os.path.abspath(str(path)))
        if key in seen:
            return
        seen.add(key)
        try:
            info = path.lstat()
        except OSError as error:
            warn(f"跳过无法读取的路径 {path}: {error}", warning_count)
            return
        if stat.S_ISREG(info.st_mode):
            yield path, info.st_size
        elif not stat.S_ISDIR(info.st_mode):
            warn(f"跳过非普通文件 {path}", warning_count)

    for value in roots:
        root = Path(value).expanduser()
        if is_linklike(root):
            warn(f"跳过符号链接或目录联接 {root}", warning_count)
            continue
        try:
            mode = root.lstat().st_mode
        except OSError as error:
            warn(f"跳过无法读取的路径 {root}: {error}", warning_count)
            continue

        if stat.S_ISREG(mode):
            yield from visit(root)
        elif stat.S_ISDIR(mode):
            def on_error(error):
                warn(f"无法遍历 {error.filename}: {error}", warning_count)

            for current, directories, filenames in os.walk(
                root, followlinks=False, onerror=on_error
            ):
                base = Path(current)
                directories[:] = [
                    name
                    for name in sorted(directories)
                    if not is_linklike(base / name)
                ]
                for name in sorted(filenames):
                    path = base / name
                    if is_linklike(path):
                        continue
                    yield from visit(path)
        else:
            warn(f"跳过非文件或目录 {root}", warning_count)


def file_digest(path, expected_size):
    before = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    after = path.stat()
    if (
        before.st_size != after.st_size
        or before.st_mtime_ns != after.st_mtime_ns
        or after.st_size != expected_size
    ):
        raise OSError("文件在扫描时发生变化")
    return digest.digest()


def format_size(size):
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB"):
        if value < 1024 or unit == "EiB":
            return f"{int(value)} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="离线查找内容相同的文件；只读扫描，不会删除或改写文件。"
    )
    parser.add_argument(
        "paths", nargs="+", metavar="PATH", help="要扫描的文件或目录"
    )
    args = parser.parse_args(argv)

    warning_count = [0]
    # ponytail: retain paths and size groups in memory; stream file bytes in 1 MiB chunks.
    size_groups = defaultdict(list)
    files_seen = 0
    for path, size in walk_files(args.paths, warning_count):
        files_seen += 1
        size_groups[size].append(path)

    duplicates = []
    for size, paths in size_groups.items():
        if len(paths) < 2:
            continue
        hashes = defaultdict(list)
        for path in paths:
            try:
                hashes[file_digest(path, size)].append(path)
            except OSError as error:
                warn(f"无法校验 {path}: {error}", warning_count)
        duplicates.extend(
            (size, matches)
            for matches in hashes.values()
            if len(matches) > 1
        )

    duplicates.sort(key=lambda item: os.path.normcase(str(item[1][0])))
    if duplicates:
        for number, (size, paths) in enumerate(duplicates, 1):
            print(f"\n重复组 {number} · {format_size(size)}")
            for path in sorted(paths, key=lambda item: os.path.normcase(str(item))):
                print(f"  {terminal_safe(str(path))}")
        duplicate_count = sum(len(paths) for _, paths in duplicates)
        print(f"\n找到 {len(duplicates)} 组、{duplicate_count} 个重复路径。")
    else:
        print("没有找到重复文件。")

    print(f"扫描了 {files_seen} 个普通文件。")
    if warning_count[0]:
        print(f"有 {warning_count[0]} 处路径未能完整读取；结果可能不完整。", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("same-same: 已中断；没有修改任何文件。", file=sys.stderr)
        raise SystemExit(130)
