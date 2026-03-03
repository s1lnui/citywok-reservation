import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from __init__ import create_app, db
from models import User, Restaurant, DiningTable

app = create_app()

with app.app_context():
    # Create all tables
    db.create_all()

    # Create admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@citywok.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)

    # Create sample restaurants if not exist
    if not Restaurant.query.first():
        r1 = Restaurant(
            name='City Wok I',
            address='Praceta Elaine Sanceau 100, 4250-202 Porto',
            phone='+351 929071651',
            opening_hours='Tue-Sun 12:00-3:00 PM ; 7:30-11:00 PM'
        )
        r2 = Restaurant(
            name='City Wok II',
            address='Estr. da Circunvalação 7234 4200, 4425-420 Porto',
            phone='+351 929071651',
            opening_hours='Tue-Sun 12:00-3:00 PM ; 7:30-11:00 PM'
        )
        r3 = Restaurant(
            name='City Wok III',
            address='Av. Dom João II, 4430-415 Vila Nova de Gaia',
            phone='+351 929071651',
            opening_hours='Tue-Sun 12:00-3:00 PM ; 7:30-11:00 PM'
        )
        
        db.session.add_all([r1, r2, r3])
        db.session.commit()
        
        # Create tables for restaurants
        tables = []
        for i in range(1, 11):
            tables.append(DiningTable(restaurant_id=r1.id, table_number=f'T{i}', capacity=2 if i <= 6 else 4))
        for i in range(1, 9):
            tables.append(DiningTable(restaurant_id=r2.id, table_number=f'A{i}', capacity=4 if i <= 5 else 6))
        for i in range(1, 7):
            tables.append(DiningTable(restaurant_id=r3.id, table_number=f'B{i}', capacity=2 if i <= 3 else 4))
        
        db.session.add_all(tables)
        db.session.commit()
        
    print('Database initialized successfully!')
    print('Admin user: admin / admin123')
