"""
Admin routes
"""
from flask import render_template, redirect, url_for, flash, request, jsonify, make_response
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from app.admin import bp
from app import db
from app.models import User, LeaveRequest, AttendanceRequest, AuditLog, LeavePolicy
from app.forms import UserForm, LeavePolicyForm, SearchForm
from app.auth.utils import admin_required
from app.utils.audit import log_user_action
from app.utils.reports import generate_leave_report, generate_user_report

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    # System statistics
    total_users = User.query.count()
    total_employees = User.query.filter_by(role='employee').count()
    total_managers = User.query.filter_by(role='manager').count()
    
    # Request statistics
    pending_leaves = LeaveRequest.query.filter_by(status='pending').count()
    approved_leaves = LeaveRequest.query.filter_by(status='approved').count()
    rejected_leaves = LeaveRequest.query.filter_by(status='rejected').count()
    
    # Recent activity
    recent_requests = LeaveRequest.query.order_by(LeaveRequest.created_at.desc()).limit(10).all()
    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_employees=total_employees,
                         total_managers=total_managers,
                         pending_leaves=pending_leaves,
                         approved_leaves=approved_leaves,
                         rejected_leaves=rejected_leaves,
                         recent_requests=recent_requests,
                         recent_logs=recent_logs)

@bp.route('/users')
@login_required
@admin_required
def users():
    """Manage users"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    
    query = User.query
    
    if search:
        query = query.filter(db.or_(
            User.username.contains(search),
            User.email.contains(search),
            User.first_name.contains(search),
            User.last_name.contains(search)
        ))
    
    if role_filter:
        query = query.filter_by(role=role_filter)
    
    users = query.order_by(User.created_at.desc())\
               .paginate(page=page, per_page=15, error_out=False)
    
    return render_template('admin/users.html', users=users, search=search, role_filter=role_filter)

@bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Create new user"""
    form = UserForm()
    
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role=form.role.data,
            department=form.department.data,
            manager_id=form.manager_id.data if form.manager_id.data != 0 else None,
            is_active=form.is_active.data
        )
        
        if form.password.data:
            user.set_password(form.password.data)
        else:
            user.set_password('password123')  # Default password
        
        db.session.add(user)
        db.session.commit()
        
        log_user_action(current_user.id, 'create_user', 'user', user.id, 
                       f'Created user: {user.username}')
        
        flash(f'User {user.username} created successfully!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/create_user.html', form=form)

@bp.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    """Edit user"""
    user = User.query.get_or_404(id)
    form = UserForm(original_user=user, obj=user)
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.role = form.role.data
        user.department = form.department.data
        user.manager_id = form.manager_id.data if form.manager_id.data != 0 else None
        user.is_active = form.is_active.data
        
        if form.password.data:
            user.set_password(form.password.data)
        
        db.session.commit()
        
        log_user_action(current_user.id, 'update_user', 'user', user.id,
                       f'Updated user: {user.username}')
        
        flash(f'User {user.username} updated successfully!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/edit_user.html', form=form, user=user)

@bp.route('/users/delete/<int:id>')
@login_required
@admin_required
def delete_user(id):
    """Deactivate user"""
    user = User.query.get_or_404(id)
    
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('admin.users'))
    
    user.is_active = False
    db.session.commit()
    
    log_user_action(current_user.id, 'deactivate_user', 'user', user.id,
                   f'Deactivated user: {user.username}')
    
    flash(f'User {user.username} deactivated successfully!', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/reports')
@login_required
@admin_required
def reports():
    """Generate reports"""
    return render_template('admin/reports.html')

@bp.route('/reports/leave_report')
@login_required
@admin_required
def leave_report():
    """Generate leave report"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    format_type = request.args.get('format', 'html')
    
    if not start_date or not end_date:
        flash('Please provide start and end dates.', 'warning')
        return redirect(url_for('admin.reports'))
    
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format.', 'danger')
        return redirect(url_for('admin.reports'))
    
    if format_type == 'pdf':
        pdf_data = generate_leave_report(start_date, end_date, 'pdf')
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=leave_report_{start_date}_{end_date}.pdf'
        return response
    
    elif format_type == 'csv':
        csv_data = generate_leave_report(start_date, end_date, 'csv')
        response = make_response(csv_data)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=leave_report_{start_date}_{end_date}.csv'
        return response
    
    else:
        # HTML format
        report_data = generate_leave_report(start_date, end_date, 'data')
        return render_template('admin/leave_report.html', 
                             report_data=report_data,
                             start_date=start_date,
                             end_date=end_date)

@bp.route('/logs')
@login_required
@admin_required
def logs():
    """View audit logs"""
    page = request.args.get('page', 1, type=int)
    user_filter = request.args.get('user', '')
    action_filter = request.args.get('action', '')
    
    query = AuditLog.query
    
    if user_filter:
        query = query.join(User).filter(User.username.contains(user_filter))
    
    if action_filter:
        query = query.filter(AuditLog.action.contains(action_filter))
    
    logs = query.order_by(AuditLog.timestamp.desc())\
              .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/logs.html', logs=logs, 
                         user_filter=user_filter, action_filter=action_filter)

@bp.route('/policies')
@login_required
@admin_required
def policies():
    """Manage leave policies"""
    policies = LeavePolicy.query.all()
    return render_template('admin/policies.html', policies=policies)

@bp.route('/policies/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_policy():
    """Create leave policy"""
    form = LeavePolicyForm()
    
    if form.validate_on_submit():
        policy = LeavePolicy(
            leave_type=form.leave_type.data,
            days_allowed=form.days_allowed.data,
            carry_forward=form.carry_forward.data,
            max_consecutive_days=form.max_consecutive_days.data,
            requires_approval=form.requires_approval.data,
            is_active=form.is_active.data
        )
        
        db.session.add(policy)
        db.session.commit()
        
        log_user_action(current_user.id, 'create_policy', 'leave_policy', policy.id,
                       f'Created leave policy: {policy.leave_type}')
        
        flash(f'Leave policy for {policy.leave_type} created successfully!', 'success')
        return redirect(url_for('admin.policies'))
    
    return render_template('admin/create_policy.html', form=form)

@bp.route('/policies/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_policy(id):
    """Edit leave policy"""
    policy = LeavePolicy.query.get_or_404(id)
    form = LeavePolicyForm(obj=policy)
    
    if form.validate_on_submit():
        policy.leave_type = form.leave_type.data
        policy.days_allowed = form.days_allowed.data
        policy.carry_forward = form.carry_forward.data
        policy.max_consecutive_days = form.max_consecutive_days.data
        policy.requires_approval = form.requires_approval.data
        policy.is_active = form.is_active.data
        
        db.session.commit()
        
        log_user_action(current_user.id, 'update_policy', 'leave_policy', policy.id,
                       f'Updated leave policy: {policy.leave_type}')
        
        flash(f'Leave policy for {policy.leave_type} updated successfully!', 'success')
        return redirect(url_for('admin.policies'))
    
    return render_template('admin/edit_policy.html', form=form, policy=policy)