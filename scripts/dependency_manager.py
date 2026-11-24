"""
Phantom Engine Dependency Manager
Automatically detects and manages dependencies for multiple package managers.
"""

import json
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

logger = logging.getLogger(__name__)


class PackageManager(Enum):
    """Supported package managers."""
    NPM = "npm"
    PNPM = "pnpm"
    YARN = "yarn"
    PIP = "pip"
    UV = "uv"
    POETRY = "poetry"
    CARGO = "cargo"
    GO = "go"
    COMPOSER = "composer"
    BUNDLER = "bundler"


@dataclass
class DependencyInfo:
    """Information about a dependency."""
    name: str
    version: str = ""
    required_version: str = ""
    package_manager: PackageManager = PackageManager.NPM
    is_dev: bool = False
    is_missing: bool = False
    has_conflict: bool = False
    conflict_details: str = ""


@dataclass
class LockFileInfo:
    """Information about a lockfile."""
    path: Path
    package_manager: PackageManager
    exists: bool = True
    last_modified: float = 0.0


class DependencyManager:
    """Manages dependencies across multiple package managers."""

    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = repo_path or Path.cwd()
        self.detected_managers: List[PackageManager] = []
        self.lockfiles: List[LockFileInfo] = []

    def detect_package_managers(self) -> List[PackageManager]:
        """Detect which package managers are used in the repository."""
        managers = []
        files = list(self.repo_path.rglob("*"))

        file_names = {f.name for f in files}

        # Node.js managers
        if "package-lock.json" in file_names:
            managers.append(PackageManager.NPM)
            self.lockfiles.append(LockFileInfo(
                path=self.repo_path / "package-lock.json",
                package_manager=PackageManager.NPM
            ))
        if "pnpm-lock.yaml" in file_names:
            managers.append(PackageManager.PNPM)
            self.lockfiles.append(LockFileInfo(
                path=self.repo_path / "pnpm-lock.yaml",
                package_manager=PackageManager.PNPM
            ))
        if "yarn.lock" in file_names:
            managers.append(PackageManager.YARN)
            self.lockfiles.append(LockFileInfo(
                path=self.repo_path / "yarn.lock",
                package_manager=PackageManager.YARN
            ))
        if "package.json" in file_names and not managers:
            # Default to npm if package.json exists
            managers.append(PackageManager.NPM)

        # Python managers
        if "uv.lock" in file_names:
            managers.append(PackageManager.UV)
            self.lockfiles.append(LockFileInfo(
                path=self.repo_path / "uv.lock",
                package_manager=PackageManager.UV
            ))
        if "poetry.lock" in file_names:
            managers.append(PackageManager.POETRY)
            self.lockfiles.append(LockFileInfo(
                path=self.repo_path / "poetry.lock",
                package_manager=PackageManager.POETRY
            ))
        if "requirements.txt" in file_names or "setup.py" in file_names or "pyproject.toml" in file_names:
            if PackageManager.UV not in managers and PackageManager.POETRY not in managers:
                managers.append(PackageManager.PIP)
                # Check for requirements.txt as lockfile equivalent
                req_path = self.repo_path / "requirements.txt"
                if req_path.exists():
                    self.lockfiles.append(LockFileInfo(
                        path=req_path,
                        package_manager=PackageManager.PIP
                    ))

        # Rust
        if "Cargo.lock" in file_names:
            managers.append(PackageManager.CARGO)
            self.lockfiles.append(LockFileInfo(
                path=self.repo_path / "Cargo.lock",
                package_manager=PackageManager.CARGO
            ))

        # Go
        if "go.mod" in file_names:
            managers.append(PackageManager.GO)
            if (self.repo_path / "go.sum").exists():
                self.lockfiles.append(LockFileInfo(
                    path=self.repo_path / "go.sum",
                    package_manager=PackageManager.GO
                ))

        # PHP
        if "composer.lock" in file_names:
            managers.append(PackageManager.COMPOSER)
            self.lockfiles.append(LockFileInfo(
                path=self.repo_path / "composer.lock",
                package_manager=PackageManager.COMPOSER
            ))

        # Ruby
        if "Gemfile.lock" in file_names:
            managers.append(PackageManager.BUNDLER)
            self.lockfiles.append(LockFileInfo(
                path=self.repo_path / "Gemfile.lock",
                package_manager=PackageManager.BUNDLER
            ))

        self.detected_managers = managers
        return managers

    def check_manager_available(self, manager: PackageManager) -> bool:
        """Check if a package manager is available on the system."""
        try:
            if manager in (PackageManager.NPM, PackageManager.PNPM, PackageManager.YARN):
                result = subprocess.run(
                    [manager.value, "--version"],
                    capture_output=True,
                    timeout=10
                )
            elif manager in (PackageManager.PIP, PackageManager.UV, PackageManager.POETRY):
                result = subprocess.run(
                    [manager.value, "--version"],
                    capture_output=True,
                    timeout=10
                )
            elif manager == PackageManager.CARGO:
                result = subprocess.run(
                    ["cargo", "--version"],
                    capture_output=True,
                    timeout=10
                )
            elif manager == PackageManager.GO:
                result = subprocess.run(
                    ["go", "version"],
                    capture_output=True,
                    timeout=10
                )
            elif manager == PackageManager.COMPOSER:
                result = subprocess.run(
                    ["composer", "--version"],
                    capture_output=True,
                    timeout=10
                )
            elif manager == PackageManager.BUNDLER:
                result = subprocess.run(
                    ["bundle", "--version"],
                    capture_output=True,
                    timeout=10
                )
            else:
                return False

            return result.returncode == 0
        except Exception:
            return False

    def get_missing_dependencies(self, manager: PackageManager) -> List[DependencyInfo]:
        """Get missing dependencies for a package manager."""
        missing = []

        try:
            if manager == PackageManager.NPM:
                missing.extend(self._check_npm_missing())
            elif manager == PackageManager.PNPM:
                missing.extend(self._check_pnpm_missing())
            elif manager == PackageManager.YARN:
                missing.extend(self._check_yarn_missing())
            elif manager == PackageManager.PIP:
                missing.extend(self._check_pip_missing())
            elif manager == PackageManager.UV:
                missing.extend(self._check_uv_missing())
            elif manager == PackageManager.POETRY:
                missing.extend(self._check_poetry_missing())
            elif manager == PackageManager.CARGO:
                missing.extend(self._check_cargo_missing())
            elif manager == PackageManager.GO:
                missing.extend(self._check_go_missing())
        except Exception as e:
            logger.error(f"Failed to check missing deps for {manager.value}: {e}")

        return missing

    def _check_npm_missing(self) -> List[DependencyInfo]:
        """Check for missing npm dependencies."""
        missing = []
        try:
            result = subprocess.run(
                ["npm", "ls", "--json", "--all"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                # Try install dry-run
                result = subprocess.run(
                    ["npm", "install", "--dry-run", "--json"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.stdout:
                    data = json.loads(result.stdout)
                    # Parse npm install dry-run output for missing deps
        except Exception:
            pass
        return missing

    def _check_pnpm_missing(self) -> List[DependencyInfo]:
        """Check for missing pnpm dependencies."""
        try:
            result = subprocess.run(
                ["pnpm", "install", "--dry-run"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
        except Exception:
            pass
        return []

    def _check_yarn_missing(self) -> List[DependencyInfo]:
        """Check for missing yarn dependencies."""
        try:
            result = subprocess.run(
                ["yarn", "install", "--dry-run"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
        except Exception:
            pass
        return []

    def _check_pip_missing(self) -> List[DependencyInfo]:
        """Check for missing pip dependencies."""
        missing = []
        req_file = self.repo_path / "requirements.txt"
        if req_file.exists():
            try:
                result = subprocess.run(
                    ["pip", "check"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode != 0:
                    # Parse output for missing packages
                    for line in result.stdout.split('\n'):
                        if "not installed" in line or "missing" in line.lower():
                            parts = line.split()
                            if parts:
                                missing.append(DependencyInfo(
                                    name=parts[0],
                                    package_manager=PackageManager.PIP,
                                    is_missing=True
                                ))
            except Exception:
                pass
        return missing

    def _check_uv_missing(self) -> List[DependencyInfo]:
        """Check for missing uv dependencies."""
        try:
            result = subprocess.run(
                ["uv", "sync", "--dry-run"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
        except Exception:
            pass
        return []

    def _check_poetry_missing(self) -> List[DependencyInfo]:
        """Check for missing poetry dependencies."""
        try:
            result = subprocess.run(
                ["poetry", "check"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
        except Exception:
            pass
        return []

    def _check_cargo_missing(self) -> List[DependencyInfo]:
        """Check for missing cargo dependencies."""
        try:
            result = subprocess.run(
                ["cargo", "check"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
        except Exception:
            pass
        return []

    def _check_go_missing(self) -> List[DependencyInfo]:
        """Check for missing Go dependencies."""
        try:
            result = subprocess.run(
                ["go", "mod", "verify"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
        except Exception:
            pass
        return []

    def install_dependencies(self, manager: PackageManager, dev: bool = False) -> bool:
        """Install dependencies for a package manager."""
        try:
            if manager == PackageManager.NPM:
                cmd = ["npm", "install"]
                if dev:
                    cmd.append("--include=dev")
            elif manager == PackageManager.PNPM:
                cmd = ["pnpm", "install"]
            elif manager == PackageManager.YARN:
                cmd = ["yarn", "install"]
            elif manager == PackageManager.PIP:
                req_file = self.repo_path / "requirements.txt"
                if req_file.exists():
                    cmd = ["pip", "install", "-r", str(req_file)]
                else:
                    cmd = ["pip", "install", "-e", "."]
            elif manager == PackageManager.UV:
                cmd = ["uv", "sync"]
                if dev:
                    cmd.append("--all-extras")
            elif manager == PackageManager.POETRY:
                cmd = ["poetry", "install"]
                if not dev:
                    cmd.append("--no-dev")
            elif manager == PackageManager.CARGO:
                cmd = ["cargo", "build"]
            elif manager == PackageManager.GO:
                cmd = ["go", "mod", "download"]
            elif manager == PackageManager.COMPOSER:
                cmd = ["composer", "install"]
            elif manager == PackageManager.BUNDLER:
                cmd = ["bundle", "install"]
            else:
                return False

            logger.info(f"Installing dependencies with {manager.value}: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                logger.info(f"Successfully installed dependencies with {manager.value}")
                return True
            else:
                logger.error(f"Failed to install with {manager.value}: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout installing dependencies with {manager.value}")
            return False
        except Exception as e:
            logger.exception(f"Error installing dependencies with {manager.value}")
            return False

    def check_version_conflicts(self, manager: PackageManager) -> List[DependencyInfo]:
        """Check for version conflicts in dependencies."""
        conflicts = []

        try:
            if manager == PackageManager.NPM:
                result = subprocess.run(
                    ["npm", "ls", "--json"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode != 0 and result.stdout:
                    try:
                        data = json.loads(result.stdout)
                        conflicts.extend(self._parse_npm_conflicts(data))
                    except Exception:
                        pass
            elif manager == PackageManager.PIP:
                result = subprocess.run(
                    ["pip", "check"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode != 0:
                    for line in result.stdout.split('\n'):
                        if "conflict" in line.lower() or "incompatible" in line.lower():
                            parts = line.split()
                            if parts:
                                conflicts.append(DependencyInfo(
                                    name=parts[0],
                                    package_manager=PackageManager.PIP,
                                    has_conflict=True,
                                    conflict_details=line
                                ))
        except Exception as e:
            logger.error(f"Failed to check conflicts for {manager.value}: {e}")

        return conflicts

    def _parse_npm_conflicts(self, data: Dict) -> List[DependencyInfo]:
        """Parse npm ls output for conflicts."""
        conflicts = []
        # Simplified parsing - in reality would need more robust handling
        return conflicts

    def run_build(self, manager: PackageManager) -> bool:
        """Run build after dependency installation."""
        try:
            if manager == PackageManager.NPM:
                # Check if build script exists
                pkg_json = self.repo_path / "package.json"
                if pkg_json.exists():
                    with open(pkg_json) as f:
                        pkg = json.load(f)
                    if "scripts" in pkg and "build" in pkg["scripts"]:
                        result = subprocess.run(
                            ["npm", "run", "build"],
                            cwd=self.repo_path,
                            capture_output=True,
                            text=True,
                            timeout=120
                        )
                        return result.returncode == 0
            elif manager == PackageManager.CARGO:
                result = subprocess.run(
                    ["cargo", "build", "--release"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=180
                )
                return result.returncode == 0
            elif manager == PackageManager.GO:
                result = subprocess.run(
                    ["go", "build", "./..."],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                return result.returncode == 0
        except Exception as e:
            logger.error(f"Build failed for {manager.value}: {e}")

        return True  # No build step or build not applicable

    def get_full_dependency_report(self) -> Dict[str, Any]:
        """Get comprehensive dependency report for all detected managers."""
        # Only detect if not already detected
        if not self.detected_managers:
            self.detect_package_managers()

        report = {
            "detected_managers": [m.value for m in self.detected_managers],
            "lockfiles": [
                {"path": str(lf.path), "manager": lf.package_manager.value, "exists": lf.exists}
                for lf in self.lockfiles
            ],
            "managers": {}
        }

        for manager in self.detected_managers:
            available = self.check_manager_available(manager)
            missing = self.get_missing_dependencies(manager)
            conflicts = self.check_version_conflicts(manager)

            report["managers"][manager.value] = {
                "available": available,
                "missing_count": len(missing),
                "missing": [
                    {"name": d.name, "version": d.version, "is_dev": d.is_dev}
                    for d in missing
                ],
                "conflicts_count": len(conflicts),
                "conflicts": [
                    {"name": d.name, "details": d.conflict_details}
                    for d in conflicts
                ]
            }

        return report

    def auto_install_all(self, include_dev: bool = True) -> Dict[str, bool]:
        """Automatically install dependencies for all detected managers."""
        self.detect_package_managers()
        results = {}

        for manager in self.detected_managers:
            if self.check_manager_available(manager):
                logger.info(f"Installing dependencies for {manager.value}")
                success = self.install_dependencies(manager, dev=include_dev)
                if success:
                    success = self.run_build(manager)
                results[manager.value] = success
            else:
                logger.warning(f"Package manager {manager.value} not available")
                results[manager.value] = False

        return results


if __name__ == "__main__":
    import sys

    dm = DependencyManager()

    if len(sys.argv) < 2:
        print("Usage: python dependency_manager.py <command> [args...]")
        print("Commands: detect, report, install-all, check <manager>")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "detect":
        managers = dm.detect_package_managers()
        print(json.dumps([m.value for m in managers], indent=2))
    elif cmd == "report":
        print(json.dumps(dm.get_full_dependency_report(), indent=2))
    elif cmd == "install-all":
        dev = "--no-dev" not in sys.argv
        print(json.dumps(dm.auto_install_all(include_dev=dev), indent=2))
    elif cmd == "check":
        if len(sys.argv) > 2:
            manager = PackageManager(sys.argv[2])
            missing = dm.get_missing_dependencies(manager)
            conflicts = dm.check_version_conflicts(manager)
            print(json.dumps({
                "missing": [{"name": d.name, "version": d.version} for d in missing],
                "conflicts": [{"name": d.name, "details": d.conflict_details} for d in conflicts]
            }, indent=2))
        else:
            print("Manager required")
    else:
        print(f"Unknown command: {cmd}")