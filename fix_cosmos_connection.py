#!/usr/bin/env python3
"""
Script to diagnose and fix Cosmos DB connection string issues
"""

import sys
import os
import logging

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_key_vault_connection():
    """Test connection to Key Vault and list available secrets"""
    try:
        from azure_keyvault import client, list_secrets, get_secret
        
        print("🔍 Testing Key Vault connection...")
        secrets = list_secrets()
        print(f"✅ Connected to Key Vault successfully")
        print(f"📋 Available secrets: {secrets}")
        
        return True
        
    except Exception as e:
        print(f"❌ Key Vault connection failed: {e}")
        return False

def diagnose_cosmos_connection():
    """Diagnose the Cosmos DB connection string"""
    try:
        from azure_keyvault import get_cosmos_connection_string
        
        print("\n🔍 Retrieving Cosmos DB connection string...")
        conn_string = get_cosmos_connection_string()
        
        if not conn_string:
            print("❌ Connection string is empty")
            return None
        
        # Show masked version for security
        masked_conn = conn_string[:50] + "..." if len(conn_string) > 50 else conn_string
        print(f"📝 Connection string preview: {masked_conn}")
        
        # Analyze the format
        print("\n🔍 Analyzing connection string format...")
        
        required_fields = ['DefaultEndpointsProtocol', 'AccountName', 'AccountKey']
        found_fields = []
        missing_fields = []
        
        for field in required_fields:
            if field.lower() in conn_string.lower():
                found_fields.append(field)
            else:
                missing_fields.append(field)
        
        if found_fields:
            print(f"✅ Found fields: {found_fields}")
        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
        
        # Check if it's just a URL
        if conn_string.startswith('https://') and '.table.core.windows.net' in conn_string:
            print("⚠️  Connection string appears to be just a table endpoint URL")
            account_name = conn_string.split('//')[1].split('.')[0]
            print(f"🏷️  Extracted account name: {account_name}")
            print("❗ Missing account key - connection will fail")
        
        # Check if it has key-value format
        elif '=' in conn_string and ';' in conn_string:
            print("✅ Connection string has key-value format")
            
            # Parse the components
            parts = {}
            for part in conn_string.split(';'):
                if '=' in part and part.strip():
                    key, value = part.split('=', 1)
                    parts[key.strip()] = value.strip()
            
            print(f"📋 Connection string components: {list(parts.keys())}")
            
            # Check for common variations
            account_name_keys = ['AccountName', 'accountname', 'Account Name']
            account_key_keys = ['AccountKey', 'accountkey', 'Account Key']
            
            account_name = None
            account_key = None
            
            for key in account_name_keys:
                if key in parts:
                    account_name = parts[key]
                    break
            
            for key in account_key_keys:
                if key in parts:
                    account_key = "***" if parts[key] else None  # Mask the key
                    break
            
            print(f"🏷️  Account Name: {account_name}")
            print(f"🔑 Account Key: {'Present' if account_key else 'Missing'}")
            
        else:
            print("❌ Connection string format not recognized")
        
        return conn_string
        
    except Exception as e:
        print(f"❌ Error diagnosing connection string: {e}")
        return None

def suggest_fixes():
    """Suggest fixes for common connection string issues"""
    print("\n💡 Common fixes for Cosmos DB connection string issues:")
    print()
    print("1. **Correct format should be:**")
    print("   DefaultEndpointsProtocol=https;AccountName=<account>;AccountKey=<key>;TableEndpoint=https://<account>.table.core.windows.net/;")
    print()
    print("2. **If you only have the table endpoint URL:**")
    print("   - Get the account key from Azure Portal > Storage Account > Access Keys")
    print("   - Update the Key Vault secret with the full connection string")
    print()
    print("3. **To update the Key Vault secret:**")
    print("   az keyvault secret set --vault-name bookmanagement-kv --name cosmos-connection-string --value \"<full_connection_string>\"")
    print()

def test_table_connection():
    """Test if we can connect to the table with current connection string"""
    print("\n🔍 Testing table connection...")
    try:
        from backend.database import CosmosTableClient
        
        client = CosmosTableClient()
        print("✅ Table client initialized successfully")
        
        # Try to list entities
        entities = client.list_entities()
        print(f"✅ Successfully connected to table. Found {len(entities)} entities.")
        
        return True
        
    except Exception as e:
        print(f"❌ Table connection failed: {e}")
        return False

def main():
    print("🚀 Cosmos DB Connection Diagnostics")
    print("=" * 50)
    
    # Test Key Vault connection
    if not test_key_vault_connection():
        print("\n❌ Cannot proceed without Key Vault access")
        return
    
    # Diagnose connection string
    conn_string = diagnose_cosmos_connection()
    
    if conn_string:
        # Test table connection
        test_table_connection()
    
    # Show suggestions
    suggest_fixes()
    
    print("\n" + "=" * 50)
    print("🏁 Diagnostics complete")

if __name__ == "__main__":
    main()
