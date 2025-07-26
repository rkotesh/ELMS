#!/usr/bin/env python3
"""
Main application launcher for Employee Leave Management System
"""
import os
from app import create_app, db
from app.models import User, LeaveRequest, AttendanceRequest, AuditLog
from flask_migrate import upgrade

app = create_app()

@app.cli.command()
def deploy():
    """Run deployment tasks."""
    # Create database tables
    upgrade()
    
    # Create default admin user if not exists
    admin = User.query.filter_by(email='admin@company.com').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@company.com',
            first_name='System',
            last_name='Administrator',
            role='admin',
            department='IT',
            manager_id=None
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Default admin user created: admin@company.com / admin123')

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'LeaveRequest': LeaveRequest,
        'AttendanceRequest': AttendanceRequest,
        'AuditLog': AuditLog
    }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)