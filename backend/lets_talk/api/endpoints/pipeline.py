"""Pipeline management API endpoints."""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse

from datetime import datetime, timezone

from lets_talk.api.models.pipeline import (
    PipelineRunRequest, PipelineRunResponse, PipelineReportsResponse
)
from lets_talk.api.models.common import JobConfig
from lets_talk.shared.config import OUTPUT_DIR

router = APIRouter(prefix="/pipeline", tags=["pipeline"])
logger = logging.getLogger(__name__)


@router.post("/run", response_model=PipelineRunResponse)
async def run_pipeline(
    background_tasks: BackgroundTasks,
    request: Optional[PipelineRunRequest] = None
):
    """Run the pipeline immediately with optional configuration."""
    # Use provided config or create one with defaults
    if request and request.config:
        config = request.config
    else:
        config = JobConfig.with_defaults()
    
    pipeline_config = config.model_dump()
    pipeline_config["job_id"] = f"manual_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    
    # Use background task to avoid blocking the API
    from lets_talk.core.pipeline.jobs import simple_pipeline_job
    background_tasks.add_task(simple_pipeline_job, pipeline_config)
    
    return PipelineRunResponse(
        message="Pipeline execution started",
        job_id=pipeline_config["job_id"]
    )


@router.get("/reports", response_model=PipelineReportsResponse)
async def list_pipeline_reports():
    """List available pipeline execution reports."""
    try:
        reports_dir = Path(OUTPUT_DIR)
        if not reports_dir.exists():
            return PipelineReportsResponse(reports=[])
        
        report_files = list(reports_dir.glob("job_report_*.json"))
        reports = []
        
        for file_path in sorted(report_files, key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                with open(file_path, 'r') as f:
                    report = json.load(f)
                    report["filename"] = file_path.name
                    reports.append(report)
            except Exception as e:
                logger.error(f"Failed to load report {file_path}: {e}")
        
        return PipelineReportsResponse(reports=reports)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/{report_filename}")
async def get_pipeline_report(report_filename: str):
    """Get details of a specific pipeline execution report."""
    try:
        report_path = Path(OUTPUT_DIR) / report_filename
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Report not found")
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
