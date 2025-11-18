"""
Feedback Engine for Session Validation

Provides actionable feedback and iteration guidance when validation fails.
Includes common issue patterns, troubleshooting steps, and remediation suggestions.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from pydantic import BaseModel, Field

from loguru import logger

from .service_validator import ValidationResult, ValidationStatus
from .session_parser import ParsedSession


class IssuePattern(BaseModel):
    """Pattern for recognizing common issues."""
    name: str = Field(description="Issue pattern name")
    keywords: List[str] = Field(description="Keywords to match in errors/details")
    category: str = Field(description="Issue category")
    severity: str = Field(description="Issue severity (low/medium/high/critical)")
    description: str = Field(description="Issue description")
    troubleshooting_steps: List[str] = Field(description="Steps to troubleshoot")
    remediation_commands: List[str] = Field(description="Commands to fix the issue")
    documentation_links: List[str] = Field(description="Relevant documentation")


class FeedbackSuggestion(BaseModel):
    """Single feedback suggestion for service improvement."""
    service_name: str = Field(description="Service this suggestion applies to")
    issue_type: str = Field(description="Type of issue identified")
    severity: str = Field(description="Issue severity")
    description: str = Field(description="What the issue is")
    immediate_actions: List[str] = Field(description="Immediate steps to take")
    investigation_commands: List[str] = Field(description="Commands to investigate further")
    remediation_steps: List[str] = Field(description="Steps to fix the issue")
    verification_commands: List[str] = Field(description="Commands to verify fix worked")


class IterationPlan(BaseModel):
    """Plan for iterating on session work based on validation results."""
    session_status: str = Field(description="Overall session status")
    priority_issues: List[FeedbackSuggestion] = Field(description="High-priority issues to address")
    secondary_issues: List[FeedbackSuggestion] = Field(description="Secondary issues")
    validation_gaps: List[str] = Field(description="What couldn't be validated")
    next_session_focus: List[str] = Field(description="What to focus on next session")
    blocked_by: List[str] = Field(description="What's blocking progress")


class FeedbackEngine:
    """Generates actionable feedback from validation results."""

    def __init__(self):
        self.issue_patterns = self._load_issue_patterns()
        self.service_troubleshooting = self._load_service_troubleshooting()

    def generate_feedback(self,
                         session: ParsedSession,
                         validation_results: List[ValidationResult]) -> IterationPlan:
        """Generate comprehensive feedback from validation results."""
        logger.info("Generating feedback from validation results")

        # Categorize validation results
        invalid_services = [r for r in validation_results if r.actual_status == ValidationStatus.INVALID]
        warning_services = [r for r in validation_results if r.actual_status == ValidationStatus.WARNING]
        unknown_services = [r for r in validation_results if r.actual_status == ValidationStatus.UNKNOWN]

        # Generate feedback suggestions
        priority_issues = []
        secondary_issues = []

        # Process invalid services (high priority)
        for result in invalid_services:
            suggestions = self._analyze_invalid_service(result)
            priority_issues.extend(suggestions)

        # Process warning services (medium priority)
        for result in warning_services:
            suggestions = self._analyze_warning_service(result)
            secondary_issues.extend(suggestions)

        # Process unknown services
        for result in unknown_services:
            suggestions = self._analyze_unknown_service(result)
            secondary_issues.extend(suggestions)

        # Identify validation gaps
        validation_gaps = self._identify_validation_gaps(session, validation_results)

        # Determine next session focus
        next_session_focus = self._determine_next_focus(
            session, priority_issues, secondary_issues, validation_gaps
        )

        # Identify blockers
        blocked_by = self._identify_blockers(priority_issues, validation_gaps)

        # Determine overall session status
        if not invalid_services and not warning_services:
            session_status = "✅ All services validated successfully"
        elif len(invalid_services) == 0 and len(warning_services) <= 2:
            session_status = "⚠️ Mostly complete - minor issues to address"
        elif len(invalid_services) <= 2:
            session_status = "🔄 In progress - some services need attention"
        else:
            session_status = "❌ Significant issues - major work needed"

        return IterationPlan(
            session_status=session_status,
            priority_issues=priority_issues,
            secondary_issues=secondary_issues,
            validation_gaps=validation_gaps,
            next_session_focus=next_session_focus,
            blocked_by=blocked_by
        )

    def _analyze_invalid_service(self, result: ValidationResult) -> List[FeedbackSuggestion]:
        """Analyze an invalid service and generate suggestions."""
        suggestions = []

        # Check error patterns
        for pattern in self.issue_patterns:
            if self._matches_pattern(result, pattern):
                suggestion = self._create_suggestion_from_pattern(result, pattern)
                suggestions.append(suggestion)

        # If no specific pattern matched, create generic suggestion
        if not suggestions:
            suggestion = self._create_generic_suggestion(result, "invalid")
            suggestions.append(suggestion)

        return suggestions

    def _analyze_warning_service(self, result: ValidationResult) -> List[FeedbackSuggestion]:
        """Analyze a service with warnings and generate suggestions."""
        suggestions = []

        if result.warnings:
            for warning in result.warnings:
                # Check if warning matches known patterns
                for pattern in self.issue_patterns:
                    if self._matches_text(warning, pattern.keywords):
                        suggestion = self._create_suggestion_from_pattern(result, pattern)
                        suggestion.description = f"Warning: {warning}"
                        suggestions.append(suggestion)
                        break

        if not suggestions:
            suggestion = self._create_generic_suggestion(result, "warning")
            suggestions.append(suggestion)

        return suggestions

    def _analyze_unknown_service(self, result: ValidationResult) -> List[FeedbackSuggestion]:
        """Analyze an unknown service status and generate suggestions."""
        suggestion = self._create_generic_suggestion(result, "unknown")
        return [suggestion]

    def _matches_pattern(self, result: ValidationResult, pattern: IssuePattern) -> bool:
        """Check if a validation result matches an issue pattern."""
        all_text = " ".join(
            result.errors +
            result.warnings +
            result.details +
            [result.service_name, result.validation_method]
        ).lower()

        return self._matches_text(all_text, pattern.keywords)

    def _matches_text(self, text: str, keywords: List[str]) -> bool:
        """Check if text contains any of the keywords."""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)

    def _create_suggestion_from_pattern(self, result: ValidationResult, pattern: IssuePattern) -> FeedbackSuggestion:
        """Create feedback suggestion from an issue pattern."""
        return FeedbackSuggestion(
            service_name=result.service_name,
            issue_type=pattern.name,
            severity=pattern.severity,
            description=pattern.description,
            immediate_actions=[
                f"Check {result.service_name} service status",
                f"Review {result.validation_method} results"
            ],
            investigation_commands=[
                f"kubectl get pods -n homelab | grep {result.service_name.lower()}",
                f"kubectl logs -n homelab -l app={result.service_name.lower().replace(' ', '-')} --tail=20"
            ],
            remediation_steps=pattern.remediation_commands,
            verification_commands=[
                f"curl -f {result.claimed_url}" if result.claimed_url else f"# Check {result.service_name} manually"
            ]
        )

    def _create_generic_suggestion(self, result: ValidationResult, issue_type: str) -> FeedbackSuggestion:
        """Create a generic suggestion when no specific pattern matches."""
        if issue_type == "invalid":
            description = f"{result.service_name} is not responding as expected"
            immediate_actions = [
                f"Check if {result.service_name} is deployed",
                f"Verify network connectivity to {result.service_name}"
            ]
            investigation_commands = [
                f"kubectl get services -n homelab | grep {result.service_name.lower()}",
                f"kubectl get pods -n homelab | grep {result.service_name.lower()}",
                f"curl -v {result.claimed_url}" if result.claimed_url else f"# No URL to test"
            ]
        elif issue_type == "warning":
            description = f"{result.service_name} has warnings that should be addressed"
            immediate_actions = [
                f"Review warnings for {result.service_name}",
                f"Check service health and performance"
            ]
            investigation_commands = [
                f"kubectl describe pods -n homelab | grep -A 10 {result.service_name.lower()}",
                f"kubectl top pods -n homelab | grep {result.service_name.lower()}"
            ]
        else:  # unknown
            description = f"Unable to validate {result.service_name} status"
            immediate_actions = [
                f"Determine how to validate {result.service_name}",
                f"Check if service should be deployed"
            ]
            investigation_commands = [
                f"kubectl get all -n homelab | grep {result.service_name.lower()}",
                f"docker ps | grep {result.service_name.lower()}"
            ]

        return FeedbackSuggestion(
            service_name=result.service_name,
            issue_type=f"Generic {issue_type} issue",
            severity="medium",
            description=description,
            immediate_actions=immediate_actions,
            investigation_commands=investigation_commands,
            remediation_steps=[
                f"# Review service configuration for {result.service_name}",
                f"# Check service logs for errors",
                f"# Restart service if necessary"
            ],
            verification_commands=[
                f"# Verify fix for {result.service_name}"
            ]
        )

    def _identify_validation_gaps(self, session: ParsedSession, results: List[ValidationResult]) -> List[str]:
        """Identify what couldn't be validated."""
        gaps = []

        # Check for claimed services that weren't validated
        validated_services = {r.service_name.lower() for r in results}
        claimed_services = {s.name.lower() for s in session.service_claims}

        missing_validations = claimed_services - validated_services
        if missing_validations:
            gaps.extend([
                f"Couldn't validate claimed services: {', '.join(missing_validations)}"
            ])

        # Check for infrastructure that should be validated
        if not self._has_kubernetes_validation(results):
            gaps.append("Kubernetes cluster status not validated")

        if not self._has_network_validation(results):
            gaps.append("Inter-node network connectivity not validated")

        return gaps

    def _determine_next_focus(self,
                            session: ParsedSession,
                            priority_issues: List[FeedbackSuggestion],
                            secondary_issues: List[FeedbackSuggestion],
                            validation_gaps: List[str]) -> List[str]:
        """Determine what should be the focus of the next session."""
        focus_items = []

        if priority_issues:
            focus_items.append("Fix high-priority service issues")

        if session.session_context.completion_percentage and session.session_context.completion_percentage < 80:
            focus_items.append("Complete remaining sprint objectives")

        if validation_gaps:
            focus_items.append("Improve validation coverage for undocumented services")

        if not priority_issues and not secondary_issues:
            focus_items.extend(session.session_context.next_steps[:2])

        return focus_items

    def _identify_blockers(self, priority_issues: List[FeedbackSuggestion], validation_gaps: List[str]) -> List[str]:
        """Identify what's blocking progress."""
        blockers = []

        for issue in priority_issues:
            if issue.severity in ["critical", "high"]:
                blockers.append(f"Critical issue with {issue.service_name}")

        if "Kubernetes cluster status not validated" in validation_gaps:
            blockers.append("Unable to validate Kubernetes infrastructure")

        return blockers

    def _has_kubernetes_validation(self, results: List[ValidationResult]) -> bool:
        """Check if any validation used Kubernetes."""
        return any("kubernetes" in r.validation_method.lower() for r in results)

    def _has_network_validation(self, results: List[ValidationResult]) -> bool:
        """Check if network connectivity was validated."""
        return any("http" in r.validation_method.lower() for r in results)

    def _load_issue_patterns(self) -> List[IssuePattern]:
        """Load common issue patterns."""
        return [
            IssuePattern(
                name="Service Not Found",
                keywords=["not found", "404", "does not exist", "missing"],
                category="deployment",
                severity="critical",
                description="Service deployment or configuration is missing",
                troubleshooting_steps=[
                    "Check if service YAML files exist",
                    "Verify namespace is correct",
                    "Check if service was applied to cluster"
                ],
                remediation_commands=[
                    "kubectl apply -f <service-manifest>.yaml",
                    "kubectl get services -n <namespace>",
                    "kubectl describe deployment <service-name>"
                ],
                documentation_links=["Kubernetes Services Documentation"]
            ),

            IssuePattern(
                name="Connection Refused",
                keywords=["connection refused", "connection reset", "network unreachable"],
                category="networking",
                severity="high",
                description="Service is not accepting connections",
                troubleshooting_steps=[
                    "Check if service is running",
                    "Verify port configuration",
                    "Check network policies",
                    "Test basic connectivity"
                ],
                remediation_commands=[
                    "kubectl get pods -n <namespace>",
                    "kubectl port-forward service/<service-name> <local-port>:<service-port>",
                    "telnet <service-ip> <service-port>"
                ],
                documentation_links=["Kubernetes Networking Documentation"]
            ),

            IssuePattern(
                name="Pod Not Ready",
                keywords=["not ready", "crashloopbackoff", "pending", "error"],
                category="pods",
                severity="high",
                description="Pods are not in ready state",
                troubleshooting_steps=[
                    "Check pod logs for errors",
                    "Verify resource requests/limits",
                    "Check image pull issues",
                    "Verify readiness/liveness probes"
                ],
                remediation_commands=[
                    "kubectl get pods -n <namespace> -o wide",
                    "kubectl logs <pod-name> -n <namespace>",
                    "kubectl describe pod <pod-name> -n <namespace>",
                    "kubectl delete pod <pod-name> -n <namespace>  # Restart pod"
                ],
                documentation_links=["Kubernetes Pod Lifecycle Documentation"]
            ),

            IssuePattern(
                name="Timeout Issues",
                keywords=["timeout", "deadline exceeded", "slow", "unresponsive"],
                category="performance",
                severity="medium",
                description="Service is responding too slowly",
                troubleshooting_steps=[
                    "Check resource utilization",
                    "Review application logs",
                    "Check for network latency",
                    "Verify dependencies are healthy"
                ],
                remediation_commands=[
                    "kubectl top pods -n <namespace>",
                    "kubectl exec -it <pod-name> -- top",
                    "kubectl get events -n <namespace> --sort-by=.metadata.creationTimestamp"
                ],
                documentation_links=["Kubernetes Resource Monitoring Documentation"]
            ),

            IssuePattern(
                name="Authentication Issues",
                keywords=["unauthorized", "forbidden", "authentication", "permission denied"],
                category="security",
                severity="high",
                description="Service authentication or authorization problems",
                troubleshooting_steps=[
                    "Check service account permissions",
                    "Verify RBAC configuration",
                    "Check secrets and config maps",
                    "Review service authentication setup"
                ],
                remediation_commands=[
                    "kubectl get serviceaccounts -n <namespace>",
                    "kubectl get roles,rolebindings -n <namespace>",
                    "kubectl get secrets -n <namespace>",
                    "kubectl auth can-i --list --namespace=<namespace>"
                ],
                documentation_links=["Kubernetes RBAC Documentation"]
            ),

            IssuePattern(
                name="Storage Issues",
                keywords=["storage", "volume", "disk", "pvc", "persistent"],
                category="storage",
                severity="high",
                description="Problems with persistent storage or volumes",
                troubleshooting_steps=[
                    "Check PVC status",
                    "Verify storage class",
                    "Check available disk space",
                    "Review volume mount configuration"
                ],
                remediation_commands=[
                    "kubectl get pvc -n <namespace>",
                    "kubectl get pv",
                    "kubectl describe pvc <pvc-name> -n <namespace>",
                    "df -h  # On node with storage issues"
                ],
                documentation_links=["Kubernetes Storage Documentation"]
            )
        ]

    def _load_service_troubleshooting(self) -> Dict[str, List[str]]:
        """Load service-specific troubleshooting guides."""
        return {
            "ollama": [
                "Check ROCm installation: rocminfo",
                "Verify GPU detection: rocm-smi",
                "Check Ollama logs: journalctl -u ollama",
                "Test API: curl http://localhost:11434/api/version"
            ],
            "n8n": [
                "Check N8n pod status: kubectl get pods -n homelab | grep n8n",
                "Review N8n logs: kubectl logs -n homelab deployment/n8n",
                "Check database connectivity",
                "Verify workflow execution status"
            ],
            "postgresql": [
                "Check PostgreSQL pod: kubectl get pods -n homelab | grep postgres",
                "Test connection: kubectl exec -it postgres-pod -- psql -U homelab -d homelab",
                "Check database logs: kubectl logs postgres-pod -n homelab",
                "Verify persistent volume claims"
            ],
            "redis": [
                "Check Redis pod: kubectl get pods -n homelab | grep redis",
                "Test Redis CLI: kubectl exec -it redis-pod -- redis-cli ping",
                "Check memory usage: kubectl top pods -n homelab | grep redis",
                "Review Redis logs for errors"
            ],
            "qdrant": [
                "Check Qdrant service: kubectl get svc -n homelab | grep qdrant",
                "Test collection access: curl http://qdrant-url:6333/collections",
                "Check storage: kubectl exec -it qdrant-pod -- ls -la /qdrant/storage",
                "Review vector DB logs"
            ]
        }

    def print_feedback(self, plan: IterationPlan) -> None:
        """Print formatted feedback to console."""
        from rich.console import Console
        from rich.panel import Panel
        from rich.syntax import Syntax
        from rich.tree import Tree

        console = Console()

        # Session status
        console.print(Panel(f"[bold blue]{plan.session_status}[/bold blue]", title="🎯 Session Status"))

        # Priority issues
        if plan.priority_issues:
            console.print("\n[bold red]🚨 Priority Issues[/bold red]")
            for issue in plan.priority_issues:
                console.print(f"\n[bold]❌ {issue.service_name}: {issue.issue_type}[/bold]")
                console.print(f"[dim]{issue.description}[/dim]")

                if issue.immediate_actions:
                    console.print("[bold]Immediate Actions:[/bold]")
                    for action in issue.immediate_actions:
                        console.print(f"  • {action}")

                if issue.investigation_commands:
                    console.print("[bold]Investigation Commands:[/bold]")
                    for cmd in issue.investigation_commands:
                        console.print(f"  {cmd}")

        # Secondary issues
        if plan.secondary_issues:
            console.print("\n[bold yellow]⚠️ Secondary Issues[/bold yellow]")
            for issue in plan.secondary_issues:
                console.print(f"• {issue.service_name}: {issue.description}")

        # Next session focus
        if plan.next_session_focus:
            console.print(f"\n[bold green]🎯 Next Session Focus[/bold green]")
            for focus in plan.next_session_focus:
                console.print(f"• {focus}")

        # Blockers
        if plan.blocked_by:
            console.print(f"\n[bold red]🚫 Blocked By[/bold red]")
            for blocker in plan.blocked_by:
                console.print(f"• {blocker}")

    def save_feedback_report(self, plan: IterationPlan, output_path: str) -> None:
        """Save feedback report to file."""
        with open(output_path, 'w') as f:
            f.write("# 🔍 Session Validation Feedback\n\n")
            f.write(f"**Session Status**: {plan.session_status}\n\n")

            if plan.priority_issues:
                f.write("## 🚨 Priority Issues\n\n")
                for issue in plan.priority_issues:
                    f.write(f"### ❌ {issue.service_name}: {issue.issue_type}\n\n")
                    f.write(f"**Severity**: {issue.severity}\n")
                    f.write(f"**Description**: {issue.description}\n\n")

                    f.write("**Immediate Actions**:\n")
                    for action in issue.immediate_actions:
                        f.write(f"- {action}\n")

                    f.write("\n**Investigation Commands**:\n")
                    for cmd in issue.investigation_commands:
                        f.write(f"```bash\n{cmd}\n```\n")

                    f.write("\n**Remediation Steps**:\n")
                    for step in issue.remediation_steps:
                        f.write(f"- {step}\n")

                    f.write("\n**Verification Commands**:\n")
                    for cmd in issue.verification_commands:
                        f.write(f"```bash\n{cmd}\n```\n")

                    f.write("\n---\n\n")

            if plan.secondary_issues:
                f.write("## ⚠️ Secondary Issues\n\n")
                for issue in plan.secondary_issues:
                    f.write(f"- **{issue.service_name}**: {issue.description}\n")

            if plan.validation_gaps:
                f.write("\n## 🔍 Validation Gaps\n\n")
                for gap in plan.validation_gaps:
                    f.write(f"- {gap}\n")

            if plan.next_session_focus:
                f.write("\n## 🎯 Next Session Focus\n\n")
                for focus in plan.next_session_focus:
                    f.write(f"- {focus}\n")

            if plan.blocked_by:
                f.write("\n## 🚫 Blocked By\n\n")
                for blocker in plan.blocked_by:
                    f.write(f"- {blocker}\n")

        logger.info(f"Feedback report saved to {output_path}")