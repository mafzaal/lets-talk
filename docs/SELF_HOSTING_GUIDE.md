# Let's Talk: Self-Hosting Guide 🐨

This comprehensive guide will walk you through setting up Let's Talk using Docker Compose for production self-hosting. Let's Talk is an AI-driven chat component that makes technical blog content interactive and searchable.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Environment Configuration](#environment-configuration)
4. [Docker Compose Architecture](#docker-compose-architecture)
5. [API Key Security](#api-key-security)
6. [Production Deployment](#production-deployment)
7. [Data Management](#data-management)
8. [Monitoring and Health Checks](#monitoring-and-health-checks)
9. [Backup and Recovery](#backup-and-recovery)
10. [Troubleshooting](#troubleshooting)
11. [Advanced Configuration](#advanced-configuration)

## Prerequisites

Before you begin, ensure you have:

- **Docker** (v20.10+) and **Docker Compose** (v2.0+) installed
- **4GB+ RAM** available for containers
- **2GB+ disk space** for databases and content storage
- **Linux/macOS/Windows** with Docker Desktop
- Basic knowledge of Docker and environment variables

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 4GB | 8GB+ |
| Storage | 2GB | 10GB+ |
| CPU | 2 cores | 4+ cores |
| Network | Internet access for AI models | High-speed connection |

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/mafzaal/lets-talk.git
cd lets-talk

# Make startup script executable
chmod +x start-docker.sh
```

### 2. Environment Configuration

Create your production environment file:

```bash
cp .env.example .env.prod
```

Edit `.env.prod` with your configuration (see [Environment Configuration](#environment-configuration) section).

### 3. Launch Services

```bash
# Start all services in detached mode
./start-docker.sh

# Or manually with docker compose
docker compose up -d
```

### 4. Verify Installation

```bash
# Check service status
docker compose ps

# View logs
docker compose logs -f api

# Test the API
curl http://localhost:9124/health
```

Your Let's Talk instance will be available at:
- **API**: http://localhost:9124 (proxied through nginx)
- **Direct API**: http://localhost:9124 (if proxy disabled)
- **API Documentation**: http://localhost:9124/docs

## Environment Configuration

### Core Environment Variables

Create a `.env.prod` file in the project root:

```bash
# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# PostgreSQL settings
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here
LANGGRAPH_DB=langgraph_db
LETS_TALK_DB=lets_talk

# Database URLs (automatically constructed)
POSTGRES_URI=postgresql://postgres:your_secure_password_here@postgres:5432/langgraph_db?sslmode=disable
DATABASE_URL=postgresql://postgres:your_secure_password_here@postgres:5432/lets_talk?sslmode=disable

# =============================================================================
# AI MODEL CONFIGURATION
# =============================================================================

# OpenAI Configuration (primary)
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=openai:gpt-4o-mini
EMBEDDING_MODEL=openai:text-embedding-3-small

# Or use Ollama for local models
# LLM_MODEL=ollama:llama3.1:8b
# EMBEDDING_MODEL=ollama:snowflake-arctic-embed2:latest
# OLLAMA_BASE_URL=http://your-ollama-server:11434

# =============================================================================
# DATA AND STORAGE
# =============================================================================

# Data directories (mounted from host)
DATA_DIR=/data/posts
OUTPUT_DIR=/data/output

# Host paths (adjust to your setup)
DATA_DIR_HOST=/home/user/lets-talk/data
OUTPUT_DIR_HOST=/home/user/lets-talk/output

# Vector database
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=blog_documents
VECTOR_STORAGE_PATH=db/vector_store

# =============================================================================
# PERFORMANCE AND PROCESSING
# =============================================================================

# Content processing
BATCH_SIZE=50
MAX_SEARCH_RESULTS=4
USE_CHUNKING=true
CHUNKING_STRATEGY=semantic
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Redis cache
REDIS_URI=redis://redis:6379

# =============================================================================
# TIMEZONE AND LOCALIZATION
# =============================================================================

TZ=UTC

# =============================================================================
# SECURITY AND AUTHENTICATION
# =============================================================================

# Auto-migration (set to false for production)
AUTO_MIGRATE_ON_STARTUP=true

# User agent
USER_AGENT=lets-talk-api

# =============================================================================
# LOGGING
# =============================================================================

LOG_LEVEL=INFO
LOGGER_NAME=lets-talk
```

### API Authentication Configuration

Create a `.env.auth` file for API key authentication:

```bash
# API Keys for accessing protected endpoints
# Add your API keys here (generate with: openssl rand -hex 32)
API_KEY_1=your_first_api_key_here
API_KEY_2=your_second_api_key_here
```

### Content Configuration

Create a pipeline configuration file (optional, for advanced content processing):

```bash
cp docs/PIPELINE_CONFIG_TEMPLATE.env .env.pipeline
```

Edit `.env.pipeline` to customize content processing, embedding models, and indexing behavior.

## Docker Compose Architecture

Let's Talk uses a microservices architecture with the following components:

### Services Overview

```yaml
services:
  postgres:    # Primary database for content and metadata
  redis:       # Cache and session storage
  qdrant:      # Vector database for semantic search
  api:         # Main Let's Talk API service
  proxy:       # Nginx reverse proxy with authentication
```

### Service Details

#### PostgreSQL Database
- **Image**: `postgres:17`
- **Purpose**: Stores metadata, user data, and system state
- **Storage**: Persistent volume `postgres-storage`
- **Health Check**: `pg_isready`

#### Redis Cache
- **Image**: `redis:8`
- **Purpose**: Caching and session management
- **Health Check**: `redis-cli ping`

#### Qdrant Vector Database
- **Image**: `qdrant/qdrant`
- **Purpose**: Vector embeddings for semantic search
- **Storage**: Persistent volume `qdrant-storage`
- **API**: Available at `http://qdrant:6333`

#### Let's Talk API
- **Image**: Built from source OR `ghcr.io/mafzaal/lets-talk:latest`
- **Purpose**: Main application API
- **Port**: Internal 8000, external via proxy
- **Dependencies**: All other services

#### Nginx Proxy
- **Image**: `nginx:alpine`
- **Purpose**: Load balancing, SSL termination, rate limiting
- **Port**: 9123 (external access point)
- **Features**: API key authentication, CORS, security headers

### Using Pre-built GitHub Package

To use the pre-built image from GitHub Container Registry, modify the `api` service in `docker-compose.yml`:

```yaml
api:
  image: ghcr.io/mafzaal/lets-talk:latest
  # Remove the 'build' section when using pre-built image
  ports:
    - "9124:8000"
  depends_on:
    redis:
      condition: service_healthy
    postgres:
      condition: service_healthy
    qdrant:
      condition: service_started
  # ... rest of configuration remains the same
```

## API Key Security

### Generating Secure API Keys

```bash
# Generate secure API keys
openssl rand -hex 32  # For API_KEY_1
openssl rand -hex 32  # For API_KEY_2

# Or use Python
python -c "import secrets; print(secrets.token_hex(32))"
```

### Authentication Endpoints

- **Public Endpoints**: `/threads/*` - No authentication required
- **Protected Endpoints**: All others require `X-API-Key` header

### Rate Limiting

The nginx proxy implements rate limiting:
- **Public API**: 30 requests/minute per IP
- **Authenticated API**: 100 requests/minute per IP

### Usage Example

```bash
# Public endpoint (no auth required)
curl http://localhost:9123/threads

# Protected endpoint (requires API key)
curl -H "X-API-Key: your_api_key_here" \
     http://localhost:9123/health
```

## Production Deployment

### 1. Security Hardening

```bash
# 1. Update default passwords
# Edit .env.prod with strong passwords

# 2. Secure file permissions
chmod 600 .env.prod .env.auth
chmod 700 data/ output/

# 3. Use non-root user (in docker-compose.yml)
# Add user mapping to services
```

### 2. SSL/TLS Configuration

For production, add SSL termination to nginx:

```nginx
# Add to nginx.conf.template
server {
    listen 443 ssl http2;
    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;
    
    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    
    # ... rest of configuration
}
```

### 3. Resource Limits

Add resource constraints to `docker-compose.yml`:

```yaml
api:
  # ... other configuration
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: '1.0'
      reservations:
        memory: 1G
        cpus: '0.5'
```

### 4. Health Monitoring

Enable comprehensive health checks:

```bash
# Check all services
docker compose ps

# Monitor resource usage
docker stats

# View aggregated logs
docker compose logs -f --tail=100
```

## Data Management

### Directory Structure

```
lets-talk/
├── data/           # Your blog content (markdown files)
├── output/         # Processing outputs and statistics
├── db/            # Local database files (if using SQLite)
└── volumes/       # Docker volume mounts
    ├── postgres/  # PostgreSQL data
    └── qdrant/    # Vector database data
```

### Content Preparation

1. **Blog Posts**: Place markdown files in `data/` directory
2. **Structure**: Use consistent frontmatter:

```markdown
---
title: "Your Blog Post Title"
date: "2024-01-15"
published: true
tags: ["ai", "rag", "tutorial"]
---

# Your content here...
```

### Data Backup

```bash
# Backup all volumes
docker compose down
sudo tar -czf lets-talk-backup-$(date +%Y%m%d).tar.gz \
    /var/lib/docker/volumes/lets-talk_postgres-storage \
    /var/lib/docker/volumes/lets-talk_qdrant-storage \
    data/ output/

# Restore from backup
sudo tar -xzf lets-talk-backup-20240115.tar.gz -C /
```

### Database Maintenance

```bash
# PostgreSQL maintenance
docker compose exec postgres psql -U postgres -d lets_talk

# Qdrant collections
curl http://localhost:9123/v1/collections

# Clear and rebuild vector store
docker compose exec api python -m lets_talk.tools.rebuild_vector_store
```

## Monitoring and Health Checks

### Built-in Health Endpoints

```bash
# API health
curl http://localhost:9123/health

# Detailed system status
curl -H "X-API-Key: your_key" http://localhost:9123/system/status

# Database connection
curl -H "X-API-Key: your_key" http://localhost:9123/system/db-status
```

### Service Monitoring

```bash
# Real-time logs
docker compose logs -f api

# Resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Container health
docker compose ps --format table
```

### Performance Metrics

The API provides metrics endpoints:

```bash
# Processing statistics
curl -H "X-API-Key: your_key" http://localhost:9123/metrics/stats

# Vector store info
curl -H "X-API-Key: your_key" http://localhost:9123/metrics/vectors
```

## Backup and Recovery

### Automated Backup Script

Create `scripts/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/lets-talk"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Stop services gracefully
docker compose down

# Backup data
tar -czf $BACKUP_DIR/data_$DATE.tar.gz data/
tar -czf $BACKUP_DIR/output_$DATE.tar.gz output/

# Backup database volumes
docker run --rm -v lets-talk_postgres-storage:/data -v $BACKUP_DIR:/backup alpine \
    tar -czf /backup/postgres_$DATE.tar.gz -C /data .

docker run --rm -v lets-talk_qdrant-storage:/data -v $BACKUP_DIR:/backup alpine \
    tar -czf /backup/qdrant_$DATE.tar.gz -C /data .

# Restart services
docker compose up -d

echo "Backup completed: $BACKUP_DIR/*_$DATE.tar.gz"
```

### Recovery Procedure

```bash
#!/bin/bash
# Recovery script
BACKUP_DATE="20240115_143000"
BACKUP_DIR="/backups/lets-talk"

# Stop services
docker compose down

# Restore data directories
tar -xzf $BACKUP_DIR/data_$BACKUP_DATE.tar.gz
tar -xzf $BACKUP_DIR/output_$BACKUP_DATE.tar.gz

# Restore database volumes
docker volume rm lets-talk_postgres-storage lets-talk_qdrant-storage
docker volume create lets-talk_postgres-storage
docker volume create lets-talk_qdrant-storage

docker run --rm -v lets-talk_postgres-storage:/data -v $BACKUP_DIR:/backup alpine \
    tar -xzf /backup/postgres_$BACKUP_DATE.tar.gz -C /data

docker run --rm -v lets-talk_qdrant-storage:/data -v $BACKUP_DIR:/backup alpine \
    tar -xzf /backup/qdrant_$BACKUP_DATE.tar.gz -C /data

# Restart services
docker compose up -d
```

## Troubleshooting

### Common Issues

#### 1. Services Won't Start

```bash
# Check logs
docker compose logs api postgres redis qdrant

# Check disk space
df -h

# Check memory
free -h

# Restart specific service
docker compose restart api
```

#### 2. Database Connection Issues

```bash
# Test PostgreSQL connection
docker compose exec postgres psql -U postgres -l

# Check environment variables
docker compose exec api env | grep -E "(DATABASE|POSTGRES)"

# Reset database
docker compose down
docker volume rm lets-talk_postgres-storage
docker compose up -d
```

#### 3. Vector Search Not Working

```bash
# Check Qdrant status
curl http://localhost:9123/qdrant/collections

# Rebuild vector store
docker compose exec api python -c "
from lets_talk.core.pipeline import run_pipeline
run_pipeline(force_recreate=True)
"

# Check embeddings configuration
docker compose exec api env | grep EMBED
```

#### 4. API Key Authentication Failing

```bash
# Verify API keys are loaded
docker compose exec proxy env | grep API_KEY

# Check nginx configuration
docker compose exec proxy nginx -t

# Restart proxy
docker compose restart proxy
```

#### 5. High Memory Usage

```bash
# Check container stats
docker stats

# Optimize batch size
# Edit .env.prod: BATCH_SIZE=25

# Restart with new config
docker compose down && docker compose up -d
```

### Log Analysis

```bash
# API errors
docker compose logs api 2>&1 | grep -i error

# Database issues
docker compose logs postgres 2>&1 | grep -E "(error|fatal)"

# Proxy access logs
docker compose logs proxy 2>&1 | grep -v "GET /health"

# Performance bottlenecks
docker compose logs api 2>&1 | grep -E "(slow|timeout|performance)"
```

### Debug Mode

Enable debug logging:

```bash
# Add to .env.prod
LOG_LEVEL=DEBUG

# Restart API service
docker compose restart api

# View detailed logs
docker compose logs -f api
```

## Advanced Configuration

### Custom Embedding Models

Configure different embedding providers:

```bash
# Ollama (local)
EMBEDDING_MODEL=ollama:snowflake-arctic-embed2:latest
OLLAMA_BASE_URL=http://your-ollama-server:11434

# Hugging Face
EMBEDDING_MODEL=huggingface:sentence-transformers/all-MiniLM-L6-v2

# OpenAI (default)
EMBEDDING_MODEL=openai:text-embedding-3-small
```

### Content Processing Optimization

```bash
# High-performance setup
BATCH_SIZE=100
MAX_CONCURRENT_OPERATIONS=8
ENABLE_BATCH_PROCESSING=true
CHUNK_SIZE=1500
USE_CHUNKING=true
CHUNKING_STRATEGY=semantic

# Memory-constrained setup
BATCH_SIZE=10
MAX_CONCURRENT_OPERATIONS=2
CHUNK_SIZE=500
```

### Multi-Language Support

```bash
# Configure for multiple languages
EMBEDDING_MODEL=huggingface:sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# Language-specific processing
DATA_DIR_PATTERN=*.{md,txt}
INDEX_ONLY_PUBLISHED_POSTS=false
```

### Horizontal Scaling

For high-traffic deployments:

```yaml
# docker-compose.scale.yml
services:
  api:
    deploy:
      replicas: 3
  
  proxy:
    environment:
      - NGINX_UPSTREAM_SERVERS=api:8000,api_2:8000,api_3:8000
```

### Custom Storage Backends

```bash
# S3-compatible storage
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET=your-lets-talk-bucket

# Google Cloud Storage
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCS_BUCKET=your-lets-talk-bucket
```

## Production Checklist

Before going live:

### Security
- [ ] Strong passwords for all services
- [ ] API keys generated and secured
- [ ] File permissions locked down (600/700)
- [ ] SSL/TLS configured
- [ ] Rate limiting enabled
- [ ] CORS configured for your domain

### Performance
- [ ] Resource limits configured
- [ ] Monitoring setup
- [ ] Log rotation configured
- [ ] Backup automation implemented

### Reliability
- [ ] Health checks working
- [ ] Graceful shutdown tested
- [ ] Recovery procedures documented
- [ ] Monitoring alerts configured

### Content
- [ ] Blog content prepared and indexed
- [ ] Vector store built successfully
- [ ] Search functionality tested
- [ ] API responses validated

## Support and Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/mafzaal/lets-talk/issues)
- **Documentation**: [Complete API documentation](docs/API_DOCUMENTATION.md)
- **Examples**: Check the `examples/` directory for usage samples
- **Live Demo**: [Try it at TheDataGuy.PRO](https://thedataguy.pro/)

---

**Happy self-hosting! 🚀**

For additional help, check the troubleshooting section or open an issue on GitHub.
