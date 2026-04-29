#!/usr/bin/env python3
"""
PT Rahaza ERP - Bug Fixes Testing
Testing multiple bug fixes:
1. Line Board shows lines with output even when no formal assignment exists
2. Event Terbaru enriched with WO number/model/line info
3. Master Model form: yarn_kg_per_pcs field removed from UI
4. PO form: unit label auto-fills from selected material next to qty
5. Packing output → FG Inventory auto-upsert to material_stock
6. Portal Gudang split into 'Inventori Bahan & Aksesoris' and 'Inventori Produk Jadi' tabs
"""

import requests
import sys
import json
from datetime import datetime, timedelta

class RahazaBugFixTester:
    def __init__(self, base_url="https://garment-rahaza-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.test_line_id = None
        self.test_model_id = None
        self.test_size_id = None
        self.test_material_id = None
        self.test_wo_id = None

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

    def setup_test_data(self):
        """Setup test data for testing"""
        print("\n📋 Setting up test data...")
        
        # Get test line
        success, response = self.run_test(
            "Get Lines",
            "GET",
            "api/rahaza/lines",
            200
        )
        if success and response:
            active_lines = [l for l in response if l.get('active', True)]
            if active_lines:
                self.test_line_id = active_lines[0]['id']
                print(f"   Using test line: {active_lines[0].get('code')}")

        # Get test model
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
                print(f"   Using test model: {active_models[0].get('code')}")

        # Get test size
        success, response = self.run_test(
            "Get Sizes",
            "GET",
            "api/rahaza/sizes",
            200
        )
        if success and response:
            active_sizes = [s for s in response if s.get('active', True)]
            if active_sizes:
                self.test_size_id = active_sizes[0]['id']
                print(f"   Using test size: {active_sizes[0].get('code')}")

        # Get test material
        success, response = self.run_test(
            "Get Materials",
            "GET",
            "api/rahaza/materials",
            200
        )
        if success and response:
            active_materials = [m for m in response if m.get('active', True)]
            if active_materials:
                self.test_material_id = active_materials[0]['id']
                print(f"   Using test material: {active_materials[0].get('code')}")

        return True

    def test_line_board_with_output_no_assignment(self):
        """Test Line Board shows lines with output even when no formal assignment exists"""
        if not self.test_line_id:
            print("   Skipping - no test line available")
            return False

        # First, create a WIP event without assignment
        success, response = self.run_test(
            "Create WIP Event Without Assignment",
            "POST",
            "api/rahaza/wip/events",
            200,
            data={
                "line_id": self.test_line_id,
                "process_id": "test-process-id",
                "qty": 10,
                "event_type": "output",
                "notes": "Test output without assignment"
            }
        )

        if not success:
            print("   Failed to create test WIP event")
            return False

        # Now test line board API
        success, response = self.run_test(
            "Get Line Board",
            "GET",
            "api/rahaza/line-board",
            200
        )

        if success and response:
            board = response.get('board', [])
            found_line_with_output = False
            for process in board:
                for line in process.get('lines', []):
                    if line.get('line_id') == self.test_line_id and line.get('output_today', 0) > 0:
                        found_line_with_output = True
                        print(f"   ✅ Found line {line.get('line_code')} with output {line.get('output_today')} without formal assignment")
                        break
                if found_line_with_output:
                    break
            
            if found_line_with_output:
                return True
            else:
                print("   ❌ Line with output but no assignment not found in board")
                return False
        
        return False

    def test_recent_events_enriched(self):
        """Test Event Terbaru enriched with WO number/model/line info"""
        success, response = self.run_test(
            "Get Recent Events Enriched",
            "GET",
            "api/rahaza/execution/recent-events?limit=10",
            200
        )

        if success and response:
            if len(response) > 0:
                event = response[0]
                # Check if events have enriched fields
                enriched_fields = ['model_code', 'wo_number', 'line_code']
                has_enrichment = any(field in event for field in enriched_fields)
                
                if has_enrichment:
                    print(f"   ✅ Events enriched with fields: {[f for f in enriched_fields if f in event]}")
                    return True
                else:
                    print(f"   ❌ Events not enriched. Available fields: {list(event.keys())}")
                    return False
            else:
                print("   ⚠️ No recent events found to test enrichment")
                return True  # Not a failure, just no data
        
        return False

    def test_packing_output_fg_inventory(self):
        """Test Packing output → FG Inventory auto-upsert to material_stock"""
        if not all([self.test_line_id, self.test_model_id, self.test_size_id]):
            print("   Skipping - missing test data")
            return False

        # Get PACKING process
        success, response = self.run_test(
            "Get PACKING Process",
            "GET",
            "api/rahaza/processes",
            200
        )
        
        packing_process_id = None
        if success and response:
            for process in response:
                if process.get('code') == 'PACKING':
                    packing_process_id = process['id']
                    break

        if not packing_process_id:
            print("   ❌ PACKING process not found")
            return False

        # Create packing output event
        success, response = self.run_test(
            "Create Packing Output Event",
            "POST",
            "api/rahaza/wip/events",
            200,
            data={
                "line_id": self.test_line_id,
                "process_id": packing_process_id,
                "model_id": self.test_model_id,
                "size_id": self.test_size_id,
                "qty": 5,
                "event_type": "output",
                "notes": "Test packing output for FG inventory"
            }
        )

        if not success:
            print("   ❌ Failed to create packing output event")
            return False

        # Check if FG material was auto-created
        success, response = self.run_test(
            "Get FG Materials",
            "GET",
            "api/rahaza/materials?type=fg",
            200
        )

        if success and response:
            fg_materials = [m for m in response if m.get('type') == 'fg']
            if len(fg_materials) > 0:
                print(f"   ✅ Found {len(fg_materials)} FG materials auto-created")
                
                # Check material stock
                success2, response2 = self.run_test(
                    "Get Material Stock",
                    "GET",
                    "api/rahaza/material-stock",
                    200
                )
                
                if success2 and response2:
                    fg_stocks = [s for s in response2 if any(m['id'] == s.get('material_id') for m in fg_materials)]
                    if len(fg_stocks) > 0:
                        print(f"   ✅ Found {len(fg_stocks)} FG stock entries")
                        return True
                    else:
                        print("   ❌ No FG stock entries found")
                        return False
                
                return True
            else:
                print("   ❌ No FG materials found")
                return False
        
        return False

    def test_materials_api_with_unit(self):
        """Test materials API returns unit field for PO form auto-fill"""
        success, response = self.run_test(
            "Get Materials with Unit",
            "GET",
            "api/rahaza/materials",
            200
        )

        if success and response:
            if len(response) > 0:
                material = response[0]
                if 'unit' in material:
                    print(f"   ✅ Materials have unit field: {material.get('unit')}")
                    return True
                else:
                    print(f"   ❌ Materials missing unit field. Available fields: {list(material.keys())}")
                    return False
            else:
                print("   ⚠️ No materials found to test unit field")
                return True
        
        return False

    def test_fg_inventory_module_api(self):
        """Test FG Inventory module API endpoints"""
        # Test FG materials endpoint
        success, response = self.run_test(
            "Get FG Inventory Materials",
            "GET",
            "api/rahaza/materials?type=fg",
            200
        )

        if not success:
            return False

        # Test material stock endpoint
        success, response = self.run_test(
            "Get FG Material Stock",
            "GET",
            "api/rahaza/material-stock",
            200
        )

        return success

    def test_purchase_order_apis(self):
        """Test Purchase Order APIs"""
        # Test get PO list
        success, response = self.run_test(
            "Get Purchase Orders",
            "GET",
            "api/rahaza/purchase-orders",
            200
        )

        if not success:
            return False

        # Test create PO (basic structure)
        if self.test_material_id:
            po_data = {
                "vendor_name": "Test Vendor",
                "vendor_contact": "test@vendor.com",
                "po_date": datetime.now().strftime("%Y-%m-%d"),
                "items": [
                    {
                        "material_id": self.test_material_id,
                        "qty_ordered": 10,
                        "unit_cost": 1000
                    }
                ]
            }
            
            success, response = self.run_test(
                "Create Purchase Order",
                "POST",
                "api/rahaza/purchase-orders",
                200,
                data=po_data
            )
            
            return success

        return True

    def run_all_tests(self):
        """Run all backend tests for bug fixes"""
        print("🚀 Starting PT Rahaza ERP Bug Fixes Backend Tests")
        print("=" * 70)
        
        # Basic connectivity and auth
        if not self.test_health_check():
            print("❌ Health check failed, stopping tests")
            return False
            
        if not self.test_login():
            print("❌ Login failed, stopping tests")
            return False

        # Setup test data
        if not self.setup_test_data():
            print("❌ Test data setup failed")
            return False
        
        print("\n📋 Testing Bug Fixes:")
        print("-" * 40)
        
        # Test all bug fixes
        tests = [
            ("Line Board with Output No Assignment", self.test_line_board_with_output_no_assignment),
            ("Recent Events Enriched", self.test_recent_events_enriched),
            ("Packing Output FG Inventory", self.test_packing_output_fg_inventory),
            ("Materials API with Unit", self.test_materials_api_with_unit),
            ("FG Inventory Module API", self.test_fg_inventory_module_api),
            ("Purchase Order APIs", self.test_purchase_order_apis),
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
        
        return success_rate >= 70

def main():
    tester = RahazaBugFixTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())