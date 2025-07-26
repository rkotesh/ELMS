"""
Authentication routes
"""
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app.auth import bp
from app.forms import LoginForm
from app.models import User
from app.utils.audit import log_user_action

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            log_user_action(None, 'failed_login', 'user', None, 
                          f'Failed login attempt for username: {form.username.data}')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('Your account has been deactivated. Please contact administrator.', 'warning')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        log_user_action(user.id, 'login', 'user', user.id, 'User logged in successfully')
        
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.dashboard')
        
        flash(f'Welcome back, {user.first_name}!', 'success')
        return redirect(next_page)
    
    return render_template('login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    """User logout"""
    if current_user.is_authenticated:
        log_user_action(current_user.id, 'logout', 'user', current_user.id, 'User logged out')
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))