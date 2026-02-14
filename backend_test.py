import requests
import sys
import json
from datetime import datetime
import uuid

class MediaBasherAPITester:
    def __init__(self, base_url="https://dashbash.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_user_id = f"testuser_{datetime.now().strftime('%H%M%S')}"
        self.test_password = "TestPass123!"

    def run_test(self, name, method, endpoint, expected_status, data=None, auth_required=True):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if auth_required and self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
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
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(str(response_data)) < 500:
                        print(f"   Response: {response_data}")
                    elif isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                except:
                    print(f"   Response: {response.text[:200]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:300]}")

            return success, response.json() if response.text and response.text.strip() else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_register(self):
        """Test user registration"""
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={
                "username": self.test_user_id,
                "password": self.test_password,
                "email": f"{self.test_user_id}@test.com"
            },
            auth_required=False
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   Registered user: {self.test_user_id}")
            return True
        return False

    def test_login_existing_user(self):
        """Test login with existing admin user"""
        success, response = self.run_test(
            "Login Existing User (admin)",
            "POST",
            "auth/login",
            200,
            data={
                "username": "admin",
                "password": "admin123"
            },
            auth_required=False
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   Logged in as admin")
            return True
        return False

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        success, response = self.run_test(
            "Invalid Login",
            "POST",
            "auth/login",
            401,
            data={
                "username": "invalid_user",
                "password": "wrong_password"
            },
            auth_required=False
        )
        return success

    def test_get_me(self):
        """Test getting current user info"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_mark_onboarded(self):
        """Test marking user as onboarded"""
        success, response = self.run_test(
            "Mark User Onboarded",
            "POST",
            "auth/mark-onboarded",
            200
        )
        return success

    def test_system_metrics(self):
        """Test system metrics endpoint"""
        success, response = self.run_test(
            "System Metrics",
            "GET",
            "system/metrics",
            200
        )
        if success:
            required_fields = ['cpu_percent', 'cpu_count', 'ram_total', 'ram_used', 'ram_percent', 
                             'storage_total', 'storage_used', 'storage_percent']
            for field in required_fields:
                if field not in response:
                    print(f"   ⚠️  Missing field: {field}")
                    return False
            print(f"   ✅ All required metrics present")
        return success

    def test_seed_apps(self):
        """Test seeding app templates"""
        success, response = self.run_test(
            "Seed App Templates",
            "POST",
            "seed-apps",
            200
        )
        return success

    def test_get_app_templates(self):
        """Test getting app templates"""
        success, response = self.run_test(
            "Get App Templates",
            "GET",
            "apps/templates",
            200
        )
        if success:
            print(f"   Found {len(response)} app templates")
            if len(response) >= 7:
                print(f"   ✅ Expected 7+ official apps found")
            else:
                print(f"   ⚠️  Expected 7+ apps, found {len(response)}")
        return success

    def test_create_custom_app(self):
        """Test creating custom app template"""
        custom_app = {
            "name": "Test Custom App",
            "description": "A test custom application",
            "category": "Testing",
            "docker_image": "nginx:latest",
            "ports": [80],
            "official": False
        }
        success, response = self.run_test(
            "Create Custom App Template",
            "POST",
            "apps/templates",
            200,
            data=custom_app
        )
        return success

    def test_list_containers(self):
        """Test listing Docker containers"""
        success, response = self.run_test(
            "List Containers",
            "GET",
            "containers/list",
            200
        )
        if success:
            print(f"   Found {len(response)} containers")
        return success

    def test_get_storage_pools(self):
        """Test getting storage pools"""
        success, response = self.run_test(
            "Get Storage Pools",
            "GET",
            "storage/pools",
            200
        )
        if success:
            print(f"   Found {len(response)} storage pools")
        return success

    def test_add_storage_pool(self):
        """Test adding storage pool"""
        storage_pool = {
            "name": "Test Pool",
            "mount_point": "/tmp",
            "pool_type": "local"
        }
        success, response = self.run_test(
            "Add Storage Pool",
            "POST",
            "storage/pools",
            200,
            data=storage_pool
        )
        return success, response.get('id') if success else None

    def test_remove_storage_pool(self, pool_id):
        """Test removing storage pool"""
        if not pool_id:
            print("   ⚠️  No pool ID to remove")
            return False
            
        success, response = self.run_test(
            "Remove Storage Pool",
            "DELETE",
            f"storage/pools/{pool_id}",
            200
        )
        return success

    def test_get_settings(self):
        """Test getting system settings"""
        success, response = self.run_test(
            "Get System Settings",
            "GET",
            "settings",
            200
        )
        return success

    def test_update_settings(self):
        """Test updating system settings"""
        settings = {
            "ddns_enabled": True,
            "ddns_provider": "noip",
            "ssl_enabled": False
        }
        success, response = self.run_test(
            "Update System Settings",
            "PUT",
            "settings",
            200,
            data=settings
        )
        return success

def main():
    print("🚀 Starting Media Basher API Tests")
    print("=" * 50)
    
    tester = MediaBasherAPITester()
    
    # Test authentication flow
    print("\n📋 AUTHENTICATION TESTS")
    print("-" * 30)
    
    # Test registration
    if not tester.test_register():
        print("❌ Registration failed, trying with existing admin user")
        if not tester.test_login_existing_user():
            print("❌ Both registration and admin login failed, stopping tests")
            return 1
    
    # Test invalid login
    tester.test_invalid_login()
    
    # Test protected endpoints
    tester.test_get_me()
    tester.test_mark_onboarded()
    
    # Test system endpoints
    print("\n📊 SYSTEM TESTS")
    print("-" * 30)
    tester.test_system_metrics()
    
    # Test app management
    print("\n📱 APPLICATION TESTS")
    print("-" * 30)
    tester.test_seed_apps()
    tester.test_get_app_templates()
    tester.test_create_custom_app()
    
    # Test container management
    print("\n🐳 CONTAINER TESTS")
    print("-" * 30)
    tester.test_list_containers()
    
    # Test storage management
    print("\n💾 STORAGE TESTS")
    print("-" * 30)
    tester.test_get_storage_pools()
    success, pool_id = tester.test_add_storage_pool()
    if success and pool_id:
        tester.test_remove_storage_pool(pool_id)
    
    # Test settings
    print("\n⚙️  SETTINGS TESTS")
    print("-" * 30)
    tester.test_get_settings()
    tester.test_update_settings()
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 FINAL RESULTS")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        failed = tester.tests_run - tester.tests_passed
        print(f"❌ {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())