#!/usr/bin/env python3
"""
PT Rahaza ERP - PDF Export Features Backend Test
Testing PDF export functionality for payslips and payroll runs.
"""

import requests
import sys
import json
from datetime import datetime, timedelta

class RahazaPDFTester:
    def __init__(self, base_url="https://fashion-catalog-69.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.payroll_run_id = None
        self.payslip_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, check_content_type=None, min_content_size=None):
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
            
            # Additional checks for PDF endpoints
            if success and check_content_type:
                content_type = response.headers.get('Content-Type', '')
                if check_content_type not in content_type:
                    print(f"❌ Failed - Expected Content-Type: {check_content_type}, got: {content_type}")
                    success = False
                else:
                    print(f"✅ Content-Type check passed: {content_type}")
            
            if success and min_content_size:
                content_length = len(response.content)
                if content_length < min_content_size:
                    print(f"❌ Failed - Expected min size: {min_content_size}KB, got: {content_length/1024:.1f}KB")
                    success = False
                else:
                    print(f"✅ Content size check passed: {content_length/1024:.1f}KB")
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    if 'application/json' in response.headers.get('Content-Type', ''):
                        return True, response.json()
                    else:
                        return True, response.content
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
            print(f"   Login response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
            if 'access_token' in response:
                self.token = response['access_token']
                print(f"   Token obtained: {self.token[:20]}...")
                return True
            elif 'token' in response:
                self.token = response['token']
                print(f"   Token obtained: {self.token[:20]}...")
                return True
        return False

    def test_payslips_list(self):
        """Test GET /api/rahaza/payslips - returns list of payslips"""
        success, response = self.run_test(
            "Get Payslips List",
            "GET",
            "api/rahaza/payslips",
            200
        )
        
        if success and isinstance(response, list) and len(response) > 0:
            # Store first payslip ID for PDF test
            self.payslip_id = response[0].get('id')
            print(f"   Found {len(response)} payslips, using ID: {self.payslip_id}")
        elif success and isinstance(response, list):
            print(f"   Found {len(response)} payslips (empty list)")
        
        return success

    def test_payroll_runs_list(self):
        """Test GET /api/rahaza/payroll-runs - returns list of payroll runs"""
        success, response = self.run_test(
            "Get Payroll Runs List",
            "GET",
            "api/rahaza/payroll-runs",
            200
        )
        
        if success and isinstance(response, list) and len(response) > 0:
            # Store first payroll run ID for PDF test
            self.payroll_run_id = response[0].get('id')
            print(f"   Found {len(response)} payroll runs, using ID: {self.payroll_run_id}")
        elif success and isinstance(response, list):
            print(f"   Found {len(response)} payroll runs (empty list)")
        
        return success

    def test_single_payslip_pdf(self):
        """Test GET /api/rahaza/payslips/{id}/pdf - returns valid PDF binary"""
        if not self.payslip_id:
            print("❌ No payslip ID available for PDF test")
            self.failed_tests.append("Single Payslip PDF: No payslip ID available")
            return False
        
        return self.run_test(
            "Single Payslip PDF Download",
            "GET",
            f"api/rahaza/payslips/{self.payslip_id}/pdf",
            200,
            check_content_type="application/pdf",
            min_content_size=2048  # 2KB minimum
        )[0]

    def test_bulk_payroll_run_pdf(self):
        """Test GET /api/rahaza/payroll-runs/{run_id}/pdf - returns valid PDF binary for all slips"""
        if not self.payroll_run_id:
            print("❌ No payroll run ID available for PDF test")
            self.failed_tests.append("Bulk Payroll Run PDF: No payroll run ID available")
            return False
        
        return self.run_test(
            "Bulk Payroll Run PDF Download",
            "GET",
            f"api/rahaza/payroll-runs/{self.payroll_run_id}/pdf",
            200,
            check_content_type="application/pdf",
            min_content_size=10240  # 10KB minimum for multiple pages
        )[0]

    def test_health_check(self):
        """Test basic health check"""
        return self.run_test("Health Check", "GET", "api/health", 200)[0]

    def run_all_tests(self):
        """Run all PDF export backend tests"""
        print("🚀 Starting PT Rahaza ERP PDF Export Backend Tests")
        print("=" * 60)
        
        # Basic connectivity
        if not self.test_health_check():
            print("❌ Health check failed, stopping tests")
            return False
            
        if not self.test_login():
            print("❌ Login failed, stopping tests")
            return False
        
        print("\n📋 Testing PDF Export Features:")
        print("-" * 40)
        
        # Test all PDF export features
        tests = [
            ("Payslips List API", self.test_payslips_list),
            ("Payroll Runs List API", self.test_payroll_runs_list),
            ("Single Payslip PDF Download", self.test_single_payslip_pdf),
            ("Bulk Payroll Run PDF Download", self.test_bulk_payroll_run_pdf),
        ]
        
        for test_name, test_func in tests:
            print(f"\n🧪 {test_name}")
            try:
                test_func()
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
                self.failed_tests.append(f"{test_name}: {str(e)}")
        
        # Print results
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.failed_tests:
            print("\n❌ Failed Tests:")
            for failure in self.failed_tests:
                print(f"   - {failure}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\n✅ Success Rate: {success_rate:.1f}%")
        
        return success_rate >= 80

def main():
    tester = RahazaPDFTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())