from app import create_app, db
from app.models import Book

# Créer l'application Flask et le contexte d'application
app = create_app()

with app.app_context():
    # Liste de livres à insérer
    books = [
        ('To Kill a Mockingbird', 'Harper Lee'),
        ('1984', 'George Orwell'),
        ('The Great Gatsby', 'F. Scott Fitzgerald'),
        ('The Catcher in the Rye', 'J.D. Salinger'),
        ('Moby Dick', 'Herman Melville'),
        ('Pride and Prejudice', 'Jane Austen'),
        ('War and Peace', 'Leo Tolstoy'),
        ('The Odyssey', 'Homer'),
        ('Crime and Punishment', 'Fyodor Dostoevsky'),
        ('The Lord of the Rings', 'J.R.R. Tolkien')
    ]

    # Insérer les livres dans la base de données
    for title, author in books:
        book = Book(title=title, author=author)
        db.session.add(book)

    db.session.commit()

    print("Books have been inserted into the database.")
