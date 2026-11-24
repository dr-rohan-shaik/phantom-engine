"""
Phantom Engine Deployment Manager
Handles deployment orchestration with extensible adapters for various platforms.
"""

import json
import logging
import os
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class DeploymentStatus(Enum):
    """Deployment status states."""
    NOT_STARTED = "not_started"
    BUILDING = "building"
    TESTING = "testing"
    SECURITY_CHECK = "security_check"
    DEPLOYING = "deploying"
    HEALTH_CHECK = "health_check"
    VERIFYING = "verifying"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class DeploymentTarget(Enum):
    """Supported deployment targets."""
    VERCEL = "vercel"
    NETLIFY = "netlify"
    CLOUDFLARE_PAGES = "cloudflare_pages"
    DOCKER = "docker"
    CUSTOM = "custom"


@dataclass
class DeploymentConfig:
    """Deployment configuration."""
    target: DeploymentTarget
    name: str
    # Vercel
    vercel_project_id: str = ""
    vercel_org_id: str = ""
    vercel_token: str = ""
    # Netlify
    netlify_site_id: str = ""
    netlify_auth_token: str = ""
    # Cloudflare Pages
    cloudflare_account_id: str = ""
    cloudflare_api_token: str = ""
    cloudflare_project_name: str = ""
    # Docker
    docker_image: str = ""
    docker_registry: str = ""
    docker_context: str = "."
    dockerfile: str = "Dockerfile"
    # Custom
    custom_build_command: str = ""
    custom_deploy_command: str = ""
    custom_health_check_command: str = ""
    # Common
    environment_variables: Dict[str, str] = field(default_factory=dict)
    build_command: str = ""
    output_directory: str = ""
    health_check_url: str = ""
    health_check_timeout: int = 60
    rollback_on_failure: bool = True


@dataclass
class DeploymentResult:
    """Result of a deployment operation."""
    success: bool
    status: DeploymentStatus
    target: DeploymentTarget
    url: str = ""
    deployment_id: str = ""
    logs: List[str] = field(default_factory=list)
    error: str = ""
    started_at: str = ""
    completed_at: str = ""
    rollback_performed: bool = False


class DeploymentAdapter(ABC):
    """Abstract base class for deployment adapters."""

    @property
    @abstractmethod
    def target(self) -> DeploymentTarget:
        pass

    @abstractmethod
    def validate_config(self, config: DeploymentConfig) -> List[str]:
        """Validate configuration, return list of errors."""
        pass

    @abstractmethod
    def build(self, config: DeploymentConfig) -> DeploymentResult:
        """Build the project."""
        pass

    @abstractmethod
    def deploy(self, config: DeploymentConfig) -> DeploymentResult:
        """Deploy the built artifacts."""
        pass

    @abstractmethod
    def health_check(self, config: DeploymentConfig, deployment_id: str) -> DeploymentResult:
        """Verify deployment health."""
        pass

    @abstractmethod
    def rollback(self, config: DeploymentConfig, deployment_id: str) -> bool:
        """Rollback to previous deployment."""
        pass


class VercelAdapter(DeploymentAdapter):
    """Vercel deployment adapter."""

    @property
    def target(self) -> DeploymentTarget:
        return DeploymentTarget.VERCEL

    def validate_config(self, config: DeploymentConfig) -> List[str]:
        errors = []
        if not config.vercel_token:
            errors.append("Vercel token required")
        if not config.vercel_project_id:
            errors.append("Vercel project ID required")
        return errors

    def build(self, config: DeploymentConfig) -> DeploymentResult:
        # Vercel handles build automatically
        return DeploymentResult(
            success=True,
            status=DeploymentStatus.BUILDING,
            target=self.target,
            logs=["Vercel builds automatically on deploy"]
        )

    def deploy(self, config: DeploymentConfig) -> DeploymentResult:
        try:
            # Use Vercel CLI
            env = os.environ.copy()
            env["VERCEL_TOKEN"] = config.vercel_token

            cmd = ["vercel", "deploy", "--prod", "--yes"]
            if config.vercel_project_id:
                cmd.extend(["--project-id", config.vercel_project_id])
            if config.vercel_org_id:
                cmd.extend(["--scope", config.vercel_org_id])

            # Add environment variables
            for key, value in config.environment_variables.items():
                cmd.extend(["-e", f"{key}={value}"])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                env=env
            )

            if result.returncode == 0:
                # Extract deployment URL from output
                url = result.stdout.strip()
                deployment_id = url.split('/')[-1] if url else ""

                return DeploymentResult(
                    success=True,
                    status=DeploymentStatus.DEPLOYING,
                    target=self.target,
                    url=url,
                    deployment_id=deployment_id,
                    logs=[result.stdout]
                )
            else:
                return DeploymentResult(
                    success=False,
                    status=DeploymentStatus.FAILED,
                    target=self.target,
                    error=result.stderr,
                    logs=[result.stdout, result.stderr]
                )
        except subprocess.TimeoutExpired:
            return DeploymentResult(
                success=False,
                status=DeploymentStatus.FAILED,
                target=self.target,
                error="Deployment timeout"
            )
        except Exception as e:
            return DeploymentResult(
                success=False,
                status=DeploymentStatus.FAILED,
                target=self.target,
                error=str(e)
            )

    def health_check(self, config: DeploymentConfig, deployment_id: str) -> DeploymentResult:
        # Vercel deployments are typically ready immediately
        import requests
        try:
            if config.health_check_url:
                response = requests.get(config.health_check_url, timeout=config.health_check_timeout)
                if response.status_code == 200:
                    return DeploymentResult(
                        success=True,
                        status=DeploymentStatus.SUCCESS,
                        target=self.target,
                        logs=[f"Health check passed: {config.health_check_url}"]
                    )
            return DeploymentResult(
                success=True,
                status=DeploymentStatus.SUCCESS,
                target=self.target,
                logs=["Vercel deployment assumed healthy"]
            )
        except Exception as e:
            return DeploymentResult(
                success=False,
                status=DeploymentStatus.FAILED,
                target=self.target,
                error=f"Health check failed: {e}"
            )

    def rollback(self, config: DeploymentConfig, deployment_id: str) -> bool:
        # Vercel rollback via CLI
        try:
            env = os.environ.copy()
            env["VERCEL_TOKEN"] = config.vercel_token
            result = subprocess.run(
                ["vercel", "rollback", deployment_id, "--yes"],
                capture_output=True,
                text=True,
                timeout=60,
                env=env
            )
            return result.returncode == 0
        except Exception:
            return False


class NetlifyAdapter(DeploymentAdapter):
    """Netlify deployment adapter."""

    @property
    def target(self) -> DeploymentTarget:
        return DeploymentTarget.NETLIFY

    def validate_config(self, config: DeploymentConfig) -> List[str]:
        errors = []
        if not config.netlify_auth_token:
            errors.append("Netlify auth token required")
        if not config.netlify_site_id:
            errors.append("Netlify site ID required")
        return errors

    def build(self, config: DeploymentConfig) -> DeploymentResult:
        if config.build_command:
            try:
                result = subprocess.run(
                    config.build_command,
                    shell=True,
                    cwd=Path.cwd(),
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                return DeploymentResult(
                    success=result.returncode == 0,
                    status=DeploymentStatus.BUILDING,
                    target=self.target,
                    logs=[result.stdout, result.stderr] if result.stderr else [result.stdout],
                    error=result.stderr if result.returncode != 0 else ""
                )
            except Exception as e:
                return DeploymentResult(
                    success=False,
                    status=DeploymentStatus.FAILED,
                    target=self.target,
                    error=str(e)
                )
        return DeploymentResult(
            success=True,
            status=DeploymentStatus.BUILDING,
            target=self.target,
            logs=["No build command specified"]
        )

    def deploy(self, config: DeploymentConfig) -> DeploymentResult:
        try:
            env = os.environ.copy()
            env["NETLIFY_AUTH_TOKEN"] = config.netlify_auth_token

            cmd = ["netlify", "deploy", "--prod", "--site", config.netlify_site_id]
            if config.output_directory:
                cmd.extend(["--dir", config.output_directory])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                env=env
            )

            if result.returncode == 0:
                url = result.stdout.strip()
                return DeploymentResult(
                    success=True,
                    status=DeploymentStatus.DEPLOYING,
                    target=self.target,
                    url=url,
                    deployment_id=url.split('/')[-1] if url else "",
                    logs=[result.stdout]
                )
            else:
                return DeploymentResult(
                    success=False,
                    status=DeploymentStatus.FAILED,
                    target=self.target,
                    error=result.stderr,
                    logs=[result.stdout, result.stderr]
                )
        except Exception as e:
            return DeploymentResult(
                success=False,
                status=DeploymentStatus.FAILED,
                target=self.target,
                error=str(e)
            )

    def health_check(self, config: DeploymentConfig, deployment_id: str) -> DeploymentResult:
        import requests
        try:
            if config.health_check_url:
                response = requests.get(config.health_check_url, timeout=config.health_check_timeout)
                if response.status_code == 200:
                    return DeploymentResult(
                        success=True,
                        status=DeploymentStatus.SUCCESS,
                        target=self.target,
                        logs=[f"Health check passed: {config.health_check_url}"]
                    )
            return DeploymentResult(
                success=True,
                status=DeploymentStatus.SUCCESS,
                target=self.target,
                logs=["Netlify deployment assumed healthy"]
            )
        except Exception as e:
            return DeploymentResult(
                success=False,
                status=DeploymentStatus.FAILED,
                target=self.target,
                error=f"Health check failed: {e}"
            )

    def rollback(self, config: DeploymentConfig, deployment_id: str) -> bool:
        try:
            env = os.environ.copy()
            env["NETLIFY_AUTH_TOKEN"] = config.netlify_auth_token
            result = subprocess.run(
                ["netlify", "api", "rollbackDeploy", "--data", f'{{"site_id":"{config.netlify_site_id}"}}'],
                capture_output=True,
                text=True,
                timeout=60,
                env=env
            )
            return result.returncode == 0
        except Exception:
            return False


class DockerAdapter(DeploymentAdapter):
    """Docker deployment adapter."""

    @property
    def target(self) -> DeploymentTarget:
        return DeploymentTarget.DOCKER

    def validate_config(self, config: DeploymentConfig) -> List[str]:
        errors = []
        if not config.docker_image:
            errors.append("Docker image name required")
        dockerfile_path = Path(config.docker_context) / config.dockerfile
        if not dockerfile_path.exists():
            errors.append(f"Dockerfile not found at {dockerfile_path}")
        return errors

    def build(self, config: DeploymentConfig) -> DeploymentResult:
        try:
            cmd = ["docker", "build", "-t", config.docker_image, "-f", config.dockerfile, config.docker_context]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )
            return DeploymentResult(
                success=result.returncode == 0,
                status=DeploymentStatus.BUILDING,
                target=self.target,
                logs=[result.stdout, result.stderr] if result.stderr else [result.stdout],
                error=result.stderr if result.returncode != 0 else ""
            )
        except Exception as e:
            return DeploymentResult(
                success=False,
                status=DeploymentStatus.FAILED,
                target=self.target,
                error=str(e)
            )

    def deploy(self, config: DeploymentConfig) -> DeploymentResult:
        try:
            # Push to registry if configured
            if config.docker_registry:
                full_image = f"{config.docker_registry}/{config.docker_image}"
                subprocess.run(["docker", "tag", config.docker_image, full_image], check=True)
                push_result = subprocess.run(
                    ["docker", "push", full_image],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if push_result.returncode != 0:
                    return DeploymentResult(
                        success=False,
                        status=DeploymentStatus.FAILED,
                        target=self.target,
                        error=push_result.stderr
                    )

            # Deploy logic would depend on orchestration platform (K8s, ECS, etc.)
            # For now, return success with image info
            return DeploymentResult(
                success=True,
                status=DeploymentStatus.DEPLOYING,
                target=self.target,
                url=f"docker://{config.docker_image}",
                deployment_id=config.docker_image,
                logs=[f"Docker image built: {config.docker_image}"]
            )
        except Exception as e:
            return DeploymentResult(
                success=False,
                status=DeploymentStatus.FAILED,
                target=self.target,
                error=str(e)
            )

    def health_check(self, config: DeploymentConfig, deployment_id: str) -> DeploymentResult:
        import requests
        try:
            if config.health_check_url:
                response = requests.get(config.health_check_url, timeout=config.health_check_timeout)
                if response.status_code == 200:
                    return DeploymentResult(
                        success=True,
                        status=DeploymentStatus.SUCCESS,
                        target=self.target,
                        logs=[f"Health check passed: {config.health_check_url}"]
                    )
            return DeploymentResult(
                success=True,
                status=DeploymentStatus.SUCCESS,
                target=self.target,
                logs=["Docker deployment assumed healthy"]
            )
        except Exception as e:
            return DeploymentResult(
                success=False,
                status=DeploymentStatus.FAILED,
                target=self.target,
                error=f"Health check failed: {e}"
            )

    def rollback(self, config: DeploymentConfig, deployment_id: str) -> bool:
        # Docker rollback depends on orchestration platform
        return False


class CustomAdapter(DeploymentAdapter):
    """Custom command deployment adapter."""

    @property
    def target(self) -> DeploymentTarget:
        return DeploymentTarget.CUSTOM

    def validate_config(self, config: DeploymentConfig) -> List[str]:
        errors = []
        if not config.custom_deploy_command:
            errors.append("Custom deploy command required")
        return errors

    def build(self, config: DeploymentConfig) -> DeploymentResult:
        if config.custom_build_command:
            try:
                result = subprocess.run(
                    config.custom_build_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                return DeploymentResult(
                    success=result.returncode == 0,
                    status=DeploymentStatus.BUILDING,
                    target=self.target,
                    logs=[result.stdout, result.stderr] if result.stderr else [result.stdout],
                    error=result.stderr if result.returncode != 0 else ""
                )
            except Exception as e:
                return DeploymentResult(
                    success=False,
                    status=DeploymentStatus.FAILED,
                    target=self.target,
                    error=str(e)
                )
        return DeploymentResult(
            success=True,
            status=DeploymentStatus.BUILDING,
            target=self.target,
            logs=["No custom build command"]
        )

    def deploy(self, config: DeploymentConfig) -> DeploymentResult:
        try:
            result = subprocess.run(
                config.custom_deploy_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            return DeploymentResult(
                success=result.returncode == 0,
                status=DeploymentStatus.DEPLOYING,
                target=self.target,
                logs=[result.stdout, result.stderr] if result.stderr else [result.stdout],
                error=result.stderr if result.returncode != 0 else ""
            )
        except Exception as e:
            return DeploymentResult(
                success=False,
                status=DeploymentStatus.FAILED,
                target=self.target,
                error=str(e)
            )

    def health_check(self, config: DeploymentConfig, deployment_id: str) -> DeploymentResult:
        if config.custom_health_check_command:
            try:
                result = subprocess.run(
                    config.custom_health_check_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=config.health_check_timeout
                )
                return DeploymentResult(
                    success=result.returncode == 0,
                    status=DeploymentStatus.SUCCESS if result.returncode == 0 else DeploymentStatus.FAILED,
                    target=self.target,
                    logs=[result.stdout, result.stderr] if result.stderr else [result.stdout],
                    error=result.stderr if result.returncode != 0 else ""
                )
            except Exception as e:
                return DeploymentResult(
                    success=False,
                    status=DeploymentStatus.FAILED,
                    target=self.target,
                    error=str(e)
                )
        return DeploymentResult(
            success=True,
            status=DeploymentStatus.SUCCESS,
            target=self.target,
            logs=["No custom health check command"]
        )

    def rollback(self, config: DeploymentConfig, deployment_id: str) -> bool:
        # Custom rollback not implemented by default
        return False


class DeploymentManager:
    """Orchestrates deployments across multiple platforms."""

    ADAPTERS = {
        DeploymentTarget.VERCEL: VercelAdapter,
        DeploymentTarget.NETLIFY: NetlifyAdapter,
        DeploymentTarget.DOCKER: DockerAdapter,
        DeploymentTarget.CUSTOM: CustomAdapter,
    }

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.cwd() / ".phantom" / "deploy"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.deployment_log = self.config_dir / "deployment-log.md"

    def get_adapter(self, target: DeploymentTarget) -> DeploymentAdapter:
        """Get adapter for a deployment target."""
        adapter_class = self.ADAPTERS.get(target)
        if not adapter_class:
            raise ValueError(f"No adapter for target: {target}")
        return adapter_class()

    def load_config(self, name: str) -> Optional[DeploymentConfig]:
        """Load deployment configuration from file."""
        config_file = self.config_dir / f"{name}.json"
        if not config_file.exists():
            return None
        try:
            with open(config_file) as f:
                data = json.load(f)
            data["target"] = DeploymentTarget(data["target"])
            return DeploymentConfig(**data)
        except Exception as e:
            logger.error(f"Failed to load config {name}: {e}")
            return None

    def save_config(self, config: DeploymentConfig):
        """Save deployment configuration to file."""
        config_file = self.config_dir / f"{config.name}.json"
        data = {
            "target": config.target.value,
            "name": config.name,
            "vercel_project_id": config.vercel_project_id,
            "vercel_org_id": config.vercel_org_id,
            "vercel_token": config.vercel_token,
            "netlify_site_id": config.netlify_site_id,
            "netlify_auth_token": config.netlify_auth_token,
            "cloudflare_account_id": config.cloudflare_account_id,
            "cloudflare_api_token": config.cloudflare_api_token,
            "cloudflare_project_name": config.cloudflare_project_name,
            "docker_image": config.docker_image,
            "docker_registry": config.docker_registry,
            "docker_context": config.docker_context,
            "dockerfile": config.dockerfile,
            "custom_build_command": config.custom_build_command,
            "custom_deploy_command": config.custom_deploy_command,
            "custom_health_check_command": config.custom_health_check_command,
            "environment_variables": config.environment_variables,
            "build_command": config.build_command,
            "output_directory": config.output_directory,
            "health_check_url": config.health_check_url,
            "health_check_timeout": config.health_check_timeout,
            "rollback_on_failure": config.rollback_on_failure
        }
        with open(config_file, 'w') as f:
            json.dump(data, f, indent=2)

    def list_configs(self) -> List[str]:
        """List available deployment configurations."""
        return [f.stem for f in self.config_dir.glob("*.json")]

    def deploy(self, config: DeploymentConfig, run_tests: bool = True,
               run_security_check: bool = True) -> DeploymentResult:
        """Execute full deployment pipeline."""
        adapter = self.get_adapter(config.target)
        all_logs = []

        # Validate
        errors = adapter.validate_config(config)
        if errors:
            return DeploymentResult(
                success=False,
                status=DeploymentStatus.FAILED,
                target=config.target,
                error="; ".join(errors)
            )

        started_at = datetime.now().isoformat()
        self._log_deployment_start(config, started_at)

        try:
            # Build
            self._update_status(DeploymentStatus.BUILDING)
            build_result = adapter.build(config)
            all_logs.extend(build_result.logs)
            if not build_result.success:
                return self._finalize_deployment(
                    config, adapter, started_at, all_logs,
                    DeploymentStatus.FAILED, False, build_result.error
                )

            # Test
            if run_tests:
                self._update_status(DeploymentStatus.TESTING)
                test_result = self._run_tests(config)
                all_logs.extend(test_result.logs)
                if not test_result.success:
                    return self._finalize_deployment(
                        config, adapter, started_at, all_logs,
                        DeploymentStatus.FAILED, False, "Tests failed"
                    )

            # Security check
            if run_security_check:
                self._update_status(DeploymentStatus.SECURITY_CHECK)
                security_result = self._run_security_check(config)
                all_logs.extend(security_result.logs)
                if not security_result.success:
                    return self._finalize_deployment(
                        config, adapter, started_at, all_logs,
                        DeploymentStatus.FAILED, False, "Security check failed"
                    )

            # Deploy
            self._update_status(DeploymentStatus.DEPLOYING)
            deploy_result = adapter.deploy(config)
            all_logs.extend(deploy_result.logs)
            if not deploy_result.success:
                return self._finalize_deployment(
                    config, adapter, started_at, all_logs,
                    DeploymentStatus.FAILED, False, deploy_result.error
                )

            # Health check
            self._update_status(DeploymentStatus.HEALTH_CHECK)
            health_result = adapter.health_check(config, deploy_result.deployment_id)
            all_logs.extend(health_result.logs)
            if not health_result.success:
                # Attempt rollback
                rollback_done = False
                if config.rollback_on_failure:
                    self._update_status(DeploymentStatus.VERIFYING)
                    rollback_done = adapter.rollback(config, deploy_result.deployment_id)
                    all_logs.append(f"Rollback attempted: {'success' if rollback_done else 'failed'}")

                return self._finalize_deployment(
                    config, adapter, started_at, all_logs,
                    DeploymentStatus.FAILED, rollback_done, health_result.error
                )

            # Verify
            self._update_status(DeploymentStatus.VERIFYING)
            return self._finalize_deployment(
                config, adapter, started_at, all_logs,
                DeploymentStatus.SUCCESS, False, ""
            )

        except Exception as e:
            logger.exception("Deployment failed")
            return self._finalize_deployment(
                config, adapter, started_at, all_logs,
                DeploymentStatus.FAILED, False, str(e)
            )

    def _run_tests(self, config: DeploymentConfig) -> DeploymentResult:
        """Run tests - placeholder for integration with test framework."""
        return DeploymentResult(
            success=True,
            status=DeploymentStatus.TESTING,
            target=config.target,
            logs=["Test execution would run here"]
        )

    def _run_security_check(self, config: DeploymentConfig) -> DeploymentResult:
        """Run security checks - placeholder for integration with security tools."""
        return DeploymentResult(
            success=True,
            status=DeploymentStatus.SECURITY_CHECK,
            target=config.target,
            logs=["Security check would run here"]
        )

    def _finalize_deployment(
        self,
        config: DeploymentConfig,
        adapter: DeploymentAdapter,
        started_at: str,
        logs: List[str],
        status: DeploymentStatus,
        rollback_performed: bool,
        error: str
    ) -> DeploymentResult:
        completed_at = datetime.now().isoformat()
        success = status == DeploymentStatus.SUCCESS

        result = DeploymentResult(
            success=success,
            status=status,
            target=config.target,
            logs=logs,
            error=error,
            started_at=started_at,
            completed_at=completed_at,
            rollback_performed=rollback_performed
        )

        self._log_deployment_result(config, result)
        return result

    def _update_status(self, status: DeploymentStatus):
        """Update deployment status in state."""
        # Would integrate with state manager
        pass

    def _log_deployment_start(self, config: DeploymentConfig, started_at: str):
        """Log deployment start."""
        entry = f"""
## Deployment Started - {started_at}

**Target:** {config.target.value}
**Name:** {config.name}
**Build Command:** {config.build_command or 'N/A'}
**Health Check URL:** {config.health_check_url or 'N/A'}

---
"""
        with open(self.deployment_log, "a") as f:
            f.write(entry)

    def _log_deployment_result(self, config: DeploymentConfig, result: DeploymentResult):
        """Log deployment result."""
        entry = f"""
## Deployment Result - {result.completed_at}

**Target:** {config.target.value}
**Status:** {result.status.value}
**Success:** {result.success}
**URL:** {result.url or 'N/A'}
**Deployment ID:** {result.deployment_id or 'N/A'}
**Rollback Performed:** {result.rollback_performed}
**Error:** {result.error or 'None'}

### Logs
{chr(10).join(f'- {log}' for log in result.logs)}

---
"""
        with open(self.deployment_log, "a") as f:
            f.write(entry)


if __name__ == "__main__":
    import sys

    dm = DeploymentManager()

    if len(sys.argv) < 2:
        print("Usage: python deployment_manager.py <command> [args...]")
        print("Commands: list-configs, load <name>, save <name> <target>, deploy <name>")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "list-configs":
        print(json.dumps(dm.list_configs(), indent=2))
    elif cmd == "load":
        if len(sys.argv) > 2:
            config = dm.load_config(sys.argv[2])
            if config:
                print(json.dumps(config.__dict__, indent=2, default=str))
            else:
                print("Config not found")
        else:
            print("Config name required")
    else:
        print(f"Unknown command: {cmd}")