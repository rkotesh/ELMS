"""
Flask-WTF forms for Employee Leave Management System
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, IntegerField, BooleanField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange
from wtforms.widgets import TextArea
from datetime import date, datetime
from app.models import User, LeavePolicy

class LoginForm(FlaskForm):
    """Login form"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class LeaveRequestForm(FlaskForm):
    """Leave request form"""
    leave_type = SelectField('Leave Type', validators=[DataRequired()], 
                           choices=[('sick', 'Sick Leave'), ('vacation', 'Vacation'), 
                                  ('personal', 'Personal Leave'), ('emergency', 'Emergency Leave')])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    reason = TextAreaField('Reason', validators=[DataRequired(), Length(min=10, max=500)],
                          render_kw={"rows": 4, "placeholder": "Please provide a detailed reason for your leave request"})
    submit = SubmitField('Submit Request')
    
    def validate_start_date(self, start_date):
        if start_date.data < date.today():
            raise ValidationError('Start date cannot be in the past.')
    
    def validate_end_date(self, end_date):
        if hasattr(self, 'start_date') and self.start_date.data and end_date.data < self.start_date.data:
            raise ValidationError('End date must be after start date.')

class AttendanceRequestForm(FlaskForm):
    """Attendance correction request form"""
    request_date = DateField('Date', validators=[DataRequired()])
    request_type = SelectField('Request Type', validators=[DataRequired()],
                             choices=[('late_arrival', 'Late Arrival'), ('early_departure', 'Early Departure'),
                                    ('missed_punch', 'Missed Punch In/Out')])
    reason = TextAreaField('Reason', validators=[DataRequired(), Length(min=10, max=500)],
                          render_kw={"rows": 4, "placeholder": "Please explain the reason for attendance correction"})
    submit = SubmitField('Submit Request')
    
    def validate_request_date(self, request_date):
        if request_date.data > date.today():
            raise ValidationError('Request date cannot be in the future.')

class ApprovalForm(FlaskForm):
    """Form for approving/rejecting requests"""
    action = SelectField('Action', validators=[DataRequired()],
                        choices=[('approved', 'Approve'), ('rejected', 'Reject')])
    comments = TextAreaField('Comments', validators=[Length(max=500)],
                           render_kw={"rows": 3, "placeholder": "Optional comments for the employee"})
    submit = SubmitField('Submit Decision')

class UserForm(FlaskForm):
    """User creation/edit form"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=1, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=1, max=50)])
    role = SelectField('Role', validators=[DataRequired()],
                      choices=[('employee', 'Employee'), ('manager', 'Manager'), ('admin', 'Admin')])
    department = StringField('Department', validators=[DataRequired(), Length(min=1, max=50)])
    manager_id = SelectField('Manager', coerce=int, validators=[])
    password = PasswordField('Password', validators=[Length(min=6, max=128)])
    password2 = PasswordField('Repeat Password', validators=[EqualTo('password')])
    is_active = BooleanField('Active')
    submit = SubmitField('Save User')
    
    def __init__(self, original_user=None, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.original_user = original_user
        # Populate manager choices
        managers = User.query.filter(User.role.in_(['manager', 'admin'])).all()
        self.manager_id.choices = [(0, 'No Manager')] + [(m.id, m.full_name) for m in managers]
    
    def validate_username(self, username):
        if self.original_user is None or username.data != self.original_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')
    
    def validate_email(self, email):
        if self.original_user is None or email.data != self.original_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('Please use a different email address.')

class LeavePolicyForm(FlaskForm):
    """Leave policy form"""
    leave_type = StringField('Leave Type', validators=[DataRequired(), Length(min=1, max=50)])
    days_allowed = IntegerField('Days Allowed', validators=[DataRequired(), NumberRange(min=0, max=365)])
    carry_forward = BooleanField('Allow Carry Forward')
    max_consecutive_days = IntegerField('Max Consecutive Days', validators=[NumberRange(min=1, max=365)])
    requires_approval = BooleanField('Requires Approval', default=True)
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Policy')

class PasswordChangeForm(FlaskForm):
    """Password change form"""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6, max=128)])
    new_password2 = PasswordField('Repeat New Password', 
                                 validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

class SearchForm(FlaskForm):
    """Search form for filtering requests"""
    employee = SelectField('Employee', coerce=int, validators=[])
    status = SelectField('Status', validators=[],
                        choices=[('', 'All Statuses'), ('pending', 'Pending'), 
                               ('approved', 'Approved'), ('rejected', 'Rejected')])
    leave_type = SelectField('Leave Type', validators=[],
                           choices=[('', 'All Types'), ('sick', 'Sick Leave'), 
                                  ('vacation', 'Vacation'), ('personal', 'Personal Leave')])
    start_date = DateField('From Date', validators=[])
    end_date = DateField('To Date', validators=[])
    submit = SubmitField('Filter')
    
    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        # Populate employee choices
        employees = User.query.filter_by(role='employee').all()
        self.employee.choices = [(0, 'All Employees')] + [(e.id, e.full_name) for e in employees]