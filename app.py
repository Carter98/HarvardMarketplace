import os
import datetime

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import re
from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///marketplace.db")

# Make sure API key is set



@app.route("/")
@login_required
def index():
    """Show all posts."""
    search = db.execute("SELECT item, price, contact, seller FROM posts")

    return render_template("index.html", search=search)



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")
    # ensures entry is not blank
    if request.form.get("symbol") == '':
        return apology("must provide symbol", 403)
    # ensures that symbol is valid
    if lookup(request.form.get("symbol")) == None:
        return apology("invalid symbol", 403)
    # ensures shares is a positive number
    if int(request.form.get("shares")) < 1:
        return apology("invalid number of shares")
    search_dict = lookup(request.form.get("symbol"))
    current_price = float(search_dict["price"])
    current_balance = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])
    current_balance = current_balance[0]["cash"]
    expenditure = current_price * int(request.form.get("shares"))
    # ensures that user has sufficient funds for purchase
    if expenditure > float(current_balance):
        return apology("you do not have sufficient funds for this purchase")
    # updates data tables accordingly
    db.execute("INSERT INTO purchases (user_id, stocks, price, company) VALUES (?,?,?,?)",
    session["user_id"], request.form.get("shares"), search_dict["price"], search_dict["symbol"])
    db.execute("UPDATE users SET cash = :new_cash WHERE id = :id", new_cash=current_balance - expenditure, id=session["user_id"])
    # redirect user to homepage
    return redirect("/")





@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    search = db.execute("SELECT item, price, contact, seller, time FROM posts WHERE user_id = :id", id=session["user_id"])


    return render_template("history.html", search=search)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        result = check_password_hash(rows[0]["hash"], request.form.get("password"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Search for a specfic item."""
    # when requested via GET, display search form
    if request.method == "GET":
        return render_template("quote.html")
    # ensure symbol is valid
    search = request.form.get("search")
    find = db.execute("SELECT item, price, contact, seller FROM posts WHERE item = ?", search)
    if request.method == "POST":
        return render_template("quoted.html", search=find)



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # when requested via GET, should display registraion form
    if request.method == "GET":
        return render_template("register.html")
    # when form is submitted via POST, insert the new user into users table
    if request.form.get("username") == '':
        return apology("must provide username", 403)
    # ensure username is not taken
    if len(db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))) == 1:
        return apology("username already exists", 403)
    # ensure something is entered for password
    if request.form.get("password") == '':
        return apology("must provide password", 403)
    if len(request.form.get("password")) < 6:
        return apology("password must contain at least 6 characters")
    if not (re.search("\W", request.form.get("password"))):
        return apology("password must include special character")
    if not (re.search("\d", request.form.get("password"))):
        return apology("password must contain at least one digit")
    # ensures confirmation is entered
    if request.form.get("confirmation") == '':
        return apology("must provide password confirmation", 403)
    # ensure that confirmation matches password
    if request.form.get("password") != request.form.get("confirmation"):
        return apology("password and confirmation do not match", 403)
    if request.form.get("email") == '':
        return apology("must provide email", 403)
    username = request.form.get("username")
    password = request.form.get("password")
    hashed_pw = generate_password_hash(request.form.get("password"))
    db.execute("INSERT INTO users (username, hash, email, phone_num) VALUES (?,?,?,?)",
    username, hashed_pw, request.form.get("email"), request.form.get("phone_num"))
    return redirect("/")
@app.route("/sell", methods=["GET", "POST"])
@login_required
def profile():
    """Update account information"""
    # when requested via GET, should display registraion form
    if request.method == "GET":
        return render_template("profile.html")
    # when form is submitted via POST, insert the new user into users table
    if request.form.get("username") == '':
        return apology("must provide username", 403)
    # ensure username is not taken
    if len(db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))) == 1:
        return apology("username already exists", 403)
    # ensure something is entered for password
    if request.form.get("password") == '':
        return apology("must provide password", 403)
    if len(request.form.get("password")) < 6:
        return apology("password must contain at least 6 characters")
    if not (re.search("\W", request.form.get("password"))):
        return apology("password must include special character")
    if not (re.search("\d", request.form.get("password"))):
        return apology("password must contain at least one digit")
    # ensures confirmation is entered
    if request.form.get("confirmation") == '':
        return apology("must provide password confirmation", 403)
    # ensure that confirmation matches password
    if request.form.get("password") != request.form.get("confirmation"):
        return apology("password and confirmation do not match", 403)
    if request.form.get("email") == '':
        return apology("must provide email", 403)
    username = request.form.get("username")
    password = request.form.get("password")
    hashed_pw = generate_password_hash(request.form.get("password"))

    db.execute("UPDATE users SET username = ?, hash = ?, email = ?, phone_num = ? WHERE id = :id",
    username, hashed_pw, request.form.get("email"), request.form.get("phone_num"),id=session["user_id"])
    return redirect("/")
@app.route("/sell", methods=["GET", "POST"])
@login_required
def manage():
    """Show all the users posted items."""
    if request.method == "GET":
        search = db.execute("SELECT name, price, description, category FROM items WHERE seller_id=?", session["user_id"])
        return render_template("manage.html", search=search)
    if request.method =="POST":
        #if request.form.get("activity") == 'deactivate':
        return redirect("/")




@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Add an item to the list"""
    if request.method == "GET":
        return render_template("sell.html")
    # ensure symbol is entered
    if request.form.get("name") == '':
        return apology("must provide item name", 403)
    # ensures that symbol is valid

    if request.form.get("price") == '':
        return apology("must set price")

    # update tables
    # have to figure out how to insert image
    db.execute("INSERT INTO items (seller_id, name, description, price, category, timestamp, isActive, image) VALUES (?,?,?,?,?,?,?,?)",
    session["user_id"], request.form.get("name"), request.form.get("description"), request.form.get("price"), request.form.get("category"), datetime.now(tz=None),"yes", request.form.get("pic"))
    return redirect("/")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
