"""FastAPI router for execution runtime endpoints."""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.browser.runtime import BrowserRuntime
from backend.browser.models import BrowserAction, BrowserActionType
from backend.governance.execution import ExecutionGovernanceValidator
from backend.replay.execution import ExecutionReplayManager
from backend.runtime.context import RuntimeExecutionContext
from backend.skills.models import SkillDefinition, SkillInvocation
from backend.skills.runtime import SkillRuntime
from backend.telemetry.execution import ExecutionTelemetryCollector
from backend.terminal.models import TerminalCommand
from backend.terminal.runtime import TerminalRuntime
from backend.workflow.engine import WorkflowEngine
from backend.workflow.models import WorkflowDefinition, WorkflowStep, WorkflowStepType


class WorkflowExecuteRequest(BaseModel):
    """Request to execute a workflow."""

    workflow_id: str = ""
    name: str = ""
    steps: List[Dict[str, Any]] = Field(default_factory=list)


class TerminalExecuteRequest(BaseModel):
    """Request to execute a terminal command."""

    session_id: str = ""
    command: str = ""
    working_dir: str = "/tmp"
    timeout_seconds: int = 30


class SkillInvokeRequest(BaseModel):
    """Request to invoke a skill."""

    skill_id: str = ""
    inputs: Dict[str, Any] = Field(default_factory=dict)


def create_execution_router(
    context: RuntimeExecutionContext,
    browser_runtime: BrowserRuntime,
    terminal_runtime: TerminalRuntime,
    workflow_engine: WorkflowEngine,
    skill_runtime: SkillRuntime,
    governance_validator: ExecutionGovernanceValidator,
    telemetry_collector: ExecutionTelemetryCollector,
    replay_manager: ExecutionReplayManager,
) -> APIRouter:
    """Create the execution API router with injected dependencies.

    Args:
        context: Execution context.
        browser_runtime: Browser session runtime.
        terminal_runtime: Terminal session runtime.
        workflow_engine: Workflow orchestration engine.
        skill_runtime: Skill plugin runtime.
        governance_validator: Execution governance validator.
        telemetry_collector: Execution telemetry collector.
        replay_manager: Execution replay manager.

    Returns:
        Configured APIRouter.
    """
    router = APIRouter(prefix="/api")

    # --- Workflow endpoints ---

    @router.post("/workflow/execute")
    def execute_workflow(request: WorkflowExecuteRequest) -> Dict[str, Any]:
        """Execute a workflow."""
        # Build workflow steps
        steps = []
        for s in request.steps:
            step_type = s.get("step_type", "CUSTOM").upper()
            try:
                step_type_enum = WorkflowStepType(step_type)
            except ValueError:
                # Invalid step type - let governance handle it
                step_type_enum = None

            if step_type_enum is None:
                # Run governance check with the raw step data
                validation = governance_validator.validate_workflow_execution(
                    {"steps": [{"step_type": step_type, "id": s.get("id", "")}]}
                )
                if not validation.permitted:
                    raise HTTPException(status_code=403, detail=validation.reason)
                # If somehow governance allows it, still fail
                raise HTTPException(
                    status_code=403, detail=f"Invalid step type: {step_type}"
                )

            steps.append(
                WorkflowStep(
                    id=s.get("id", ""),
                    name=s.get("name", ""),
                    step_type=step_type_enum,
                    config=s.get("config", {}),
                    depends_on=s.get("depends_on", []),
                )
            )

        # Governance validation
        validation = governance_validator.validate_workflow_execution(
            {"steps": [{"step_type": s.step_type.value, "id": s.id} for s in steps]}
        )
        if not validation.permitted:
            raise HTTPException(status_code=403, detail=validation.reason)

        # Create and execute workflow
        workflow_id = request.workflow_id or f"wf-{context.now_iso()}"
        definition = WorkflowDefinition(
            id=workflow_id,
            name=request.name or "API Workflow",
            steps=steps,
        )
        workflow_engine.create_workflow(definition)
        execution = workflow_engine.execute_workflow(workflow_id)

        # Telemetry
        for step_result in execution.steps_completed:
            telemetry_collector.record_workflow_trace(
                execution_id=execution.id,
                step_id=step_result.step_id,
                result={"status": step_result.status},
            )

        # Replay
        replay_manager.record_workflow_execution(
            execution.id,
            [sr.model_dump() for sr in execution.steps_completed],
        )

        return {
            "execution_id": execution.id,
            "workflow_id": execution.workflow_id,
            "state": execution.state.value,
            "steps_completed": [sr.model_dump() for sr in execution.steps_completed],
        }

    @router.get("/workflow/{execution_id}/status")
    def get_workflow_status(execution_id: str) -> Dict[str, Any]:
        """Get workflow execution status."""
        execution = workflow_engine.get_execution(execution_id)
        if execution is None:
            raise HTTPException(status_code=404, detail="Execution not found")
        return {
            "execution_id": execution.id,
            "workflow_id": execution.workflow_id,
            "state": execution.state.value,
            "steps_completed": len(execution.steps_completed),
            "current_step_id": execution.current_step_id,
            "start_timestamp": execution.start_timestamp,
            "end_timestamp": execution.end_timestamp,
        }

    @router.get("/workflow/executions")
    def list_workflow_executions() -> Dict[str, Any]:
        """List all workflow executions."""
        executions = workflow_engine.list_executions()
        return {
            "executions": [
                {
                    "id": e.id,
                    "workflow_id": e.workflow_id,
                    "state": e.state.value,
                    "start_timestamp": e.start_timestamp,
                }
                for e in executions
            ],
            "total": len(executions),
        }

    # --- Browser endpoints ---

    @router.post("/browser/start")
    def start_browser_session(request: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new browser session with governance validation."""
        url = request.get("url", "")

        # Governance validation on the URL before starting session
        validation = governance_validator.validate_browser_action({"target": url})
        if not validation.permitted:
            raise HTTPException(status_code=403, detail=validation.reason)

        session = browser_runtime.start_session(url)

        # Telemetry
        telemetry_collector.record_browser_trace(
            session_id=session.id,
            action={"type": "START", "url": url},
            result={"state": session.state.value},
        )

        return {
            "session_id": session.id,
            "url": session.url,
            "state": session.state.value,
            "creation_timestamp": session.creation_timestamp,
        }

    @router.post("/browser/{session_id}/action")
    def execute_browser_action(session_id: str, action: BrowserAction) -> Dict[str, Any]:
        """Execute a browser action within a session with governance validation."""
        # Governance validation
        validation = governance_validator.validate_browser_action(
            {"target": action.target}
        )
        if not validation.permitted:
            raise HTTPException(status_code=403, detail=validation.reason)

        # Execute the action
        session = browser_runtime.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        result = browser_runtime.execute_action(session_id, action)

        # Telemetry
        telemetry_collector.record_browser_trace(
            session_id=session_id,
            action={"type": action.action_type.value, "target": action.target},
            result={"success": result.success},
        )

        # Replay
        replay_manager.record_browser_session(
            session_id,
            [{"action": action.model_dump(), "result": result.model_dump()}],
        )

        return {
            "session_id": session_id,
            "success": result.success,
            "action_type": action.action_type.value,
            "target": action.target,
            "timestamp": result.timestamp,
            "error": result.error,
        }

    @router.get("/browser/sessions")
    def list_browser_sessions() -> Dict[str, Any]:
        """List all browser sessions."""
        sessions = browser_runtime.list_sessions()
        return {
            "sessions": [
                {
                    "id": s.id,
                    "url": s.url,
                    "state": s.state.value,
                    "creation_timestamp": s.creation_timestamp,
                }
                for s in sessions
            ],
            "total": len(sessions),
        }

    @router.get("/browser/{session_id}/status")
    def get_browser_status(session_id: str) -> Dict[str, Any]:
        """Get browser session status."""
        session = browser_runtime.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return {
            "id": session.id,
            "url": session.url,
            "state": session.state.value,
            "screenshots": len(session.screenshots),
            "recording_length": len(session.recording),
        }

    # --- Terminal endpoints ---

    @router.post("/terminal/execute")
    def execute_terminal_command(request: TerminalExecuteRequest) -> Dict[str, Any]:
        """Execute a terminal command."""
        # Governance validation
        validation = governance_validator.validate_terminal_command(request.command)
        if not validation.permitted:
            raise HTTPException(status_code=403, detail=validation.reason)

        # Create session if needed
        session_id = request.session_id
        if not session_id:
            session = terminal_runtime.create_session()
            session_id = session.id

        session = terminal_runtime.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        # Execute command
        command = TerminalCommand(
            command=request.command,
            working_dir=request.working_dir,
            timeout_seconds=request.timeout_seconds,
        )
        result = terminal_runtime.execute_command(session_id, command)

        # Telemetry
        telemetry_collector.record_terminal_trace(
            session_id=session_id,
            command=request.command,
            result={"exit_code": result.exit_code},
        )

        # Replay
        replay_manager.record_terminal_session(
            session_id,
            [{"command": result.command, "exit_code": result.exit_code, "stdout": result.stdout}],
        )

        return {
            "session_id": session_id,
            "command": result.command,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.exit_code,
            "duration_ms": result.duration_ms,
        }

    @router.get("/terminal/{session_id}/status")
    def get_terminal_status(session_id: str) -> Dict[str, Any]:
        """Get terminal session status."""
        session = terminal_runtime.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return {
            "id": session.id,
            "state": session.state.value,
            "command_count": len(session.command_history),
            "creation_timestamp": session.creation_timestamp,
        }

    # --- Skills endpoints ---

    @router.get("/skills")
    def list_skills() -> Dict[str, Any]:
        """List all registered skills."""
        skills = skill_runtime.list_skills()
        return {
            "skills": [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                    "version": s.version,
                }
                for s in skills
            ],
            "total": len(skills),
        }

    @router.post("/skills/invoke")
    def invoke_skill(request: SkillInvokeRequest) -> Dict[str, Any]:
        """Invoke a registered skill."""
        # Governance validation
        registered = [s.id for s in skill_runtime.list_skills()]
        validation = governance_validator.validate_skill_invocation(
            {"skill_id": request.skill_id},
            registered_skills=registered,
        )
        if not validation.permitted:
            raise HTTPException(status_code=403, detail=validation.reason)

        invocation = SkillInvocation(
            skill_id=request.skill_id,
            inputs=request.inputs,
            timestamp=context.now_iso(),
        )

        try:
            result = skill_runtime.invoke_skill(invocation)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

        # Telemetry
        telemetry_collector.record_skill_trace(
            skill_id=request.skill_id,
            invocation={"inputs": request.inputs},
            result={"success": result.success},
        )

        return {
            "skill_id": result.skill_id,
            "outputs": result.outputs,
            "success": result.success,
            "duration_ms": result.duration_ms,
            "error": result.error,
        }

    # --- Replay endpoints ---

    @router.get("/replay/{session_type}/{session_id}")
    def get_replay(session_type: str, session_id: str) -> Dict[str, Any]:
        """Get replay records for a session."""
        if session_type == "browser":
            data = replay_manager.replay_browser_session(session_id)
        elif session_type == "terminal":
            data = replay_manager.replay_terminal_session(session_id)
        elif session_type == "workflow":
            data = replay_manager.replay_workflow_execution(session_id)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid session type: {session_type}")

        if data is None:
            raise HTTPException(status_code=404, detail="Replay data not found")

        return {
            "session_type": session_type,
            "session_id": session_id,
            "records": data,
            "total": len(data),
        }

    # --- Telemetry endpoints ---

    @router.get("/telemetry/executions")
    def get_execution_telemetry() -> Dict[str, Any]:
        """Get execution telemetry metrics."""
        metrics = telemetry_collector.get_execution_metrics()
        health = telemetry_collector.get_execution_health()
        return {
            "metrics": metrics,
            "health": health,
        }

    return router
