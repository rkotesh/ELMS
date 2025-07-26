"""
Manager routes
"""
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from app.manager import bp
from app import db
from app.models import LeaveRequest, AttendanceRequest, User
from app.forms import ApprovalForm, SearchForm
from app.auth.utils import manager_or_admin_required
from app.utils.audit import log_user_action

@bp.route('/dashboard')
@login_required
@manager_or_admin_required
def dashboard():
    """Manager dashboard"""
    # Get subordinates
    subordinates = current_user.get_subordinates()
    subordinate_ids = [s.id for s in subordinates]
    
    # Get pending requests
    pending_leaves = LeaveRequest.query.filter(LeaveRequest.employee_id.in_(subordinate_ids))\
                                     .filter_by(status='pending').count()
    
    pending_attendance = AttendanceRequest.query.filter(AttendanceRequest.employee_id.in_(subordinate_ids))\
                                                .filter_by(status='pending').count()
    
    # Get recent requests
    recent_requests = LeaveRequest.query.filter(LeaveRequest.employee_id.in_(subordinate_ids))\
                                       .order_by(LeaveRequest.created_at.desc())\
                                       .limit(10).all()
    
    # Team statistics
    total_team_members = len(subordinates)
    
    return render_template('manager/dashboard.html',
                         pending_leaves=pending_leaves,
                         pending_attendance=pending_attendance,
                         recent_requests=recent_requests,
                         total_team_members=total_team_members,
                         subordinates=subordinates)

@bp.route('/approve_requests')
@login_required
@manager_or_admin_required
def approve_requests():
    """View and approve requests"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'pending')
    request_type = request.args.get('type', 'leave')
    
    # Get subordinates
    subordinates = current_user.get_subordinates()
    subordinate_ids = [s.id for s in subordinates]
    
    if request_type == 'leave':
        query = LeaveRequest.query.filter(LeaveRequest.employee_id.in_(subordinate_ids))
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        requests = query.order_by(LeaveRequest.created_at.desc())\
                       .paginate(page=page, per_page=10, error_out=False)
        
        return render_template('manager/approve_requests.html',
                             requests=requests,
                             status_filter=status_filter,
                             request_type=request_type)
    
    else:  # attendance requests
        query = AttendanceRequest.query.filter(AttendanceRequest.employee_id.in_(subordinate_ids))
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        requests = query.order_by(AttendanceRequest.created_at.desc())\
                       .paginate(page=page, per_page=10, error_out=False)
        
        return render_template('manager/approve_requests.html',
                             requests=requests,
                             status_filter=status_filter,
                             request_type=request_type)

@bp.route('/approve_leave/<int:id>', methods=['GET', 'POST'])
@login_required
@manager_or_admin_required
def approve_leave(id):
    """Approve or reject leave request"""
    leave_request = LeaveRequest.query.get_or_404(id)
    
    # Check if manager has authority over this employee
    if leave_request.employee.manager_id != current_user.id and not current_user.is_admin():
        flash('You do not have authority to approve this request.', 'danger')
        return redirect(url_for('manager.approve_requests'))
    
    form = ApprovalForm()
    
    if form.validate_on_submit():
        leave_request.status = form.action.data
        leave_request.manager_id = current_user.id
        leave_request.manager_comments = form.comments.data
        leave_request.approved_at = datetime.utcnow()
        
        db.session.commit()
        
        action_text = 'approved' if form.action.data == 'approved' else 'rejected'
        log_user_action(current_user.id, f'{action_text}_leave_request', 'leave_request',
                       leave_request.id, f'Leave request {action_text}')
        
        flash(f'Leave request {action_text} successfully!', 'success')
        return redirect(url_for('manager.approve_requests'))
    
    return render_template('manager/approve_leave.html', leave_request=leave_request, form=form)

@bp.route('/approve_attendance/<int:id>', methods=['GET', 'POST'])
@login_required
@manager_or_admin_required
def approve_attendance(id):
    """Approve or reject attendance request"""
    attendance_request = AttendanceRequest.query.get_or_404(id)
    
    # Check if manager has authority over this employee
    if attendance_request.employee.manager_id != current_user.id and not current_user.is_admin():
        flash('You do not have authority to approve this request.', 'danger')
        return redirect(url_for('manager.approve_requests'))
    
    form = ApprovalForm()
    
    if form.validate_on_submit():
        attendance_request.status = form.action.data
        attendance_request.manager_id = current_user.id
        attendance_request.manager_comments = form.comments.data
        attendance_request.approved_at = datetime.utcnow()
        
        db.session.commit()
        
        action_text = 'approved' if form.action.data == 'approved' else 'rejected'
        log_user_action(current_user.id, f'{action_text}_attendance_request', 'attendance_request',
                       attendance_request.id, f'Attendance request {action_text}')
        
        flash(f'Attendance request {action_text} successfully!', 'success')
        return redirect(url_for('manager.approve_requests'))
    
    return render_template('manager/approve_attendance.html', 
                         attendance_request=attendance_request, form=form)

@bp.route('/team_overview')
@login_required
@manager_or_admin_required
def team_overview():
    """Team overview with leave calendar"""
    subordinates = current_user.get_subordinates()
    subordinate_ids = [s.id for s in subordinates]
    
    # Get upcoming leaves
    upcoming_leaves = LeaveRequest.query.filter(LeaveRequest.employee_id.in_(subordinate_ids))\
                                       .filter_by(status='approved')\
                                       .filter(LeaveRequest.start_date >= date.today())\
                                       .order_by(LeaveRequest.start_date)\
                                       .limit(10).all()
    
    # Get current leaves (people on leave today)
    current_leaves = LeaveRequest.query.filter(LeaveRequest.employee_id.in_(subordinate_ids))\
                                      .filter_by(status='approved')\
                                      .filter(LeaveRequest.start_date <= date.today())\
                                      .filter(LeaveRequest.end_date >= date.today()).all()
    
    return render_template('manager/team_overview.html',
                         subordinates=subordinates,
                         upcoming_leaves=upcoming_leaves,
                         current_leaves=current_leaves)

@bp.route('/performance')
@login_required
@manager_or_admin_required
def performance():
    """Team performance metrics"""
    subordinates = current_user.get_subordinates()
    subordinate_ids = [s.id for s in subordinates]
    
    # Calculate metrics for each team member
    team_metrics = []
    for employee in subordinates:
        # Leave statistics
        total_leaves = LeaveRequest.query.filter_by(employee_id=employee.id, status='approved').count()
        pending_leaves = LeaveRequest.query.filter_by(employee_id=employee.id, status='pending').count()
        
        # Days taken this year
        current_year = date.today().year
        approved_leaves = LeaveRequest.query.filter_by(employee_id=employee.id, status='approved')\
                                           .filter(db.extract('year', LeaveRequest.start_date) == current_year)\
                                           .all()
        days_taken = sum(leave.days_requested for leave in approved_leaves)
        
        team_metrics.append({
            'employee': employee,
            'total_leaves': total_leaves,
            'pending_leaves': pending_leaves,
            'days_taken': days_taken,
            'leave_balance': max(0, 25 - days_taken)
        })
    
    return render_template('manager/performance.html', team_metrics=team_metrics)

@bp.route('/api/team_calendar')
@login_required
@manager_or_admin_required
def api_team_calendar():
    """API endpoint for team calendar events"""
    subordinates = current_user.get_subordinates()
    subordinate_ids = [s.id for s in subordinates]
    
    approved_leaves = LeaveRequest.query.filter(LeaveRequest.employee_id.in_(subordinate_ids))\
                                       .filter_by(status='approved').all()
    
    events = []
    colors = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1', '#fd7e14']
    
    for i, leave in enumerate(approved_leaves):
        events.append({
            'title': f'{leave.employee.first_name} - {leave.leave_type.title()}',
            'start': leave.start_date.isoformat(),
            'end': (leave.end_date + timedelta(days=1)).isoformat(),
            'color': colors[i % len(colors)]
        })
    
    return jsonify(events)