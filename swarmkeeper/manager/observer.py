"""Manager/Observer module for analyzing tmux sessions with LLM."""

import os
from pathlib import Path
from typing import Optional

from openai import OpenAI

from ..config.manager import load_config
from ..session.manager import add_check
from ..tmux.wrapper import capture_pane, session_exists
from .schemas import AnalysisResult, SessionReport


def get_system_prompt() -> str:
    """Load the system prompt for LLM analysis."""
    project_root = Path(__file__).parent.parent.parent
    prompt_path = project_root / "prompts" / "swarmkeeper_check.md"

    if prompt_path.exists():
        return prompt_path.read_text()

    # Fallback prompt if file not found
    return """You are a Meta Manager that analyzes tmux session output.
Determine if the agent is working or stopped, and describe what it was doing.
Return JSON with: {"status": "working|stopped", "log": "brief description"}"""


def create_llm_client() -> OpenAI:
    """Create OpenAI client with API key and base URL from config."""
    config = load_config()
    # Support both camelCase (apiKey) and snake_case (api_key)
    api_key = config.get("apiKey") or config.get("api_key")
    # Support both camelCase (apiBase) and snake_case (api_base)
    base_url = config.get("apiBase") or config.get("api_base")

    if not api_key:
        raise RuntimeError(
            "OpenAI API key not configured. Please set it in ~/swarmkeeper/config.json"
        )

    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    return OpenAI(**client_kwargs)


def analyze_session_output(session_output: str) -> AnalysisResult:
    """Analyze tmux session output using LLM.

    Args:
        session_output: Text captured from tmux session

    Returns:
        AnalysisResult with status and log
    """
    client = create_llm_client()
    system_prompt = get_system_prompt()

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": session_output},
        ],
        response_format=AnalysisResult,
    )

    parsed = response.choices[0].message.parsed
    if parsed is None:
        raise RuntimeError("LLM returned empty response")

    return parsed


def check_session_health(session_name: str) -> SessionReport:
    """Check health of a single session.

    Args:
        session_name: Name of the tmux session

    Returns:
        SessionReport with analysis results
    """
    from datetime import datetime

    # Check if session exists
    is_alive = session_exists(session_name)

    if not is_alive:
        return SessionReport(
            session_name=session_name,
            status="stopped",
            log="Session no longer exists",
            timestamp=datetime.now().isoformat(),
            is_alive=False,
        )

    # Capture session output
    session_output = capture_pane(session_name, lines=100)

    # Analyze with LLM
    try:
        analysis = analyze_session_output(session_output)
        return SessionReport(
            session_name=session_name,
            status=analysis.status,
            log=analysis.log,
            timestamp=datetime.now().isoformat(),
            is_alive=True,
        )
    except Exception as e:
        return SessionReport(
            session_name=session_name,
            status="error",
            log=f"Analysis failed: {str(e)}",
            timestamp=datetime.now().isoformat(),
            is_alive=True,
        )


def generate_report(sessions_registry: dict) -> list[SessionReport]:
    """Generate health report for all tracked sessions.

    Args:
        sessions_registry: Dictionary of session_name -> session_data

    Returns:
        List of SessionReport for each session
    """
    reports = []

    for session_name in sessions_registry.keys():
        report = check_session_health(session_name)
        reports.append(report)

    return reports


def run_manager(sessions_registry: dict) -> dict:
    """Run manager to check all sessions and update registry.

    Args:
        sessions_registry: Current sessions registry

    Returns:
        Updated sessions registry with new check entries
    """
    reports = generate_report(sessions_registry)
    dead_sessions = []

    for report in reports:
        if report.session_name in sessions_registry:
            if not report.is_alive:
                # Session is dead, mark for removal
                print(
                    f"Session {report.session_name} is dead => removing from registry"
                )
                dead_sessions.append(report.session_name)
            else:
                # Session is alive, add check
                session = sessions_registry[report.session_name]
                add_check(session, report.status, report.log)

    # Remove dead sessions from registry
    for session_name in dead_sessions:
        del sessions_registry[session_name]

    return sessions_registry
