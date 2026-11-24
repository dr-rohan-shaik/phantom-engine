"""
Tests for Phantom Engine Dependency Manager
"""

import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from scripts.dependency_manager import (
    DependencyManager,
    PackageManager,
    DependencyInfo,
    LockFileInfo
)


class TestDependencyManager:
    """Test cases for DependencyManager."""

    @pytest.fixture
    def dep_manager(self):
        """Create DependencyManager."""
        return DependencyManager(repo_path=Path("/fake/repo"))

    def _create_mock_file(self, name: str) -> MagicMock:
        """Create a mock file with proper name attribute."""
        m = MagicMock()
        m.name = name
        return m

    def test_detect_package_managers_npm(self, dep_manager):
        """Test npm detection."""
        mock_files = [
            self._create_mock_file("package-lock.json"),
            self._create_mock_file("package.json")
        ]

        with patch.object(dep_manager, "repo_path", new_callable=MagicMock) as mock_repo:
            mock_repo.rglob.return_value = mock_files
            managers = dep_manager.detect_package_managers()

            assert PackageManager.NPM in managers
            assert len(dep_manager.lockfiles) >= 1

    def test_detect_package_managers_pnpm(self, dep_manager):
        """Test pnpm detection."""
        mock_files = [
            self._create_mock_file("pnpm-lock.yaml"),
            self._create_mock_file("package.json")
        ]

        with patch.object(dep_manager, "repo_path", new_callable=MagicMock) as mock_repo:
            mock_repo.rglob.return_value = mock_files
            managers = dep_manager.detect_package_managers()

            assert PackageManager.PNPM in managers

    def test_detect_package_managers_pip(self, dep_manager):
        """Test pip detection."""
        mock_files = [
            self._create_mock_file("requirements.txt"),
            self._create_mock_file("setup.py")
        ]

        with patch.object(dep_manager, "repo_path", new_callable=MagicMock) as mock_repo:
            mock_repo.rglob.return_value = mock_files
            managers = dep_manager.detect_package_managers()

            assert PackageManager.PIP in managers

    def test_detect_package_managers_uv(self, dep_manager):
        """Test uv detection."""
        mock_files = [
            self._create_mock_file("uv.lock"),
            self._create_mock_file("pyproject.toml")
        ]

        with patch.object(dep_manager, "repo_path", new_callable=MagicMock) as mock_repo:
            mock_repo.rglob.return_value = mock_files
            managers = dep_manager.detect_package_managers()

            assert PackageManager.UV in managers

    def test_detect_package_managers_cargo(self, dep_manager):
        """Test cargo detection."""
        mock_files = [
            self._create_mock_file("Cargo.lock"),
            self._create_mock_file("Cargo.toml")
        ]

        with patch.object(dep_manager, "repo_path", new_callable=MagicMock) as mock_repo:
            mock_repo.rglob.return_value = mock_files
            managers = dep_manager.detect_package_managers()

            assert PackageManager.CARGO in managers

    def test_detect_package_managers_go(self, dep_manager):
        """Test Go detection."""
        mock_files = [
            self._create_mock_file("go.mod"),
            self._create_mock_file("go.sum")
        ]

        with patch.object(dep_manager, "repo_path", new_callable=MagicMock) as mock_repo:
            mock_repo.rglob.return_value = mock_files
            managers = dep_manager.detect_package_managers()

            assert PackageManager.GO in managers

    def test_check_manager_available(self, dep_manager):
        """Test checking manager availability."""
        with patch("scripts.dependency_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = dep_manager.check_manager_available(PackageManager.NPM)

            assert result is True
            mock_run.assert_called_once()

    def test_check_manager_unavailable(self, dep_manager):
        """Test checking unavailable manager."""
        with patch("scripts.dependency_manager.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            result = dep_manager.check_manager_available(PackageManager.NPM)

            assert result is False

    def test_install_dependencies_npm(self, dep_manager):
        """Test npm install."""
        with patch("scripts.dependency_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result = dep_manager.install_dependencies(PackageManager.NPM)

            assert result is True
            args = mock_run.call_args[0][0]
            assert args == ["npm", "install"]

    def test_install_dependencies_pip(self, dep_manager):
        """Test pip install."""
        with patch("scripts.dependency_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            # Mock requirements.txt existence
            with patch.object(dep_manager, "repo_path", new_callable=MagicMock) as mock_repo:
                req_mock = MagicMock()
                req_mock.exists.return_value = True
                req_mock.__str__ = lambda self: "requirements.txt"
                mock_repo.__truediv__.return_value = req_mock
                result = dep_manager.install_dependencies(PackageManager.PIP)

                assert result is True
                args = mock_run.call_args[0][0]
                assert args == ["pip", "install", "-r", "requirements.txt"]

    def test_install_dependencies_uv(self, dep_manager):
        """Test uv sync."""
        with patch("scripts.dependency_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = dep_manager.install_dependencies(PackageManager.UV)

            assert result is True
            args = mock_run.call_args[0][0]
            assert args == ["uv", "sync"]

    def test_install_dependencies_cargo(self, dep_manager):
        """Test cargo build."""
        with patch("scripts.dependency_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = dep_manager.install_dependencies(PackageManager.CARGO)

            assert result is True
            args = mock_run.call_args[0][0]
            assert args == ["cargo", "build"]

    def test_run_build_npm(self, dep_manager):
        """Test npm build."""
        with patch("scripts.dependency_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            # Mock package.json with build script
            with patch.object(dep_manager, "repo_path", new_callable=MagicMock) as mock_repo:
                pkg_mock = MagicMock()
                pkg_mock.exists.return_value = True
                mock_repo.__truediv__.return_value = pkg_mock
                with patch("builtins.open", mock_open(read_data='{"scripts": {"build": "webpack"}}')):
                    result = dep_manager.run_build(PackageManager.NPM)

                    assert result is True
                    args = mock_run.call_args[0][0]
                    assert args == ["npm", "run", "build"]

    def test_run_build_no_script(self, dep_manager):
        """Test build with no build script."""
        with patch.object(dep_manager, "repo_path", new_callable=MagicMock) as mock_repo:
            pkg_mock = MagicMock()
            pkg_mock.exists.return_value = True
            mock_repo.__truediv__.return_value = pkg_mock
            with patch("builtins.open", mock_open(read_data='{"scripts": {}}')):
                result = dep_manager.run_build(PackageManager.NPM)

                assert result is True  # No build step is success

    def test_check_version_conflicts_pip(self, dep_manager):
        """Test pip version conflict checking."""
        with patch("scripts.dependency_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="package1 1.0.0 has conflict with package2 2.0.0 (incompatible)",
                stderr=""
            )

            conflicts = dep_manager.check_version_conflicts(PackageManager.PIP)

            assert len(conflicts) >= 1
            assert any("package1" in c.name for c in conflicts)

    def test_get_full_dependency_report(self, dep_manager):
        """Test full dependency report."""
        # Set up the detected managers directly since detect_package_managers is mocked
        dep_manager.detected_managers = [PackageManager.NPM]
        dep_manager.lockfiles = [LockFileInfo(
            path=Path("package-lock.json"),
            package_manager=PackageManager.NPM,
            exists=True
        )]

        with patch.object(dep_manager, "check_manager_available", return_value=True):
            with patch.object(dep_manager, "get_missing_dependencies", return_value=[]):
                with patch.object(dep_manager, "check_version_conflicts", return_value=[]):

                    report = dep_manager.get_full_dependency_report()

                    assert "detected_managers" in report
                    assert "managers" in report
                    assert "npm" in report["managers"]


class TestPackageManager:
    """Test PackageManager enum."""

    def test_values(self):
        """Test all package manager values."""
        assert PackageManager.NPM.value == "npm"
        assert PackageManager.PNPM.value == "pnpm"
        assert PackageManager.YARN.value == "yarn"
        assert PackageManager.PIP.value == "pip"
        assert PackageManager.UV.value == "uv"
        assert PackageManager.POETRY.value == "poetry"
        assert PackageManager.CARGO.value == "cargo"
        assert PackageManager.GO.value == "go"
        assert PackageManager.COMPOSER.value == "composer"
        assert PackageManager.BUNDLER.value == "bundler"


class TestDependencyInfo:
    """Test DependencyInfo dataclass."""

    def test_creation(self):
        """Test dependency info creation."""
        dep = DependencyInfo(
            name="test-package",
            version="1.0.0",
            package_manager=PackageManager.NPM,
            is_dev=True,
            is_missing=False
        )

        assert dep.name == "test-package"
        assert dep.version == "1.0.0"
        assert dep.package_manager == PackageManager.NPM
        assert dep.is_dev is True
        assert dep.is_missing is False


class TestLockFileInfo:
    """Test LockFileInfo dataclass."""

    def test_creation(self):
        """Test lockfile info creation."""
        lf = LockFileInfo(
            path=Path("package-lock.json"),
            package_manager=PackageManager.NPM,
            exists=True,
            last_modified=1234567890.0
        )

        assert lf.path == Path("package-lock.json")
        assert lf.package_manager == PackageManager.NPM
        assert lf.exists is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])