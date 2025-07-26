"""
Audit logging utilities
"""
from flask import request
from app import db
from app.models import AuditLog

def log_user_action(user_id, action, resource_type, resource_id=None, details=None):
    """Log user action for audit trail"""
    try:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent') if request else None
        )
        
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        # Log the error but don't break the main functionality
        print(f"Error logging audit action: {e}")
        db.session.rollback()

def get_user_activity(user_id, limit=10):
    """Get recent user activity"""
    return AuditLog.query.filter_by(user_id=user_id)\
                        .order_by(AuditLog.timestamp.desc())\
                        .limit(limit).all()

def get_system_activity(limit=50):
    """Get recent system activity"""
    return AuditLog.query.order_by(AuditLog.timestamp.desc())\
                        .limit(limit).all()