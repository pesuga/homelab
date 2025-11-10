#!/usr/bin/env python3
"""
MCP Tool: Git Workflow for Homelab Development
Enhances Claude Code with intelligent git operations and workflow automation
"""

import asyncio
import json
import os
import sys
import subprocess
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

class GitWorkflowMCP:
    """
    Intelligent git workflow tool for homelab development.
    Provides smart commit generation, branch management, and workflow automation.
    """

    def __init__(self):
        self.repo_path = Path.cwd()
        self.main_branch = "main"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from git config and environment"""
        config = {
            "pre_commit_tests": os.getenv("GIT_PRE_COMMIT_TESTS", "true").lower() == "true",
            "auto_push": os.getenv("GIT_AUTO_PUSH", "false").lower() == "true",
            "commit_template": os.getenv("GIT_COMMIT_TEMPLATE", "homelab"),
            "require_issue_link": os.getenv("GIT_REQUIRE_ISSUE_LINK", "false").lower() == "true"
        }

        # Load git config
        try:
            result = subprocess.run(
                ["git", "config", "--list"],
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )

            for line in result.stdout.strip().split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key] = value
        except Exception:
            pass

        return config

    async def get_repo_status(self) -> Dict[str, Any]:
        """
        Get comprehensive repository status and analysis
        """
        try:
            # Get basic git status
            result = subprocess.run(
                ["git", "status", "--porcelain", "--branch"],
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )

            status_lines = result.stdout.strip().split('\n')
            branch_info = status_lines[0] if status_lines else ""
            file_changes = status_lines[1:] if len(status_lines) > 1 else []

            # Parse branch info
            current_branch = self._extract_current_branch(branch_info)
            ahead_behind = self._extract_ahead_behind(branch_info)

            # Analyze file changes
            staged_files = []
            modified_files = []
            untracked_files = []
            deleted_files = []

            for change in file_changes:
                if not change.strip():
                    continue

                status = change[:2]
                file_path = change[3:]

                if status[0] in ['A', 'M', 'D', 'R', 'C']:
                    staged_files.append({
                        "path": file_path,
                        "status": status[0],
                        "status_text": self._get_status_text(status[0])
                    })

                if status[1] in ['M', 'D']:
                    modified_files.append({
                        "path": file_path,
                        "status": status[1],
                        "status_text": self._get_status_text(status[1])
                    })

                if status == "??":
                    untracked_files.append(file_path)

                if status[0] == 'D' or status[1] == 'D':
                    deleted_files.append(file_path)

            # Get recent commits
            recent_commits = await self._get_recent_commits(5)

            # Check for issues
            issues = await self._detect_repo_issues()

            return {
                "repository_path": str(self.repo_path),
                "current_branch": current_branch,
                "branch_info": {
                    "ahead_behind": ahead_behind,
                    "is_main": current_branch == self.main_branch,
                    "is_clean": len(file_changes) == 0
                },
                "files": {
                    "staged": staged_files,
                    "modified": modified_files,
                    "untracked": untracked_files,
                    "deleted": deleted_files,
                    "total_changes": len(staged_files) + len(modified_files) + len(untracked_files)
                },
                "recent_commits": recent_commits,
                "issues": issues,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "error": str(e),
                "repository_path": str(self.repo_path),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def create_feature_branch(self, feature_name: str, base_branch: str = None,
                                   issue_number: str = None) -> Dict[str, Any]:
        """
        Create a feature branch with intelligent naming and setup
        """
        try:
            # Determine base branch
            if base_branch is None:
                base_branch = self.main_branch

            # Generate branch name
            branch_name = self._generate_branch_name(feature_name, issue_number)

            # Check if branch already exists
            existing_branches = await self._get_branches()
            if branch_name in existing_branches:
                return {
                    "success": False,
                    "error": f"Branch '{branch_name}' already exists",
                    "existing_branch": True
                }

            # Ensure we're on main and up to date
            await self._run_git_command(["checkout", base_branch])
            await self._run_git_command(["pull", "origin", base_branch])

            # Create and checkout new branch
            await self._run_git_command(["checkout", "-b", branch_name])

            # Get branch info
            new_branch_info = await self._get_branch_info(branch_name)

            return {
                "success": True,
                "branch_name": branch_name,
                "base_branch": base_branch,
                "feature_name": feature_name,
                "issue_number": issue_number,
                "branch_info": new_branch_info,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "feature_name": feature_name,
                "timestamp": datetime.utcnow().isoformat()
            }

    async def smart_commit(self, message: str = None, run_tests: bool = None,
                          auto_push: bool = None) -> Dict[str, Any]:
        """
        Smart commit with automatic message generation and pre-commit checks
        """
        try:
            # Get current status
            status = await self.get_repo_status()

            if status["files"]["total_changes"] == 0:
                return {
                    "success": False,
                    "error": "No changes to commit",
                    "status": "no_changes"
                }

            # Run tests if requested
            test_results = None
            if (run_tests is True) or (run_tests is None and self.config["pre_commit_tests"]):
                test_results = await self._run_pre_commit_tests()

                if not test_results["passed"]:
                    return {
                        "success": False,
                        "error": "Pre-commit tests failed",
                        "test_results": test_results,
                        "status": "tests_failed"
                    }

            # Generate commit message if not provided
            if message is None:
                message = await self._generate_commit_message(status)

            # Validate commit message
            validation = await self._validate_commit_message(message)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": f"Invalid commit message: {validation['error']}",
                    "validation": validation,
                    "status": "invalid_message"
                }

            # Stage files
            if status["files"]["modified"]:
                await self._run_git_command(["add", "."])

            # Create commit
            commit_result = await self._run_git_command(["commit", "-m", message])

            # Auto push if requested
            push_result = None
            if (auto_push is True) or (auto_push is None and self.config["auto_push"]):
                push_result = await self._auto_push()

            # Get commit hash
            commit_hash = await self._get_current_commit_hash()

            return {
                "success": True,
                "commit_hash": commit_hash,
                "commit_message": message,
                "files_committed": status["files"]["total_changes"],
                "test_results": test_results,
                "push_result": push_result,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def create_pull_request(self, target_branch: str = None,
                                 draft: bool = False,
                                 auto_assign: bool = True) -> Dict[str, Any]:
        """
        Create pull request with intelligent description generation
        """
        try:
            # Get current branch info
            current_status = await self.get_repo_status()
            current_branch = current_status["current_branch"]

            if current_branch == self.main_branch:
                return {
                    "success": False,
                    "error": "Cannot create pull request from main branch"
                }

            # Determine target branch
            if target_branch is None:
                target_branch = self.main_branch

            # Get commits since branching
            commits = await self._get_commits_since_branch(current_branch, target_branch)

            if not commits:
                return {
                    "success": False,
                    "error": "No commits to include in pull request"
                }

            # Generate PR title and description
            pr_title = await self._generate_pr_title(current_branch, commits)
            pr_description = await self._generate_pr_description(current_branch, commits)

            # Check if PR already exists
            existing_pr = await self._check_existing_pr(current_branch, target_branch)

            if existing_pr:
                return {
                    "success": False,
                    "error": "Pull request already exists",
                    "existing_pr": existing_pr
                }

            # Create PR using gh CLI
            pr_command = ["gh", "pr", "create", "--title", pr_title, "--body", pr_description]

            if draft:
                pr_command.append("--draft")

            if auto_assign:
                pr_command.extend(["--assignee", "@me"])

            pr_command.extend(["--base", target_branch])

            pr_result = await self._run_command(pr_command)

            # Extract PR URL from result
            pr_url = self._extract_pr_url(pr_result.stdout)

            return {
                "success": True,
                "pr_url": pr_url,
                "pr_title": pr_title,
                "target_branch": target_branch,
                "source_branch": current_branch,
                "commits_count": len(commits),
                "description_generated": True,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def analyze_code_changes(self, file_paths: List[str] = None) -> Dict[str, Any]:
        """
        Analyze code changes for impact and quality assessment
        """
        try:
            # Get changed files if not specified
            if file_paths is None:
                status = await self.get_repo_status()
                file_paths = [
                    f["path"] for f in status["files"]["staged"] + status["files"]["modified"]
                ]

            if not file_paths:
                return {
                    "success": False,
                    "error": "No files to analyze"
                }

            analysis = {
                "files": {},
                "summary": {
                    "total_files": len(file_paths),
                    "languages": {},
                    "risk_level": "low",
                    "recommendations": []
                },
                "timestamp": datetime.utcnow().isoformat()
            }

            total_lines_added = 0
            total_lines_deleted = 0

            for file_path in file_paths:
                try:
                    file_analysis = await self._analyze_file_changes(file_path)
                    analysis["files"][file_path] = file_analysis

                    # Update summary
                    language = file_analysis.get("language", "unknown")
                    analysis["summary"]["languages"][language] = \
                        analysis["summary"]["languages"].get(language, 0) + 1

                    total_lines_added += file_analysis.get("lines_added", 0)
                    total_lines_deleted += file_analysis.get("lines_deleted", 0)

                    # Assess risk
                    if file_analysis.get("risk_level") == "high":
                        analysis["summary"]["risk_level"] = "high"
                    elif file_analysis.get("risk_level") == "medium" and analysis["summary"]["risk_level"] == "low":
                        analysis["summary"]["risk_level"] = "medium"

                except Exception as e:
                    analysis["files"][file_path] = {
                        "error": str(e),
                        "analyzed": False
                    }

            analysis["summary"]["lines_added"] = total_lines_added
            analysis["summary"]["lines_deleted"] = total_lines_deleted
            analysis["summary"]["net_change"] = total_lines_added - total_lines_deleted

            # Generate recommendations
            analysis["summary"]["recommendations"] = await self._generate_change_recommendations(
                analysis["files"]
            )

            return {
                "success": True,
                "analysis": analysis,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def rollback_commit(self, commit_hash: str = None,
                              soft: bool = False) -> Dict[str, Any]:
        """
        Safely rollback commits with backup and recovery options
        """
        try:
            # Get current commit hash for backup
            current_commit = await self._get_current_commit_hash()

            # Determine commit to rollback
            if commit_hash is None:
                commit_hash = current_commit

            # Get commit info for rollback confirmation
            commit_info = await self._get_commit_info(commit_hash)

            if not commit_info:
                return {
                    "success": False,
                    "error": f"Commit {commit_hash} not found"
                }

            # Create backup branch before rollback
            backup_branch = f"backup/rollback-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            await self._run_git_command(["branch", backup_branch, current_commit])

            # Perform rollback
            if soft:
                await self._run_git_command(["reset", "--soft", commit_hash + "^"])
                rollback_type = "soft"
            else:
                await self._run_git_command(["reset", "--hard", commit_hash + "^"])
                rollback_type = "hard"

            # Get new status
            new_status = await self.get_repo_status()

            return {
                "success": True,
                "rollback_type": rollback_type,
                "rolled_back_commit": commit_hash,
                "commit_info": commit_info,
                "backup_branch": backup_branch,
                "new_status": new_status,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    # Helper methods
    def _extract_current_branch(self, branch_info: str) -> str:
        """Extract current branch from git status output"""
        match = re.search(r'## ([^\s.]+)', branch_info)
        return match.group(1) if match else "unknown"

    def _extract_ahead_behind(self, branch_info: str) -> Dict[str, int]:
        """Extract ahead/behind info from git status"""
        ahead = behind = 0

        match = re.search(r'ahead (\d+)', branch_info)
        if match:
            ahead = int(match.group(1))

        match = re.search(r'behind (\d+)', branch_info)
        if match:
            behind = int(match.group(1))

        return {"ahead": ahead, "behind": behind}

    def _get_status_text(self, status_char: str) -> str:
        """Get human readable status text"""
        status_map = {
            'M': 'modified',
            'A': 'added',
            'D': 'deleted',
            'R': 'renamed',
            'C': 'copied',
            '??': 'untracked',
            '!!': 'ignored'
        }
        return status_map.get(status_char, 'unknown')

    async def _get_recent_commits(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent commits with details"""
        try:
            result = await self._run_git_command([
                "log", f"-{count}", "--pretty=format:%H|%s|%an|%ad", "--date=iso"
            ])

            commits = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split('|', 3)
                    if len(parts) >= 4:
                        commits.append({
                            "hash": parts[0],
                            "message": parts[1],
                            "author": parts[2],
                            "date": parts[3]
                        })

            return commits
        except Exception:
            return []

    async def _detect_repo_issues(self) -> List[Dict[str, Any]]:
        """Detect repository issues and problems"""
        issues = []

        try:
            # Check for uncommitted changes
            result = await self._run_git_command(["status", "--porcelain"])
            if result.stdout.strip():
                issues.append({
                    "type": "uncommitted_changes",
                    "severity": "warning",
                    "message": "There are uncommitted changes in the repository"
                })

            # Check if on main branch with changes
            current_branch = await self._get_current_branch()
            if current_branch == self.main_branch:
                result = await self._run_git_command(["status", "--porcelain"])
                if result.stdout.strip():
                    issues.append({
                        "type": "main_branch_changes",
                        "severity": "warning",
                        "message": f"Making changes directly on {self.main_branch} branch"
                    })

            # Check for large files
            result = await self._run_git_command(["ls-files", "-s"])
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 4:
                        size = int(parts[3])
                        if size > 10 * 1024 * 1024:  # 10MB
                            issues.append({
                                "type": "large_file",
                                "severity": "info",
                                "message": f"Large file detected: {parts[3]} ({size/1024/1024:.1f}MB)"
                            })

        except Exception:
            pass

        return issues

    async def _run_git_command(self, command: List[str]) -> subprocess.CompletedProcess:
        """Run git command and return result"""
        return await self._run_command(["git"] + command)

    async def _run_command(self, command: List[str]) -> subprocess.CompletedProcess:
        """Run command and return result"""
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.repo_path
        )

        stdout, stderr = await process.communicate()

        return subprocess.CompletedProcess(
            args=command,
            returncode=process.returncode,
            stdout=stdout.decode('utf-8', errors='ignore'),
            stderr=stderr.decode('utf-8', errors='ignore')
        )

    def _generate_branch_name(self, feature_name: str, issue_number: str = None) -> str:
        """Generate a standardized branch name"""
        # Clean and normalize feature name
        clean_name = re.sub(r'[^a-zA-Z0-9\s-]', '', feature_name.lower())
        clean_name = re.sub(r'\s+', '-', clean_name.strip())

        # Remove leading/trailing dashes
        clean_name = clean_name.strip('-')

        # Add issue number if provided
        if issue_number:
            return f"feature/{issue_number}-{clean_name}"
        else:
            return f"feature/{clean_name}"

    async def _get_branches(self) -> List[str]:
        """Get all local branches"""
        try:
            result = await self._run_git_command(["branch", "--format=%(refname:short)"])
            return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        except Exception:
            return []

    async def _get_branch_info(self, branch_name: str) -> Dict[str, Any]:
        """Get detailed branch information"""
        try:
            result = await self._run_git_command(["show-branch", "--no-name", branch_name])
            commits = result.stdout.strip().split('\n') if result.stdout.strip() else []

            return {
                "name": branch_name,
                "commit_count": len([c for c in commits if c.strip()]),
                "latest_commit": commits[0].strip() if commits else None
            }
        except Exception:
            return {"name": branch_name, "error": "Failed to get branch info"}

    async def _get_current_branch(self) -> str:
        """Get current branch name"""
        try:
            result = await self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
            return result.stdout.strip()
        except Exception:
            return "unknown"

    async def _run_pre_commit_tests(self) -> Dict[str, Any]:
        """Run pre-commit tests and checks"""
        try:
            # Basic linting (can be extended)
            test_results = {
                "passed": True,
                "tests": []
            }

            # Check for Python syntax errors
            python_files = []
            try:
                result = await self._run_git_command(["diff", "--cached", "--name-only", "--diff-filter=ACM", "*.py"])
                python_files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip().endswith('.py')]
            except Exception:
                pass

            for py_file in python_files:
                try:
                    file_path = self.repo_path / py_file
                    if file_path.exists():
                        with open(file_path, 'r') as f:
                            compile(f.read(), file_path, 'exec')
                        test_results["tests"].append({
                            "type": "python_syntax",
                            "file": py_file,
                            "passed": True
                        })
                except SyntaxError as e:
                    test_results["passed"] = False
                    test_results["tests"].append({
                        "type": "python_syntax",
                        "file": py_file,
                        "passed": False,
                        "error": str(e)
                    })

            return test_results

        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }

    async def _generate_commit_message(self, status: Dict[str, Any]) -> str:
        """Generate intelligent commit message based on changes"""
        file_types = set()

        # Analyze file types
        for category in ["staged", "modified"]:
            for file_info in status["files"][category]:
                ext = Path(file_info["path"]).suffix.lower()
                if ext:
                    file_types.add(ext)

        # Determine primary change type
        primary_type = "code"
        if '.py' in file_types:
            primary_type = "python"
        elif '.js' in file_types or '.jsx' in file_types:
            primary_type = "javascript"
        elif '.ts' in file_types or '.tsx' in file_types:
            primary_type = "typescript"
        elif '.md' in file_types:
            primary_type = "docs"
        elif '.yaml' in file_types or '.yml' in file_types:
            primary_type = "config"

        # Generate message
        total_changes = status["files"]["total_changes"]
        if total_changes == 1:
            return f"Update {primary_type} files"
        elif total_changes <= 5:
            return f"Update {total_changes} {primary_type} files"
        else:
            return f"Multiple {primary_type} improvements and updates"

    async def _validate_commit_message(self, message: str) -> Dict[str, Any]:
        """Validate commit message format"""
        validation = {"valid": True, "warnings": []}

        # Check length
        if len(message.split('\n')[0]) > 72:
            validation["valid"] = False
            validation["error"] = "First line exceeds 72 characters"
        elif len(message.split('\n')[0]) < 10:
            validation["warnings"].append("First line is very short")

        # Check for required issue link if configured
        if self.config["require_issue_link"] and not re.search(r'#\d+', message):
            validation["valid"] = False
            validation["error"] = "Commit message must reference an issue number"

        return validation

    async def _auto_push(self) -> Dict[str, Any]:
        """Auto push current branch to remote"""
        try:
            current_branch = await self._get_current_branch()

            # Push current branch
            result = await self._run_git_command(["push", "-u", "origin", current_branch])

            return {
                "success": True,
                "branch": current_branch,
                "output": result.stdout
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def _get_current_commit_hash(self) -> str:
        """Get current commit hash"""
        try:
            result = await self._run_git_command(["rev-parse", "HEAD"])
            return result.stdout.strip()
        except Exception:
            return "unknown"

    async def _get_commits_since_branch(self, branch: str, base_branch: str) -> List[Dict[str, Any]]:
        """Get commits since branch diverged from base"""
        try:
            result = await self._run_git_command([
                "log", f"{base_branch}..{branch}", "--pretty=format:%H|%s|%an"
            ])

            commits = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split('|', 2)
                    if len(parts) >= 3:
                        commits.append({
                            "hash": parts[0],
                            "message": parts[1],
                            "author": parts[2]
                        })

            return commits
        except Exception:
            return []

    async def _generate_pr_title(self, branch: str, commits: List[Dict]) -> str:
        """Generate PR title from branch name and commits"""
        # Extract feature name from branch
        feature_match = re.search(r'feature/(\d+-)?(.+)', branch)
        if feature_match:
            feature_name = feature_match.group(2).replace('-', ' ').title()
        else:
            feature_name = branch.replace('/', ' ').title()

        # If there's only one commit, use its message
        if len(commits) == 1:
            return commits[0]["message"]

        return f"Feature: {feature_name}"

    async def _generate_pr_description(self, branch: str, commits: List[Dict]) -> str:
        """Generate PR description"""
        description = f"## Changes\n\n"
        description += f"This PR implements changes based on branch `{branch}`.\n\n"

        if commits:
            description += f"### Commits ({len(commits)})\n\n"
            for commit in commits:
                description += f"- {commit['message']} ({commit['hash'][:8]})\n"

        description += f"\n---\n\n*Auto-generated by homelab git workflow tool*"

        return description

    async def _check_existing_pr(self, branch: str, target_branch: str) -> Optional[Dict[str, Any]]:
        """Check if PR already exists"""
        try:
            result = await self._run_command([
                "gh", "pr", "list", "--head", branch, "--base", target_branch, "--json", "number,url,title"
            ])

            if result.stdout.strip():
                pr_data = json.loads(result.stdout)
                return pr_data[0] if pr_data else None
        except Exception:
            pass

        return None

    def _extract_pr_url(self, stdout: str) -> Optional[str]:
        """Extract PR URL from gh CLI output"""
        # Look for URLs in the output
        url_match = re.search(r'https://github\.com/[^\s]+', stdout)
        return url_match.group(0) if url_match else None

    async def _analyze_file_changes(self, file_path: str) -> Dict[str, Any]:
        """Analyze changes in a specific file"""
        try:
            # Get file type and language
            path = Path(file_path)
            language = self._detect_file_language(path)

            # Get diff stats
            result = await self._run_git_command(["diff", "--numstat", "--", file_path])
            diff_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []

            lines_added = 0
            lines_deleted = 0

            if diff_lines and diff_lines[0].strip():
                parts = diff_lines[0].split('\t')
                if len(parts) >= 2:
                    lines_added = int(parts[0]) if parts[0] != '-' else 0
                    lines_deleted = int(parts[1]) if parts[1] != '-' else 0

            # Assess risk based on file type and changes
            risk_level = self._assess_file_risk(file_path, language, lines_added, lines_deleted)

            return {
                "path": file_path,
                "language": language,
                "lines_added": lines_added,
                "lines_deleted": lines_deleted,
                "net_change": lines_added - lines_deleted,
                "risk_level": risk_level
            }

        except Exception as e:
            return {
                "path": file_path,
                "error": str(e),
                "analyzed": False
            }

    def _detect_file_language(self, path: Path) -> str:
        """Detect programming language from file extension"""
        suffix_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'react',
            '.ts': 'typescript',
            '.tsx': 'react-typescript',
            '.css': 'css',
            '.scss': 'scss',
            '.html': 'html',
            '.md': 'markdown',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.dockerfile': 'docker',
            '.sh': 'shell'
        }

        return suffix_map.get(path.suffix.lower(), 'text')

    def _assess_file_risk(self, file_path: str, language: str,
                         lines_added: int, lines_deleted: int) -> str:
        """Assess risk level of file changes"""
        risk_score = 0

        # High risk files
        if any(path in file_path for path in ['docker', 'kubernetes', 'production', 'secret']):
            risk_score += 3

        # Database migrations
        if 'migration' in file_path or 'migrate' in file_path:
            risk_score += 3

        # Large changes
        total_changes = lines_added + lines_deleted
        if total_changes > 500:
            risk_score += 2
        elif total_changes > 200:
            risk_score += 1

        # Critical languages
        if language in ['python', 'typescript', 'javascript'] and total_changes > 100:
            risk_score += 1

        if risk_score >= 4:
            return "high"
        elif risk_score >= 2:
            return "medium"
        else:
            return "low"

    async def _generate_change_recommendations(self, file_analysis: Dict) -> List[str]:
        """Generate recommendations based on file analysis"""
        recommendations = []

        for file_path, analysis in file_analysis.items():
            if not analysis.get("analyzed"):
                continue

            lines_added = analysis.get("lines_added", 0)
            lines_deleted = analysis.get("lines_deleted", 0)

            # Large file changes
            if lines_added > 300:
                recommendations.append(f"Consider breaking up large changes in {file_path}")

            # Risky files
            if analysis.get("risk_level") == "high":
                recommendations.append(f"High-risk file {file_path} requires careful review")

            # Database changes
            if 'migration' in file_path or 'migrate' in file_path:
                recommendations.append(f"Database migration {file_path} needs rollback strategy")

        return recommendations

    async def _get_commit_info(self, commit_hash: str) -> Optional[Dict[str, Any]]:
        """Get detailed commit information"""
        try:
            result = await self._run_git_command([
                "show", "--format=%H|%s|%an|%ad|%b", "--date=iso", commit_hash
            ])

            lines = result.stdout.strip().split('\n')
            if len(lines) >= 4:
                return {
                    "hash": lines[0],
                    "message": lines[1],
                    "author": lines[2],
                    "date": lines[3],
                    "body": '\n'.join(lines[4:]) if len(lines) > 4 else ""
                }
        except Exception:
            pass

        return None

# MCP Server Interface
async def main():
    """MCP Server entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--describe":
        print(json.dumps({
            "name": "homelab-git",
            "description": "Intelligent git workflow automation for homelab development",
            "version": "1.0.0",
            "tools": [
                {
                    "name": "get_repo_status",
                    "description": "Get comprehensive repository status and analysis",
                    "parameters": {}
                },
                {
                    "name": "create_feature_branch",
                    "description": "Create feature branch with intelligent naming",
                    "parameters": {
                        "feature_name": {"type": "string", "required": True},
                        "base_branch": {"type": "string", "required": False},
                        "issue_number": {"type": "string", "required": False}
                    }
                },
                {
                    "name": "smart_commit",
                    "description": "Smart commit with message generation and pre-commit tests",
                    "parameters": {
                        "message": {"type": "string", "required": False},
                        "run_tests": {"type": "boolean", "required": False},
                        "auto_push": {"type": "boolean", "required": False}
                    }
                },
                {
                    "name": "create_pull_request",
                    "description": "Create pull request with auto-generated description",
                    "parameters": {
                        "target_branch": {"type": "string", "required": False},
                        "draft": {"type": "boolean", "required": False},
                        "auto_assign": {"type": "boolean", "required": False}
                    }
                },
                {
                    "name": "analyze_code_changes",
                    "description": "Analyze code changes for impact assessment",
                    "parameters": {
                        "file_paths": {"type": "array", "required": False}
                    }
                },
                {
                    "name": "rollback_commit",
                    "description": "Safely rollback commits with backup",
                    "parameters": {
                        "commit_hash": {"type": "string", "required": False},
                        "soft": {"type": "boolean", "required": False}
                    }
                }
            ]
        }))
        return

    git_workflow = GitWorkflowMCP()

    # Example usage for testing
    if len(sys.argv) > 2:
        command = sys.argv[1]
        args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}

        if command == "get_repo_status":
            result = await git_workflow.get_repo_status()
        elif command == "create_feature_branch":
            result = await git_workflow.create_feature_branch(**args)
        elif command == "smart_commit":
            result = await git_workflow.smart_commit(**args)
        elif command == "create_pull_request":
            result = await git_workflow.create_pull_request(**args)
        elif command == "analyze_code_changes":
            result = await git_workflow.analyze_code_changes(**args)
        elif command == "rollback_commit":
            result = await git_workflow.rollback_commit(**args)
        else:
            result = {"error": f"Unknown command: {command}"}

        print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())