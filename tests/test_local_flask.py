#!/usr/bin/env python3
"""
Local Flask Application Testing Script

This script provides an easy way to test the Flask application locally
with different configurations and port options.

Usage:
    python3 test_local_flask.py [--port PORT] [--debug] [--production]
"""

import argparse
import os
import sys

# Add the root directory to Python path so we can import from src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils import load_game_data

def test_data_availability():
    """Test if the required data is available"""
    print("Testing data availability...")
    
    try:
        data = load_game_data()
        if data.empty:
            print("❌ No data available - please ensure full-game-stats.csv exists")
            return False
        else:
            print(f"✅ Data loaded successfully: {data.shape[0]} games, {data.shape[1]} columns")
            
            # Show available divisions
            if 'GameDivisionDisplay' in data.columns:
                divisions = data['GameDivisionDisplay'].unique()
                print(f"📊 Available divisions: {len(divisions)}")
                for div in divisions[:5]:  # Show first 5 divisions
                    print(f"   - {div}")
                if len(divisions) > 5:
                    print(f"   ... and {len(divisions) - 5} more")
            return True
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return False

def test_flask_import():
    """Test if Flask app can be imported"""
    print("\nTesting Flask application import...")
    
    try:
        from src.app import app
        print("✅ Flask app imported successfully")
        
        # Test routes
        with app.test_client() as client:
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Home route (/) working")
            else:
                print(f"❌ Home route returned status code: {response.status_code}")
                
            response = client.get('/statistics')
            if response.status_code == 200:
                print("✅ Statistics route (/statistics) working")
            else:
                print(f"❌ Statistics route returned status code: {response.status_code}")
            
            response = client.get('/player-detail')
            if response.status_code == 200:
                print("✅ Player detail route (/player-detail) working")
            else:
                print(f"❌ Player detail route returned status code: {response.status_code}")
                
        return True
    except Exception as e:
        print(f"❌ Error importing Flask app: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_flask_server(port=5000, debug=True, production=False):
    """Run the Flask development server"""
    
    if not test_data_availability():
        print("\n⚠️  Warning: Continuing with limited functionality due to data issues")
    
    if not test_flask_import():
        print("\n❌ Cannot start server due to import errors")
        return False
    
    print(f"\n🚀 Starting Flask server...")
    print(f"   Port: {port}")
    print(f"   Debug mode: {debug and not production}")
    print(f"   Production mode: {production}")
    print(f"   Local URL: http://localhost:{port}")
    print(f"   Local URL: http://127.0.0.1:{port}")
    print("\n💡 Press Ctrl+C to stop the server")
    
    try:
        from src.app import app
        
        if production:
            # Use gunicorn for production-like testing
            import subprocess
            cmd = [
                'gunicorn',
                '--bind', f'127.0.0.1:{port}',
                '--workers', '1',
                '--timeout', '30',
                'app:app'
            ]
            print(f"🔧 Running with gunicorn: {' '.join(cmd)}")
            subprocess.run(cmd)
        else:
            # Use Flask development server
            app.run(debug=debug, port=port, host='0.0.0.0')
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Test Flask application locally')
    parser.add_argument('--port', '-p', type=int, default=5000,
                        help='Port to run the server on (default: 5000)')
    parser.add_argument('--debug', '-d', action='store_true', default=True,
                        help='Run in debug mode (default: True)')
    parser.add_argument('--production', '-prod', action='store_true',
                        help='Run in production mode using gunicorn')
    parser.add_argument('--test-only', '-t', action='store_true',
                        help='Only run tests, don\'t start server')
    
    args = parser.parse_args()
    
    print("🏀 FLBB Statistics - Local Flask Application Tester")
    print("=" * 50)
    
    # Run tests
    data_ok = test_data_availability()
    flask_ok = test_flask_import()
    
    if args.test_only:
        if data_ok and flask_ok:
            print("\n✅ All tests passed! Ready to deploy.")
            return 0
        else:
            print("\n❌ Some tests failed. Please fix issues before deployment.")
            return 1
    
    if not flask_ok:
        print("\n❌ Cannot start server due to critical errors")
        return 1
        
    # Start server
    success = run_flask_server(
        port=args.port,
        debug=args.debug and not args.production,
        production=args.production
    )
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())