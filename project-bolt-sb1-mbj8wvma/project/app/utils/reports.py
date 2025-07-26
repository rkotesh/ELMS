"""
Report generation utilities
"""
import io
import csv
from datetime import datetime
from flask import render_template_string
from weasyprint import HTML, CSS
import pandas as pd
from app.models import LeaveRequest, User, AttendanceRequest

def generate_leave_report(start_date, end_date, format_type='data'):
    """Generate leave report for given date range"""
    # Query leave requests in date range
    leave_requests = LeaveRequest.query.filter(
        LeaveRequest.start_date >= start_date,
        LeaveRequest.end_date <= end_date
    ).join(User).all()
    
    # Prepare data
    report_data = []
    for leave in leave_requests:
        report_data.append({
            'Employee': leave.employee.full_name,
            'Department': leave.employee.department,
            'Leave Type': leave.leave_type.title(),
            'Start Date': leave.start_date.strftime('%Y-%m-%d'),
            'End Date': leave.end_date.strftime('%Y-%m-%d'),
            'Days': leave.days_requested,
            'Status': leave.status.title(),
            'Applied On': leave.created_at.strftime('%Y-%m-%d'),
            'Manager': leave.manager.full_name if leave.manager else 'N/A'
        })
    
    if format_type == 'data':
        return {
            'requests': report_data,
            'total_requests': len(report_data),
            'approved_requests': len([r for r in report_data if r['Status'] == 'Approved']),
            'pending_requests': len([r for r in report_data if r['Status'] == 'Pending']),
            'rejected_requests': len([r for r in report_data if r['Status'] == 'Rejected']),
            'total_days': sum([r['Days'] for r in report_data if r['Status'] == 'Approved'])
        }
    
    elif format_type == 'csv':
        output = io.StringIO()
        if report_data:
            writer = csv.DictWriter(output, fieldnames=report_data[0].keys())
            writer.writeheader()
            writer.writerows(report_data)
        return output.getvalue()
    
    elif format_type == 'pdf':
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Leave Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; text-align: center; }
                .summary { background: #f8f9fa; padding: 15px; margin: 20px 0; border-radius: 5px; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; font-weight: bold; }
                .status-approved { color: #28a745; font-weight: bold; }
                .status-pending { color: #ffc107; font-weight: bold; }
                .status-rejected { color: #dc3545; font-weight: bold; }
            </style>
        </head>
        <body>
            <h1>Leave Report</h1>
            <p><strong>Period:</strong> {{ start_date }} to {{ end_date }}</p>
            <p><strong>Generated on:</strong> {{ generated_date }}</p>
            
            <div class="summary">
                <h3>Summary</h3>
                <p><strong>Total Requests:</strong> {{ total_requests }}</p>
                <p><strong>Approved:</strong> {{ approved_requests }}</p>
                <p><strong>Pending:</strong> {{ pending_requests }}</p>
                <p><strong>Rejected:</strong> {{ rejected_requests }}</p>
                <p><strong>Total Approved Days:</strong> {{ total_days }}</p>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Employee</th>
                        <th>Department</th>
                        <th>Leave Type</th>
                        <th>Start Date</th>
                        <th>End Date</th>
                        <th>Days</th>
                        <th>Status</th>
                        <th>Applied On</th>
                    </tr>
                </thead>
                <tbody>
                    {% for request in requests %}
                    <tr>
                        <td>{{ request['Employee'] }}</td>
                        <td>{{ request['Department'] }}</td>
                        <td>{{ request['Leave Type'] }}</td>
                        <td>{{ request['Start Date'] }}</td>
                        <td>{{ request['End Date'] }}</td>
                        <td>{{ request['Days'] }}</td>
                        <td class="status-{{ request['Status'].lower() }}">{{ request['Status'] }}</td>
                        <td>{{ request['Applied On'] }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </body>
        </html>
        """
        
        data = generate_leave_report(start_date, end_date, 'data')
        html_content = render_template_string(html_template,
                                            start_date=start_date,
                                            end_date=end_date,
                                            generated_date=datetime.now().strftime('%Y-%m-%d %H:%M'),
                                            requests=data['requests'],
                                            total_requests=data['total_requests'],
                                            approved_requests=data['approved_requests'],
                                            pending_requests=data['pending_requests'],
                                            rejected_requests=data['rejected_requests'],
                                            total_days=data['total_days'])
        
        pdf = HTML(string=html_content).write_pdf()
        return pdf

def generate_user_report(format_type='data'):
    """Generate user report"""
    users = User.query.all()
    
    report_data = []
    for user in users:
        # Calculate leave statistics
        total_leaves = LeaveRequest.query.filter_by(employee_id=user.id).count()
        approved_leaves = LeaveRequest.query.filter_by(employee_id=user.id, status='approved').count()
        
        report_data.append({
            'Username': user.username,
            'Full Name': user.full_name,
            'Email': user.email,
            'Role': user.role.title(),
            'Department': user.department,
            'Manager': user.manager.full_name if user.manager else 'N/A',
            'Active': 'Yes' if user.is_active else 'No',
            'Hire Date': user.hire_date.strftime('%Y-%m-%d') if user.hire_date else 'N/A',
            'Total Leaves': total_leaves,
            'Approved Leaves': approved_leaves
        })
    
    if format_type == 'csv':
        output = io.StringIO()
        if report_data:
            writer = csv.DictWriter(output, fieldnames=report_data[0].keys())
            writer.writeheader()
            writer.writerows(report_data)
        return output.getvalue()
    
    return report_data

def generate_department_summary():
    """Generate department-wise summary"""
    departments = {}
    users = User.query.all()
    
    for user in users:
        dept = user.department
        if dept not in departments:
            departments[dept] = {
                'total_employees': 0,
                'active_employees': 0,
                'total_leaves': 0,
                'approved_leaves': 0
            }
        
        departments[dept]['total_employees'] += 1
        if user.is_active:
            departments[dept]['active_employees'] += 1
        
        # Count leaves
        total_leaves = LeaveRequest.query.filter_by(employee_id=user.id).count()
        approved_leaves = LeaveRequest.query.filter_by(employee_id=user.id, status='approved').count()
        
        departments[dept]['total_leaves'] += total_leaves
        departments[dept]['approved_leaves'] += approved_leaves
    
    return departments