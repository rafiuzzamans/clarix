#!/usr/bin/env python3
"""
Master test runner — runs all backend service unit tests.
Usage:  python run_tests.py
        python run_tests.py --fast      (skip slow/integration tests)
        python run_tests.py --service ai (run one service only)
"""
import subprocess
import sys
import argparse
import os

SERVICES = [
    ("auth-service",       "services/auth-service"),
    ("ai-service",         "services/ai-service"),
    ("case-service",       "services/case-service"),
    ("automation-service", "services/automation-service"),
]


def run_tests(service_name: str, service_path: str, fast: bool) -> tuple[bool, str]:
    test_dir = os.path.join(service_path, "tests")
    if not os.path.exists(test_dir):
        return True, f"[SKIP] {service_name} — no tests directory"

    cmd = [sys.executable, "-m", "pytest", test_dir, "-v", "--tb=short", "--color=yes"]
    if fast:
        cmd += ["-m", "not slow"]

    print(f"\n{'='*60}")
    print(f"  Running: {service_name}")
    print(f"{'='*60}")

    result = subprocess.run(cmd, cwd=service_path, capture_output=False)
    return result.returncode == 0, service_name


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fast",    action="store_true", help="Skip slow tests")
    parser.add_argument("--service", help="Run only this service")
    args = parser.parse_args()

    targets = SERVICES
    if args.service:
        targets = [(n, p) for n, p in SERVICES if args.service in n]
        if not targets:
            print(f"Service '{args.service}' not found. Available: {[n for n,_ in SERVICES]}")
            sys.exit(1)

    results = []
    for name, path in targets:
        passed, label = run_tests(name, path, args.fast)
        results.append((label, passed))

    # Summary
    print(f"\n{'='*60}")
    print("  TEST SUMMARY")
    print(f"{'='*60}")
    all_passed = True
    for label, passed in results:
        icon = "✅" if passed else "❌"
        print(f"  {icon}  {label}")
        if not passed:
            all_passed = False

    print()
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
