from wtforms import Form, StringField, validators, PasswordField


class RegistrationForm(Form):
    username = StringField('Username', [validators.length(min=4, max=20)])
    email = StringField('Email Address', [validators.length(min=6, max=50)])
    password = PasswordField('Password', [validators.EqualTo(
        'confirm', message='Passwords must match.')])
    confirm = PasswordField('Repeat Password')
