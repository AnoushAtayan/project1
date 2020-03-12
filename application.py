import os

from flask import Flask, session, render_template, request, redirect, url_for, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from passlib.hash import sha256_crypt
from werkzeug.security import generate_password_hash, check_password_hash

from forms import RegistrationForm

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/register", methods=['GET', 'POST'])
def register():
    try:
        form = RegistrationForm(request.form)
        if request.method == 'POST' and form.validate():
            username = form.username.data
            print(username)
            email = form.email.data
            password = generate_password_hash(form.password.data, method='sha256')
            # user = User.query.filter_by(username=username).first()
            # if user:
            #     flash('Email address already exists')
            #     return redirect(url_for('signup'))
            #
            # new_user = User(username=username, email=email, password=password)

        return render_template('register.html', form=form)
    except Exception as e:
        return str(e)


@app.route("/login")
def login():
    return render_template('login.html')
