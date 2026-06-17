import httpx

BASE_URL = "http://127.0.0.1:8000"

def test_signup_validation():
    print("=== Testing Signup Validation ===")
    
    # 1. Invalid email format
    r = httpx.post(f"{BASE_URL}/auth/signup", json={
        "email": "invalidemail",
        "password": "password123",
        "name": "Test User",
        "role": "student",
        "roll_no": "123"
    })
    print(f"Invalid email check: Status {r.status_code} (Expected: 422)")
    assert r.status_code == 422
    assert "value is not a valid email address" in r.text or "Invalid email format" in r.text

    # 2. Empty/whitespace name
    r = httpx.post(f"{BASE_URL}/auth/signup", json={
        "email": "test@example.com",
        "password": "password123",
        "name": "   ",
        "role": "student",
        "roll_no": "123"
    })
    print(f"Empty name check: Status {r.status_code} (Expected: 422)")
    assert r.status_code == 422
    assert "Name cannot be empty or contain only whitespace" in r.text

    # 3. Short password
    r = httpx.post(f"{BASE_URL}/auth/signup", json={
        "email": "test@example.com",
        "password": "123",
        "name": "Test User",
        "role": "student",
        "roll_no": "123"
    })
    print(f"Short password check: Status {r.status_code} (Expected: 422)")
    assert r.status_code == 422
    assert "at least 6 characters" in r.text

    # 4. Student missing roll_no
    r = httpx.post(f"{BASE_URL}/auth/signup", json={
        "email": "test@example.com",
        "password": "password123",
        "name": "Test User",
        "role": "student"
    })
    print(f"Missing student roll_no check: Status {r.status_code} (Expected: 422)")
    assert r.status_code == 422
    assert "roll_no is required for student role" in r.text

    # 5. Worker missing zone
    r = httpx.post(f"{BASE_URL}/auth/signup", json={
        "email": "test@example.com",
        "password": "password123",
        "name": "Test User",
        "role": "worker",
        "employee_id": "W123"
    })
    print(f"Missing worker zone check: Status {r.status_code} (Expected: 422)")
    assert r.status_code == 422
    assert "zone is required for worker role" in r.text

    print("Signup validation tests PASSED!\n")


def test_list_apis():
    print("=== Testing List Endpoints ===")
    
    # Test public profiles list
    r = httpx.get(f"{BASE_URL}/profiles/public/list")
    print(f"GET /profiles/public/list: Status {r.status_code} (Expected: 200)")
    assert r.status_code == 200
    assert "profiles" in r.json()
    assert "count" in r.json()

    # Test public workers list
    r = httpx.get(f"{BASE_URL}/profiles/public/workers")
    print(f"GET /profiles/public/workers: Status {r.status_code} (Expected: 200)")
    assert r.status_code == 200
    assert "profiles" in r.json()
    assert "count" in r.json()

    # Test public tasks list
    r = httpx.get(f"{BASE_URL}/tasks/public/list")
    print(f"GET /tasks/public/list: Status {r.status_code} (Expected: 200)")
    assert r.status_code == 200
    assert "tasks" in r.json()
    assert "count" in r.json()

    print("List endpoint tests PASSED!\n")


if __name__ == "__main__":
    test_signup_validation()
    test_list_apis()
    print("All integration tests completed successfully!")
