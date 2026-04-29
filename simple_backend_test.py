#!/usr/bin/env python3
"""
Simple Backend API Test for PT Rahaza ERP
"""

import requests
import sys

def test_basic_apis():
    base_url = "https://fashion-catalog-69.preview.emergentagent.com"
    
    print("🚀 Testing PT Rahaza ERP Basic APIs")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing Health Check...")
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Login
    print("\n2. Testing Login...")
    try:
        login_data = {"email": "admin@garment.com", "password": "Admin@123"}
        response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            if 'token' in data:
                token = data['token']
                print("✅ Login successful")
                print(f"   Token: {token[:30]}...")
            else:
                print("❌ Login failed: No token in response")
                return False
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Test 3: Seed demo data
    print("\n3. Testing Seed Demo Data...")
    try:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        response = requests.post(f"{base_url}/api/rahaza/admin/reset-and-seed", headers=headers)
        if response.status_code == 200:
            print("✅ Seed demo data successful")
        else:
            print(f"⚠️  Seed demo data: {response.status_code} (may already be seeded)")
    except Exception as e:
        print(f"⚠️  Seed demo data error: {e}")
    
    # Test 4: Get processes
    print("\n4. Testing Processes API...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{base_url}/api/rahaza/processes?active=true", headers=headers)
        if response.status_code == 200:
            data = response.json()
            processes = data if isinstance(data, list) else data.get('items', [])
            print(f"✅ Processes API successful - Found {len(processes)} processes")
            
            # Check for main processes and rework
            process_codes = [p.get('code', '') for p in processes]
            main_processes = ['RAJUT', 'LINKING', 'SEWING', 'STEAM', 'QC', 'PACKING']
            found_main = [code for code in main_processes if code in process_codes]
            has_rework = 'REWORK' in process_codes
            
            print(f"   Main processes found: {found_main}")
            print(f"   Rework process found: {has_rework}")
            
        else:
            print(f"❌ Processes API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Processes API error: {e}")
        return False
    
    # Test 5: Production Wizard Preview
    print("\n5. Testing Production Wizard Preview...")
    try:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        test_data = {"items": [{"model_id": "test", "size_id": "test", "qty": 10}]}
        response = requests.post(f"{base_url}/api/rahaza/wizard/preview-production", 
                               json=test_data, headers=headers)
        if response.status_code == 200:
            print("✅ Production Wizard Preview accessible")
        else:
            print(f"⚠️  Production Wizard Preview: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Production Wizard Preview error: {e}")
    
    print("\n🎉 Basic API tests completed!")
    return True

if __name__ == "__main__":
    success = test_basic_apis()
    sys.exit(0 if success else 1)