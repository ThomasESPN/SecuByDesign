from app import create_app, db
from app.models import Borrow, User

# Créer l'application Flask et le contexte d'application
app = create_app()

with app.app_context():
    # Vider la table borrow
    Borrow.query.delete()
    User.query.delete()
    db.session.commit()

    print("Tables vidées avec succès")
