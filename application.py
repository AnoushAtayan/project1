import os

import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

from forms import RegistrationForm, LoginForm, ReviewForm
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
            return redirect('/login')

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
            session['user_id'] = user['id']
            session['username'] = user['username']

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
@login_required
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


@app.route("/book/<isbn>", methods=['GET', 'POST'])
@login_required
def book(isbn):
    try:
        form = ReviewForm(request.form)
        book_row = db.execute("SELECT * FROM books WHERE isbn = :isbn", {'isbn': isbn})
        book_data = book_row.fetchone()
        book_id = book_data[0]
        user_id = session["user_id"]

        if request.method == 'POST':
            # Fetch form data
            rating = int(form.rating.data)
            review = form.review.data

            db.execute("INSERT INTO reviews (user_id, book_id, review, rating) VALUES \
                        (:user_id, :book_id, :review, :rating)",
                       {'user_id': user_id, 'book_id': book_id, 'review': review, 'rating': rating})

            # Commit transactions to DB and close the connection
            db.commit()

            flash('Review has been successfully submitted!')
            return redirect(url_for('book', isbn=isbn))

        # Get request
        key = os.getenv('GOODREADS_KEY')

        # Query the api with key and ISBN as parameters
        query = requests.get('https://www.goodreads.com/book/review_counts.json',
                             params={'key': key, 'isbns': isbn})

        # Convert the response to JSON
        response = query.json()['books'][0]

        # get all reviews
        results = db.execute("SELECT users.username, review, rating, \
                                    to_char(date, 'DD Mon YYYY') as date \
                                    FROM users \
                                    INNER JOIN reviews \
                                    ON users.id = reviews.user_id \
                                    WHERE book_id = :book \
                                    ORDER BY date",
                             {"book": book_id})

        reviews = results.fetchall()

        has_review = False
        for review in reviews:
            if review[0] == session["username"]:
                has_review = True
                break

        return render_template('book.html',
                               form=form,
                               book_data=book_data,
                               average_rating=response['average_rating'],
                               work_ratings_count=response['work_ratings_count'],
                               has_review=has_review,
                               reviews=reviews
                               )
    except Exception as e:
        return str(e)


@app.route("/api/<isbn>")
@login_required
def api_call(isbn):
    """
    Return a JSON response containing the book’s title, author, publication date,
    ISBN number, review count, and average score.
    """
    row = db.execute("SELECT title, author, year, isbn, \
                    COUNT(reviews.id) as review_count, \
                    AVG(reviews.rating) as average_score \
                    FROM books \
                    INNER JOIN reviews \
                    ON books.id = reviews.book_id \
                    WHERE isbn = :isbn \
                    GROUP BY title, author, year, isbn",
                     {"isbn": isbn})

    if row.rowcount == 0:
        return jsonify({"Error": "Invalid book ISBN"}), 422

    # Convert to dict
    result = dict(row.fetchone().items())

    result['average_score'] = format(result['average_score'], '.2f')

    return jsonify(result)
