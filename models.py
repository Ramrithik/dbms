from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Admins(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class Staff(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(255))
    phone_number = db.Column(db.BigInteger)
    role = db.Column(db.String(100))
    email = db.Column(db.String(255), unique=True)
    complaints = db.relationship('Complaint', backref='staff', lazy=True)


class Student(db.Model):
    __tablename__ = 'student'

    Roll_no = db.Column("roll_no", db.String(255), primary_key=True)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    phone_number = db.Column(db.BigInteger)
    dob = db.Column(db.Date)
    gender = db.Column(db.String(50))
    address = db.Column(db.Text)
    password = db.Column(db.String(255))  
    complaints = db.relationship('Complaint', backref='student', lazy=True)
    leave_logs = db.relationship('LeaveLog', backref='student_ref', lazy=True)
    allocated_room = db.relationship('AllocateRoom', backref='student_ref', lazy=True)
    maintenance_requests = db.relationship('Maintainence', backref='student_ref', lazy=True)
    payments = db.relationship('Payment', backref='student_ref', lazy=True)
    visit_logs = db.relationship('VisitLog', backref='student_ref', lazy=True)


class Room(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    capacity = db.Column(db.BigInteger)
    status = db.Column(db.Boolean, default=True, nullable=False) 
    allocations = db.relationship('AllocateRoom', backref='room', lazy=True)
    maintenance_requests = db.relationship('Maintainence', backref='room', lazy=True)


class AllocateRoom(db.Model):
    __tablename__ = 'allocate_room'
    id = db.Column(db.BigInteger, primary_key=True)
    student = db.Column(db.String(255), db.ForeignKey('student.roll_no'))
    room_id = db.Column(db.BigInteger, db.ForeignKey('room.id'))
    alloc_date = db.Column(db.Date)
    release_date = db.Column(db.Date)


class Complaint(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    student_id = db.Column(db.String(255), db.ForeignKey('student.roll_no'))
    issue = db.Column(db.String(255))
    complaint_date = db.Column(db.Date)
    status = db.Column(db.Boolean)
    staff_id = db.Column(db.BigInteger, db.ForeignKey('staff.id'))


class LeaveLog(db.Model):
    __tablename__ = 'leave_log'
    id = db.Column(db.BigInteger, primary_key=True)
    student = db.Column(db.String(255), db.ForeignKey('student.roll_no'))
    leave_date = db.Column(db.Date)
    return_date = db.Column(db.Date)


class Maintainence(db.Model):
    __tablename__ = 'maintainence'
    id = db.Column(db.BigInteger, primary_key=True)
    room_id = db.Column(db.BigInteger, db.ForeignKey('room.id'))
    student = db.Column(db.String(255), db.ForeignKey('student.roll_no'))
    issue = db.Column(db.Text)
    status = db.Column(db.Boolean)
    request_date = db.Column(db.Date)


class Payment(db.Model):
    transaction_id = db.Column(db.BigInteger, primary_key=True)
    student = db.Column(db.String(255), db.ForeignKey('student.roll_no'))
    amount = db.Column(db.BigInteger)
    date = db.Column(db.Date)
    status = db.Column(db.Boolean)


class VisitLog(db.Model):
    __tablename__ = 'visit_log'
    id = db.Column(db.BigInteger, primary_key=True)
    date = db.Column(db.Date)
    student = db.Column(db.String(255), db.ForeignKey('student.roll_no'))
    visitor = db.Column(db.String(255))
