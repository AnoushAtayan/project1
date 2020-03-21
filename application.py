import os

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

from forms import RegistrationForm, LoginForm
from helpers import login_required

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
@login_required
def index():
    return render_template('index.html')


@app.route("/register", methods=['GET', 'POST'])
def register():
    try:
        form = RegistrationForm(request.form)
        if request.method == 'POST' and form.validate():
            username = form.username.data
            user = db.execute("SELECT * FROM users WHERE username = :username",
                              {'username': username}).fetchone()

            if user:
                flash('Username already exists.')
                return redirect(url_for('register'))

            email = form.email.data
            password = form.password.data
            confirm = form.confirm.data

            if password != confirm:
                flash('Passwords do not match')
                return redirect(url_for('register'))

            password = generate_password_hash(password, method='sha256')
            # Insert new object
            db.execute(
                "INSERT INTO users (username, email, password) "
                "VALUES (:username, :email, :password)",
                {'username': username, 'email': email, 'password': password})
            # Commit changes to database
            db.commit()

            # Redirect user to login page
            return redirect("/login")

        return render_template('register.html', form=form)
    except Exception as e:
        return str(e)


@app.route("/login", methods=['GET', 'POST'])
def login():
    try:
        form = LoginForm(request.form)
        if request.method == 'POST' and form.validate():
            username = form.username.data
            user = db.execute("SELECT * FROM users WHERE username = :username",
                              {'username': username}).fetchone()

            if user is None or not check_password_hash(user['password'], form.password.data):
                flash('Invalid username and/or password.')
                return redirect(url_for('login'))

            # Add to session
            session["user_id"] = user['id']
            session["username"] = user['username']

            # Redirect user to home page
            return redirect("/")

        return render_template('login.html', form=form)
    except Exception as e:
        return str(e)


@app.route("/logout")
def logout():
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/search")
def search():
    text = request.args.get('book')
    query = f'%{text}%'

    rows = db.execute("SELECT isbn, title, author, year FROM books WHERE \
    isbn LIKE :query OR title LIKE :query OR author LIKE :query",
                      {'query': query})

    if rows.rowcount == 0:
        flash('No book is found with that description!')
        return render_template("results.html")

    # Get all the results
    books = rows.fetchall()
    return render_template("results.html", books=books)
