"""Pydantic schemas for settings API."""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime


class SettingSchema(BaseModel):
    """Schema for individual setting representation."""
    key: str = Field(..., description="Unique identifier for the setting")
    value: str = Field(..., description="Current value of the setting")
    default_value: str = Field(..., description="Default value of the setting")
    data_type: str = Field(..., description="Data type: string, integer, boolean, float")
    is_secret: bool = Field(..., description="Whether this is a secret setting")
    section: str = Field(..., description="Setting section/category")
    description: Optional[str] = Field(None, description="Human-readable description")
    is_read_only: bool = Field(..., description="Whether this setting is read-only")
    created_at: datetime = Field(..., description="When the setting was created")
    updated_at: datetime = Field(..., description="When the setting was last updated")

    class Config:
        from_attributes = True


class SettingDisplaySchema(BaseModel):
    """Schema for displaying settings (masks secrets)."""
    key: str
    value: str  # This will be masked if is_secret is True
    default_value: str
    data_type: str
    is_secret: bool
    section: str
    description: Optional[str]
    is_read_only: bool

    class Config:
        from_attributes = True


class SettingUpdateSchema(BaseModel):
    """Schema for updating a single setting."""
    key: str = Field(..., description="Setting key to update")
    value: str = Field(..., description="New value for the setting")


class SettingsUpdateSchema(BaseModel):
    """Schema for updating multiple settings."""
    settings: List[SettingUpdateSchema] = Field(..., description="List of settings to update")


class SettingsResponse(BaseModel):
    """Response schema for settings list."""
    settings: List[SettingDisplaySchema] = Field(..., description="List of all settings")
    sections: List[str] = Field(..., description="Available setting sections")


class SettingsUpdateResponse(BaseModel):
    """Response schema for settings update."""
    success: bool = Field(..., description="Whether the update was successful")
    message: str = Field(..., description="Success or error message")
    updated_settings: List[str] = Field(..., description="List of updated setting keys")
    failed_settings: List[Dict[str, str]] = Field(..., description="List of failed updates with errors")


class RestoreDefaultsResponse(BaseModel):
    """Response schema for restore defaults."""
    success: bool = Field(..., description="Whether the restore was successful")
    message: str = Field(..., description="Success or error message")
    restored_count: int = Field(..., description="Number of settings restored to defaults")


class SettingError(BaseModel):
    """Schema for setting-related errors."""
    key: str = Field(..., description="Setting key that caused the error")
    error: str = Field(..., description="Error message")