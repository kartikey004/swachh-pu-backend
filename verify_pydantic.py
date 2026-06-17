import sys
import os

from pydantic import ValidationError
from app.models.auth import SignUpRequest

def test_validation(payload, test_name):
    print(f"--- Running test: {test_name} ---")
    try:
        req = SignUpRequest(**payload)
        print("SUCCESS! Validated payload:")
        print(f"  Email: {req.email}")
        print(f"  Name: {req.name}")
        print(f"  Role: {req.role}")
        print(f"  Roll No: {req.roll_no}")
        print(f"  Employee ID: {req.employee_id}")
        print(f"  Zone: {req.zone}")
        print(f"  Phone: {req.phone}")
    except ValidationError as e:
        print("VALIDATION ERROR (Expected):")
        for err in e.errors():
            loc = " -> ".join(str(x) for x in err["loc"])
            print(f"  {loc}: {err['msg']}")

# Test case 1: Invalid email format
test_validation({
    "email": "invalidemail",
    "password": "password123",
    "name": "Rajesh Kumar",
    "role": "student",
    "roll_no": "12345"
}, "Test case 1: Invalid email format")

# Test case 2: Empty/Whitespace name
test_validation({
    "email": "rajesh@example.com",
    "password": "password123",
    "name": "   ",
    "role": "student",
    "roll_no": "12345"
}, "Test case 2: Empty/Whitespace name")

# Test case 3: Student missing roll_no
test_validation({
    "email": "rajesh@example.com",
    "password": "password123",
    "name": "Rajesh Kumar",
    "role": "student"
}, "Test case 3: Student missing roll_no")

# Test case 4: Worker missing employee_id/zone
test_validation({
    "email": "worker@example.com",
    "password": "password123",
    "name": "Worker Name",
    "role": "worker",
    "employee_id": "W123"
}, "Test case 4: Worker missing zone")

# Test case 5: Invalid phone number
test_validation({
    "email": "student@example.com",
    "password": "password123",
    "name": "Student Name",
    "role": "student",
    "roll_no": "S123",
    "phone": "123-456"
}, "Test case 5: Invalid phone format")

# Test case 6: Valid student signup
test_validation({
    "email": "student@example.com",
    "password": "password123",
    "name": "Student Name",
    "role": "student",
    "roll_no": "S123",
    "phone": "9876543210"
}, "Test case 6: Valid student signup")

# Test case 7: Valid worker signup
test_validation({
    "email": "worker@example.com",
    "password": "password123",
    "name": "Worker Name",
    "role": "worker",
    "employee_id": "W123",
    "zone": "Sector 14",
    "phone": "9876543210"
}, "Test case 7: Valid worker signup")
