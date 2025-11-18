"""
Session Parser for SESSION-STATE.md files

Extracts completion claims, service deployments, and objectives from session documentation
to enable validation of actual vs. claimed completion status.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

from loguru import logger


class ServiceClaim(BaseModel):
    """Represents a claimed service deployment or status."""

    name: str = Field(description="Service name")
    status: str = Field(description="Claimed status (✅, ⚠️, ❌, 🔄)")
    description: str = Field(description="What was claimed to be done")
    url: Optional[str] = Field(None, description="Service URL if mentioned")
    version: Optional[str] = Field(None, description="Version if specified")
    location: Optional[str] = Field(None, description="Where service should be running")
    timestamp: Optional[datetime] = Field(None, description="When claimed")


class SprintObjective(BaseModel):
    """Represents a sprint objective or task."""

    sprint_id: str = Field(description="Sprint identifier")
    title: str = Field(description="Objective title")
    status: str = Field(description="Completion status")
    description: str = Field(description="What was supposed to be done")
    completion_date: Optional[datetime] = Field(None, description="When marked complete")


class SessionContext(BaseModel):
    """Overall session context and state."""

    session_date: Optional[datetime] = Field(None, description="Session date")
    current_phase: str = Field(description="Current development phase")
    active_tasks: List[str] = Field(default_factory=list, description="Active tasks")
    completed_work: List[str] = Field(default_factory=list, description="Completed items")
    next_steps: List[str] = Field(default_factory=list, description="Next steps planned")
    branch: str = Field(description="Git branch")
    directory: str = Field(description="Working directory")
    completion_percentage: Optional[float] = Field(None, description="Progress percentage")


@dataclass
class ParsedSession:
    """Complete parsed session information."""

    session_context: SessionContext
    service_claims: List[ServiceClaim] = field(default_factory=list)
    sprint_objectives: List[SprintObjective] = field(default_factory=list)
    endpoints: Dict[str, str] = field(default_factory=dict)
    raw_sections: Dict[str, str] = field(default_factory=dict)


class SessionParser:
    """Parser for SESSION-STATE.md and related documentation."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.session_state_path = self.project_root / "docs" / "SESSION-STATE.md"

    def parse_session(self) -> ParsedSession:
        """Parse the current session state documentation."""
        if not self.session_state_path.exists():
            logger.warning(f"SESSION-STATE.md not found at {self.session_state_path}")
            return self._create_empty_session()

        logger.info(f"Parsing session state from {self.session_state_path}")

        with open(self.session_state_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split into sections
        sections = self._split_sections(content)

        # Parse different components
        session_context = self._parse_session_context(sections)
        service_claims = self._parse_service_claims(sections, content)
        sprint_objectives = self._parse_sprint_objectives(sections, content)
        endpoints = self._parse_endpoints(sections, content)

        return ParsedSession(
            session_context=session_context,
            service_claims=service_claims,
            sprint_objectives=sprint_objectives,
            endpoints=endpoints,
            raw_sections=sections
        )

    def _split_sections(self, content: str) -> Dict[str, str]:
        """Split markdown content into sections."""
        sections = {}

        # Find section headers (## or ###)
        section_pattern = r'^(#{2,3})\s+(.+)$'
        current_section = "header"
        current_content = []

        for line in content.split('\n'):
            match = re.match(section_pattern, line)
            if match:
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()

                # Start new section
                level = len(match.group(1))
                section_name = match.group(2).strip().lower()
                current_section = section_name
                current_content = []
            else:
                current_content.append(line)

        # Save final section
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()

        return sections

    def _parse_session_context(self, sections: Dict[str, str]) -> SessionContext:
        """Parse overall session context."""
        # Extract basic info from Current Status section
        current_status = sections.get("current status", "")

        # Find current phase
        phase_match = re.search(r'Current Phase[^\n]*\*\*([^*]+)\*\*', current_status)
        current_phase = phase_match.group(1) if phase_match else "Unknown"

        # Find completion percentage
        percentage_match = re.search(r'(\d+)%', current_status)
        completion_percentage = float(percentage_match.group(1)) if percentage_match else None

        # Find session date and branch info
        session_info = sections.get("🚀 resume command", "")
        branch_match = re.search(r'Branch:\s*(\w+)', session_info.lower())
        branch = branch_match.group(1) if branch_match else "main"

        # Extract directory from resume command
        dir_match = re.search(r'cd\s+([^\n]+)', session_info)
        directory = dir_match.group(1).strip() if dir_match else str(self.project_root)

        # Parse session date
        date_match = re.search(r'Session State - (\d{4}-\d{2}-\d{2})', sections.get("header", ""))
        session_date = None
        if date_match:
            try:
                session_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
            except ValueError:
                pass

        # Extract active tasks and next steps
        next_steps_section = sections.get("📝 next steps", "")
        next_steps = self._extract_task_list(next_steps_section)

        # Extract completed work from completed work section
        completed_section = sections.get("✅ completed work", "")
        completed_work = self._extract_completed_items(completed_section)

        return SessionContext(
            session_date=session_date,
            current_phase=current_phase,
            active_tasks=next_steps[:5],  # First 5 as "active"
            completed_work=completed_work,
            next_steps=next_steps,
            branch=branch,
            directory=directory,
            completion_percentage=completion_percentage
        )

    def _parse_service_claims(self, sections: Dict[str, str], content: str) -> List[ServiceClaim]:
        """Extract service deployment claims from the content."""
        claims = []

        # Look for completed service deployments in Completed Work section
        completed_work = sections.get("✅ completed work", "")

        # Pattern for service deployment claims
        # ✅ **Service Name**: Description (version info)
        service_pattern = r'✅\s*\*\*([^*]+)\*\*[:\s]*([^\n]+)'

        for match in re.finditer(service_pattern, completed_work):
            name = match.group(1).strip()
            description = match.group(2).strip()

            # Extract version if present
            version_match = re.search(r'v?(\d+\.?\d*\.?\d*)', description)
            version = version_match.group(1) if version_match else None

            # Extract URL if present
            url_match = re.search(r'https?://[^\s\)]+', description)
            url = url_match.group(0) if url_match else None

            # Determine location based on service name and content
            location = self._determine_service_location(name, description)

            claims.append(ServiceClaim(
                name=name,
                status="✅",
                description=description,
                url=url,
                version=version,
                location=location
            ))

        # Also check for services mentioned in Infrastructure Deployed section
        infra_section = sections.get("infrastructure deployed (service node - asuna)", "")
        for match in re.finditer(service_pattern, infra_section):
            name = match.group(1).strip()
            description = match.group(2).strip()

            # Extract port/URL info
            port_match = re.search(r':(\d+)', description)
            url = f"http://100.81.76.55:{port_match.group(1)}" if port_match else None

            claims.append(ServiceClaim(
                name=name,
                status="✅",
                description=description,
                url=url,
                location="asuna (service node)"
            ))

        return claims

    def _parse_sprint_objectives(self, sections: Dict[str, str], content: str) -> List[SprintObjective]:
        """Extract sprint objectives and their completion status."""
        objectives = []

        # Look for sprint sections
        sprint_pattern = r'### Sprint (\d+): ([^\n]+)'

        for match in re.finditer(sprint_pattern, content):
            sprint_id = f"Sprint {match.group(1)}"
            title = match.group(2).strip()

            # Find the status indicator near the sprint
            context_start = match.start()
            context_end = match.start() + 200  # Look ahead 200 chars
            context = content[context_start:context_end]

            # Determine status
            if "✅ COMPLETED" in context:
                status = "✅ COMPLETED"
            elif "🔄 IN PROGRESS" in context:
                status = "🔄 IN PROGRESS"
            elif "⏳ PENDING" in context:
                status = "⏳ PENDING"
            else:
                status = "Unknown"

            objectives.append(SprintObjective(
                sprint_id=sprint_id,
                title=title,
                status=status,
                description=title  # Use title as description for now
            ))

        return objectives

    def _parse_endpoints(self, sections: Dict[str, str], content: str) -> Dict[str, str]:
        """Extract service endpoints and URLs."""
        endpoints = {}

        # Look for Important Endpoints section
        endpoints_section = sections.get("🔗 important endpoints", "")

        # Pattern for extracting URLs
        url_pattern = r'\*\*([^*]+)\*\*[^\n]*:\s*([^\n]+)'

        for match in re.finditer(url_pattern, endpoints_section):
            service_name = match.group(1).strip()
            url_info = match.group(2).strip()

            # Extract actual URL
            url_match = re.search(r'https?://[^\s\)]+', url_info)
            if url_match:
                endpoints[service_name] = url_match.group(0)

        return endpoints

    def _extract_task_list(self, text: str) -> List[str]:
        """Extract task items from markdown text."""
        tasks = []

        # Look for - [ ] or - [x] patterns
        task_pattern = r'-\s*\[([ x])\]\s*([^\n]+)'

        for match in re.finditer(task_pattern, text):
            status = match.group(1)
            task = match.group(2).strip()

            if status == " ":  # Uncompleted
                tasks.append(task)

        return tasks

    def _extract_completed_items(self, text: str) -> List[str]:
        """Extract completed items from markdown text."""
        items = []

        # Look for - [x] patterns or just bullet points in completed section
        task_pattern = r'-\s*\[(?:x|✓)\]\s*([^\n]+)'

        for match in re.finditer(task_pattern, text):
            items.append(match.group(1).strip())

        # Also extract service deployments that are marked as complete
        service_pattern = r'✅\s*\*\*([^*]+)\*\*[:\s]*([^\n]+)'
        for match in re.finditer(service_pattern, text):
            service_name = match.group(1).strip()
            description = match.group(2).strip()
            items.append(f"Deployed {service_name}: {description}")

        return items

    def _determine_service_location(self, name: str, description: str) -> str:
        """Determine where a service should be located based on name and description."""
        name_lower = name.lower()
        desc_lower = description.lower()

        # Compute node services
        if any(term in name_lower for term in ["ollama", "gpu", "compute", "llm"]):
            return "pesubuntu (compute node)"

        # Service node services
        if any(term in name_lower for term in ["kubernetes", "k8s", "n8n", "database", "redis", "postgres"]):
            return "asuna (service node)"

        # Check description for location hints
        if "compute node" in desc_lower or "100.72.98.106" in desc_lower:
            return "pesubuntu (compute node)"
        elif "service node" in desc_lower or "100.81.76.55" in desc_lower:
            return "asuna (service node)"

        return "Unknown location"

    def _create_empty_session(self) -> ParsedSession:
        """Create an empty session when no SESSION-STATE.md exists."""
        return ParsedSession(
            session_context=SessionContext(
                current_phase="Unknown",
                branch="main",
                directory=str(self.project_root)
            )
        )

    def get_validation_targets(self) -> List[ServiceClaim]:
        """Get list of services that should be validated."""
        session = self.parse_session()

        # Filter for services that are claimed to be complete/working
        targets = []
        for claim in session.service_claims:
            if claim.status in ["✅", "🔄"]:  # Complete or in progress
                targets.append(claim)

        # Add services from endpoints that should be working
        for service_name, url in session.endpoints.items():
            # Check if we already have this service
            if not any(claim.name.lower() == service_name.lower() for claim in targets):
                targets.append(ServiceClaim(
                    name=service_name,
                    status="✅",
                    description=f"Service should be accessible at {url}",
                    url=url
                ))

        return targets