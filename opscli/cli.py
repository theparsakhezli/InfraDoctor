import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path



def disk_command(args: argparse.Namespace) -> int:
    if args.warning >= args.critical:
        print(
            "Error: Warning threshold must be lower than critical threshold",
            file=sys.stderr
        )
        return 2
    
    try:
        usage= shutil.disk_usage(args.path)
        usage_percent = (usage.used / usage.total) * 100
        if usage_percent >= args.critical:
            status = "CRITICAL"
        elif usage_percent >= args.warning:
            status = "WARNING"
        else:
            status = "HEALTHY"
    except OSError as exc:
        print(f"Disk check failed: {exc}", file=sys.stderr)
        return 2
    
    data = {
        "path": str(args.path),
        "total_gib": round(usage.total / 1024**3, 2),
        "used_gib": round(usage.used / 1024**3, 2),
        "usage_pecentage": usage_percent,
        "free_gib": round(usage.free / 1024**3, 2),
        "status": status
    }

    if args.json: 
        print(json.dumps(data, indent=2))
    else:
        print(
            f"{data['path']}: "
            f"{data['used_gib']} GiB used, "
            f"{data['free_gib']} GiB free"
        )
    return 0


def service_command(args: argparse.Namespace) -> int:
    try:
        result = subprocess.run(
            ["systemctl", "is-active", args.name],
            capture_output=True,
            text=True,
            timeout=5,
            check=False
            )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"service check failed: {exc}", file=sys.stderr)
        return 2
    status = result.stdout.strip() or "unknown"
    print(f"{args.name}:{status}")
    
    return 0 if result.returncode == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="opsctl",
        description="Basic infrastructure checks"
    )
    
    commands = parser.add_subparsers(required=True)
    
    disk = commands.add_parser(
        "disk",
        help="check disk usage"
    )
    disk.add_arguement(
        "path",
        nargs="?",
        type=Path,
        default=Path("/")
    )
    disk.add_argument(
        "--json",
        action="store_true",
        help="JSON Output",
    )
    disk.add_argument("--warning", type=float, default=80)
    disk.add_argument("--critical", type=float, default=90)
    disk.set_defaults(func=disk_command)
    
    service = commands.add_parser(
        "service",
        help="Check a systemd service",
    )
    service.add_argument("name")
    service.set_defaults(func=service_command)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
