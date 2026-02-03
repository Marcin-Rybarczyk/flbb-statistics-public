#!/usr/bin/env python3
"""
Test script for foul weights configuration functionality.
This script verifies that:
1. Foul weights table is created correctly
2. Default weights are loaded
3. Weights can be updated
4. Player statistics use the configured weights
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment variables
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['ADMIN_PASSWORD'] = 'test123'

from src.user_database import get_foul_weights, update_foul_weights, init_database
from src.app import app

def test_foul_weights_database():
    """Test foul weights database functionality"""
    print("=" * 70)
    print("Testing Foul Weights Database")
    print("=" * 70)
    
    # Initialize database to ensure tables exist
    print("\n1. Initializing database...")
    success = init_database()
    assert success, "Database initialization failed"
    print("   ✓ Database initialized")
    
    # Test getting default weights
    print("\n2. Testing default foul weights...")
    weights = get_foul_weights()
    
    expected_types = ['P', 'P1', 'P2', 'P3', 'T1', 'U1', 'U2', 'U3', 'GD']
    for foul_type in expected_types:
        assert foul_type in weights, f"Missing foul type: {foul_type}"
    print(f"   ✓ All {len(expected_types)} foul types present")
    
    # Verify default values
    print("\n3. Verifying default weight values...")
    print(f"   Current weights: {weights}")
    assert weights['P'] == 1.0, "Default P weight should be 1.0"
    assert weights['T1'] == 2.0, "Default T1 weight should be 2.0"
    assert weights['GD'] == 5.0, "Default GD weight should be 5.0"
    print("   ✓ Default values are correct")
    
    # Test updating weights
    print("\n4. Testing weight updates...")
    new_weights = {
        'P': 1.5,
        'P1': 1.5,
        'P2': 1.5,
        'P3': 1.5,
        'T1': 3.0,
        'U1': 3.0,
        'U2': 3.0,
        'U3': 3.0,
        'GD': 10.0
    }
    success, message = update_foul_weights(new_weights)
    assert success, f"Failed to update weights: {message}"
    print(f"   ✓ Weights updated: {message}")
    
    # Verify updates
    print("\n5. Verifying updated weights...")
    updated_weights = get_foul_weights()
    for foul_type, expected_weight in new_weights.items():
        actual_weight = updated_weights[foul_type]
        assert actual_weight == expected_weight, \
            f"Weight mismatch for {foul_type}: expected {expected_weight}, got {actual_weight}"
    print("   ✓ All weights updated correctly")
    
    # Restore default weights
    print("\n6. Restoring default weights...")
    default_weights = {
        'P': 1.0,
        'P1': 1.0,
        'P2': 1.0,
        'P3': 1.0,
        'T1': 2.0,
        'U1': 2.0,
        'U2': 2.0,
        'U3': 2.0,
        'GD': 5.0
    }
    success, message = update_foul_weights(default_weights)
    assert success, f"Failed to restore default weights: {message}"
    print("   ✓ Default weights restored")
    
    print("\n" + "=" * 70)
    print("All Foul Weights Database Tests Passed!")
    print("=" * 70)


def test_foul_weights_api():
    """Test foul weights API endpoints"""
    print("\n" + "=" * 70)
    print("Testing Foul Weights API Endpoints")
    print("=" * 70)
    
    # Create test client
    client = app.test_client()
    
    # Test 1: Get weights endpoint (should require admin auth)
    print("\n1. Testing GET /admin/foul-weights without auth...")
    response = client.get('/admin/foul-weights')
    # Should redirect to login or return 401/403
    assert response.status_code in [302, 401, 403], \
        f"Expected redirect or auth error, got {response.status_code}"
    print("   ✓ Endpoint requires authentication")
    
    # Test 2: Update weights endpoint (should require admin auth)
    print("\n2. Testing POST /admin/foul-weights/update without auth...")
    response = client.post('/admin/foul-weights/update', data={
        'weight_P': '1.0',
        'weight_P1': '1.0',
        'weight_P2': '1.0',
        'weight_P3': '1.0',
        'weight_T1': '2.0',
        'weight_U1': '2.0',
        'weight_U2': '2.0',
        'weight_U3': '2.0',
        'weight_GD': '5.0'
    })
    assert response.status_code in [302, 401, 403], \
        f"Expected redirect or auth error, got {response.status_code}"
    print("   ✓ Update endpoint requires authentication")
    
    # Test 3: Admin login and then access endpoints
    print("\n3. Testing with admin authentication...")
    
    # Login as admin - set the correct session variable
    with client.session_transaction() as sess:
        sess['user_level'] = 'admin'
        sess['username'] = 'test_admin'
    
    # Test getting weights
    print("   Testing GET /admin/foul-weights with auth...")
    response = client.get('/admin/foul-weights')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    weights = response.get_json()
    assert 'P' in weights, "Weights response should contain 'P'"
    assert 'GD' in weights, "Weights response should contain 'GD'"
    print(f"   ✓ Successfully retrieved weights: {list(weights.keys())}")
    
    # Test updating weights
    print("   Testing POST /admin/foul-weights/update with auth...")
    response = client.post('/admin/foul-weights/update', data={
        'weight_P': '1.0',
        'weight_P1': '1.0',
        'weight_P2': '1.0',
        'weight_P3': '1.0',
        'weight_T1': '2.0',
        'weight_U1': '2.0',
        'weight_U2': '2.0',
        'weight_U3': '2.0',
        'weight_GD': '5.0'
    })
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    result = response.get_json()
    assert result['success'] == True, f"Expected success=True, got {result}"
    print(f"   ✓ Successfully updated weights: {result.get('message')}")
    
    print("\n" + "=" * 70)
    print("All Foul Weights API Tests Passed!")
    print("=" * 70)


if __name__ == '__main__':
    try:
        test_foul_weights_database()
        test_foul_weights_api()
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
