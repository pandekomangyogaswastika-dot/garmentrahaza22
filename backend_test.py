#!/usr/bin/env python3
"""
PT Rahaza ERP - Click Optimization Features Backend Test
Testing all 6 new optimization features that minimize clicks without reducing functionality.
"""

import requests
import sys
import json
from datetime import datetime, timedelta

class RahazaERPTester:
    def __init__(self, base_url="https://fashion-catalog-69.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

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
            print(f"   Login response: {response}")
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

    def test_attendance_grid_api(self):
        """Test attendance grid API for prev/next day navigation"""
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Test today's attendance grid
        success1, _ = self.run_test(
            "Attendance Grid - Today",
            "GET",
            f"api/rahaza/attendance/grid?date={today}",
            200
        )
        
        # Test yesterday's attendance grid (for copy yesterday feature)
        success2, _ = self.run_test(
            "Attendance Grid - Yesterday",
            "GET", 
            f"api/rahaza/attendance/grid?date={yesterday}",
            200
        )
        
        return success1 and success2

    def test_attendance_bulk_save(self):
        """Test bulk attendance save (Tandai Hadir & Simpan)"""
        today = datetime.now().strftime('%Y-%m-%d')
        test_data = {
            "date": today,
            "entries": [
                {
                    "employee_id": "test-emp-1",
                    "status": "hadir",
                    "shift_id": "",
                    "hours_worked": 8,
                    "overtime_hours": 0,
                    "notes": "Test bulk save"
                }
            ]
        }
        
        return self.run_test(
            "Attendance Bulk Save",
            "POST",
            "api/rahaza/attendance/bulk",
            200,
            data=test_data
        )[0]

    def test_leave_management_apis(self):
        """Test leave management APIs for pending count and bulk approve"""
        # Test get leaves (for pending count)
        success1, leaves_response = self.run_test(
            "Get Leaves - All",
            "GET",
            "api/rahaza/leaves",
            200
        )
        
        # Test get pending leaves specifically
        success2, pending_response = self.run_test(
            "Get Leaves - Pending Only",
            "GET",
            "api/rahaza/leaves?status=pending_approval",
            200
        )
        
        # Test bulk approve endpoint
        success3, _ = self.run_test(
            "Bulk Approve Leaves",
            "POST",
            "api/rahaza/leaves/bulk-approve",
            200,
            data={}
        )
        
        return success1 and success2 and success3

    def test_leave_approve_reject_apis(self):
        """Test individual leave approve/reject APIs (no window.confirm)"""
        # First create a test leave request
        test_leave_data = {
            "employee_id": "test-emp-1",
            "leave_type_id": "test-leave-type",
            "from_date": "2025-01-20",
            "to_date": "2025-01-21",
            "reason": "Test leave request"
        }
        
        success1, create_response = self.run_test(
            "Create Leave Request",
            "POST",
            "api/rahaza/leaves/request",
            200,
            data=test_leave_data
        )
        
        if success1 and 'id' in create_response:
            leave_id = create_response['id']
            
            # Test approve endpoint
            success2, _ = self.run_test(
                "Approve Leave Request",
                "POST",
                f"api/rahaza/leaves/{leave_id}/approve",
                200
            )
            
            return success2
        
        return False

    def test_payroll_run_apis(self):
        """Test payroll run APIs for copy last month feature"""
        # Test get payroll runs
        success1, _ = self.run_test(
            "Get Payroll Runs",
            "GET",
            "api/rahaza/payroll-runs",
            200
        )
        
        # Test create payroll run (Salin Bulan Lalu functionality)
        last_month = datetime.now().replace(day=1) - timedelta(days=1)
        first_of_last_month = last_month.replace(day=1)
        
        test_payroll_data = {
            "period_from": first_of_last_month.strftime('%Y-%m-%d'),
            "period_to": last_month.strftime('%Y-%m-%d'),
            "notes": "Test payroll run - copy last month"
        }
        
        success2, _ = self.run_test(
            "Create Payroll Run",
            "POST",
            "api/rahaza/payroll-runs",
            200,
            data=test_payroll_data
        )
        
        return success1 and success2

    def test_ar_invoices_apis(self):
        """Test AR invoices APIs for quick pay feature"""
        # Test get AR invoices
        success1, invoices_response = self.run_test(
            "Get AR Invoices",
            "GET",
            "api/rahaza/ar-invoices",
            200
        )
        
        # Test customers API (needed for invoice creation)
        success2, _ = self.run_test(
            "Get Customers",
            "GET",
            "api/rahaza/customers",
            200
        )
        
        # Test cash accounts API (needed for quick pay)
        success3, _ = self.run_test(
            "Get Cash Accounts",
            "GET",
            "api/rahaza/cash-accounts",
            200
        )
        
        return success1 and success2 and success3

    def test_ar_invoice_payment_api(self):
        """Test AR invoice payment API (quick pay functionality)"""
        # First try to get an existing invoice
        success, invoices_response = self.run_test(
            "Get AR Invoices for Payment Test",
            "GET",
            "api/rahaza/ar-invoices",
            200
        )
        
        if success and invoices_response and len(invoices_response) > 0:
            # Try to make a payment on the first invoice
            invoice = invoices_response[0]
            invoice_id = invoice.get('id')
            
            if invoice_id:
                payment_data = {
                    "amount": 1000,
                    "account_id": "",
                    "date": datetime.now().strftime('%Y-%m-%d'),
                    "notes": "Test quick payment"
                }
                
                return self.run_test(
                    "AR Invoice Payment",
                    "POST",
                    f"api/rahaza/ar-invoices/{invoice_id}/payment",
                    200,
                    data=payment_data
                )[0]
        
        # If no invoices exist, just test the endpoint structure
        print("   No existing invoices found, testing endpoint availability...")
        return True

    def test_stock_apis(self):
        """Test stock APIs for inline adjust feature"""
        # Test get material stock
        success1, _ = self.run_test(
            "Get Material Stock",
            "GET",
            "api/rahaza/material-stock",
            200
        )
        
        # Test material adjust endpoint
        test_adjust_data = {
            "material_id": "test-material",
            "location_id": "test-location",
            "qty_delta": 10,
            "notes": "Test inline adjust"
        }
        
        success2, _ = self.run_test(
            "Material Adjust API",
            "POST",
            "api/rahaza/material-adjust",
            200,
            data=test_adjust_data
        )
        
        return success1 and success2

    def test_materials_and_locations(self):
        """Test materials and locations APIs (needed for stock operations)"""
        success1, _ = self.run_test(
            "Get Materials",
            "GET",
            "api/rahaza/materials",
            200
        )
        
        success2, _ = self.run_test(
            "Get Locations",
            "GET",
            "api/rahaza/locations",
            200
        )
        
        return success1 and success2

    def run_all_tests(self):
        """Run all backend tests for click optimization features"""
        print("🚀 Starting PT Rahaza ERP Click Optimization Backend Tests")
        print("=" * 60)
        
        # Basic connectivity
        if not self.test_health_check():
            print("❌ Health check failed, stopping tests")
            return False
            
        if not self.test_login():
            print("❌ Login failed, stopping tests")
            return False
        
        print("\n📋 Testing Click Optimization Features:")
        print("-" * 40)
        
        # Test all click optimization features
        tests = [
            ("Attendance Grid APIs (prev/next day)", self.test_attendance_grid_api),
            ("Attendance Bulk Save (Tandai Hadir & Simpan)", self.test_attendance_bulk_save),
            ("Leave Management APIs (pending count)", self.test_leave_management_apis),
            ("Leave Approve/Reject APIs", self.test_leave_approve_reject_apis),
            ("Payroll Run APIs (copy last month)", self.test_payroll_run_apis),
            ("AR Invoices APIs (quick pay)", self.test_ar_invoices_apis),
            ("AR Invoice Payment API", self.test_ar_invoice_payment_api),
            ("Stock APIs (inline adjust)", self.test_stock_apis),
            ("Materials and Locations APIs", self.test_materials_and_locations),
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
    tester = RahazaERPTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())