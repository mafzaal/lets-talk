"""FastAPI endpoints for settings management."""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
import logging

from lets_talk.api.models.settings import (
    SettingsResponse,
    SettingsUpdateSchema,
    SettingsUpdateResponse,
    RestoreDefaultsResponse
)
from lets_talk.core.services.settings import SettingsService
from lets_talk.core.services.settings_init import settings_initializer
from lets_talk.shared.config import LOGGER_NAME

logger = logging.getLogger(f"{LOGGER_NAME}.api.settings")

router = APIRouter(
    prefix="/settings",
    tags=["settings"],
    responses={404: {"description": "Not found"}},
)


def get_settings_service():
    """Dependency to get settings service instance."""
    return SettingsService()


@router.get("/", response_model=SettingsResponse)
async def get_settings(settings_service: SettingsService = Depends(get_settings_service)):
    """
    Get all system settings.
    
    Returns all settings with secrets masked and organized by sections.
    """
    try:
        # Ensure settings are initialized
        if not settings_initializer.ensure_settings_initialized():
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize settings database"
            )
        
        settings = settings_service.get_all_settings()
        sections = settings_service.get_sections()
        
        return SettingsResponse(
            settings=settings,
            sections=sorted(sections)
        )
    
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/", response_model=SettingsUpdateResponse)
async def update_settings(
    update_request: SettingsUpdateSchema,
    settings_service: SettingsService = Depends(get_settings_service)
):
    """
    Update multiple system settings.
    
    Only read-write settings can be updated. Read-only settings will be rejected.
    """
    try:
        # Ensure settings are initialized
        if not settings_initializer.ensure_settings_initialized():
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize settings database"
            )
        
        successful_updates, failed_updates = settings_service.update_settings(
            update_request.settings
        )
        
        success = len(failed_updates) == 0
        message = "All settings updated successfully" if success else "Some settings failed to update"
        
        return SettingsUpdateResponse(
            success=success,
            message=message,
            updated_settings=successful_updates,
            failed_settings=failed_updates
        )
    
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/restore-defaults", response_model=RestoreDefaultsResponse)
async def restore_default_settings(
    settings_service: SettingsService = Depends(get_settings_service)
):
    """
    Restore all read-write settings to their default values.
    
    This will reset all editable settings to their original default values.
    Read-only settings are not affected.
    """
    try:
        # Ensure settings are initialized
        if not settings_initializer.ensure_settings_initialized():
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize settings database"
            )
        
        restored_count = settings_service.restore_defaults()
        
        return RestoreDefaultsResponse(
            success=True,
            message=f"Successfully restored {restored_count} settings to defaults",
            restored_count=restored_count
        )
    
    except Exception as e:
        logger.error(f"Error restoring defaults: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )