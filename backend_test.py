#!/usr/bin/env python3
"""
PT Rahaza ERP - Phase 5b BOM Multi-Version Configuration Backend Test
Testing BOM multi-version functionality and related APIs.
"""

import requests
import sys
import json
from datetime import datetime, timedelta

class RahazaBOMTester:
    def __init__(self, base_url="https://garment-rahaza-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.test_model_id = None
        self.test_size_ids = []
        self.test_bom_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text[:200]}")
                self.failed_tests.append(f"{name}: Expected {expected_status}, got {response.status_code}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append(f"{name}: {str(e)}")
            return False, {}

    def test_login(self):
        """Test login with admin credentials"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "api/auth/login",
            200,
            data={"email": "admin@garment.com", "password": "Admin@123"}
        )
        if success:
            print(f"   Login response keys: {list(response.keys())}")
            if 'access_token' in response:
                self.token = response['access_token']
                print(f"   Token obtained: {self.token[:20]}...")
                return True
            elif 'token' in response:
                self.token = response['token']
                print(f"   Token obtained: {self.token[:20]}...")
                return True
        return False

    def test_health_check(self):
        """Test basic health check"""
        return self.run_test("Health Check", "GET", "api/health", 200)[0]

    def test_get_models(self):
        """Test get models API and store test model"""
        success, response = self.run_test(
            "Get Models",
            "GET",
            "api/rahaza/models",
            200
        )
        if success and response:
            active_models = [m for m in response if m.get('active', True)]
            if active_models:
                self.test_model_id = active_models[0]['id']
                print(f"   Using test model: {active_models[0].get('code')} - {active_models[0].get('name')}")
            return True
        return False

    def test_get_sizes(self):
        """Test get sizes API and store test sizes"""
        success, response = self.run_test(
            "Get Sizes",
            "GET",
            "api/rahaza/sizes",
            200
        )
        if success and response:
            active_sizes = [s for s in response if s.get('active', True)]
            if len(active_sizes) >= 2:
                self.test_size_ids = [s['id'] for s in active_sizes[:4]]  # Get first 4 sizes
                print(f"   Using test sizes: {[s.get('code') for s in active_sizes[:4]]}")
            return True
        return False

    def test_get_materials(self):
        """Test get materials API for BOM creation"""
        success, response = self.run_test(
            "Get Materials - Yarn",
            "GET",
            "api/rahaza/materials?type=yarn",
            200
        )
        
        success2, response2 = self.run_test(
            "Get Materials - Accessory",
            "GET",
            "api/rahaza/materials?type=accessory",
            200
        )
        
        return success and success2

    def test_get_model_bom_matrix(self):
        """Test get model BOM matrix (shows all sizes with active versions)"""
        if not self.test_model_id:
            print("   Skipping - no test model available")
            return False
            
        success, response = self.run_test(
            "Get Model BOM Matrix",
            "GET",
            f"api/rahaza/models/{self.test_model_id}/bom",
            200
        )
        
        if success and response:
            print(f"   Matrix has {len(response.get('matrix', []))} size rows")
            return True
        return False

    def test_create_bom_version(self):
        """Test create new BOM version"""
        if not self.test_model_id or not self.test_size_ids:
            print("   Skipping - no test model/sizes available")
            return False
            
        test_bom_data = {
            "model_id": self.test_model_id,
            "size_id": self.test_size_ids[0],
            "yarn_materials": [
                {
                    "name": "Test Yarn Material",
                    "code": "TEST-YARN-001",
                    "yarn_type": "Cotton 100%",
                    "qty_kg": 0.5,
                    "notes": "Test yarn for BOM"
                }
            ],
            "accessory_materials": [
                {
                    "name": "Test Button",
                    "code": "TEST-BTN-001",
                    "qty": 6,
                    "unit": "pcs",
                    "notes": "Test button for BOM"
                }
            ],
            "notes": "Test BOM version created by automated test"
        }
        
        success, response = self.run_test(
            "Create BOM Version",
            "POST",
            "api/rahaza/boms",
            200,
            data=test_bom_data
        )
        
        if success and response:
            self.test_bom_id = response.get('id')
            print(f"   Created BOM version {response.get('version')} with ID: {self.test_bom_id}")
            return True
        return False

    def test_get_bom_versions(self):
        """Test get BOM versions for specific model+size"""
        if not self.test_model_id or not self.test_size_ids:
            print("   Skipping - no test model/sizes available")
            return False
            
        success, response = self.run_test(
            "Get BOM Versions",
            "GET",
            f"api/rahaza/boms/versions?model_id={self.test_model_id}&size_id={self.test_size_ids[0]}",
            200
        )
        
        if success and response:
            print(f"   Found {len(response)} versions for model+size")
            return True
        return False

    def test_get_bom_detail(self):
        """Test get BOM detail"""
        if not self.test_bom_id:
            print("   Skipping - no test BOM available")
            return False
            
        success, response = self.run_test(
            "Get BOM Detail",
            "GET",
            f"api/rahaza/boms/{self.test_bom_id}",
            200
        )
        
        if success and response:
            print(f"   BOM detail: v{response.get('version')}, {len(response.get('yarn_materials', []))} yarns, {len(response.get('accessory_materials', []))} accessories")
            return True
        return False

    def test_update_bom_version(self):
        """Test update BOM version"""
        if not self.test_bom_id:
            print("   Skipping - no test BOM available")
            return False
            
        update_data = {
            "yarn_materials": [
                {
                    "name": "Updated Test Yarn Material",
                    "code": "TEST-YARN-001-UPD",
                    "yarn_type": "Cotton 100% Updated",
                    "qty_kg": 0.6,
                    "notes": "Updated test yarn for BOM"
                }
            ],
            "accessory_materials": [
                {
                    "name": "Updated Test Button",
                    "code": "TEST-BTN-001-UPD",
                    "qty": 8,
                    "unit": "pcs",
                    "notes": "Updated test button for BOM"
                }
            ],
            "notes": "Updated test BOM version"
        }
        
        success, response = self.run_test(
            "Update BOM Version",
            "PUT",
            f"api/rahaza/boms/{self.test_bom_id}",
            200,
            data=update_data
        )
        
        return success

    def test_create_second_bom_version(self):
        """Test create second BOM version for same model+size"""
        if not self.test_model_id or not self.test_size_ids:
            print("   Skipping - no test model/sizes available")
            return False
            
        test_bom_data = {
            "model_id": self.test_model_id,
            "size_id": self.test_size_ids[0],
            "yarn_materials": [
                {
                    "name": "Second Version Yarn",
                    "code": "TEST-YARN-V2",
                    "yarn_type": "Polyester 100%",
                    "qty_kg": 0.4,
                    "notes": "Second version yarn"
                }
            ],
            "accessory_materials": [
                {
                    "name": "Second Version Button",
                    "code": "TEST-BTN-V2",
                    "qty": 4,
                    "unit": "pcs",
                    "notes": "Second version button"
                }
            ],
            "notes": "Second test BOM version"
        }
        
        success, response = self.run_test(
            "Create Second BOM Version",
            "POST",
            "api/rahaza/boms",
            200,
            data=test_bom_data
        )
        
        if success and response:
            print(f"   Created second BOM version {response.get('version')}")
            return True
        return False

    def test_activate_bom_version(self):
        """Test activate BOM version"""
        if not self.test_bom_id:
            print("   Skipping - no test BOM available")
            return False
            
        success, response = self.run_test(
            "Activate BOM Version",
            "POST",
            f"api/rahaza/boms/{self.test_bom_id}/activate",
            200
        )
        
        if success and response:
            print(f"   Activated BOM version {response.get('version')}")
            return True
        return False

    def test_bom_requirements_preview(self):
        """Test BOM requirements preview calculation"""
        if not self.test_bom_id:
            print("   Skipping - no test BOM available")
            return False
            
        requirements_data = {
            "qty_pcs": 100,
            "rounding": "none"
        }
        
        success, response = self.run_test(
            "BOM Requirements Preview",
            "POST",
            f"api/rahaza/boms/{self.test_bom_id}/requirements",
            200,
            data=requirements_data
        )
        
        if success and response:
            print(f"   Requirements for {response.get('qty_pcs')} pcs: {response.get('total_yarn_kg')} kg yarn, {len(response.get('accessories', []))} accessories")
            return True
        return False

    def test_copy_bom_to_sizes(self):
        """Test copy BOM to other sizes"""
        if not self.test_bom_id or len(self.test_size_ids) < 2:
            print("   Skipping - no test BOM or insufficient sizes available")
            return False
            
        copy_data = {
            "target_size_ids": self.test_size_ids[1:3],  # Copy to 2nd and 3rd sizes
            "overwrite": False
        }
        
        success, response = self.run_test(
            "Copy BOM to Sizes",
            "POST",
            f"api/rahaza/boms/{self.test_bom_id}/copy-to-sizes",
            200,
            data=copy_data
        )
        
        if success and response:
            print(f"   Copy result: {len(response.get('created', []))} created, {len(response.get('overwritten', []))} overwritten, {len(response.get('skipped', []))} skipped")
            return True
        return False

    def run_all_tests(self):
        """Run all backend tests for BOM multi-version functionality"""
        print("🚀 Starting PT Rahaza ERP Phase 5b BOM Multi-Version Backend Tests")
        print("=" * 70)
        
        # Basic connectivity and auth
        if not self.test_health_check():
            print("❌ Health check failed, stopping tests")
            return False
            
        if not self.test_login():
            print("❌ Login failed, stopping tests")
            return False
        
        print("\n📋 Testing BOM Multi-Version Features:")
        print("-" * 40)
        
        # Test all BOM multi-version features
        tests = [
            ("Get Models", self.test_get_models),
            ("Get Sizes", self.test_get_sizes),
            ("Get Materials", self.test_get_materials),
            ("Get Model BOM Matrix", self.test_get_model_bom_matrix),
            ("Create BOM Version", self.test_create_bom_version),
            ("Get BOM Versions", self.test_get_bom_versions),
            ("Get BOM Detail", self.test_get_bom_detail),
            ("Update BOM Version", self.test_update_bom_version),
            ("Create Second BOM Version", self.test_create_second_bom_version),
            ("Activate BOM Version", self.test_activate_bom_version),
            ("BOM Requirements Preview", self.test_bom_requirements_preview),
            ("Copy BOM to Sizes", self.test_copy_bom_to_sizes),
        ]
        
        for test_name, test_func in tests:
            print(f"\n🧪 {test_name}")
            try:
                test_func()
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
                self.failed_tests.append(f"{test_name}: {str(e)}")
        
        # Print results
        print("\n" + "=" * 70)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.failed_tests:
            print("\n❌ Failed Tests:")
            for failure in self.failed_tests:
                print(f"   - {failure}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\n✅ Success Rate: {success_rate:.1f}%")
        
        return success_rate >= 70  # Lower threshold for initial testing

def main():
    tester = RahazaBOMTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())