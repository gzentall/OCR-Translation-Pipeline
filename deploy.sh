#!/bin/bash

# ===========================================
# OCR Translation Pipeline - Deployment Script
# ===========================================
#
# This script helps with deployment tasks.
# Run with: bash deploy.sh [command]
#
# Commands:
#   setup       - Initial setup (install dependencies, create dirs)
#   init-db     - Initialize database tables
#   seed-db     - Create admin user
#   test        - Test all integrations
#   backup-db   - Backup database
#   start       - Start application (development)
#   docker      - Build and start Docker containers
#   help        - Show this help message
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_header() {
    echo ""
    echo "============================================"
    echo "$1"
    echo "============================================"
    echo ""
}

# Check if .env exists
check_env() {
    if [ ! -f .env ]; then
        print_warning ".env file not found!"
        print_info "Copy env.template to .env and fill in your values:"
        echo "  cp env.template .env"
        echo "  nano .env"
        return 1
    fi
    return 0
}

# Setup command
cmd_setup() {
    print_header "Setting up OCR Translation Pipeline"
    
    # Check Python version
    print_info "Checking Python version..."
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python $python_version"
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_info "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    print_info "Activating virtual environment..."
    source venv/bin/activate
    
    # Install dependencies
    print_info "Installing Python dependencies..."
    pip install -r requirements.txt
    print_success "Dependencies installed"
    
    # Create directories
    print_info "Creating required directories..."
    mkdir -p letters/inbox
    mkdir -p letters/work
    mkdir -p letters/out/en
    mkdir -p letters/out/pdf
    mkdir -p letters/out/qa
    mkdir -p ocr_storage/documents
    mkdir -p ocr_storage/people
    mkdir -p static/css
    print_success "Directories created"
    
    # Make scripts executable
    print_info "Setting script permissions..."
    chmod +x scripts/*.sh
    print_success "Script permissions set"
    
    # Check for .env
    if [ ! -f .env ]; then
        print_warning ".env file not found"
        print_info "Creating from template..."
        cp env.template .env
        print_success ".env file created - please edit with your values"
    fi
    
    print_success "Setup complete!"
    print_info "Next steps:"
    echo "  1. Edit .env with your configuration"
    echo "  2. Run: bash deploy.sh init-db"
    echo "  3. Run: bash deploy.sh seed-db"
    echo "  4. Run: bash deploy.sh test"
}

# Initialize database
cmd_init_db() {
    print_header "Initializing Database"
    
    check_env || exit 1
    
    source venv/bin/activate
    
    print_info "Creating database tables..."
    python3 << EOF
from scripts.database import init_db, Base, engine
Base.metadata.create_all(engine)
print("✓ Database initialized successfully")
EOF
    
    print_success "Database tables created"
}

# Seed database
cmd_seed_db() {
    print_header "Seeding Database"
    
    check_env || exit 1
    
    source venv/bin/activate
    
    print_info "Creating admin user..."
    python3 seed_database.py
    
    print_success "Database seeded"
}

# Test integrations
cmd_test() {
    print_header "Testing Integrations"
    
    check_env || exit 1
    
    source venv/bin/activate
    
    print_info "Running integration tests..."
    python3 test_integrations.py
}

# Backup database
cmd_backup() {
    print_header "Backing Up Database"
    
    check_env || exit 1
    
    # Load DATABASE_URL from .env
    export $(cat .env | grep DATABASE_URL | xargs)
    
    if [ -z "$DATABASE_URL" ]; then
        print_error "DATABASE_URL not set in .env"
        exit 1
    fi
    
    # Create backup directory
    mkdir -p backups
    
    # Generate backup filename
    backup_file="backups/backup_$(date +%Y%m%d_%H%M%S).sql"
    
    print_info "Creating backup: $backup_file"
    pg_dump "$DATABASE_URL" > "$backup_file"
    
    print_success "Backup created: $backup_file"
    
    # Compress backup
    print_info "Compressing backup..."
    gzip "$backup_file"
    print_success "Compressed: ${backup_file}.gz"
    
    # List recent backups
    print_info "Recent backups:"
    ls -lh backups/ | tail -5
}

# Start application (development)
cmd_start() {
    print_header "Starting Application (Development)"
    
    check_env || exit 1
    
    source venv/bin/activate
    
    print_info "Starting Flask application..."
    print_info "Access at: http://localhost:5001"
    print_warning "Press Ctrl+C to stop"
    
    python3 app.py
}

# Docker deployment
cmd_docker() {
    print_header "Docker Deployment"
    
    check_env || exit 1
    
    print_info "Building Docker images..."
    docker-compose build
    
    print_info "Starting containers..."
    docker-compose up -d
    
    print_success "Containers started"
    
    # Wait for database
    print_info "Waiting for database to be ready..."
    sleep 5
    
    # Initialize database
    print_info "Initializing database..."
    docker-compose exec web python3 -c "from scripts.database import init_db, Base, engine; Base.metadata.create_all(engine)"
    
    # Seed database
    print_info "Seeding database..."
    docker-compose exec web python3 seed_database.py
    
    print_success "Deployment complete!"
    print_info "Application running at: http://localhost:5001"
    print_info "View logs: docker-compose logs -f web"
    print_info "Stop: docker-compose down"
}

# Production start
cmd_production() {
    print_header "Starting in Production Mode"
    
    check_env || exit 1
    
    source venv/bin/activate
    
    # Install gunicorn if not present
    if ! command -v gunicorn &> /dev/null; then
        print_info "Installing gunicorn..."
        pip install gunicorn
    fi
    
    print_info "Starting with Gunicorn..."
    print_info "Workers: 4, Timeout: 300s"
    print_warning "Press Ctrl+C to stop"
    
    gunicorn -w 4 -b 0.0.0.0:5001 --timeout 300 app:app
}

# Help
cmd_help() {
    echo "OCR Translation Pipeline - Deployment Script"
    echo ""
    echo "Usage: bash deploy.sh [command]"
    echo ""
    echo "Commands:"
    echo "  setup       - Initial setup (install dependencies, create dirs)"
    echo "  init-db     - Initialize database tables"
    echo "  seed-db     - Create admin user"
    echo "  test        - Test all integrations"
    echo "  backup-db   - Backup database"
    echo "  start       - Start application (development mode)"
    echo "  production  - Start with Gunicorn (production mode)"
    echo "  docker      - Build and start Docker containers"
    echo "  help        - Show this help message"
    echo ""
    echo "Examples:"
    echo "  bash deploy.sh setup"
    echo "  bash deploy.sh init-db"
    echo "  bash deploy.sh start"
    echo ""
}

# Main script
main() {
    case "$1" in
        setup)
            cmd_setup
            ;;
        init-db)
            cmd_init_db
            ;;
        seed-db)
            cmd_seed_db
            ;;
        test)
            cmd_test
            ;;
        backup-db|backup)
            cmd_backup
            ;;
        start)
            cmd_start
            ;;
        production|prod)
            cmd_production
            ;;
        docker)
            cmd_docker
            ;;
        help|--help|-h)
            cmd_help
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            cmd_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"



