"""
Employee routes
"""
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from app.employee import bp
from app import db
from app.models import LeaveRequest, AttendanceRequest, User
from app.forms import LeaveRequestForm, AttendanceRequestForm
from app.utils.audit import log_user_action

@bp.route('/dashboard')
@login_required
def dashboard():
    """Employee dashboard"""
    # Get recent leave requests
    recent_leaves = LeaveRequest.query.filter_by(employee_id=current_user.id)\
                                    .order_by(LeaveRequest.created_at.desc())\
                                    .limit(5).all()
    
    # Get pending requests count
    pending_leaves = LeaveRequest.query.filter_by(employee_id=current_user.id, status='pending').count()
    pending_attendance = AttendanceRequest.query.filter_by(employee_id=current_user.id, status='pending').count()
    
    # Calculate leave balance (simplified - in real app, this would be more complex)
    current_year = date.today().year
    approved_leaves = LeaveRequest.query.filter_by(employee_id=current_user.id, status='approved')\
                                       .filter(db.extract('year', LeaveRequest.start_date) == current_year)\
                                       .all()
    
    total_days_taken = sum(leave.days_requested for leave in approved_leaves)
    leave_balance = max(0, 25 - total_days_taken)  # Assuming 25 days annual leave
    
    return render_template('employee/dashboard.html',
                         recent_leaves=recent_leaves,
                         pending_leaves=pending_leaves,
                         pending_attendance=pending_attendance,
                         leave_balance=leave_balance,
                         total_days_taken=total_days_taken)

@bp.route('/apply_leave', methods=['GET', 'POST'])
@login_required
def apply_leave():
    """Apply for leave"""
    form = LeaveRequestForm()
    
    if form.validate_on_submit():
        # Calculate days requested
        start_date = form.start_date.data
        end_date = form.end_date.data
        days_requested = (end_date - start_date).days + 1
        
        # Create leave request
        leave_request = LeaveRequest(
            employee_id=current_user.id,
            leave_type=form.leave_type.data,
            start_date=start_date,
            end_date=end_date,
            days_requested=days_requested,
            reason=form.reason.data,
            manager_id=current_user.manager_id
        )
        
        db.session.add(leave_request)
        db.session.commit()
        
        log_user_action(current_user.id, 'create_leave_request', 'leave_request', 
                       leave_request.id, f'Applied for {form.leave_type.data} leave')
        
        flash(f'Leave request submitted successfully for {days_requested} days!', 'success')
        return redirect(url_for('employee.leave_history'))
    
    return render_template('employee/apply_leave.html', form=form)

@bp.route('/attendance_request', methods=['GET', 'POST'])
@login_required
def attendance_request():
    """Request attendance correction"""
    form = AttendanceRequestForm()
    
    if form.validate_on_submit():
        attendance_request = AttendanceRequest(
            employee_id=current_user.id,
            request_date=form.request_date.data,
            request_type=form.request_type.data,
            reason=form.reason.data,
            manager_id=current_user.manager_id
        )
        
        db.session.add(attendance_request)
        db.session.commit()
        
        log_user_action(current_user.id, 'create_attendance_request', 'attendance_request',
                       attendance_request.id, f'Requested {form.request_type.data} correction')
        
        flash('Attendance correction request submitted successfully!', 'success')
        return redirect(url_for('employee.dashboard'))
    
    return render_template('employee/attendance_request.html', form=form)

@bp.route('/leave_history')
@login_required
def leave_history():
    """View leave history"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = LeaveRequest.query.filter_by(employee_id=current_user.id)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    leaves = query.order_by(LeaveRequest.created_at.desc())\
                 .paginate(page=page, per_page=10, error_out=False)
    
    return render_template('employee/leave_history.html', leaves=leaves, status_filter=status_filter)

@bp.route('/cancel_leave/<int:id>')
@login_required
def cancel_leave(id):
    """Cancel a pending leave request"""
    leave_request = LeaveRequest.query.get_or_404(id)
    
    if leave_request.employee_id != current_user.id:
        flash('You can only cancel your own leave requests.', 'danger')
        return redirect(url_for('employee.leave_history'))
    
    if not leave_request.can_be_cancelled():
        flash('This leave request cannot be cancelled.', 'warning')
        return redirect(url_for('employee.leave_history'))
    
    leave_request.status = 'cancelled'
    db.session.commit()
    
    log_user_action(current_user.id, 'cancel_leave_request', 'leave_request',
                   leave_request.id, 'Cancelled leave request')
    
    flash('Leave request cancelled successfully.', 'success')
    return redirect(url_for('employee.leave_history'))

@bp.route('/calendar')
@login_required
def calendar():
    """View calendar with leave dates"""
    # Get approved leaves for calendar display
    approved_leaves = LeaveRequest.query.filter_by(employee_id=current_user.id, status='approved').all()
    
    # Format for calendar
    calendar_events = []
    for leave in approved_leaves:
        calendar_events.append({
            'title': f'{leave.leave_type.title()} Leave',
            'start': leave.start_date.isoformat(),
            'end': (leave.end_date + timedelta(days=1)).isoformat(),  # FullCalendar end is exclusive
            'color': '#28a745' if leave.leave_type == 'vacation' else '#dc3545'
        })
    
    return render_template('employee/calendar.html', events=calendar_events)

@bp.route('/api/calendar_events')
@login_required
def api_calendar_events():
    """API endpoint for calendar events"""
    approved_leaves = LeaveRequest.query.filter_by(employee_id=current_user.id, status='approved').all()
    
    events = []
    for leave in approved_leaves:
        events.append({
            'title': f'{leave.leave_type.title()} Leave',
            'start': leave.start_date.isoformat(),
            'end': (leave.end_date + timedelta(days=1)).isoformat(),
            'color': '#28a745' if leave.leave_type == 'vacation' else '#dc3545'
        })
    
    return jsonify(events)