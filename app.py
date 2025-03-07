from flask import Flask, request, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
import secrets

app = Flask(__name__)

# Database configuration using the provided credentials
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:W7301%40jqir%23@localhost/library_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Setting the secret key
app.secret_key = secrets.token_hex(16)

# Logging setup
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s | %(levelname)s | %(message)s', 
                    handlers=[logging.FileHandler("logs/app.log"),
                              logging.StreamHandler()])  # Add console logging

# Database setup
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Database models
class Member(db.Model):
    __tablename__ = 'members'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255))

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    author = db.Column(db.String(255))
    is_issued = db.Column(db.Boolean, default=False)

@app.route('/')
def index():
    app.logger.debug('Home page accessed')
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            data = request.form
            existing_member = Member.query.filter_by(email=data['email']).first()
            if existing_member:
                return "Email already registered! Please log in instead.", 400
            
            new_member = Member(name=data['name'], email=data['email'], password=data['password'])
            db.session.add(new_member)
            db.session.commit()
            app.logger.info(f"New member signed up: {data['email']}")
            return redirect(url_for('login'))

        except Exception as e:
            logging.error(f"Signup error: {str(e)}")
            return "An error occurred during signup.", 500

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            data = request.form
            member = Member.query.filter_by(email=data['email'], password=data['password']).first()
            if member:
                session['member_id'] = member.id
                app.logger.info(f"{data['email']} logged in.")
                return redirect(url_for('index'))

            return "Invalid email or password", 400

        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            return "An error occurred during login.", 500

    return render_template('login.html')

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        try:
            data = request.form
            new_book = Book(title=data['title'], author=data['author'])
            db.session.add(new_book)
            db.session.commit()
            app.logger.info(f"New book added: {data['title']}")
            return redirect(url_for('show_books'))

        except Exception as e:
            logging.error(f"Add book error: {str(e)}")
            return "An error occurred while adding the book.", 500

    return render_template('add_book.html')

@app.route('/remove_book', methods=['GET', 'POST'])
def remove_book():
    if request.method == 'POST':
        try:
            book_id = request.form['book_id']
            book = Book.query.get(book_id)
            if book:
                db.session.delete(book)
                db.session.commit()
                app.logger.info(f"Book removed: {book.title}")
                return redirect(url_for('show_books'))

            return "Book not found!", 404

        except Exception as e:
            logging.error(f"Remove book error: {str(e)}")
            return "An error occurred while removing the book.", 500

    return render_template('remove_book.html')

@app.route('/show_books', methods=['GET'])
def show_books():
    try:
        books = Book.query.all()
        return render_template('show_books.html', books=books)

    except Exception as e:
        logging.error(f"Show books error: {str(e)}")
        return "An error occurred while retrieving books.", 500

@app.route('/search_books', methods=['GET'])
def search_books():
    query = request.args.get('query')
    try:
        if query:
            books = Book.query.filter(
                (Book.title.contains(query)) | 
                (Book.author.contains(query)) | 
                (Book.id == query)
            ).all()
        else:
            books = []
        return render_template('search_books.html', books=books, query=query)

    except Exception as e:
        logging.error(f"Search books error: {str(e)}")
        return "An error occurred while searching for books.", 500

@app.route('/issue_book/<int:book_id>', methods=['POST'])
def issue_book(book_id):
    try:
        book = Book.query.get(book_id)
        if book and not book.is_issued:
            book.is_issued = True
            db.session.commit()
            app.logger.info(f"Book issued: {book.title}")
            return redirect(url_for('show_books'))
        return "Book not found or already issued", 404

    except Exception as e:
        logging.error(f"Issue book error: {str(e)}")
        return "An error occurred while issuing the book.", 500

@app.route('/return_book/<int:book_id>', methods=['POST'])
def return_book(book_id):
    try:
        book = Book.query.get(book_id)
        if book and book.is_issued:
            book.is_issued = False
            db.session.commit()
            app.logger.info(f"Book returned: {book.title}")
            return redirect(url_for('show_books'))
        return "Book not found or not issued", 404

    except Exception as e:
        logging.error(f"Return book error: {str(e)}")
        return "An error occurred while returning the book.", 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Creates tables if they don’t exist
    print("Starting the Flask application...")
    app.run(host='127.0.0.1', port=5000, debug=True)
