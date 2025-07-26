"""
Authentication utilities
"""
from functools import wraps
from flask import abort
from flask_login import current_user

def role_required(role):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            if role == 'admin' and not current_user.is_admin():
                abort(403)
            elif role == 'manager' and not current_user.is_manager():
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def manager_or_admin_required(f):
    """Decorator to require manager or admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        
        if not current_user.is_manager():
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        
        if not current_user.is_admin():
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function