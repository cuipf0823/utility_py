# !/usr/bin/python
# coding=utf-8

from flask import render_template
from flask import redirect
from flask import request
from flask import url_for
from flask import flash
from flask_login import login_user
from flask_login import logout_user
from flask_login import login_required
from flask_login import current_user
from . import auth
from ..models import UsersManager
from .forms import LoginForm
from .forms import RegistrationForm
from .forms import ChangePwdForm
from ..email import send_mail


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = UsersManager.init_user(form.email.data)
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.rem_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password!')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out!')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = UsersManager.add_user(form.username.data, form.password.data, form.email.data)
        if user is not None:
            token = user.generate_confirmation_token()
            send_mail(form.email.data, 'Confirm Your Account', 'auth/email/confirm', user=user, token=token)
            flash('A confirmation email has been sent to you by email.')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('You have confirmed your account, Thanks')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('main.index'))


# 程序可以决定用户确认账户之前可以做什么操作，允许未确认账户登录，但是只显示一个页面，要求用户在获取权限之前先确认账户
# 使用before_request 钩子完成 before_request钩子只能应用于属于蓝本的请求上；
# 全局钩子，必须使用before_app_request修饰器

@auth.before_app_request
def before_request():
    if current_user.is_authenticated \
            and not current_user.confirmed \
            and request.endpoint[:5] != 'auth.' \
            and request.endpoint != 'static':
        return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_mail(current_user.email, 'Confirm Your Account', 'auth/email/confirm', user=current_user, token=token)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for('main.index'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_pwd():
    form = ChangePwdForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_pwd.data):
            current_user.password_hash = form.pwd.data
            UsersManager.update_pwd(current_user.id, current_user.password_hash)
            flash('You password has been updated.')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid password')
    return render_template('auth/change_password.html', form=form)




