"""Database migration manager for Alembic integration."""
import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from alembic.config import Config
from alembic.command import upgrade, downgrade, current, history, revision, show
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from alembic.environment import EnvironmentContext
from sqlalchemy import create_engine

from lets_talk.shared.config import DATABASE_URL, LOGGER_NAME

logger = logging.getLogger(f"{LOGGER_NAME}.migrations")


@dataclass
class MigrationInfo:
    """Information about a migration."""
    revision: str
    description: str
    is_current: bool = False
    is_head: bool = False


class MigrationManager:
    """Manager for database migrations using Alembic."""
    
    def __init__(self, alembic_cfg_path: Optional[str] = None):
        """Initialize the migration manager."""
        if alembic_cfg_path is None:
            # Default to the alembic.ini in the project root
            project_root = Path(__file__).parent.parent.parent.parent.parent
            alembic_cfg_path = str(project_root / "alembic.ini")
        
        self.alembic_cfg_path = str(alembic_cfg_path)
        self.config = Config(self.alembic_cfg_path)
        
        # Ensure the database URL is set
        self.config.set_main_option("sqlalchemy.url", DATABASE_URL)
        
        logger.info(f"Migration manager initialized with config: {self.alembic_cfg_path}")
        logger.info(f"Using database URL: {DATABASE_URL}")
    
    def get_current_revision(self) -> Optional[str]:
        """Get the current database revision."""
        try:
            engine = create_engine(DATABASE_URL)
            with engine.connect() as connection:
                context = MigrationContext.configure(connection)
                return context.get_current_revision()
        except Exception as e:
            logger.error(f"Failed to get current revision: {e}")
            return None
    
    def get_migration_history(self) -> List[MigrationInfo]:
        """Get the migration history."""
        try:
            script = ScriptDirectory.from_config(self.config)
            revisions = []
            current_rev = self.get_current_revision()
            head_rev = script.get_current_head()
            
            for revision in script.walk_revisions():
                info = MigrationInfo(
                    revision=revision.revision,
                    description=revision.doc or "No description",
                    is_current=revision.revision == current_rev,
                    is_head=revision.revision == head_rev
                )
                revisions.append(info)
            
            return revisions
        except Exception as e:
            logger.error(f"Failed to get migration history: {e}")
            return []
    
    def upgrade_to_head(self) -> bool:
        """Upgrade database to the latest revision."""
        try:
            logger.info("Upgrading database to head...")
            upgrade(self.config, "head")
            logger.info("Database upgrade completed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to upgrade database: {e}")
            return False
    
    def upgrade_to_revision(self, revision: str) -> bool:
        """Upgrade database to a specific revision."""
        try:
            logger.info(f"Upgrading database to revision: {revision}")
            upgrade(self.config, revision)
            logger.info(f"Database upgraded to revision {revision} successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to upgrade to revision {revision}: {e}")
            return False
    
    def downgrade_to_revision(self, revision: str) -> bool:
        """Downgrade database to a specific revision."""
        try:
            logger.info(f"Downgrading database to revision: {revision}")
            downgrade(self.config, revision)
            logger.info(f"Database downgraded to revision {revision} successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to downgrade to revision {revision}: {e}")
            return False
    
    def downgrade_by_steps(self, steps: int = 1) -> bool:
        """Downgrade database by a number of steps."""
        try:
            revision = f"-{steps}"
            logger.info(f"Downgrading database by {steps} step(s)")
            downgrade(self.config, revision)
            logger.info(f"Database downgraded by {steps} step(s) successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to downgrade by {steps} steps: {e}")
            return False
    
    def create_migration(self, message: str, autogenerate: bool = True) -> Optional[str]:
        """Create a new migration."""
        try:
            logger.info(f"Creating new migration: {message}")
            
            # The revision function returns a Script object, but we need to handle it carefully
            script_result = revision(self.config, message, autogenerate=autogenerate)
            
            # Get the latest revision from the script directory
            script = ScriptDirectory.from_config(self.config)
            latest_revision = script.get_current_head()
            
            if latest_revision:
                logger.info(f"Migration created successfully: {latest_revision}")
                return latest_revision
            else:
                logger.warning("Migration creation completed but no revision ID found")
                return None
        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current migration status."""
        current_rev = self.get_current_revision()
        history = self.get_migration_history()
        
        status = {
            "current_revision": current_rev,
            "total_migrations": len(history),
            "pending_migrations": [],
            "applied_migrations": [],
            "is_up_to_date": False
        }
        
        if history:
            head_revision = None
            for migration in history:
                if migration.is_head:
                    head_revision = migration.revision
                
                if migration.is_current:
                    # All migrations after current are pending
                    found_current = False
                    for m in reversed(history):
                        if m.revision == current_rev:
                            found_current = True
                            continue
                        if found_current:
                            status["pending_migrations"].append({
                                "revision": m.revision,
                                "description": m.description
                            })
                        else:
                            status["applied_migrations"].append({
                                "revision": m.revision,
                                "description": m.description
                            })
            
            status["is_up_to_date"] = current_rev == head_revision
        
        return status
    
    def check_for_pending_migrations(self) -> bool:
        """Check if there are pending migrations."""
        status = self.get_status()
        return len(status["pending_migrations"]) > 0
    
    def auto_upgrade_if_needed(self) -> bool:
        """Automatically upgrade if there are pending migrations."""
        if self.check_for_pending_migrations():
            logger.info("Pending migrations detected, auto-upgrading...")
            return self.upgrade_to_head()
        else:
            logger.info("No pending migrations found")
            return True


def get_migration_manager() -> MigrationManager:
    """Get a configured migration manager instance."""
    return MigrationManager()


def ensure_database_is_migrated() -> bool:
    """Ensure the database is up to date with migrations."""
    manager = get_migration_manager()
    return manager.auto_upgrade_if_needed()
