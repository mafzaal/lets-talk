"""
System health checking module.

This module provides comprehensive health checks for the entire
incremental indexing system including vector store, metadata, and configuration.
"""

import logging
import os
import time
from typing import Dict, Any

import pandas as pd

from lets_talk.shared.config import (
    BATCH_SIZE,
    CHECKSUM_ALGORITHM,
    CHUNK_SIZE,
    MAX_BACKUP_FILES,
    METADATA_CSV_FILE
)
from .performance_monitor import PerformanceMonitor
from .vector_store_manager import VectorStoreManager
from ..utils.common_utils import handle_exceptions

logger = logging.getLogger(__name__)


class HealthChecker:
    """
    Performs comprehensive health checks of the pipeline system.
    """
    
    def __init__(
        self,
        storage_path: str,
        collection_name: str,
        qdrant_url: str,
        embedding_model: str,
        metadata_csv_path: str = METADATA_CSV_FILE
    ):
        """
        Initialize the health checker.
        
        Args:
            storage_path: Path to the vector store
            collection_name: Name of the collection
            qdrant_url: Qdrant server URL
            embedding_model: Embedding model name
            metadata_csv_path: Path to metadata CSV file
        """
        self.storage_path = storage_path
        self.collection_name = collection_name
        self.qdrant_url = qdrant_url
        self.embedding_model = embedding_model
        self.metadata_csv_path = metadata_csv_path
        
        self.vector_store_manager = VectorStoreManager(
            storage_path, collection_name, qdrant_url, embedding_model
        )
        self.performance_monitor = PerformanceMonitor()
    
    @handle_exceptions(default_return={})
    def comprehensive_health_check(self) -> Dict[str, Any]:
        """
        Perform a comprehensive health check of the entire system.
        
        Returns:
            Dictionary with detailed health check results
        """
        health_report = {
            "overall_status": "unknown",
            "timestamp": time.time(),
            "checks": {},
            "recommendations": [],
            "errors": []
        }
        
        try:
            # Check 1: Vector store health
            logger.info("Checking vector store health...")
            health_report["checks"]["vector_store"] = self._check_vector_store_health()
            
            # Check 2: Metadata file integrity
            logger.info("Checking metadata file integrity...")
            health_report["checks"]["metadata"] = self._check_metadata_integrity()
            
            # Check 3: System resources
            logger.info("Checking system resources...")
            health_report["checks"]["system_resources"] = self._check_system_resources()
            
            # Check 4: Configuration validation
            logger.info("Checking configuration...")
            health_report["checks"]["configuration"] = self._check_configuration()
            
            # Check 5: Backup file management
            logger.info("Checking backup files...")
            health_report["checks"]["backups"] = self._check_backup_files()
            
            # Generate overall status and recommendations
            self._analyze_health_results(health_report)
            
            logger.info(f"System health check completed: {health_report['overall_status']}")
            return health_report
            
        except Exception as e:
            health_report["overall_status"] = "error"
            health_report["errors"].append(f"Health check failed: {e}")
            logger.error(f"System health check failed: {e}")
            return health_report
    
    def _check_vector_store_health(self) -> Dict[str, Any]:
        """Check vector store health and accessibility."""
        try:
            vector_store_healthy = self.vector_store_manager.validate_health()
            return {
                "status": "healthy" if vector_store_healthy else "unhealthy",
                "details": "Vector store is accessible and responsive" if vector_store_healthy else "Vector store is not accessible",
                "url": self.qdrant_url or self.storage_path,
                "collection": self.collection_name
            }
        except Exception as e:
            return {
                "status": "error",
                "details": f"Error checking vector store: {e}",
                "url": self.qdrant_url or self.storage_path,
                "collection": self.collection_name
            }
    
    def _check_metadata_integrity(self) -> Dict[str, Any]:
        """Check metadata file integrity and readability."""
        metadata_exists = os.path.exists(self.metadata_csv_path)
        metadata_readable = False
        metadata_record_count = 0
        error_details = None
        
        if metadata_exists:
            try:
                df = pd.read_csv(self.metadata_csv_path)
                metadata_readable = True
                metadata_record_count = len(df)
                
                # Check for required columns
                required_columns = ["source", "content_checksum", "indexed_timestamp"]
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    error_details = f"Missing required columns: {missing_columns}"
                    
            except Exception as e:
                error_details = f"Error reading metadata file: {e}"
        
        status = "healthy" if (metadata_exists and metadata_readable and not error_details) else "unhealthy"
        
        return {
            "status": status,
            "exists": metadata_exists,
            "readable": metadata_readable,
            "record_count": metadata_record_count,
            "file_path": self.metadata_csv_path,
            "error_details": error_details
        }
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource availability."""
        system_stats = self.performance_monitor.get_system_stats()
        
        memory_ok = True
        disk_ok = True
        cpu_ok = True
        warnings = []
        
        if "memory_percent" in system_stats:
            if system_stats["memory_percent"] > 90:
                memory_ok = False
                warnings.append(f"High memory usage: {system_stats['memory_percent']:.1f}%")
            elif system_stats["memory_percent"] > 80:
                warnings.append(f"Elevated memory usage: {system_stats['memory_percent']:.1f}%")
        
        if "disk_percent" in system_stats:
            if system_stats["disk_percent"] > 95:
                disk_ok = False
                warnings.append(f"Very low disk space: {system_stats['disk_percent']:.1f}% used")
            elif system_stats["disk_percent"] > 85:
                warnings.append(f"Low disk space: {system_stats['disk_percent']:.1f}% used")
        
        if "cpu_percent" in system_stats:
            if system_stats["cpu_percent"] > 95:
                cpu_ok = False
                warnings.append(f"Very high CPU usage: {system_stats['cpu_percent']:.1f}%")
            elif system_stats["cpu_percent"] > 80:
                warnings.append(f"High CPU usage: {system_stats['cpu_percent']:.1f}%")
        
        # Determine overall status
        if not (memory_ok and disk_ok and cpu_ok):
            status = "unhealthy"
        elif warnings:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "memory_ok": memory_ok,
            "disk_ok": disk_ok,
            "cpu_ok": cpu_ok,
            "warnings": warnings,
            "details": system_stats
        }
    
    def _check_configuration(self) -> Dict[str, Any]:
        """Check configuration parameters for validity."""
        config_valid = True
        config_issues = []
        
        # Check batch size
        if BATCH_SIZE <= 0:
            config_valid = False
            config_issues.append("Invalid batch size: must be positive")
        
        # Check chunk size
        if CHUNK_SIZE <= 0:
            config_valid = False
            config_issues.append("Invalid chunk size: must be positive")
        
        # Check checksum algorithm
        if CHECKSUM_ALGORITHM.lower() not in ["sha256", "md5"]:
            config_valid = False
            config_issues.append(f"Invalid checksum algorithm: {CHECKSUM_ALGORITHM}")
        
        # Check paths
        if not os.path.isabs(self.metadata_csv_path):
            config_issues.append("Metadata CSV path should be absolute")
        
        # Check embedding model
        if not self.embedding_model:
            config_valid = False
            config_issues.append("Embedding model not specified")
        
        return {
            "status": "healthy" if config_valid else "unhealthy",
            "issues": config_issues,
            "batch_size": BATCH_SIZE,
            "chunk_size": CHUNK_SIZE,
            "checksum_algorithm": CHECKSUM_ALGORITHM,
            "embedding_model": self.embedding_model
        }
    
    def _check_backup_files(self) -> Dict[str, Any]:
        """Check backup file management."""
        backup_files = []
        if os.path.exists(self.metadata_csv_path):
            import glob
            backup_pattern = f"{self.metadata_csv_path}.backup.*"
            backup_files = glob.glob(backup_pattern)
        
        backup_count_ok = len(backup_files) <= MAX_BACKUP_FILES * 2  # Allow some buffer
        
        # Check backup file ages
        old_backups = []
        current_time = time.time()
        max_age_days = 30
        
        for backup_file in backup_files:
            try:
                file_age_days = (current_time - os.path.getmtime(backup_file)) / (24 * 3600)
                if file_age_days > max_age_days:
                    old_backups.append((backup_file, file_age_days))
            except OSError:
                pass
        
        warnings = []
        if not backup_count_ok:
            warnings.append(f"Too many backup files: {len(backup_files)} (max recommended: {MAX_BACKUP_FILES})")
        if old_backups:
            warnings.append(f"{len(old_backups)} backup files older than {max_age_days} days")
        
        return {
            "status": "healthy" if backup_count_ok and not old_backups else "warning",
            "backup_count": len(backup_files),
            "max_allowed": MAX_BACKUP_FILES,
            "old_backup_count": len(old_backups),
            "warnings": warnings
        }
    
    def _analyze_health_results(self, health_report: Dict[str, Any]) -> None:
        """Analyze health check results and generate overall status and recommendations."""
        checks = health_report["checks"]
        
        # Determine overall status
        check_statuses = [check["status"] for check in checks.values()]
        if any(status == "error" for status in check_statuses):
            health_report["overall_status"] = "error"
        elif any(status == "unhealthy" for status in check_statuses):
            health_report["overall_status"] = "unhealthy"
        elif any(status == "warning" for status in check_statuses):
            health_report["overall_status"] = "warning"
        else:
            health_report["overall_status"] = "healthy"
        
        # Generate recommendations
        recommendations = []
        
        # Vector store recommendations
        if checks["vector_store"]["status"] != "healthy":
            recommendations.append("Check vector store configuration and connectivity")
        
        # Metadata recommendations
        metadata_check = checks["metadata"]
        if not metadata_check["exists"] or not metadata_check["readable"]:
            recommendations.append("Recreate or repair metadata file")
        if metadata_check.get("error_details"):
            recommendations.append(f"Fix metadata issues: {metadata_check['error_details']}")
        
        # System resource recommendations
        resource_check = checks["system_resources"]
        if not resource_check["memory_ok"]:
            recommendations.append("Reduce batch size or free up system memory")
        if not resource_check["disk_ok"]:
            recommendations.append("Free up disk space")
        if not resource_check["cpu_ok"]:
            recommendations.append("Reduce processing load or upgrade CPU")
        
        # Configuration recommendations
        if checks["configuration"]["status"] != "healthy":
            recommendations.append("Review and fix configuration parameters")
        
        # Backup recommendations
        backup_check = checks["backups"]
        if backup_check["status"] != "healthy":
            if backup_check["backup_count"] > MAX_BACKUP_FILES:
                recommendations.append("Clean up old backup files")
            if backup_check.get("old_backup_count", 0) > 0:
                recommendations.append("Remove very old backup files")
        
        health_report["recommendations"] = recommendations
    
    def quick_health_check(self) -> Dict[str, str]:
        """
        Perform a quick health check with minimal resource usage.
        
        Returns:
            Dictionary with basic health status
        """
        quick_status = {
            "overall": "unknown",
            "vector_store": "unknown",
            "metadata": "unknown",
            "timestamp": str(time.time())
        }
        
        try:
            # Quick vector store check
            if self.vector_store_manager.validate_health():
                quick_status["vector_store"] = "healthy"
            else:
                quick_status["vector_store"] = "unhealthy"
            
            # Quick metadata check
            if os.path.exists(self.metadata_csv_path):
                quick_status["metadata"] = "healthy"
            else:
                quick_status["metadata"] = "missing"
            
            # Overall status
            if quick_status["vector_store"] == "healthy" and quick_status["metadata"] == "healthy":
                quick_status["overall"] = "healthy"
            else:
                quick_status["overall"] = "issues_detected"
            
        except Exception as e:
            quick_status["overall"] = "error"
            quick_status["error"] = str(e)
        
        return quick_status


# Convenience function for backward compatibility
def comprehensive_system_health_check(
    storage_path: str,
    collection_name: str,
    qdrant_url: str,
    embedding_model: str,
    metadata_csv_path: str
) -> Dict[str, Any]:
    """
    Perform a comprehensive health check of the entire incremental indexing system.
    
    Args:
        storage_path: Path to the vector store
        collection_name: Name of the collection
        qdrant_url: Qdrant server URL
        embedding_model: Embedding model name
        metadata_csv_path: Path to metadata CSV file
        
    Returns:
        Dictionary with detailed health check results
    """
    checker = HealthChecker(
        storage_path, collection_name, qdrant_url, embedding_model, metadata_csv_path
    )
    return checker.comprehensive_health_check()
