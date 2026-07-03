"""Kubectl executor.

A small, reusable utility that safely runs ``kubectl`` commands via
``subprocess`` and returns a structured result. Every inspector in this package
goes through this executor so command execution, error handling, and logging
live in one place.

This intentionally shells out to ``kubectl`` (not the Kubernetes Python SDK).
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from typing import Any

from app.core.config import Settings, get_settings
from app.core.logging import logger


@dataclass
class KubectlResult:
    """Structured result of a single kubectl invocation."""

    command: list[str]
    success: bool
    returncode: int
    stdout: str = ""
    stderr: str = ""
    error: str | None = None  # populated when kubectl could not run at all

    def json(self) -> Any:
        """Parse stdout as JSON. Returns ``None`` if it is not valid JSON."""
        if not self.stdout.strip():
            return None
        try:
            return json.loads(self.stdout)
        except json.JSONDecodeError:
            logger.warning("Could not parse kubectl output as JSON: {cmd}", cmd=self.command)
            return None


@dataclass
class KubectlExecutor:
    """Runs kubectl commands with consistent settings and logging."""

    settings: Settings = field(default_factory=get_settings)

    @property
    def binary(self) -> str:
        return self.settings.kubectl_binary

    @property
    def timeout(self) -> int:
        return self.settings.kubectl_timeout_seconds

    def _env(self) -> dict[str, str]:
        """Build the environment, honoring KUBECONFIG_PATH when provided."""
        env = os.environ.copy()
        if self.settings.kubeconfig_path:
            env["KUBECONFIG"] = self.settings.kubeconfig_path
        return env

    def run(self, args: list[str]) -> KubectlResult:
        """Run ``kubectl <args>`` and capture the outcome.

        Failures (missing binary, non-zero exit, timeouts) are handled
        gracefully and reported in the returned :class:`KubectlResult` rather
        than raising.
        """
        command = [self.binary, *args]
        logger.info("Running kubectl command: {cmd}", cmd=" ".join(command))

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=self._env(),
                check=False,
            )
        except FileNotFoundError:
            message = f"kubectl binary not found: '{self.binary}'"
            logger.error(message)
            return KubectlResult(command=command, success=False, returncode=-1, error=message)
        except subprocess.TimeoutExpired:
            message = f"kubectl command timed out after {self.timeout}s"
            logger.error("{msg}: {cmd}", msg=message, cmd=" ".join(command))
            return KubectlResult(command=command, success=False, returncode=-1, error=message)
        except OSError as exc:  # pragma: no cover - defensive
            message = f"Failed to execute kubectl: {exc}"
            logger.error(message)
            return KubectlResult(command=command, success=False, returncode=-1, error=message)

        success = completed.returncode == 0
        if not success:
            logger.warning(
                "kubectl exited with code {code}: {err}",
                code=completed.returncode,
                err=completed.stderr.strip(),
            )

        return KubectlResult(
            command=command,
            success=success,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            error=None if success else (completed.stderr.strip() or "kubectl command failed"),
        )

    def get_json(self, args: list[str]) -> tuple[Any, KubectlResult]:
        """Run a command expected to emit JSON (adds ``-o json``).

        Returns a tuple of ``(parsed_json_or_none, result)`` so callers can both
        use the data and inspect what happened.
        """
        result = self.run([*args, "-o", "json"])
        return (result.json() if result.success else None, result)
