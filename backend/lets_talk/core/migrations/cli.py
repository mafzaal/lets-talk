#!/usr/bin/env python3
"""Command-line interface for database migrations."""
import argparse
import sys
from typing import Optional

from lets_talk.core.migrations.manager import get_migration_manager


def cmd_status(args):
    """Show migration status."""
    manager = get_migration_manager()
    status = manager.get_status()
    
    print("=== Migration Status ===")
    print(f"Current revision: {status['current_revision'] or 'None'}")
    print(f"Total migrations: {status['total_migrations']}")
    print(f"Up to date: {'Yes' if status['is_up_to_date'] else 'No'}")
    
    if status['pending_migrations']:
        print(f"\nPending migrations ({len(status['pending_migrations'])}):")
        for migration in status['pending_migrations']:
            print(f"  - {migration['revision'][:8]}: {migration['description']}")
    
    if status['applied_migrations']:
        print(f"\nApplied migrations ({len(status['applied_migrations'])}):")
        for migration in status['applied_migrations']:
            print(f"  - {migration['revision'][:8]}: {migration['description']}")


def cmd_history(args):
    """Show migration history."""
    manager = get_migration_manager()
    history = manager.get_migration_history()
    
    print("=== Migration History ===")
    if not history:
        print("No migrations found.")
        return
    
    for migration in history:
        current_marker = " (CURRENT)" if migration.is_current else ""
        head_marker = " (HEAD)" if migration.is_head else ""
        print(f"{migration.revision[:8]}: {migration.description}{current_marker}{head_marker}")


def cmd_upgrade(args):
    """Upgrade database."""
    manager = get_migration_manager()
    
    if args.revision:
        success = manager.upgrade_to_revision(args.revision)
        action = f"upgrade to revision {args.revision}"
    else:
        success = manager.upgrade_to_head()
        action = "upgrade to head"
    
    if success:
        print(f"Successfully completed {action}")
        return 0
    else:
        print(f"Failed to {action}")
        return 1


def cmd_downgrade(args):
    """Downgrade database."""
    manager = get_migration_manager()
    
    if args.revision:
        success = manager.downgrade_to_revision(args.revision)
        action = f"downgrade to revision {args.revision}"
    elif args.steps:
        success = manager.downgrade_by_steps(args.steps)
        action = f"downgrade by {args.steps} step(s)"
    else:
        print("Error: Must specify either --revision or --steps for downgrade")
        return 1
    
    if success:
        print(f"Successfully completed {action}")
        return 0
    else:
        print(f"Failed to {action}")
        return 1


def cmd_create(args):
    """Create a new migration."""
    manager = get_migration_manager()
    
    revision_id = manager.create_migration(args.message, autogenerate=args.autogenerate)
    
    if revision_id:
        print(f"Successfully created migration: {revision_id}")
        return 0
    else:
        print("Failed to create migration")
        return 1


def cmd_check(args):
    """Check for pending migrations."""
    manager = get_migration_manager()
    
    if manager.check_for_pending_migrations():
        print("Pending migrations found")
        return 1
    else:
        print("No pending migrations")
        return 0


def cmd_auto_upgrade(args):
    """Auto-upgrade if needed."""
    manager = get_migration_manager()
    
    success = manager.auto_upgrade_if_needed()
    
    if success:
        print("Database is up to date")
        return 0
    else:
        print("Failed to upgrade database")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Database migration management for lets_talk",
        prog="migrate"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Status command
    parser_status = subparsers.add_parser("status", help="Show migration status")
    parser_status.set_defaults(func=cmd_status)
    
    # History command
    parser_history = subparsers.add_parser("history", help="Show migration history")
    parser_history.set_defaults(func=cmd_history)
    
    # Upgrade command
    parser_upgrade = subparsers.add_parser("upgrade", help="Upgrade database")
    parser_upgrade.add_argument("--revision", help="Upgrade to specific revision")
    parser_upgrade.set_defaults(func=cmd_upgrade)
    
    # Downgrade command
    parser_downgrade = subparsers.add_parser("downgrade", help="Downgrade database")
    parser_downgrade.add_argument("--revision", help="Downgrade to specific revision")
    parser_downgrade.add_argument("--steps", type=int, help="Downgrade by number of steps")
    parser_downgrade.set_defaults(func=cmd_downgrade)
    
    # Create command
    parser_create = subparsers.add_parser("create", help="Create new migration")
    parser_create.add_argument("message", help="Migration description")
    parser_create.add_argument("--no-autogenerate", dest="autogenerate", action="store_false",
                              default=True, help="Don't auto-generate migration content")
    parser_create.set_defaults(func=cmd_create)
    
    # Check command
    parser_check = subparsers.add_parser("check", help="Check for pending migrations")
    parser_check.set_defaults(func=cmd_check)
    
    # Auto-upgrade command
    parser_auto = subparsers.add_parser("auto-upgrade", help="Auto-upgrade if needed")
    parser_auto.set_defaults(func=cmd_auto_upgrade)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not hasattr(args, 'func'):
        parser.print_help()
        return 1
    
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
