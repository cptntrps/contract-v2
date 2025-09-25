"""
Security audit logging for Contract Analyzer

Provides comprehensive security event logging and monitoring capabilities.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from enum import Enum


class SecurityEventType(Enum):
    """Security event types for categorization"""
    FILE_UPLOAD = "file_upload"
    FILE_VALIDATION_FAILED = "file_validation_failed"
    PATH_TRAVERSAL_ATTEMPT = "path_traversal_attempt"
    SUSPICIOUS_FILENAME = "suspicious_filename"
    LARGE_FILE_UPLOAD = "large_file_upload"
    INVALID_MIME_TYPE = "invalid_mime_type"
    API_ACCESS = "api_access"
    AUTHENTICATION_FAILED = "authentication_failed"
    PROMPT_MODIFIED = "prompt_modified"
    CONFIG_CHANGED = "config_changed"
    SERVER_STARTED = "server_started"
    SERVER_STOPPED = "server_stopped"
    ERROR_OCCURRED = "error_occurred"
    REPORT_DOWNLOADED = "report_downloaded"
    REDLINED_DOCUMENT_DOWNLOADED = "redlined_document_downloaded"
    CHANGES_TABLE_DOWNLOADED = "changes_table_downloaded"
    REPORT_GENERATION_STARTED = "report_generation_started"
    REPORT_GENERATION_COMPLETED = "report_generation_completed"
    REPORT_GENERATION_FAILED = "report_generation_failed"
    REPORT_GENERATION_ERROR = "report_generation_error"


class SecurityAuditor:
    """
    Security audit logging system
    """
    
    def __init__(self, log_file: str = "security_audit.log"):
        """Initialize security auditor"""
        self.log_file = Path(log_file)
        self.logger = logging.getLogger("security_audit")
        
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup file handler for security logs
        handler = logging.FileHandler(self.log_file)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        if not self.logger.handlers:
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_security_event(
        self,
        event_type: SecurityEventType,
        details: Dict[str, Any],
        severity: str = "INFO",
        user_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Log a security event
        
        Args:
            event_type: Type of security event
            details: Event details dictionary
            severity: Event severity (INFO, WARNING, ERROR, CRITICAL)
            user_ip: User IP address if available
            user_agent: User agent string if available
        """
        event_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type.value,
            "severity": severity,
            "details": details,
            "user_ip": user_ip,
            "user_agent": user_agent,
            "session_id": self._generate_session_id()
        }
        
        # Log as JSON for structured logging
        log_message = json.dumps(event_data, ensure_ascii=False)
        
        # Log at appropriate level
        if severity == "CRITICAL":
            self.logger.critical(log_message)
        elif severity == "ERROR":
            self.logger.error(log_message)
        elif severity == "WARNING":
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def log_file_upload(
        self,
        filename: str,
        file_size: int,
        file_hash: str,
        validation_result: Dict[str, Any],
        user_ip: Optional[str] = None
    ):
        """Log file upload event"""
        details = {
            "filename": filename,
            "file_size": file_size,
            "file_hash": file_hash,
            "validation_passed": validation_result.get("validation_passed", False),
            "mime_type": validation_result.get("mime_type"),
            "extension": validation_result.get("extension")
        }
        
        severity = "INFO" if validation_result.get("validation_passed") else "WARNING"
        event_type = SecurityEventType.FILE_UPLOAD
        
        if not validation_result.get("validation_passed"):
            event_type = SecurityEventType.FILE_VALIDATION_FAILED
            severity = "ERROR"
        
        self.log_security_event(event_type, details, severity, user_ip)
    
    def log_path_traversal_attempt(
        self,
        attempted_path: str,
        user_ip: Optional[str] = None
    ):
        """Log path traversal attempt"""
        details = {
            "attempted_path": attempted_path,
            "attack_type": "path_traversal"
        }
        
        self.log_security_event(
            SecurityEventType.PATH_TRAVERSAL_ATTEMPT,
            details,
            "CRITICAL",
            user_ip
        )
    
    def log_suspicious_filename(
        self,
        filename: str,
        reason: str,
        user_ip: Optional[str] = None
    ):
        """Log suspicious filename detection"""
        details = {
            "filename": filename,
            "reason": reason,
            "attack_type": "suspicious_filename"
        }
        
        self.log_security_event(
            SecurityEventType.SUSPICIOUS_FILENAME,
            details,
            "WARNING",
            user_ip
        )
    
    def log_api_access(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float,
        user_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log API access"""
        details = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "response_time_ms": round(response_time * 1000, 2)
        }
        
        severity = "INFO"
        if status_code >= 400:
            severity = "WARNING"
        if status_code >= 500:
            severity = "ERROR"
        
        self.log_security_event(
            SecurityEventType.API_ACCESS,
            details,
            severity,
            user_ip,
            user_agent
        )
    
    def log_prompt_modification(
        self,
        prompt_type: str,
        old_version: str,
        new_version: str,
        user_ip: Optional[str] = None
    ):
        """Log prompt modification"""
        details = {
            "prompt_type": prompt_type,
            "old_version": old_version,
            "new_version": new_version,
            "action": "prompt_modified"
        }
        
        self.log_security_event(
            SecurityEventType.PROMPT_MODIFIED,
            details,
            "INFO",
            user_ip
        )
    
    def log_config_change(
        self,
        config_section: str,
        changed_keys: list,
        user_ip: Optional[str] = None
    ):
        """Log configuration change"""
        details = {
            "config_section": config_section,
            "changed_keys": changed_keys,
            "action": "config_changed"
        }
        
        self.log_security_event(
            SecurityEventType.CONFIG_CHANGED,
            details,
            "INFO",
            user_ip
        )
    
    def log_server_event(self, event_type: str, details: Dict[str, Any]):
        """Log server lifecycle events"""
        if event_type == "started":
            event = SecurityEventType.SERVER_STARTED
        elif event_type == "stopped":
            event = SecurityEventType.SERVER_STOPPED
        else:
            event = SecurityEventType.ERROR_OCCURRED
        
        self.log_security_event(event, details, "INFO")
    
    def get_security_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get security event summary for the last N hours
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Security summary dictionary
        """
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
            
            events = []
            for line in lines:
                try:
                    # Extract JSON from log line
                    json_start = line.find('{')
                    if json_start > 0:
                        event_data = json.loads(line[json_start:])
                        event_time = datetime.fromisoformat(event_data['timestamp']).timestamp()
                        
                        if event_time >= cutoff_time:
                            events.append(event_data)
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
            
            # Analyze events
            summary = {
                "total_events": len(events),
                "time_range_hours": hours,
                "events_by_type": {},
                "events_by_severity": {},
                "top_source_ips": {},
                "recent_critical_events": []
            }
            
            for event in events:
                # Count by type
                event_type = event.get('event_type', 'unknown')
                summary["events_by_type"][event_type] = summary["events_by_type"].get(event_type, 0) + 1
                
                # Count by severity
                severity = event.get('severity', 'INFO')
                summary["events_by_severity"][severity] = summary["events_by_severity"].get(severity, 0) + 1
                
                # Count by IP
                user_ip = event.get('user_ip')
                if user_ip:
                    summary["top_source_ips"][user_ip] = summary["top_source_ips"].get(user_ip, 0) + 1
                
                # Collect critical events
                if severity == "CRITICAL":
                    summary["recent_critical_events"].append(event)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to generate security summary: {e}")
            return {"error": str(e)}
    
    def _generate_session_id(self) -> str:
        """Generate a session ID for correlation"""
        import hashlib
        import random
        
        data = f"{time.time()}{random.randint(1000, 9999)}"
        return hashlib.md5(data.encode()).hexdigest()[:8]


# Create default auditor instance
default_auditor = SecurityAuditor()

# Convenience functions
def audit_security_event(
    event_type: SecurityEventType,
    details: Dict[str, Any],
    severity: str = "INFO",
    user_ip: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Log security event using default auditor"""
    default_auditor.log_security_event(event_type, details, severity, user_ip, user_agent)

def audit_file_upload(
    filename: str,
    file_size: int,
    file_hash: str,
    validation_result: Dict[str, Any],
    user_ip: Optional[str] = None
):
    """Log file upload using default auditor"""
    default_auditor.log_file_upload(filename, file_size, file_hash, validation_result, user_ip)

def audit_api_access(
    endpoint: str,
    method: str,
    status_code: int,
    response_time: float,
    user_ip: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Log API access using default auditor"""
    default_auditor.log_api_access(endpoint, method, status_code, response_time, user_ip, user_agent)


__all__ = [
    'SecurityAuditor',
    'SecurityEventType',
    'default_auditor',
    'audit_security_event',
    'audit_file_upload',
    'audit_api_access'
]