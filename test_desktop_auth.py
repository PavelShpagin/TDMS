#!/usr/bin/env python
"""Test script to verify desktop OAuth configuration."""

import json
from pathlib import Path
import requests
import time

def test_oauth_config():
    """Test if OAuth client secrets are available."""
    print("=" * 60)
    print("Testing OAuth Configuration")
    print("=" * 60)
    
    secrets_dir = Path("secrets")
    if not secrets_dir.exists():
        print("[FAIL] ERROR: secrets/ directory not found")
        return False
    
    client_secret_files = list(secrets_dir.glob("client_secret_*.json"))
    if not client_secret_files:
        print("[FAIL] ERROR: No client_secret files found in secrets/")
        return False
    
    print(f"[OK] Found {len(client_secret_files)} client_secret file(s)")
    
    # Load first client secret file
    with open(client_secret_files[0]) as f:
        data = json.load(f)
    
    # Check if it has installed or web config
    if "installed" in data:
        client_id = data["installed"].get("client_id", "")
        client_secret = data["installed"].get("client_secret", "")
        print(f"[OK] Found 'installed' OAuth config")
    elif "web" in data:
        client_id = data["web"].get("client_id", "")
        client_secret = data["web"].get("client_secret", "")
        print(f"[OK] Found 'web' OAuth config")
    else:
        print("[FAIL] ERROR: client_secret file has invalid format")
        return False
    
    print(f"  Client ID: {client_id[:20]}...")
    print(f"  Client Secret: {'***' if client_secret else 'MISSING'}")
    
    if not client_id or not client_secret:
        print("[FAIL] ERROR: Client ID or Secret is empty")
        return False
    
    print("\n[OK] OAuth configuration is valid")
    return True


def test_desktop_app_url():
    """Test if desktop app serves the page correctly."""
    print("\n" + "=" * 60)
    print("Testing Desktop App URL")
    print("=" * 60)
    
    # Try different ports (desktop app uses 8001-8099)
    for port in range(8001, 8010):
        try:
            url = f"http://127.0.0.1:{port}?desktop=true"
            print(f"Trying {url}...")
            response = requests.get(url, timeout=2)
            
            if response.status_code == 200:
                print(f"[OK] Desktop app is running on port {port}")
                
                # Check if page contains expected content
                html = response.text
                
                if "Table Database" in html:
                    print("  [OK] Page title found")
                else:
                    print("  [FAIL] Page title not found")
                
                if "google_client_id" in html or "googleAccessToken" in html:
                    print("  [OK] Google OAuth variables present")
                else:
                    print("  [WARN] Google OAuth variables not found in HTML")
                
                # Check if is_desktop flag is set
                if "const isDesktop = true" in html or "isDesktop = true" in html:
                    print("  [OK] Desktop mode detected in template")
                else:
                    print("  [WARN] Desktop mode flag not found (might use {{ is_desktop|lower }})")
                
                return True
                
        except requests.exceptions.ConnectionError:
            pass
        except requests.exceptions.Timeout:
            pass
    
    print("[FAIL] ERROR: Desktop app is not running")
    print("   Please start it with: python -m src.desktop.simple_app")
    return False


def test_oauth_status_endpoint():
    """Test OAuth status endpoint."""
    print("\n" + "=" * 60)
    print("Testing OAuth Status Endpoint")
    print("=" * 60)
    
    for port in range(8001, 8010):
        try:
            url = f"http://127.0.0.1:{port}/api/google/oauth/status"
            response = requests.get(url, timeout=2)
            
            if response.status_code == 200:
                data = response.json()
                print(f"[OK] OAuth status endpoint responding on port {port}")
                print(f"  Configured: {data.get('configured', False)}")
                print(f"  Authenticated: {data.get('authenticated', False)}")
                return True
                
        except requests.exceptions.ConnectionError:
            pass
        except requests.exceptions.Timeout:
            pass
    
    print("[WARN] OAuth status endpoint not reachable")
    return False


def test_databases_list():
    """Test if databases endpoint works."""
    print("\n" + "=" * 60)
    print("Testing Databases List")
    print("=" * 60)
    
    for port in range(8001, 8010):
        try:
            url = f"http://127.0.0.1:{port}/databases"
            response = requests.get(url, timeout=2)
            
            if response.status_code == 200:
                data = response.json()
                print(f"[OK] Databases endpoint responding on port {port}")
                print(f"  Active database: {data.get('active', 'N/A')}")
                print(f"  Available databases: {data.get('databases', [])}")
                
                if not data.get('databases'):
                    print("\n  [WARN] No databases found. This is normal for fresh install.")
                    print("    Create one using the UI or import from Drive.")
                
                return True
                
        except requests.exceptions.ConnectionError:
            pass
        except requests.exceptions.Timeout:
            pass
    
    print("[WARN] Databases endpoint not reachable")
    return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("DESKTOP AUTH DIAGNOSTIC TOOL")
    print("=" * 60 + "\n")
    
    results = []
    
    # Test 1: OAuth configuration files
    results.append(("OAuth Config", test_oauth_config()))
    
    # Test 2: Desktop app URL
    results.append(("Desktop App", test_desktop_app_url()))
    
    # Test 3: OAuth status endpoint
    results.append(("OAuth Status API", test_oauth_status_endpoint()))
    
    # Test 4: Databases list
    results.append(("Databases API", test_databases_list()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status:10} {name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n[OK] All tests passed!")
        print("\nNext steps:")
        print("1. Open the desktop app")
        print("2. Click 'Load Drive' or 'Sync Drive' on a database")
        print("3. Complete OAuth authorization in browser")
        print("4. Verify token is saved and operation succeeds")
    else:
        print("\n[FAIL] Some tests failed. Please review errors above.")
    
    print("\n" + "=" * 60 + "\n")
    return all_passed


if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        exit(1)

