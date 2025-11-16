from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, Admins, Student, Room, AllocateRoom, Complaint, Maintainence, Payment, LeaveLog, VisitLog
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/project'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'd04a41a8f065fdd8b6663a0ec60b865512d9bbab845b63a0'
db.init_app(app)

@app.route('/')
def index():
    if 'role' not in session:
        return redirect(url_for('login'))

    if session['role'] == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif session['role'] == 'student':
        return redirect(url_for('student_dashboard'))
    else:
        return redirect(url_for('logout'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admins.query.filter_by(username=username, password=password).first()
        if admin:
            session['role'] = 'admin'
            session['username'] = admin.username
            session['user_id'] = admin.id
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        student = Student.query.filter_by(Roll_no=username, password=password).first()
        if student:
            session['role'] = 'student'
            session['username'] = student.Roll_no  
            session['student_name'] = student.name
            flash(f'Welcome, {student.name}!', 'success')
            return redirect(url_for('student_dashboard'))

        flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/student_dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    roll_no = session.get('username')
    student = Student.query.filter_by(Roll_no=roll_no).first()

    if not student:
        flash('Invalid student.', 'danger')
        return redirect(url_for('logout'))

    allocation = AllocateRoom.query.filter_by(student=roll_no).first()
    pending_complaints = Complaint.query.filter_by(
        student_id=roll_no, 
        status=False 
    ).order_by(Complaint.complaint_date.desc()).all()

    return render_template(
        'student_dashboard.html', 
        student=student, 
        allocation=allocation,
        pending_complaints=pending_complaints  
    )

@app.route('/request_room', methods=['POST'])
def request_room():
    if 'username' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('login'))

    roll_no = session.get('username')
    existing_alloc = AllocateRoom.query.filter_by(student=roll_no).first()
    if existing_alloc:
        flash(f'You are already allocated to Room {existing_alloc.room_id}.', 'info')
        return redirect(url_for('student_dashboard'))
    
    available_rooms = Room.query.filter_by(status=True).all()
    room_found = False
    
    if not available_rooms:
        flash('Sorry, no rooms are currently available or accepting new occupants.', 'warning')
        return redirect(url_for('student_dashboard'))

    for room in available_rooms:
        current_occupancy = AllocateRoom.query.filter_by(room_id=room.id).count()
        
        if current_occupancy < room.capacity:
            allocation = AllocateRoom(
                student=roll_no, 
                room_id=room.id, 
                alloc_date=datetime.now().date()
            )
            db.session.add(allocation)
            if (current_occupancy + 1) == room.capacity:
                room.status = False  
            
            db.session.commit()
            flash(f'Room {room.id} allocated successfully!', 'success')
            room_found = True
            break 

    if not room_found:
        flash('Sorry, all available rooms are currently at full capacity.', 'warning')

    return redirect(url_for('student_dashboard'))

@app.route('/release_room', methods=['POST'])
def release_room():
    if 'username' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('login'))

    roll_no = session.get('username')
    allocation = AllocateRoom.query.filter_by(student=roll_no).first()
    if not allocation:
        flash('You do not have a room to release.', 'info')
        return redirect(url_for('student_dashboard'))

    room = Room.query.get(allocation.room_id)
    room.status = True
    db.session.delete(allocation)
    db.session.commit()

    flash(f'Room {room.id} released successfully!', 'success')
    return redirect(url_for('student_dashboard'))

@app.route('/file_complaint', methods=['GET', 'POST'])
def file_complaint():
    if session.get('role') != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            issue_text = request.form['issue']
            roll_no = session.get('username')
            
            new_complaint = Complaint(
                student_id=roll_no,
                issue=issue_text,
                complaint_date=datetime.now().date(),
                status=False 
            )
            
            db.session.add(new_complaint)
            db.session.commit()
            flash('Complaint filed successfully!', 'success')
            return redirect(url_for('my_complaints'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error filing complaint: {e}', 'danger')

    return render_template('file_complaint.html')

@app.route('/my_complaints')
def my_complaints():
    if session.get('role') != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    roll_no = session.get('username')
    complaints = Complaint.query.filter_by(student_id=roll_no).order_by(Complaint.complaint_date.desc()).all()
    return render_template('my_complaints.html', complaints=complaints)

@app.route('/my_payments')
def my_payments():
    if session.get('role') != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    roll_no = session.get('username')
    
    try:
        payments = Payment.query.filter_by(student=roll_no).order_by(Payment.date.desc()).all()
        total_paid = sum(payment.amount for payment in payments)
    except Exception as e:
        flash(f"Error loading payments: {e}", "danger")
        payments = []
        total_paid = 0

    return render_template('my_payments.html', payments=payments, total_paid=total_paid)

@app.route('/my_leave_requests')
def my_leave_requests():
    if session.get('role') != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    roll_no = session.get('username')
    try:
        requests = LeaveLog.query.filter_by(student=roll_no).order_by(LeaveLog.leave_date.desc()).all()
    except Exception as e:
        flash(f'Error loading leave requests: {e}', 'danger')
        requests = []
        
    return render_template('my_leave_requests.html', requests=requests)

@app.route('/request_leave', methods=['GET', 'POST'])
def request_leave():
    if session.get('role') != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            start_date_str = request.form['leave_date']
            end_date_str = request.form['return_date']
            roll_no = session.get('username')

            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            if end_date < start_date:
                flash('Return date cannot be before leave date.', 'danger')
                return render_template('request_leave.html')
            new_leave = LeaveLog(
                student=roll_no,
                leave_date=start_date,
                return_date=end_date
            )
            db.session.add(new_leave)
            db.session.commit()
            flash('Leave logged successfully!', 'success')
            return redirect(url_for('my_leave_requests'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting request: {e}', 'danger')
            
    return render_template('request_leave.html')


@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    try:
        stats = {
            'total_students': Student.query.count(),
            'rooms_available': Room.query.filter_by(status=True).count(),
            'rooms_occupied': Room.query.filter_by(status=False).count(),
            'pending_complaints': Complaint.query.filter_by(status=False).count()
        }
    except Exception as e:
        flash(f"Error loading dashboard: {e}", "danger")
        stats = {'total_students': 0, 'rooms_available': 0, 'rooms_occupied': 0, 'pending_complaints': 0}

    return render_template('admin_dashboard.html', stats=stats)


@app.route('/students')
def list_students():
    if session.get('role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    students = Student.query.all()
    return render_template('students.html', students=students)

@app.route('/student/add', methods=['POST'])
def add_student():
    if session.get('role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    try:
        roll_no = request.form['roll_no']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']

        if Student.query.get(roll_no):
            flash(f'Student with Roll No {roll_no} already exists.', 'danger')
            return redirect(url_for('list_students'))

        new_student = Student(Roll_no=roll_no, name=name, email=email, phone_number=phone, password=password)
        db.session.add(new_student)
        db.session.commit()
        flash('Student added successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error adding student: {e}', 'danger')

    return redirect(url_for('list_students'))

@app.route('/students/edit/<roll_no>', methods=['GET', 'POST'])
def edit_student(roll_no):
    if session.get('role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    student = Student.query.filter_by(Roll_no=roll_no).first()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('list_students'))

    if request.method == 'POST':
        student.name = request.form['name']
        student.email = request.form['email']
        student.phone_number = request.form['phone']
        db.session.commit()
        flash('Student details updated successfully.', 'success')
        return redirect(url_for('list_students'))

    return render_template('edit_student.html', student=student)

@app.route('/student/delete/<string:roll_no>')
def delete_student(roll_no):
    if session.get('role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    try:
        student = Student.query.get(roll_no)
        if not student:
            flash('Student not found.', 'warning')
            return redirect(url_for('list_students'))
        
        allocation = AllocateRoom.query.filter_by(student=roll_no).first()
        if allocation:
            room = Room.query.get(allocation.room_id)
            if room:
                room.status = True  
            db.session.delete(allocation)
            
        Complaint.query.filter_by(student_id=roll_no).delete(synchronize_session=False)
        Maintainence.query.filter_by(student=roll_no).delete(synchronize_session=False)
        Payment.query.filter_by(student=roll_no).delete(synchronize_session=False)
        LeaveLog.query.filter_by(student=roll_no).delete(synchronize_session=False)
        VisitLog.query.filter_by(student=roll_no).delete(synchronize_session=False)
        
        db.session.delete(student)
        db.session.commit()
        flash('Student and all related records deleted successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting student: {e}', 'danger')

    return redirect(url_for('list_students'))

@app.route('/rooms')
def list_rooms():
    if session.get('role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    rooms = Room.query.all()
    return render_template('rooms.html', rooms=rooms)

@app.route('/room/add', methods=['POST'])
def add_room():
    if session.get('role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    try:
        capacity = request.form['capacity']
        new_room = Room(capacity=capacity) 
        db.session.add(new_room)
        db.session.commit()
        flash('Room added successfully! It is now available.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding room: {e}', 'danger')

    return redirect(url_for('list_rooms'))

@app.route('/room/delete/<int:room_id>')
def delete_room(room_id):
    if session.get('role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    try:
        room = Room.query.get(room_id)
        if room:
            if AllocateRoom.query.filter_by(room_id=room_id).first():
                flash('Cannot delete. Students are allocated to this room.', 'danger')
                return redirect(url_for('list_rooms'))

            db.session.delete(room)
            db.session.commit()
            flash('Room deleted successfully!', 'success')
        else:
            flash('Room not found.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting room: {e}', 'danger')

    return redirect(url_for('list_rooms'))



@app.route('/admin/complaints')
def view_complaints():
    if session.get('role') != 'admin':
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('index'))

    try:
        complaints = Complaint.query.order_by(Complaint.complaint_date.desc()).all()
    except Exception as e:
        flash(f"Error fetching complaints: {e}", "danger")
        complaints = []

    return render_template('view_complaints.html', complaints=complaints)

@app.route('/admin/complaint/resolve/<int:complaint_id>')
def resolve_complaint(complaint_id):
    if session.get('role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    try:
        complaint = Complaint.query.get(complaint_id)
        if complaint:
            complaint.status = True 
            db.session.commit()
            flash(f'Complaint {complaint_id} marked as resolved.', 'success')
        else:
            flash('Complaint not found.', 'warning')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error resolving complaint: {e}', 'danger')

    return redirect(url_for('view_complaints'))



@app.route('/admin/payments')
def payment_management():
    if session.get('role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    try:
        students = Student.query.all()
        
        payments = db.session.query(
            Payment, Student.name
        ).join(
            Student, Payment.student == Student.Roll_no
        ).order_by(Payment.date.desc()).all()
        
    except Exception as e:
        flash(f"Error loading payments: {e}", "danger")
        students = []
        payments = []

    today_str = datetime.now().strftime('%Y-%m-%d')
    return render_template(
        'payment_management.html', 
        students=students, 
        payments=payments, 
        today=today_str 
    )

@app.route('/admin/payments/add', methods=['POST'])
def add_payment():
    if session.get('role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    try:
        roll_no = request.form['roll_no']
        amount = request.form['amount']
        payment_date_str = request.form['payment_date']
        payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
        new_payment = Payment(
            student=roll_no,
            amount=amount,
            date=payment_date,
            status=True  
        )
        db.session.add(new_payment)
        db.session.commit()
        flash('Payment logged successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error adding payment: {e}', 'danger')

    return redirect(url_for('payment_management'))

@app.route('/admin/visitors', methods=['GET', 'POST'])
def visitor_log_management():
    if session.get('role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            student_id = request.form['student_id']
            visitor_name = request.form['visitor_name']


            new_visit = VisitLog(
                student=student_id,
                visitor=visitor_name,
                date=datetime.now().date()
            )
            db.session.add(new_visit)
            db.session.commit()
            flash('Visitor logged successfully!', 'success')
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error logging visitor: {e}', 'danger')
        
        return redirect(url_for('visitor_log_management'))

    try:
        students = Student.query.all()
        visits = db.session.query(
            VisitLog, Student.name
        ).join(
            Student, VisitLog.student == Student.Roll_no
        ).order_by(VisitLog.date.desc()).all()
        
    except Exception as e:
        flash(f'Error loading visitor log: {e}', 'danger')
        students = []
        visits = []

    return render_template('visitor_log.html', students=students, visits=visits)
@app.route('/admin/leave_management')
def leave_management():
    if session.get('role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    try:
     
        requests = db.session.query(
            LeaveLog, Student.name
        ).join(
            Student, LeaveLog.student == Student.Roll_no
        ).order_by(LeaveLog.leave_date.desc()).all()
        
    except Exception as e:
        flash(f'Error loading leave requests: {e}', 'danger')
        requests = []

    return render_template('leave_management.html', requests=requests)


@app.route('/admin/maintenance', methods=['GET', 'POST'])
def maintenance_log():
    if session.get('role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            room_id = request.form.get('room_id')
            student_id = request.form.get('student_id') 
            issue = request.form['issue']
            
            if not room_id and not student_id:
                flash('Please select either a Room or a Student.', 'danger')
                return redirect(url_for('maintenance_log'))

            new_maint = Maintainence(
                room_id=room_id if room_id else None,
                student=student_id if student_id else None,
                issue=issue,
                status=False, 
                request_date=datetime.now().date()
            )
            db.session.add(new_maint)
            db.session.commit()
            flash('Maintenance request logged successfully!', 'success')
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error logging maintenance: {e}', 'danger')
        
        return redirect(url_for('maintenance_log'))

    try:
        students = Student.query.all()
        rooms = Room.query.all()
      
        logs = db.session.query(
            Maintainence, 
            Student.name, 
            Room.id
        ).outerjoin(
            Student, Maintainence.student == Student.Roll_no
        ).outerjoin(
            Room, Maintainence.room_id == Room.id
        ).order_by(Maintainence.request_date.desc()).all()
        
    except Exception as e:
        flash(f'Error loading maintenance log: {e}', 'danger')
        students = []
        rooms = []
        logs = []

    return render_template('maintenance_log.html', students=students, rooms=rooms, logs=logs)


@app.route('/admin/maintenance/resolve/<int:maint_id>')
def resolve_maintenance(maint_id):
    if session.get('role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    try:
        maint_request = Maintainence.query.get(maint_id)
        if maint_request:
            maint_request.status = True 
            db.session.commit()
            flash(f'Maintenance request {maint_id} marked as completed.', 'success')
        else:
            flash('Request not found.', 'warning')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error resolving request: {e}', 'danger')

    return redirect(url_for('maintenance_log'))



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
