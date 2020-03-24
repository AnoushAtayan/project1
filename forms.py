from wtforms import Form, StringField, validators, PasswordField, IntegerField


class RegistrationForm(Form):
    username = StringField('Username', [validators.length(min=4, max=20)])
    email = StringField('Email Address', [validators.length(min=6, max=50)])
    password = PasswordField('Password')
    confirm = PasswordField('Repeat Password')


class LoginForm(Form):
    username = StringField('Username', [validators.length(min=4, max=20)])
    password = PasswordField('Password')


class ReviewForm(Form):
    rating = IntegerField('Rating')
    review = StringField('Review')
