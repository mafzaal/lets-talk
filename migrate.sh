#!/bin/bash

# Database Migration Management Script for lets_talk
# This script provides convenient access to database migration commands

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Function to show help
show_help() {
    cat << EOF
Database Migration Management for lets_talk

Usage: $0 [command] [options]

Commands:
    status              Show current migration status
    history             Show migration history
    upgrade             Upgrade database to latest version
    upgrade <revision>  Upgrade to specific revision
    downgrade <steps>   Downgrade by number of steps
    downgrade <revision> Downgrade to specific revision
    create <message>    Create new migration
    check               Check for pending migrations
    auto-upgrade        Auto-upgrade if needed
    reset               Reset database (WARNING: destructive)
    help                Show this help message

Examples:
    $0 status                           # Show current status
    $0 upgrade                          # Upgrade to latest
    $0 create "Add user table"          # Create new migration
    $0 downgrade 1                      # Downgrade by 1 step
    $0 check                            # Check for pending migrations

Direct Alembic commands:
    alembic-cmd <args>                  # Run alembic commands directly

Environment:
    DATABASE_URL        Database connection string (from config)
    OUTPUT_DIR          Output directory for database files

EOF
}

# Function to run migration CLI
run_migrate() {
    uv run python backend/lets_talk/core/migrations/cli.py "$@"
}

# Function to run alembic directly
run_alembic() {
    uv run alembic "$@"
}

# Function to reset database (dangerous)
reset_database() {
    print_warning "This will DELETE all data and reset the database!"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        print_status "Resetting database..."
        
        # Remove database file if it exists (for SQLite)
        if [ -f "output/lets_talk.db" ]; then
            rm -f "output/lets_talk.db"
            print_status "Database file removed"
        fi
        
        # Run initial migration
        print_status "Running initial migrations..."
        run_alembic upgrade head
        print_status "Database reset complete"
    else
        print_status "Database reset cancelled"
    fi
}

# Main script logic
case "${1:-help}" in
    "status")
        print_header "Migration Status"
        run_migrate status
        ;;
    "history")
        print_header "Migration History"
        run_migrate history
        ;;
    "upgrade")
        if [ -n "$2" ]; then
            print_header "Upgrading to revision $2"
            run_migrate upgrade --revision "$2"
        else
            print_header "Upgrading to latest version"
            run_migrate upgrade
        fi
        ;;
    "downgrade")
        if [ -n "$2" ]; then
            if [[ "$2" =~ ^[0-9]+$ ]]; then
                print_header "Downgrading by $2 steps"
                run_migrate downgrade --steps "$2"
            else
                print_header "Downgrading to revision $2"
                run_migrate downgrade --revision "$2"
            fi
        else
            print_error "Downgrade requires a revision or number of steps"
            exit 1
        fi
        ;;
    "create")
        if [ -n "$2" ]; then
            print_header "Creating new migration: $2"
            run_migrate create "$2"
        else
            print_error "Create requires a migration message"
            exit 1
        fi
        ;;
    "check")
        print_header "Checking for pending migrations"
        run_migrate check
        ;;
    "auto-upgrade")
        print_header "Auto-upgrading if needed"
        run_migrate auto-upgrade
        ;;
    "reset")
        reset_database
        ;;
    "alembic-cmd")
        shift
        print_header "Running Alembic command: $*"
        run_alembic "$@"
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo
        show_help
        exit 1
        ;;
esac
