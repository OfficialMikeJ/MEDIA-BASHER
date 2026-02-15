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
        self.user_id = None

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
        """Test user registration"""
        timestamp = datetime.now().strftime("%H%M%S")
        user_data = {
            "username": f"testuser_{timestamp}",
            "password": "testpass123",
            "email": f"test_{timestamp}@example.com"
        }
        
        success, status, response = self.make_request('POST', 'auth/register', user_data, 200)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            return self.log_test("User Registration", True, f"- Token received, User ID: {self.user_id}")
        else:
            return self.log_test("User Registration", False, f"- Status: {status}, Response: {response}")

    def test_valid_login(self):
        """Test login with valid credentials (admin/admin123)"""
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        success, status, response = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            return self.log_test("Valid Login (admin/admin123)", True, f"- Token received")
        else:
            return self.log_test("Valid Login (admin/admin123)", False, f"- Status: {status}, Response: {response}")

    def test_invalid_login(self):
        """Test login with invalid credentials - should return 401"""
        login_data = {
            "username": "admin",
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
        
        if success and 'cpu_percent' in response and 'ram_total' in response:
            return self.log_test("System Metrics", True, f"- CPU: {response['cpu_percent']}%, RAM: {response['ram_percent']}%")
        else:
            return self.log_test("System Metrics", False, f"- Status: {status}, Response: {response}")

    def test_storage_pool_creation(self):
        """Test storage pool creation with /tmp mount point"""
        pool_data = {
            "name": "Test Storage",
            "mount_point": "/tmp",
            "pool_type": "local"
        }
        
        success, status, response = self.make_request('POST', 'storage/pools', pool_data, 200)
        
        if success and 'id' in response and 'total_space' in response:
            pool_id = response['id']
            total_space = response['total_space']
            used_space = response['used_space']
            return self.log_test("Storage Pool Creation (/tmp)", True, 
                               f"- Pool ID: {pool_id}, Total: {total_space//1024//1024}MB, Used: {used_space//1024//1024}MB"), pool_id
        else:
            return self.log_test("Storage Pool Creation (/tmp)", False, 
                               f"- Status: {status}, Response: {response}"), None

    def test_get_storage_pools(self):
        """Test getting storage pools"""
        success, status, response = self.make_request('GET', 'storage/pools', expected_status=200)
        
        if success and isinstance(response, list):
            return self.log_test("Get Storage Pools", True, f"- Found {len(response)} pools")
        else:
            return self.log_test("Get Storage Pools", False, f"- Status: {status}, Response: {response}")

    def test_get_settings(self):
        """Test getting system settings"""
        success, status, response = self.make_request('GET', 'settings', expected_status=200)
        
        if success and 'ddns_enabled' in response:
            return self.log_test("Get System Settings", True, f"- DDNS enabled: {response['ddns_enabled']}")
        else:
            return self.log_test("Get System Settings", False, f"- Status: {status}, Response: {response}")

    def test_app_templates(self):
        """Test getting app templates"""
        success, status, response = self.make_request('GET', 'apps/templates', expected_status=200)
        
        if success and isinstance(response, list):
            return self.log_test("Get App Templates", True, f"- Found {len(response)} templates")
        else:
            return self.log_test("Get App Templates", False, f"- Status: {status}, Response: {response}")

    def test_containers_list(self):
        """Test listing containers"""
        success, status, response = self.make_request('GET', 'containers/list', expected_status=200)
        
        if success and isinstance(response, list):
            return self.log_test("List Containers", True, f"- Found {len(response)} containers")
        else:
            return self.log_test("List Containers", False, f"- Status: {status}, Response: {response}")

    def cleanup_storage_pool(self, pool_id):
        """Clean up created storage pool"""
        if pool_id:
            success, status, response = self.make_request('DELETE', f'storage/pools/{pool_id}', expected_status=200)
            if success:
                print(f"🧹 Cleaned up storage pool: {pool_id}")
            else:
                print(f"⚠️  Failed to cleanup storage pool: {pool_id}")

def main():
    print("🚀 Starting Media Basher API Tests")
    print("=" * 50)
    
    tester = MediaBasherAPITester()
    
    # Test invalid login first (no auth needed)
    print("\n📋 Testing Authentication...")
    tester.test_invalid_login()
    
    # Test valid login to get token
    if not tester.test_valid_login():
        print("❌ Cannot proceed without valid authentication")
        return 1
    
    # Test authenticated endpoints
    print("\n📋 Testing Authenticated Endpoints...")
    tester.test_get_me()
    tester.test_system_metrics()
    
    # Test storage functionality (main focus)
    print("\n📋 Testing Storage Management...")
    success, pool_id = tester.test_storage_pool_creation()
    tester.test_get_storage_pools()
    
    # Test other endpoints
    print("\n📋 Testing Other Features...")
    tester.test_get_settings()
    tester.test_app_templates()
    tester.test_containers_list()
    
    # Cleanup
    if pool_id:
        tester.cleanup_storage_pool(pool_id)
    
    # Test registration (separate user)
    print("\n📋 Testing User Registration...")
    tester.test_register()
    
    # Final results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! Application is working correctly.")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed. Check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())