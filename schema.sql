CREATE TABLE admins (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE staff (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255),
    phone_number BIGINT,
    role VARCHAR(100),
    email VARCHAR(255) UNIQUE
);

CREATE TABLE student (
    Roll_no VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    phone_number BIGINT,
    dob DATE,
    gender VARCHAR(50),
    address TEXT
);

CREATE TABLE room (
    id BIGSERIAL PRIMARY KEY,
    capacity BIGINT,
    status BOOLEAN 
);

CREATE TABLE allocate_room (
    id BIGSERIAL PRIMARY KEY,
    student VARCHAR(255) REFERENCES student(Roll_no),
    room_id BIGINT REFERENCES room(id),
    alloc_date DATE,
    release_date DATE
);

CREATE TABLE complaint (
    id BIGSERIAL PRIMARY KEY,
    student_id VARCHAR(255) REFERENCES student(Roll_no),
    issue VARCHAR(255),
    complaint_date DATE,
    status BOOLEAN, 
    staff_id BIGINT REFERENCES staff(id)
);

CREATE TABLE leave_log (
    id BIGSERIAL PRIMARY KEY,
    student VARCHAR(255) REFERENCES student(Roll_no),
    leave_date DATE,
    return_date DATE
);

CREATE TABLE maintainence ( 
    id BIGSERIAL PRIMARY KEY,
    room_id BIGINT REFERENCES room(id),
    student VARCHAR(255) REFERENCES student(Roll_no),
    issue TEXT,
    status BOOLEAN, 
    request_date DATE
);

CREATE TABLE payment (
    transaction_id BIGSERIAL PRIMARY KEY,
    student VARCHAR(255) REFERENCES student(Roll_no),
    amount BIGINT,
    date DATE,
    status BOOLEAN 
);

CREATE TABLE visit_log (
    id BIGSERIAL PRIMARY KEY,
    date DATE,
    student VARCHAR(255) REFERENCES student(Roll_no),
    visitor VARCHAR(255)
);
INSERT INTO admins (username, password) VALUES ('admin', 'admin');