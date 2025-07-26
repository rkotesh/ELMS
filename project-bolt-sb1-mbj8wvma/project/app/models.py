"""
SQLAlchemy models for Employee Leave Management System
"""
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    """User model for employees, managers, and admins"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='employee')  # employee, manager, admin
    department = db.Column(db.String(50), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    hire_date = db.Column(db.Date, default=date.today)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    manager = db.relationship('User', remote_side=[id], backref='subordinates')
    leave_requests = db.relationship('LeaveRequest', backref='employee', lazy='dynamic')
    attendance_requests = db.relationship('AttendanceRequest', backref='employee', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Get full name"""
        return f"{self.first_name} {self.last_name}"
    
    def is_manager(self):
        """Check if user is a manager"""
        return self.role in ['manager', 'admin']
    
    def is_admin(self):
        """Check if user is an admin"""
        return self.role == 'admin'
    
    def get_subordinates(self):
        """Get all subordinates for managers"""
        if self.is_manager():
            return User.query.filter_by(manager_id=self.id).all()
        return []
    
    def __repr__(self):
        return f'<User {self.username}>'

class LeaveRequest(db.Model):
    """Leave request model"""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)  # sick, vacation, personal, etc.
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    days_requested = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, cancelled
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    manager_comments = db.Column(db.Text, nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    manager = db.relationship('User', foreign_keys=[manager_id], backref='managed_leaves')
    
    def can_be_cancelled(self):
        """Check if leave request can be cancelled"""
        return self.status == 'pending' and self.start_date > date.today()
    
    def can_be_edited(self):
        """Check if leave request can be edited"""
        return self.status == 'pending' and self.start_date > date.today()
    
    @property
    def duration_text(self):
        """Get human readable duration"""
        if self.days_requested == 1:
            return "1 day"
        return f"{self.days_requested} days"
    
    def __repr__(self):
        return f'<LeaveRequest {self.id}: {self.employee.username} - {self.leave_type}>'

class AttendanceRequest(db.Model):
    """Attendance correction request model"""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    request_date = db.Column(db.Date, nullable=False)
    request_type = db.Column(db.String(50), nullable=False)  # late_arrival, early_departure, missed_punch
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    manager_comments = db.Column(db.Text, nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    manager = db.relationship('User', foreign_keys=[manager_id], backref='managed_attendance')
    
    def __repr__(self):
        return f'<AttendanceRequest {self.id}: {self.employee.username} - {self.request_type}>'

class LeavePolicy(db.Model):
    """Leave policy configuration"""
    id = db.Column(db.Integer, primary_key=True)
    leave_type = db.Column(db.String(50), nullable=False, unique=True)
    days_allowed = db.Column(db.Integer, nullable=False)
    carry_forward = db.Column(db.Boolean, default=False)
    max_consecutive_days = db.Column(db.Integer, nullable=True)
    requires_approval = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<LeavePolicy {self.leave_type}: {self.days_allowed} days>'

class AuditLog(db.Model):
    """Audit log for tracking user actions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)  # leave_request, user, etc.
    resource_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<AuditLog {self.id}: {self.user.username} - {self.action}>'