"""
Custom decorators for role-based access control
"""
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def role_required(*roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def manager_required(f):
    """Decorator to require manager or admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        
        if not current_user.is_manager():
            flash('Manager access required.', 'danger')
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
            flash('Administrator access required.', 'danger')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def owns_resource(resource_class, resource_id_param='id', user_field='employee_id'):
    """Decorator to ensure user owns the resource"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            resource_id = kwargs.get(resource_id_param)
            if not resource_id:
                abort(400)
            
            resource = resource_class.query.get_or_404(resource_id)
            
            # Admin can access everything
            if current_user.is_admin():
                return f(*args, **kwargs)
            
            # Check ownership
            if getattr(resource, user_field) != current_user.id:
                flash('You can only access your own resources.', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator