from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import secrets

from __init__ import db, login_manager, mail
from models import User, Restaurant, DiningTable, Reservation, SupportTicket

bp = Blueprint('main', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@bp.route('/')
def index():
    restaurants = Restaurant.query.all()
    return render_template('index.html', restaurants=restaurants)

@bp.route('/info')
def info():
    return render_template('info.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('main.register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('main.register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('main.index'))

@bp.route('/restaurants')
@login_required
def restaurants():
    restaurants = Restaurant.query.all()
    return render_template('restaurants.html', restaurants=restaurants)

@bp.route('/reservation/<int:restaurant_id>', methods=['GET', 'POST'])
@login_required
def make_reservation(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    
    if request.method == 'POST':
        reservation_date = request.form['date']
        reservation_time = request.form['time']
        guests = int(request.form['guests'])
        table_id = request.form.get('table_id')
        
        if not table_id:
            flash('Please select a table', 'error')
            return redirect(url_for('main.make_reservation', restaurant_id=restaurant_id))
        
        # Convert string date to date object
        reservation_date_obj = datetime.strptime(reservation_date, '%Y-%m-%d').date()
        
        # Verify table exists and belongs to this restaurant
        selected_table = DiningTable.query.filter_by(id=table_id, restaurant_id=restaurant_id).first()
        
        if not selected_table:
            flash('Invalid table selection', 'error')
            return redirect(url_for('main.make_reservation', restaurant_id=restaurant_id))
        
        # Check if table is already reserved for this date/time or within 2 hours
        # Parse the requested time
        requested_time = datetime.strptime(f"{reservation_date} {reservation_time}", '%Y-%m-%d %H:%M')
        
        # Get all active reservations for this table on this date
        existing_reservations = Reservation.query.filter_by(
            table_id=table_id,
            reservation_date=reservation_date_obj,
            status='active'
        ).all()
        
        # Check if any reservation conflicts (within 2 hours before or after)
        for existing in existing_reservations:
            existing_time = datetime.strptime(f"{existing.reservation_date} {existing.reservation_time}", '%Y-%m-%d %H:%M')
            time_diff = abs((requested_time - existing_time).total_seconds() / 3600)  # Convert to hours
            
            if time_diff < 2:
                flash(f'This table is already reserved at {existing.reservation_time}. Please choose a time at least 2 hours apart.', 'error')
                return redirect(url_for('main.make_reservation', restaurant_id=restaurant_id))
        
        # Create reservation
        reservation = Reservation(
            user_id=current_user.id,
            table_id=table_id,
            reservation_date=reservation_date_obj,
            reservation_time=reservation_time,
            guests=guests
        )
        
        db.session.add(reservation)
        db.session.commit()
        
        # Send confirmation email with HTML
        try:
            # Plain text version
            text_body = f'''Dear {current_user.username},

Your reservation has been confirmed!

Reservation Details:
-------------------
Restaurant: {restaurant.name}
Address: {restaurant.address}
Date: {reservation_date_obj.strftime('%A, %B %d, %Y')}
Time: {reservation_time}
Table: {selected_table.table_number}
Number of Guests: {guests}

Please arrive on time. If you need to cancel or modify your reservation, please contact us as soon as possible.

Restaurant Contact:
Phone: {restaurant.phone}
Hours: {restaurant.opening_hours}

Thank you for choosing CityWok!

Best regards,
CityWok Team'''

            # HTML version with logo and food images
            html_body = f'''
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #1a0000; color: #d4af37; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, rgba(139, 0, 0, 0.9) 0%, rgba(75, 0, 0, 0.95) 100%); padding: 30px; border-radius: 10px; position: relative; }}
        .bg-image {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0.1; border-radius: 10px; overflow: hidden; }}
        .bg-image img {{ width: 100%; height: 100%; object-fit: cover; }}
        .header {{ text-align: center; margin-bottom: 30px; padding: 20px; background: rgba(212, 175, 55, 0.1); border-radius: 10px; position: relative; z-index: 1; }}
        .logo {{ max-width: 200px; height: auto; margin-bottom: 15px; }}
        .title {{ color: #ffd700; font-size: 24px; margin: 10px 0; }}
        .content {{ background: rgba(139, 0, 0, 0.5); padding: 25px; border-radius: 10px; border: 2px solid rgba(212, 175, 55, 0.3); margin: 20px 0; position: relative; z-index: 1; }}
        .detail-row {{ padding: 10px 0; border-bottom: 1px solid rgba(212, 175, 55, 0.2); }}
        .detail-label {{ color: #ffd700; font-weight: bold; }}
        .detail-value {{ color: #d4af37; margin-top: 5px; }}
        .footer {{ text-align: center; margin-top: 30px; padding: 20px; color: #999; font-size: 14px; position: relative; z-index: 1; }}
        .highlight {{ background: rgba(212, 175, 55, 0.2); padding: 15px; border-radius: 8px; border-left: 4px solid #ffd700; margin: 15px 0; position: relative; z-index: 1; }}
        .food-banner {{ width: 100%; max-height: 200px; object-fit: cover; border-radius: 10px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="bg-image">
            <img src="cid:food_bg" alt="Food Background">
        </div>
        
        <div class="header">
            <img src="cid:logo" alt="CityWok Logo" class="logo">
            <h1 class="title">Reservation Confirmed!</h1>
        </div>
        
        <p style="color: #d4af37; font-size: 16px; position: relative; z-index: 1;">Dear <strong style="color: #ffd700;">{current_user.username}</strong>,</p>
        
        <p style="color: #ccc; position: relative; z-index: 1;">Your reservation has been confirmed! We look forward to serving you.</p>
        
        <div class="content">
            <h2 style="color: #ffd700; margin-top: 0;">Reservation Details</h2>
            
            <div class="detail-row">
                <div class="detail-label">Restaurant</div>
                <div class="detail-value">{restaurant.name}</div>
            </div>
            
            <div class="detail-row">
                <div class="detail-label">Address</div>
                <div class="detail-value">{restaurant.address}</div>
            </div>
            
            <div class="detail-row">
                <div class="detail-label">Date</div>
                <div class="detail-value">{reservation_date_obj.strftime('%A, %B %d, %Y')}</div>
            </div>
            
            <div class="detail-row">
                <div class="detail-label">Time</div>
                <div class="detail-value">{reservation_time}</div>
            </div>
            
            <div class="detail-row">
                <div class="detail-label">Table</div>
                <div class="detail-value">{selected_table.table_number}</div>
            </div>
            
            <div class="detail-row" style="border-bottom: none;">
                <div class="detail-label">Number of Guests</div>
                <div class="detail-value">{guests}</div>
            </div>
        </div>
        
        <div class="highlight">
            <p style="margin: 0; color: #ffd700;"><strong>Important:</strong></p>
            <p style="margin: 5px 0 0 0; color: #d4af37;">Please arrive on time. If you need to cancel or modify your reservation, please contact us as soon as possible.</p>
        </div>
        
        <div class="content">
            <h3 style="color: #ffd700; margin-top: 0;">Restaurant Contact</h3>
            <p style="color: #d4af37; margin: 5px 0;"><strong style="color: #ffd700;">Phone:</strong> {restaurant.phone}</p>
            <p style="color: #d4af37; margin: 5px 0;"><strong style="color: #ffd700;">Hours:</strong> {restaurant.opening_hours}</p>
        </div>
        
        <div class="footer">
            <p style="color: #ffd700; font-size: 16px; margin-bottom: 10px;">Thank you for choosing CityWok!</p>
            <p style="color: #999;">Best regards,<br>CityWok Team</p>
        </div>
    </div>
</body>
</html>
'''

            msg = Message(
                subject='Reservation Confirmation - CityWok',
                recipients=[current_user.email],
                sender=('CityWok Restaurant', current_app.config['SUPPORT_EMAIL']),
                body=text_body,
                html=html_body,
                reply_to=current_app.config['SUPPORT_EMAIL']
            )
            
            # Set additional headers to avoid spam
            msg.extra_headers = {
                'X-Priority': '1',
                'X-MSMail-Priority': 'High',
                'Importance': 'High',
                'X-Mailer': 'CityWok Reservation System'
            }
            
            # Attach logo image
            with current_app.open_resource('static/images/logo_fundoescuro_citywok.png') as logo:
                msg.attach('logo_fundoescuro_citywok.png', 'image/png', logo.read(), 'inline', headers=[['Content-ID', '<logo>']])
            
            # Attach background food image
            with current_app.open_resource('static/images/istockphoto-1357284270-612x612.jpg') as food_bg:
                msg.attach('food_bg.jpg', 'image/jpeg', food_bg.read(), 'inline', headers=[['Content-ID', '<food_bg>']])
            
            mail.send(msg)
            print(f"✓ Confirmation email sent to {current_user.email}")
        except Exception as e:
            print(f"✗ Error sending confirmation email: {str(e)}")
            print(f"   Email config - Server: {current_app.config['MAIL_SERVER']}, Port: {current_app.config['MAIL_PORT']}")
            print(f"   Username: {current_app.config['MAIL_USERNAME']}")
            # Don't fail the reservation if email fails
        
        flash('Reservation created successfully! A confirmation email has been sent.', 'success')
        return redirect(url_for('main.my_reservations'))
    
    # Get all tables for this restaurant
    all_tables = DiningTable.query.filter_by(restaurant_id=restaurant_id).order_by(DiningTable.table_number).all()
    
    # Default to tomorrow for reservation date
    default_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Filter out tables that are reserved (will be done via AJAX when date/time is selected)
    return render_template('reservation.html', restaurant=restaurant, tables=all_tables, default_date=default_date)

@bp.route('/api/available-tables/<int:restaurant_id>')
@login_required
def get_available_tables(restaurant_id):
    """API endpoint to get available tables for a specific date, time, and number of guests"""
    reservation_date = request.args.get('date')
    reservation_time = request.args.get('time')
    guests = request.args.get('guests', type=int)
    
    if not reservation_date or not reservation_time:
        return jsonify({'error': 'Date and time are required'}), 400
    
    try:
        # Parse the requested date and time
        reservation_date_obj = datetime.strptime(reservation_date, '%Y-%m-%d').date()
        requested_datetime = datetime.strptime(f"{reservation_date} {reservation_time}", '%Y-%m-%d %H:%M')
        
        # Get all tables for this restaurant that can accommodate the number of guests
        if guests:
            all_tables = DiningTable.query.filter(
                DiningTable.restaurant_id == restaurant_id,
                DiningTable.capacity >= guests
            ).all()
        else:
            all_tables = DiningTable.query.filter_by(restaurant_id=restaurant_id).all()
        
        # Get all active reservations for this date
        reservations = Reservation.query.filter_by(
            reservation_date=reservation_date_obj,
            status='active'
        ).all()
        
        # Build a set of unavailable table IDs
        unavailable_table_ids = set()
        
        for reservation in reservations:
            # Parse reservation time
            reservation_datetime = datetime.strptime(
                f"{reservation.reservation_date} {reservation.reservation_time}", 
                '%Y-%m-%d %H:%M'
            )
            
            # Check if within 2 hours
            time_diff = abs((requested_datetime - reservation_datetime).total_seconds() / 3600)
            
            if time_diff < 2:
                unavailable_table_ids.add(reservation.table_id)
        
        # Filter available tables
        available_tables = [
            {
                'id': table.id,
                'table_number': table.table_number,
                'capacity': table.capacity
            }
            for table in all_tables
            if table.id not in unavailable_table_ids
        ]
        
        return jsonify({
            'available_tables': available_tables,
            'total_tables': len(all_tables),
            'available_count': len(available_tables)
        })
        
    except ValueError as e:
        return jsonify({'error': 'Invalid date or time format'}), 400

@bp.route('/my-reservations')
@login_required
def my_reservations():
    reservations = Reservation.query.filter_by(user_id=current_user.id).order_by(Reservation.reservation_date.desc()).all()
    return render_template('my_reservations.html', reservations=reservations)

@bp.route('/cancel-reservation/<int:reservation_id>')
@login_required
def cancel_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    
    # Check if user owns this reservation or is admin
    if reservation.user_id != current_user.id and not current_user.is_admin:
        flash('You can only cancel your own reservations', 'error')
        return redirect(url_for('main.my_reservations'))
    
    reservation.status = 'cancelled'
    db.session.commit()
    
    flash('Reservation cancelled successfully', 'success')
    
    # Redirect based on user type
    if current_user.is_admin:
        return redirect(url_for('main.admin_reservations'))
    else:
        return redirect(url_for('main.my_reservations'))

@bp.route('/delete-reservation/<int:reservation_id>', methods=['POST'])
@login_required
def delete_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    
    # Only regular users can delete their own reservations from history
    if current_user.is_admin:
        flash('Admins cannot delete reservation history', 'error')
        return redirect(url_for('main.admin_reservations'))
    
    # Check if user owns this reservation
    if reservation.user_id != current_user.id:
        flash('You can only delete your own reservations', 'error')
        return redirect(url_for('main.my_reservations'))
    
    # Delete the reservation
    db.session.delete(reservation)
    db.session.commit()
    
    flash('Reservation deleted from history', 'success')
    return redirect(url_for('main.my_reservations'))

@bp.route('/admin/reservation/<int:reservation_id>/toggle-attendance', methods=['POST'])
@login_required
def toggle_attendance(reservation_id):
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.customer_showed_up = not reservation.customer_showed_up
    db.session.commit()
    
    return redirect(url_for('main.admin_reservations'))

@bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    total_reservations = Reservation.query.count()
    active_reservations = Reservation.query.filter_by(status='active').count()
    total_users = User.query.count()
    total_restaurants = Restaurant.query.count()
    
    return render_template('admin/dashboard.html',
                         total_reservations=total_reservations,
                         active_reservations=active_reservations,
                         total_users=total_users,
                         total_restaurants=total_restaurants)

@bp.route('/admin/reservations')
@login_required
def admin_reservations():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    reservations = Reservation.query.order_by(Reservation.reservation_date.desc()).all()
    return render_template('admin/reservations.html', reservations=reservations)

@bp.route('/admin/restaurants')
@login_required
def admin_restaurants():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    restaurants = Restaurant.query.all()
    return render_template('admin/restaurants.html', restaurants=restaurants)

def send_support_email(email, subject, message):
    """Send support email to admin with logo and food images"""
    try:
        from __init__ import mail
        
        # Plain text version
        text_body = f'''
New Support Ticket Received

From: {email}
Subject: {subject}

Message:
{message}

---
Please reply to: {email}
        '''
        
        # HTML version with logo
        html_body = f'''
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #1a0000; color: #d4af37; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, rgba(139, 0, 0, 0.9) 0%, rgba(75, 0, 0, 0.95) 100%); padding: 30px; border-radius: 10px; }}
        .header {{ text-align: center; margin-bottom: 30px; padding: 20px; background: rgba(212, 175, 55, 0.1); border-radius: 10px; }}
        .logo {{ max-width: 180px; height: auto; margin-bottom: 15px; }}
        .title {{ color: #ffd700; font-size: 22px; margin: 10px 0; }}
        .content {{ background: rgba(139, 0, 0, 0.5); padding: 20px; border-radius: 10px; border: 2px solid rgba(212, 175, 55, 0.3); margin: 20px 0; }}
        .label {{ color: #ffd700; font-weight: bold; margin-top: 15px; }}
        .value {{ color: #d4af37; margin-top: 5px; padding: 10px; background: rgba(0,0,0,0.3); border-radius: 5px; }}
        .footer {{ text-align: center; margin-top: 20px; color: #999; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="cid:logo" alt="CityWok Logo" class="logo">
            <h1 class="title">New Support Ticket</h1>
        </div>
        
        <div class="content">
            <div class="label">From:</div>
            <div class="value">{email}</div>
            
            <div class="label">Subject:</div>
            <div class="value">{subject}</div>
            
            <div class="label">Message:</div>
            <div class="value">{message}</div>
        </div>
        
        <div class="footer">
            <p style="color: #ffd700;">Please reply to: {email}</p>
            <p>CityWok Support System</p>
        </div>
    </div>
</body>
</html>
        '''
        
        msg = Message(
            subject=f'🎫 Support Ticket: {subject}',
            recipients=[current_app.config['SUPPORT_EMAIL']],
            body=text_body,
            html=html_body,
            reply_to=email
        )
        
        # Attach logo
        with current_app.open_resource('static/images/logo_fundoescuro_citywok.png') as logo:
            msg.attach('logo_fundoescuro_citywok.png', 'image/png', logo.read(), 'inline', headers=[['Content-ID', '<logo>']])
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

@bp.route('/support', methods=['GET', 'POST'])
def support():
    if request.method == 'POST':
        email = request.form.get('email', '')
        subject = request.form.get('subject', '')
        message = request.form.get('message', '')
        
        if email and subject and message:
            # Generate unique ticket number
            ticket_number = f"TKT-{datetime.utcnow().strftime('%Y%m%d')}-{SupportTicket.query.count() + 1:04d}"
            
            # Save to database
            ticket = SupportTicket(
                ticket_number=ticket_number,
                email=email,
                subject=subject,
                message=message
            )
            db.session.add(ticket)
            db.session.commit()
            
            # Send confirmation email to user
            # Send confirmation email to user
            try:
                # Plain text version
                text_body = f'''Dear Customer,

Your support ticket has been created successfully.

Ticket Details:
--------------
Ticket Number: {ticket_number}
Subject: {subject}
Status: Open

Your Message:
{message}

Our support team will review your ticket and respond as soon as possible. You will receive an email notification when we reply.

Please keep your ticket number for reference.

Best regards,
CityWok Support Team'''

                # HTML version with logo and design
                html_body = f'''
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #1a0000; color: #d4af37; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, rgba(139, 0, 0, 0.9) 0%, rgba(75, 0, 0, 0.95) 100%); padding: 30px; border-radius: 10px; position: relative; }}
        .bg-image {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0.1; border-radius: 10px; overflow: hidden; }}
        .bg-image img {{ width: 100%; height: 100%; object-fit: cover; }}
        .header {{ text-align: center; margin-bottom: 30px; padding: 20px; background: rgba(212, 175, 55, 0.1); border-radius: 10px; position: relative; z-index: 1; }}
        .logo {{ max-width: 200px; height: auto; margin-bottom: 15px; }}
        .title {{ color: #ffd700; font-size: 24px; margin: 10px 0; }}
        .content {{ background: rgba(139, 0, 0, 0.5); padding: 25px; border-radius: 10px; border: 2px solid rgba(212, 175, 55, 0.3); margin: 20px 0; position: relative; z-index: 1; }}
        .detail-row {{ padding: 10px 0; border-bottom: 1px solid rgba(212, 175, 55, 0.2); }}
        .detail-label {{ color: #ffd700; font-weight: bold; }}
        .detail-value {{ color: #d4af37; margin-top: 5px; }}
        .footer {{ text-align: center; margin-top: 30px; padding: 20px; color: #999; font-size: 14px; position: relative; z-index: 1; }}
        .highlight {{ background: rgba(212, 175, 55, 0.2); padding: 15px; border-radius: 8px; border-left: 4px solid #ffd700; margin: 15px 0; position: relative; z-index: 1; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="bg-image">
            <img src="cid:food_bg" alt="Food Background">
        </div>
        
        <div class="header">
            <img src="cid:logo" alt="CityWok Logo" class="logo">
            <h1 class="title">Support Ticket Created</h1>
        </div>
        
        <p style="color: #d4af37; font-size: 16px; position: relative; z-index: 1;">Dear Customer,</p>
        
        <p style="color: #ccc; position: relative; z-index: 1;">Your support ticket has been created successfully.</p>
        
        <div class="content">
            <h2 style="color: #ffd700; margin-top: 0;">Ticket Details</h2>
            
            <div class="detail-row">
                <div class="detail-label">Ticket Number</div>
                <div class="detail-value">{ticket_number}</div>
            </div>
            
            <div class="detail-row">
                <div class="detail-label">Subject</div>
                <div class="detail-value">{subject}</div>
            </div>
            
            <div class="detail-row" style="border-bottom: none;">
                <div class="detail-label">Status</div>
                <div class="detail-value" style="color: #90EE90;">✓ Open</div>
            </div>
        </div>
        
        <div class="content">
            <h3 style="color: #ffd700; margin-top: 0;">Your Message</h3>
            <p style="color: #d4af37; margin: 0;">{message}</p>
        </div>
        
        <div class="highlight">
            <p style="margin: 0; color: #ffd700;"><strong>What's Next?</strong></p>
            <p style="margin: 5px 0 0 0; color: #d4af37;">Our support team will review your ticket and respond as soon as possible. You will receive an email notification when we reply.</p>
        </div>
        
        <div class="footer">
            <p style="color: #ffd700; font-size: 16px; margin-bottom: 10px;">Please keep your ticket number for reference</p>
            <p style="color: #999;">Best regards,<br>CityWok Support Team</p>
        </div>
    </div>
</body>
</html>
'''

                msg = Message(
                    subject=f'Support Ticket Created - {ticket_number}',
                    recipients=[email],
                    sender=('CityWok Support', current_app.config['SUPPORT_EMAIL']),
                    body=text_body,
                    html=html_body,
                    reply_to=current_app.config['SUPPORT_EMAIL']
                )
                
                # Attach logo
                with current_app.open_resource('static/images/logo_fundoescuro_citywok.png') as logo:
                    msg.attach('logo_fundoescuro_citywok.png', 'image/png', logo.read(), 'inline', headers=[['Content-ID', '<logo>']])
                
                # Attach background
                with current_app.open_resource('static/images/istockphoto-1357284270-612x612.jpg') as food_bg:
                    msg.attach('food_bg.jpg', 'image/jpeg', food_bg.read(), 'inline', headers=[['Content-ID', '<food_bg>']])
                
                mail.send(msg)
                print(f"✓ Ticket confirmation sent to {email}")
            except Exception as e:
                print(f"✗ Error sending ticket confirmation: {str(e)}")
            
            # Send notification to admin
            try:
                admin_msg = Message(
                    subject=f'New Support Ticket: {ticket_number}',
                    recipients=[current_app.config['SUPPORT_EMAIL']],
                    sender=current_app.config['SUPPORT_EMAIL'],
                    body=f'''New Support Ticket Received

Ticket Number: {ticket_number}
From: {email}
Subject: {subject}

Message:
{message}

---
Login to admin panel to respond: {url_for('main.admin_support_tickets', _external=True)}
                    '''
                )
                mail.send(admin_msg)
                print(f"✓ Admin notification sent")
            except Exception as e:
                print(f"✗ Error sending admin notification: {str(e)}")
            
            flash(f'Thank you for contacting us! Your ticket number is {ticket_number}. We will get back to you soon.', 'success')
            return redirect(url_for('main.support'))
        else:
            flash('Please fill in all fields', 'error')
    
    return render_template('support.html')

@bp.route('/admin/support-tickets')
@login_required
def admin_support_tickets():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    tickets = SupportTicket.query.order_by(SupportTicket.created_at.desc()).all()
    return render_template('admin/support_tickets.html', tickets=tickets)

@bp.route('/admin/support-ticket/<int:ticket_id>/close', methods=['POST'])
@login_required
def close_support_ticket(ticket_id):
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    ticket = SupportTicket.query.get_or_404(ticket_id)
    ticket.status = 'closed'
    db.session.commit()
    flash('Support ticket closed', 'success')
    return redirect(url_for('main.admin_support_tickets'))

@bp.route('/admin/support-ticket/<int:ticket_id>/respond', methods=['POST'])
@login_required
def respond_support_ticket(ticket_id):
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    ticket = SupportTicket.query.get_or_404(ticket_id)
    response = request.form.get('response', '').strip()
    
    if not response:
        flash('Please enter a response', 'error')
        return redirect(url_for('main.admin_support_tickets'))
    
    ticket.admin_response = response
    ticket.status = 'answered'
    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    
    # Send response email to user
    try:
        # Plain text version
        text_body = f'''Dear Customer,

We have responded to your support ticket.

Ticket Number: {ticket.ticket_number}
Subject: {ticket.subject}
Status: Answered

Your Original Message:
{ticket.message}

Our Response:
{response}

If you have any further questions, please reply to this email or create a new support ticket.

Best regards,
CityWok Support Team'''

        # HTML version with logo
        html_body = f'''
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #1a0000; color: #d4af37; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, rgba(139, 0, 0, 0.9) 0%, rgba(75, 0, 0, 0.95) 100%); padding: 30px; border-radius: 10px; }}
        .header {{ text-align: center; margin-bottom: 30px; padding: 20px; background: rgba(212, 175, 55, 0.1); border-radius: 10px; }}
        .logo {{ max-width: 180px; height: auto; margin-bottom: 15px; }}
        .title {{ color: #ffd700; font-size: 22px; margin: 10px 0; }}
        .content {{ background: rgba(139, 0, 0, 0.5); padding: 20px; border-radius: 10px; border: 2px solid rgba(212, 175, 55, 0.3); margin: 20px 0; }}
        .label {{ color: #ffd700; font-weight: bold; margin-top: 15px; }}
        .value {{ color: #d4af37; margin-top: 5px; padding: 10px; background: rgba(0,0,0,0.3); border-radius: 5px; }}
        .response-box {{ background: rgba(212, 175, 55, 0.2); padding: 15px; border-radius: 8px; border-left: 4px solid #ffd700; margin: 15px 0; }}
        .footer {{ text-align: center; margin-top: 20px; color: #999; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="cid:logo" alt="CityWok Logo" class="logo">
            <h1 class="title">Support Ticket Response</h1>
        </div>
        
        <p style="color: #d4af37; font-size: 16px;">Dear Customer,</p>
        
        <p style="color: #ccc;">We have responded to your support ticket.</p>
        
        <div class="content">
            <div class="label">Ticket Number:</div>
            <div class="value">{ticket.ticket_number}</div>
            
            <div class="label">Subject:</div>
            <div class="value">{ticket.subject}</div>
            
            <div class="label">Status:</div>
            <div class="value" style="color: #90EE90;">✓ Answered</div>
            
            <div class="label">Your Original Message:</div>
            <div class="value">{ticket.message}</div>
        </div>
        
        <div class="response-box">
            <div class="label">Our Response:</div>
            <p style="color: #d4af37; margin-top: 10px;">{response}</p>
        </div>
        
        <div class="content">
            <p style="color: #ccc; margin: 0;">If you have any further questions, please reply to this email or create a new support ticket.</p>
        </div>
        
        <div class="footer">
            <p style="color: #ffd700;">Best regards,<br>CityWok Support Team</p>
        </div>
    </div>
</body>
</html>
'''
        
        msg = Message(
            subject=f'✉️ Response to Your Support Ticket - {ticket.ticket_number}',
            recipients=[ticket.email],
            sender=current_app.config['SUPPORT_EMAIL'],
            body=text_body,
            html=html_body
        )
        
        # Attach logo
        with current_app.open_resource('static/images/logo_fundoescuro_citywok.png') as logo:
            msg.attach('logo_fundoescuro_citywok.png', 'image/png', logo.read(), 'inline', headers=[['Content-ID', '<logo>']])
        
        mail.send(msg)
        print(f"✓ Response sent to {ticket.email}")
        flash('Response sent successfully!', 'success')
    except Exception as e:
        print(f"✗ Error sending response email: {str(e)}")
        flash('Response saved but email failed to send', 'error')
    
    return redirect(url_for('main.admin_support_tickets'))

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Update email only
        new_email = request.form.get('email', current_user.email)
        if new_email != current_user.email:
            if User.query.filter_by(email=new_email).first():
                flash('Email already in use', 'error')
            else:
                current_user.email = new_email
                db.session.commit()
                flash('Email updated successfully!', 'success')
        else:
            flash('No changes made', 'success')
        return redirect(url_for('main.profile'))
    
    return render_template('profile.html')

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if not current_user.check_password(current_password):
                flash('Current password is incorrect', 'error')
            elif new_password != confirm_password:
                flash('New passwords do not match', 'error')
            elif len(new_password) < 6:
                flash('Password must be at least 6 characters', 'error')
            else:
                current_user.set_password(new_password)
                db.session.commit()
                flash('Password changed successfully!', 'success')
                return redirect(url_for('main.settings'))
        
        elif action == 'update_email':
            new_email = request.form.get('new_email')
            if User.query.filter_by(email=new_email).first():
                flash('Email already in use', 'error')
            else:
                current_user.email = new_email
                db.session.commit()
                flash('Email updated successfully!', 'success')
                return redirect(url_for('main.settings'))
        
        elif action == 'request_deletion':
            reason = request.form.get('deletion_reason', '').strip()
            if not reason:
                flash('Please provide a reason for account deletion', 'error')
            elif not current_user.deletion_requested:
                current_user.deletion_requested = True
                current_user.deletion_requested_at = datetime.utcnow()
                current_user.deletion_reason = reason
                db.session.commit()
                flash('Account deletion request submitted. An administrator will review your request.', 'success')
            else:
                flash('You have already requested account deletion', 'error')
            return redirect(url_for('main.settings'))
        
        elif action == 'cancel_deletion':
            if current_user.deletion_requested:
                current_user.deletion_requested = False
                current_user.deletion_requested_at = None
                current_user.deletion_reason = None
                db.session.commit()
                flash('Account deletion request has been cancelled', 'success')
            return redirect(url_for('main.settings'))
    
    return render_template('settings.html')

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            # Send reset email
            try:
                reset_url = url_for('main.reset_password', token=token, _external=True)
                
                # Plain text version
                text_body = f'''Hello {user.username},

You requested to reset your password. Click the link below to reset it:

{reset_url}

This link will expire in 1 hour.

If you didn't request this, please ignore this email.

Best regards,
CityWok Team'''

                # HTML version with logo and food images
                html_body = f'''
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #1a0000; color: #d4af37; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, rgba(139, 0, 0, 0.9) 0%, rgba(75, 0, 0, 0.95) 100%); padding: 30px; border-radius: 10px; }}
        .header {{ text-align: center; margin-bottom: 30px; padding: 20px; background: rgba(212, 175, 55, 0.1); border-radius: 10px; }}
        .logo {{ max-width: 180px; height: auto; margin-bottom: 15px; }}
        .food-banner {{ display: flex; justify-content: center; gap: 8px; margin: 15px 0; }}
        .title {{ color: #ffd700; font-size: 22px; margin: 10px 0; }}
        .content {{ background: rgba(139, 0, 0, 0.5); padding: 20px; border-radius: 10px; border: 2px solid rgba(212, 175, 55, 0.3); margin: 20px 0; }}
        .btn {{ display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #d4af37 0%, #ffd700 100%); color: #1a0000; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 20px; color: #999; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="cid:logo" alt="CityWok Logo" class="logo">
            <h1 class="title">Password Reset Request</h1>
        </div>
        
        <p style="color: #d4af37; font-size: 16px;">Hello <strong style="color: #ffd700;">{user.username}</strong>,</p>
        
        <div class="content">
            <p style="color: #ccc;">You requested to reset your password. Click the button below to reset it:</p>
            
            <div style="text-align: center;">
                <a href="{reset_url}" class="btn">Reset Password</a>
            </div>
            
            <p style="color: #999; font-size: 14px; margin-top: 20px;">Or copy this link: <br><span style="color: #d4af37; word-break: break-all;">{reset_url}</span></p>
            
            <p style="color: #ff9999; margin-top: 20px;"><strong>⚠️ This link will expire in 1 hour.</strong></p>
            
            <p style="color: #999; font-size: 14px;">If you didn't request this, please ignore this email.</p>
        </div>
        
        <div class="footer">
            <p style="color: #ffd700;">Best regards,<br>CityWok Team</p>
        </div>
    </div>
</body>
</html>
'''
                
                msg = Message(
                    subject='🔐 Password Reset Request - CityWok',
                    recipients=[user.email],
                    body=text_body,
                    html=html_body
                )
                
                # Attach logo
                with current_app.open_resource('static/images/logo_fundoescuro_citywok.png') as logo:
                    msg.attach('logo_fundoescuro_citywok.png', 'image/png', logo.read(), 'inline', headers=[['Content-ID', '<logo>']])
                
                mail.send(msg)
                flash('Password reset instructions have been sent to your email', 'success')
            except Exception as e:
                flash('Error sending email. Please try again later.', 'error')
                print(f"Email error: {str(e)}")
        else:
            # Don't reveal if email exists
            flash('If that email exists, password reset instructions have been sent', 'success')
        
        return redirect(url_for('main.login'))
    
    return render_template('forgot_password.html')

@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        flash('Invalid or expired reset link', 'error')
        return redirect(url_for('main.forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash('Passwords do not match', 'error')
        elif len(new_password) < 6:
            flash('Password must be at least 6 characters', 'error')
        else:
            user.set_password(new_password)
            user.reset_token = None
            user.reset_token_expiry = None
            db.session.commit()
            flash('Password reset successful! You can now log in.', 'success')
            return redirect(url_for('main.login'))
    
    return render_template('reset_password.html', token=token)

@bp.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    search_query = request.args.get('search', '').strip()
    
    if search_query:
        users = User.query.filter(
            (User.username.like(f'%{search_query}%')) | 
            (User.email.like(f'%{search_query}%'))
        ).order_by(User.created_at.desc()).all()
    else:
        users = User.query.order_by(User.created_at.desc()).all()
    
    return render_template('admin/users.html', users=users, search_query=search_query)

@bp.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'error')
        return redirect(url_for('main.admin_users'))
    
    if user.is_admin:
        flash('You cannot delete another administrator account', 'error')
        return redirect(url_for('main.admin_users'))
    
    # Delete user's reservations first
    Reservation.query.filter_by(user_id=user.id).delete()
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} has been deleted', 'success')
    return redirect(url_for('main.admin_users'))
