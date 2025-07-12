"""Settings service for managing system configuration."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from lets_talk.core.models.settings import Setting, get_settings_session
from lets_talk.api.models.settings import SettingDisplaySchema, SettingUpdateSchema
from lets_talk.shared.config import LOGGER_NAME

logger = logging.getLogger(f"{LOGGER_NAME}.settings")


class SettingsService:
    """Service for managing system settings."""
    
    def __init__(self):
        self.session: Optional[Session] = None
    
    def _get_session(self) -> Session:
        """Get database session."""
        if self.session is None:
            self.session = get_settings_session()
        return self.session
    
    def _close_session(self):
        """Close database session."""
        if self.session:
            self.session.close()
            self.session = None
    
    def get_all_settings(self) -> List[SettingDisplaySchema]:
        """Get all settings with secret masking."""
        session = self._get_session()
        try:
            settings = session.query(Setting).all()
            result = []
            
            for setting in settings:
                display_setting = SettingDisplaySchema(
                    key=setting.key,
                    value="***HIDDEN***" if setting.is_secret else setting.value,
                    default_value=setting.default_value,
                    data_type=setting.data_type,
                    is_secret=setting.is_secret,
                    section=setting.section,
                    description=setting.description,
                    is_read_only=setting.is_read_only
                )
                result.append(display_setting)
            
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error getting settings: {e}")
            return []
        finally:
            self._close_session()
    
    def get_sections(self) -> List[str]:
        """Get all available setting sections."""
        session = self._get_session()
        try:
            sections = session.query(Setting.section).distinct().all()
            return [section[0] for section in sections]
        except SQLAlchemyError as e:
            logger.error(f"Database error getting sections: {e}")
            return []
        finally:
            self._close_session()
    
    def update_settings(self, updates: List[SettingUpdateSchema]) -> Tuple[List[str], List[Dict[str, str]]]:
        """
        Update multiple settings.
        
        Returns:
            Tuple of (successful_updates, failed_updates)
        """
        session = self._get_session()
        successful_updates = []
        failed_updates = []
        
        try:
            for update in updates:
                try:
                    setting = session.query(Setting).filter(Setting.key == update.key).first()
                    if not setting:
                        failed_updates.append({
                            "key": update.key,
                            "error": "Setting not found"
                        })
                        continue
                    
                    if setting.is_read_only:
                        failed_updates.append({
                            "key": update.key,
                            "error": "Setting is read-only"
                        })
                        continue
                    
                    # Validate data type
                    if not self._validate_setting_value(update.value, setting.data_type):
                        failed_updates.append({
                            "key": update.key,
                            "error": f"Invalid value for data type {setting.data_type}"
                        })
                        continue
                    
                    # Update the setting
                    setting.value = update.value
                    session.commit()
                    successful_updates.append(update.key)
                    
                except SQLAlchemyError as e:
                    logger.error(f"Error updating setting {update.key}: {e}")
                    failed_updates.append({
                        "key": update.key,
                        "error": str(e)
                    })
                    session.rollback()
            
            return successful_updates, failed_updates
        
        except Exception as e:
            logger.error(f"Unexpected error updating settings: {e}")
            session.rollback()
            return [], [{"key": "general", "error": str(e)}]
        finally:
            self._close_session()
    
    def restore_defaults(self) -> int:
        """Restore all read-write settings to their default values."""
        session = self._get_session()
        try:
            # Only restore read-write settings
            settings = session.query(Setting).filter(Setting.is_read_only == False).all()
            
            restored_count = 0
            for setting in settings:
                setting.value = setting.default_value
                restored_count += 1
            
            session.commit()
            logger.info(f"Restored {restored_count} settings to defaults")
            return restored_count
        
        except SQLAlchemyError as e:
            logger.error(f"Database error restoring defaults: {e}")
            session.rollback()
            return 0
        finally:
            self._close_session()
    
    def _validate_setting_value(self, value: str, data_type: str) -> bool:
        """Validate that a value matches the expected data type."""
        try:
            if data_type == "integer":
                int(value)
            elif data_type == "float":
                float(value)
            elif data_type == "boolean":
                if value.lower() not in ["true", "false"]:
                    return False
            # string type doesn't need validation
            return True
        except (ValueError, TypeError):
            return False
    
    def get_setting_by_key(self, key: str) -> Optional[Setting]:
        """Get a specific setting by key."""
        session = self._get_session()
        try:
            setting = session.query(Setting).filter(Setting.key == key).first()
            return setting
        except SQLAlchemyError as e:
            logger.error(f"Database error getting setting {key}: {e}")
            return None
        finally:
            self._close_session()
    
    def create_setting(self, key: str, value: str, default_value: str, data_type: str,
                      is_secret: bool = False, section: str = "General", 
                      description: Optional[str] = None, is_read_only: bool = False) -> bool:
        """Create a new setting."""
        session = self._get_session()
        try:
            # Check if setting already exists
            existing = session.query(Setting).filter(Setting.key == key).first()
            if existing:
                logger.warning(f"Setting {key} already exists")
                return False
            
            setting = Setting(
                key=key,
                value=value,
                default_value=default_value,
                data_type=data_type,
                is_secret=is_secret,
                section=section,
                description=description,
                is_read_only=is_read_only
            )
            
            session.add(setting)
            session.commit()
            logger.info(f"Created new setting: {key}")
            return True
        
        except SQLAlchemyError as e:
            logger.error(f"Database error creating setting {key}: {e}")
            session.rollback()
            return False
        finally:
            self._close_session()