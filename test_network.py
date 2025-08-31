#!/usr/bin/env python3
"""
Simple network connectivity test for Ollama Cloud API.
"""

import requests
import socket

def test_dns_resolution():
    """Test DNS resolution for api.ollama.ai"""
    print("🔍 Testing DNS Resolution")
    print("=" * 30)
    
    try:
        ip = socket.gethostbyname('api.ollama.ai')
        print(f"✅ DNS Resolution successful: api.ollama.ai -> {ip}")
        return True
    except socket.gaierror as e:
        print(f"❌ DNS Resolution failed: {e}")
        return False

def test_basic_connectivity():
    """Test basic HTTP connectivity"""
    print("\n🌐 Testing Basic Connectivity")
    print("=" * 30)
    
    try:
        response = requests.get('https://api.ollama.ai', timeout=10)
        print(f"✅ Basic connectivity successful: Status {response.status_code}")
        return True
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection failed: {e}")
        return False
    except requests.exceptions.Timeout:
        print("❌ Connection timeout")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_api_endpoint():
    """Test the specific API endpoint"""
    print("\n🔧 Testing API Endpoint")
    print("=" * 30)
    
    try:
        # Test the models endpoint (should work without auth)
        response = requests.get('https://api.ollama.ai/v1/models', timeout=10)
        print(f"✅ API endpoint accessible: Status {response.status_code}")
        if response.status_code == 401:
            print("   (401 is expected - authentication required)")
        return True
    except requests.exceptions.ConnectionError as e:
        print(f"❌ API endpoint connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ API endpoint error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Network Connectivity Test for Ollama Cloud")
    print("=" * 50)
    
    success = True
    
    if not test_dns_resolution():
        success = False
    
    if not test_basic_connectivity():
        success = False
    
    if not test_api_endpoint():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Network connectivity is working!")
    else:
        print("❌ Network connectivity issues detected.")
        print("\n💡 Possible solutions:")
        print("   1. Check your internet connection")
        print("   2. Try using a VPN if behind corporate firewall")
        print("   3. Check DNS settings")
        print("   4. Verify api.ollama.ai is accessible from your network")