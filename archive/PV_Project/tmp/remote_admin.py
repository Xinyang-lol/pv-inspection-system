from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import paramiko

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def connect() -> paramiko.SSHClient:
    host = os.environ["PV_REMOTE_HOST"]
    port = int(os.environ.get("PV_REMOTE_PORT", "22"))
    user = os.environ["PV_REMOTE_USER"]
    password = os.environ["PV_REMOTE_PASS"]

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=host,
        port=port,
        username=user,
        password=password,
        timeout=30,
        banner_timeout=30,
        auth_timeout=30,
    )
    return client


def run_exec(client: paramiko.SSHClient, command: str) -> int:
    stdin, stdout, stderr = client.exec_command(command, get_pty=False)
    del stdin
    for line in iter(stdout.readline, ""):
        print(line, end="")
    err = stderr.read().decode("utf-8", errors="replace")
    if err:
        print(err, file=sys.stderr, end="")
    return stdout.channel.recv_exit_status()


def upload(client: paramiko.SSHClient, local_path: Path, remote_path: str) -> None:
    with client.open_sftp() as sftp:
        parent = remote_path.rsplit("/", 1)[0]
        run_exec(client, f"mkdir -p {quote(parent)}")
        sftp.put(str(local_path), remote_path)


def download(client: paramiko.SSHClient, remote_path: str, local_path: Path) -> None:
    local_path.parent.mkdir(parents=True, exist_ok=True)
    with client.open_sftp() as sftp:
        sftp.get(remote_path, str(local_path))


def quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    exec_parser = subparsers.add_parser("exec")
    exec_parser.add_argument("command", nargs="?")

    upload_parser = subparsers.add_parser("upload")
    upload_parser.add_argument("local")
    upload_parser.add_argument("remote")

    download_parser = subparsers.add_parser("download")
    download_parser.add_argument("remote")
    download_parser.add_argument("local")

    args = parser.parse_args()
    client = connect()
    try:
        if args.cmd == "exec":
            command = args.command or os.environ["PV_REMOTE_COMMAND"]
            return run_exec(client, command)
        if args.cmd == "upload":
            upload(client, Path(args.local), args.remote)
            return 0
        if args.cmd == "download":
            download(client, args.remote, Path(args.local))
            return 0
    finally:
        client.close()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
