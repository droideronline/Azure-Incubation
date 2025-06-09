#!/usr/bin/env python3
"""
Test script to debug JWT validation issues in production
"""

import requests
import jwt
import json
import sys
import os
from datetime import datetime, timezone

# Add the backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import our auth module
try:
    from auth import get_public_keys, CLIENT_ID, TENANT_ID, JWKS_URL
    print(f"✅ Successfully imported auth module")
    print(f"CLIENT_ID: {CLIENT_ID[:8]}...")
    print(f"TENANT_ID: {TENANT_ID}")
    print(f"JWKS_URL: {JWKS_URL}")
except Exception as e:
    print(f"❌ Failed to import auth module: {e}")
    sys.exit(1)

def test_jwks_endpoint():
    """Test if we can fetch JWKS from Azure AD"""
    print("\n🔍 Testing JWKS endpoint...")
    try:
        jwks = get_public_keys()
        if jwks:
            keys_count = len(jwks.get('keys', []))
            print(f"✅ Retrieved {keys_count} public keys")
            
            # Show available key IDs
            kids = [key.get('kid') for key in jwks.get('keys', []) if key.get('kid')]
            print(f"Available key IDs: {kids[:3]}..." if len(kids) > 3 else f"Available key IDs: {kids}")
            
            return jwks
        else:
            print("❌ Failed to retrieve JWKS")
            return None
    except Exception as e:
        print(f"❌ JWKS test failed: {e}")
        return None

def test_token_decode(sample_token=None):
    """Test token decoding without verification"""
    if not sample_token:
        print("\n⚠️  No sample token provided for testing")
        return
    
    print(f"\n🔍 Testing token decode (first 20 chars): {sample_token[:20]}...")
    
    try:
        # Decode header
        header = jwt.get_unverified_header(sample_token)
        print(f"Token header: {json.dumps(header, indent=2)}")
        
        # Decode payload without verification
        payload = jwt.decode(sample_token, options={"verify_signature": False})
        
        # Show relevant fields
        relevant_fields = ['iss', 'aud', 'exp', 'name', 'preferred_username', 'email', 'sub', 'tid']
        filtered_payload = {k: v for k, v in payload.items() if k in relevant_fields}
        print(f"Token payload (filtered): {json.dumps(filtered_payload, indent=2)}")
        
        # Check expiration
        exp = payload.get('exp')
        if exp:
            exp_time = datetime.fromtimestamp(exp, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            print(f"Token expires: {exp_time}")
            print(f"Current time: {now}")
            print(f"Is expired: {exp_time < now}")
        
        return header, payload
        
    except Exception as e:
        print(f"❌ Token decode failed: {e}")
        return None, None

def test_key_matching(jwks, token_header):
    """Test if we can find matching key for token"""
    if not jwks or not token_header:
        return None
    
    print(f"\n🔍 Testing key matching...")
    token_kid = token_header.get('kid')
    print(f"Token kid: {token_kid}")
    
    matching_key = None
    for key in jwks.get('keys', []):
        if key.get('kid') == token_kid:
            matching_key = key
            print(f"✅ Found matching key: {key.get('kty')} {key.get('alg', 'N/A')}")
            break
    
    if not matching_key:
        available_kids = [k.get('kid') for k in jwks.get('keys', [])]
        print(f"❌ No matching key found")
        print(f"Available kids: {available_kids}")
    
    return matching_key

def main():
    print("🚀 JWT Validation Debug Tool")
    print("=" * 50)
    
    # Test JWKS endpoint
    jwks = test_jwks_endpoint()
    
    # If a token is provided as command line argument, test it
    if len(sys.argv) > 1:
        sample_token = sys.argv[1]
        header, payload = test_token_decode(sample_token)
        
        if header and jwks:
            matching_key = test_key_matching(jwks, header)
            
            if matching_key:
                print(f"\n🔧 Attempting signature verification...")
                try:
                    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(matching_key)
                    
                    # Try different validation approaches
                    strategies = [
                        {"audience": CLIENT_ID, "issuer": f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"},
                        {"audience": CLIENT_ID, "issuer": "https://login.microsoftonline.com/common/v2.0"},
                        {"issuer": f"https://login.microsoftonline.com/{TENANT_ID}/v2.0", "options": {"verify_aud": False}},
                        {"audience": CLIENT_ID, "options": {"verify_iss": False}},
                        {"options": {"verify_aud": False, "verify_iss": False}}
                    ]
                    
                    for i, strategy in enumerate(strategies, 1):
                        try:
                            kwargs = {"jwt": sample_token, "key": public_key, "algorithms": ["RS256"]}
                            kwargs.update(strategy)
                            
                            decoded = jwt.decode(**kwargs)
                            print(f"✅ Strategy {i} succeeded!")
                            print(f"Strategy details: {strategy}")
                            break
                        except Exception as e:
                            print(f"❌ Strategy {i} failed: {e}")
                    
                except Exception as e:
                    print(f"❌ Key conversion failed: {e}")
    else:
        print("\n💡 To test a specific token, run:")
        print(f"python {sys.argv[0]} <your_jwt_token>")
    
    print("\n" + "=" * 50)
    print("🏁 Debug complete")

if __name__ == "__main__":
    main()
