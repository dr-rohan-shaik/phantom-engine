"""
Tests for Phantom Engine Deployment Manager
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from scripts.deployment_manager import (
    DeploymentManager,
    DeploymentConfig,
    DeploymentTarget,
    DeploymentStatus,
    DeploymentResult,
    VercelAdapter,
    NetlifyAdapter,
    DockerAdapter,
    CustomAdapter
)


class TestDeploymentConfig:
    """Test DeploymentConfig dataclass."""

    def test_creation(self):
        """Test config creation."""
        config = DeploymentConfig(
            target=DeploymentTarget.VERCEL,
            name="production",
            vercel_project_id="prj_123",
            vercel_token="token_123",
            health_check_url="https://app.example.com/health"
        )

        assert config.target == DeploymentTarget.VERCEL
        assert config.name == "production"
        assert config.vercel_project_id == "prj_123"
        assert config.health_check_url == "https://app.example.com/health"

    def test_defaults(self):
        """Test default values."""
        config = DeploymentConfig(
            target=DeploymentTarget.DOCKER,
            name="docker-deploy",
            docker_image="myapp:latest"
        )

        assert config.docker_context == "."
        assert config.dockerfile == "Dockerfile"
        assert config.health_check_timeout == 60
        assert config.rollback_on_failure is True


class TestDeploymentResult:
    """Test DeploymentResult dataclass."""

    def test_creation(self):
        """Test result creation."""
        result = DeploymentResult(
            success=True,
            status=DeploymentStatus.SUCCESS,
            target=DeploymentTarget.VERCEL,
            url="https://app.vercel.app",
            deployment_id="dpl_123"
        )

        assert result.success is True
        assert result.status == DeploymentStatus.SUCCESS
        assert result.url == "https://app.vercel.app"


class TestVercelAdapter:
    """Test VercelAdapter."""

    @pytest.fixture
    def adapter(self):
        return VercelAdapter()

    @pytest.fixture
    def config(self):
        return DeploymentConfig(
            target=DeploymentTarget.VERCEL,
            name="test",
            vercel_project_id="prj_123",
            vercel_token="token_123"
        )

    def test_target(self, adapter):
        assert adapter.target == DeploymentTarget.VERCEL

    def test_validate_config_success(self, adapter, config):
        errors = adapter.validate_config(config)
        assert errors == []

    def test_validate_config_missing_token(self, adapter):
        config = DeploymentConfig(
            target=DeploymentTarget.VERCEL,
            name="test",
            vercel_project_id="prj_123"
        )
        errors = adapter.validate_config(config)
        assert "Vercel token required" in errors

    def test_validate_config_missing_project_id(self, adapter):
        config = DeploymentConfig(
            target=DeploymentTarget.VERCEL,
            name="test",
            vercel_token="token_123"
        )
        errors = adapter.validate_config(config)
        assert "Vercel project ID required" in errors

    @patch("scripts.deployment_manager.subprocess.run")
    def test_deploy_success(self, mock_run, adapter, config):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="https://app.vercel.app\n"
        )

        result = adapter.deploy(config)

        assert result.success is True
        assert result.url == "https://app.vercel.app"
        assert result.deployment_id == "app.vercel.app"

    @patch("scripts.deployment_manager.subprocess.run")
    def test_deploy_failure(self, mock_run, adapter, config):
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="Deployment failed"
        )

        result = adapter.deploy(config)

        assert result.success is False
        assert "Deployment failed" in result.error


class TestNetlifyAdapter:
    """Test NetlifyAdapter."""

    @pytest.fixture
    def adapter(self):
        return NetlifyAdapter()

    @pytest.fixture
    def config(self):
        return DeploymentConfig(
            target=DeploymentTarget.NETLIFY,
            name="test",
            netlify_site_id="site_123",
            netlify_auth_token="token_123",
            output_directory="dist"
        )

    def test_target(self, adapter):
        assert adapter.target == DeploymentTarget.NETLIFY

    def test_validate_config(self, adapter, config):
        errors = adapter.validate_config(config)
        assert errors == []

    @patch("scripts.deployment_manager.subprocess.run")
    def test_build_with_command(self, mock_run, adapter, config):
        config.build_command = "npm run build"
        mock_run.return_value = MagicMock(returncode=0, stdout="Build complete")

        result = adapter.build(config)

        assert result.success is True

    @patch("scripts.deployment_manager.subprocess.run")
    def test_deploy(self, mock_run, adapter, config):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="https://site.netlify.app\n"
        )

        result = adapter.deploy(config)

        assert result.success is True
        assert "netlify.app" in result.url


class TestDockerAdapter:
    """Test DockerAdapter."""

    @pytest.fixture
    def adapter(self):
        return DockerAdapter()

    @pytest.fixture
    def config(self):
        return DeploymentConfig(
            target=DeploymentTarget.DOCKER,
            name="test",
            docker_image="myapp:latest",
            dockerfile="Dockerfile",
            docker_context="."
        )

    def test_target(self, adapter):
        assert adapter.target == DeploymentTarget.DOCKER

    def test_validate_config_missing_image(self, adapter):
        config = DeploymentConfig(
            target=DeploymentTarget.DOCKER,
            name="test",
            dockerfile="Dockerfile"
        )
        errors = adapter.validate_config(config)
        assert "Docker image name required" in errors

    @patch("scripts.deployment_manager.subprocess.run")
    @patch("pathlib.Path.exists")
    def test_build(self, mock_exists, mock_run, adapter, config):
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="Built image")

        result = adapter.build(config)

        assert result.success is True
        args = mock_run.call_args[0][0]
        assert "docker" in args
        assert "build" in args
        assert "myapp:latest" in args


class TestCustomAdapter:
    """Test CustomAdapter."""

    @pytest.fixture
    def adapter(self):
        return CustomAdapter()

    @pytest.fixture
    def config(self):
        return DeploymentConfig(
            target=DeploymentTarget.CUSTOM,
            name="test",
            custom_deploy_command="./deploy.sh",
            custom_build_command="./build.sh",
            custom_health_check_command="./health.sh"
        )

    def test_target(self, adapter):
        assert adapter.target == DeploymentTarget.CUSTOM

    def test_validate_config_missing_deploy(self, adapter):
        config = DeploymentConfig(
            target=DeploymentTarget.CUSTOM,
            name="test",
            custom_build_command="./build.sh"
        )
        errors = adapter.validate_config(config)
        assert "Custom deploy command required" in errors

    @patch("scripts.deployment_manager.subprocess.run")
    def test_deploy(self, mock_run, adapter, config):
        mock_run.return_value = MagicMock(returncode=0, stdout="Deployed")

        result = adapter.deploy(config)

        assert result.success is True

    @patch("scripts.deployment_manager.subprocess.run")
    def test_health_check(self, mock_run, adapter, config):
        mock_run.return_value = MagicMock(returncode=0, stdout="OK")

        result = adapter.health_check(config, "deployment-1")

        assert result.success is True


class TestDeploymentManager:
    """Test DeploymentManager."""

    @pytest.fixture
    def dep_manager(self, tmp_path):
        return DeploymentManager(config_dir=tmp_path / ".phantom" / "deploy")

    def test_get_adapter_vercel(self, dep_manager):
        adapter = dep_manager.get_adapter(DeploymentTarget.VERCEL)
        assert isinstance(adapter, VercelAdapter)

    def test_get_adapter_netlify(self, dep_manager):
        adapter = dep_manager.get_adapter(DeploymentTarget.NETLIFY)
        assert isinstance(adapter, NetlifyAdapter)

    def test_get_adapter_docker(self, dep_manager):
        adapter = dep_manager.get_adapter(DeploymentTarget.DOCKER)
        assert isinstance(adapter, DockerAdapter)

    def test_get_adapter_custom(self, dep_manager):
        adapter = dep_manager.get_adapter(DeploymentTarget.CUSTOM)
        assert isinstance(adapter, CustomAdapter)

    def test_get_adapter_unknown(self, dep_manager):
        with pytest.raises(ValueError):
            dep_manager.get_adapter(DeploymentTarget.CLOUDFLARE_PAGES)

    def test_save_and_load_config(self, dep_manager, tmp_path):
        config = DeploymentConfig(
            target=DeploymentTarget.VERCEL,
            name="production",
            vercel_project_id="prj_123",
            vercel_token="token_123"
        )

        dep_manager.save_config(config)
        loaded = dep_manager.load_config("production")

        assert loaded is not None
        assert loaded.name == "production"
        assert loaded.target == DeploymentTarget.VERCEL
        assert loaded.vercel_project_id == "prj_123"

    def test_load_nonexistent_config(self, dep_manager):
        config = dep_manager.load_config("nonexistent")
        assert config is None

    def test_list_configs(self, dep_manager):
        config_dir = dep_manager.config_dir
        config_dir.mkdir(parents=True, exist_ok=True)

        # Create config files
        (config_dir / "prod.json").write_text("{}")
        (config_dir / "staging.json").write_text("{}")

        configs = dep_manager.list_configs()
        assert "prod" in configs
        assert "staging" in configs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])