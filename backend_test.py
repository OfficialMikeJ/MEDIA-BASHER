import requests
import sys
import json
from datetime import datetime

class MediaBasherAPITester:
    def __init__(self, base_url="https://mediabasher.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.username = None

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            return success, response.status_code, response_data
            
        except Exception as e:
            print(f"Request failed: {str(e)}")
            return False, 0, {"error": str(e)}

    def test_register(self):
        """Test user registration as specified in review request"""
        user_data = {
            "username": "testuser123",
            "password": "testpass123",
            "email": "test@test.com"
        }
        
        success, status, response = self.make_request('POST', 'auth/register', user_data, 200)
        
        if success and 'token' in response:
            self.token = response['token']
            return self.log_test("User Registration", True, f"- Token received: {self.token[:20]}...")
        else:
            return self.log_test("User Registration", False, f"- Status: {status}, Response: {response}")

    def test_valid_login(self):
        """Test login with existing user mike/test123 as specified in review request"""
        login_data = {
            "username": "mike",
            "password": "test123"
        }
        
        success, status, response = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success and 'token' in response:
            self.token = response['token']
            self.username = response.get('username')
            first_login = response.get('first_login')
            return self.log_test("Valid Login (mike/test123)", True, 
                               f"- Token received, Username: {self.username}, First login: {first_login}")
        else:
            return self.log_test("Valid Login (mike/test123)", False, f"- Status: {status}, Response: {response}")

    def test_invalid_login(self):
        """Test login with invalid credentials - should return 401"""
        login_data = {
            "username": "mike",
            "password": "wrongpassword"
        }
        
        success, status, response = self.make_request('POST', 'auth/login', login_data, 401)
        
        if success and 'detail' in response:
            return self.log_test("Invalid Login Error Handling", True, f"- Proper 401 error: {response['detail']}")
        else:
            return self.log_test("Invalid Login Error Handling", False, f"- Expected 401, got {status}: {response}")

    def test_get_me(self):
        """Test getting current user info"""
        success, status, response = self.make_request('GET', 'auth/me', expected_status=200)
        
        if success and 'username' in response:
            return self.log_test("Get Current User", True, f"- Username: {response['username']}")
        else:
            return self.log_test("Get Current User", False, f"- Status: {status}, Response: {response}")

    def test_system_metrics(self):
        """Test system metrics endpoint"""
        success, status, response = self.make_request('GET', 'system/metrics', expected_status=200)
        
        if success and 'cpu' in response and 'memory' in response:
            return self.log_test("System Metrics", True, f"- CPU: {response['cpu']}%, Memory: {response['memory']['percent']}%")
        else:
            return self.log_test("System Metrics", False, f"- Status: {status}, Response: {response}")

    def test_cors_headers(self):
        """Test CORS headers are properly set"""
        url = f"{self.base_url}/api/auth/login"
        headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.options(url, headers=headers, timeout=10)
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            if cors_headers['Access-Control-Allow-Origin'] == '*':
                return self.log_test("CORS Headers", True, f"- Headers: {cors_headers}")
            else:
                return self.log_test("CORS Headers", False, f"- Missing or incorrect CORS headers: {cors_headers}")
                
        except Exception as e:
            return self.log_test("CORS Headers", False, f"- Error: {str(e)}")

    def test_storage_pool_creation(self):
        """Test storage pool creation with /tmp path"""
        pool_data = {
            "name": "Test Storage Pool",
            "path": "/tmp"
        }
        
        success, status, response = self.make_request('POST', 'storage/pools', pool_data, 200)
        
        if success and 'message' in response:
            return self.log_test("Storage Pool Creation (/tmp)", True, f"- {response['message']}")
        else:
            return self.log_test("Storage Pool Creation (/tmp)", False, f"- Status: {status}, Response: {response}")

    def test_storage_pool_root_path(self):
        """Test storage pool creation with root path / as specified in review request"""
        pool_data = {
            "name": "Main Storage",
            "path": "/"
        }
        
        success, status, response = self.make_request('POST', 'storage/pools', pool_data, 200)
        
        if success and 'message' in response:
            return self.log_test("Storage Pool Creation (Root /)", True, f"- {response['message']}")
        else:
            # Check if error response is properly formatted (string, not object)
            error_detail = response.get('detail', 'Unknown error')
            if isinstance(error_detail, str):
                return self.log_test("Storage Pool Creation (Root /)", False, f"- Status: {status}, Error: {error_detail} (Proper string format)")
            else:
                return self.log_test("Storage Pool Creation (Root /)", False, f"- Status: {status}, Error format issue: {response}")

    def test_storage_pool_invalid_path(self):
        """Test storage pool creation with invalid path to check error format"""
        pool_data = {
            "name": "Invalid Storage",
            "path": "/nonexistent/path/12345"
        }
        
        success, status, response = self.make_request('POST', 'storage/pools', pool_data, 400)
        
        if success and 'detail' in response:
            error_detail = response['detail']
            if isinstance(error_detail, str):
                return self.log_test("Storage Pool Invalid Path Error Format", True, f"- Proper string error: {error_detail}")
            else:
                return self.log_test("Storage Pool Invalid Path Error Format", False, f"- Error not string format: {response}")
        else:
            return self.log_test("Storage Pool Invalid Path Error Format", False, f"- Status: {status}, Response: {response}")

    def test_get_storage_pools(self):
        """Test getting storage pools"""
        success, status, response = self.make_request('GET', 'storage/pools', expected_status=200)
        
        if success and isinstance(response, list):
            return self.log_test("Get Storage Pools", True, f"- Found {len(response)} pools")
        else:
            return self.log_test("Get Storage Pools", False, f"- Status: {status}, Response: {response}")

    def test_containers_list(self):
        """Test listing containers"""
        success, status, response = self.make_request('GET', 'containers/list', expected_status=200)
        
        if success and isinstance(response, list):
            return self.log_test("List Containers (/containers/list)", True, f"- Found {len(response)} containers")
        else:
            return self.log_test("List Containers (/containers/list)", False, f"- Status: {status}, Response: {response}")

    def test_containers_endpoint(self):
        """Test containers endpoint (alternative endpoint)"""
        success, status, response = self.make_request('GET', 'containers', expected_status=200)
        
        if success and isinstance(response, list):
            return self.log_test("List Containers (/containers)", True, f"- Found {len(response)} containers")
        else:
            return self.log_test("List Containers (/containers)", False, f"- Status: {status}, Response: {response}")

    def test_applications_before_seed(self):
        """Test applications endpoint before seeding"""
        success, status, response = self.make_request('GET', 'applications', expected_status=200)
        
        if success and isinstance(response, list):
            return self.log_test("Applications Before Seed", True, f"- Found {len(response)} applications")
        else:
            return self.log_test("Applications Before Seed", False, f"- Status: {status}, Response: {response}")

    def test_seed_applications(self):
        """Test seeding applications as specified in review request"""
        success, status, response = self.make_request('POST', 'seed-apps', expected_status=200)
        
        if success and 'message' in response:
            return self.log_test("Seed Applications", True, f"- {response['message']}")
        else:
            return self.log_test("Seed Applications", False, f"- Status: {status}, Response: {response}")

    def test_applications_after_seed(self):
        """Test applications endpoint after seeding"""
        success, status, response = self.make_request('GET', 'applications', expected_status=200)
        
        if success and isinstance(response, list) and len(response) > 0:
            app_names = [app.get('name', 'Unknown') for app in response]
            return self.log_test("Applications After Seed", True, f"- Found {len(response)} applications: {', '.join(app_names[:3])}...")
        else:
            return self.log_test("Applications After Seed", False, f"- Status: {status}, Response: {response}")

    def create_test_user(self):
        """Create mike user for testing if it doesn't exist"""
        user_data = {
            "username": "mike",
            "password": "test123",
            "email": "mike@test.com"
        }
        
        success, status, response = self.make_request('POST', 'auth/register', user_data, 200)
        
        if success:
            return self.log_test("Create Test User (mike)", True, "- User created successfully")
        elif status == 400 and 'already exists' in str(response):
            return self.log_test("Create Test User (mike)", True, "- User already exists")
        else:
            return self.log_test("Create Test User (mike)", False, f"- Status: {status}, Response: {response}")

def main():
    print("🚀 Starting Media Basher Authentication API Tests")
    print("=" * 60)
    
    tester = MediaBasherAPITester()
    
    # Test CORS headers first
    print("\n📋 Testing CORS Configuration...")
    tester.test_cors_headers()
    
    # Create test user if needed
    print("\n📋 Setting up Test User...")
    tester.create_test_user()
    
    # Test invalid login first (no auth needed)
    print("\n📋 Testing Authentication Errors...")
    tester.test_invalid_login()
    
    # Test registration with specific data from review request
    print("\n📋 Testing User Registration...")
    tester.test_register()
    
    # Test valid login to get token (mike/test123)
    print("\n📋 Testing Valid Login...")
    if not tester.test_valid_login():
        print("❌ Cannot proceed without valid authentication")
        return 1
    
    # Test protected endpoints with token
    print("\n📋 Testing Protected Endpoints...")
    tester.test_get_me()
    tester.test_system_metrics()
    tester.test_containers_list()
    
    # Test storage functionality
    print("\n📋 Testing Storage Management...")
    tester.test_storage_pool_creation()
    tester.test_get_storage_pools()
    
    # Final results
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All backend API tests passed! Backend is working correctly.")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed. Check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())