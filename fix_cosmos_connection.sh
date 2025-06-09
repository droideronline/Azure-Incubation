#!/bin/bash
# fix_cosmos_connection.sh - Script to fix Cosmos DB connection string on Azure VM

echo "🚀 Fixing Cosmos DB Connection String"
echo "===================================="

# Check if running on Azure VM
if [[ -f "/opt/bookmanagement/backend/database.py" ]]; then
    echo "✅ Detected Azure VM environment"
    SCRIPT_DIR="/opt/bookmanagement"
else
    echo "❌ Not running on expected Azure VM path"
    exit 1
fi

cd "$SCRIPT_DIR"

# Check current connection string in Key Vault
echo "🔍 Checking current connection string..."
python3 -c "
import sys
sys.path.append('.')
from azure_keyvault import get_cosmos_connection_string
try:
    conn_str = get_cosmos_connection_string()
    print(f'Current connection string length: {len(conn_str)} chars')
    print(f'Preview: {conn_str[:60]}...')
    
    # Check format
    if 'AccountName=' in conn_str and 'AccountKey=' in conn_str:
        print('✅ Connection string has proper format')
    elif 'https://' in conn_str and '.table.core.windows.net' in conn_str:
        print('⚠️  Connection string is just a URL - missing account key')
        # Extract account name
        account_name = conn_str.split('//')[1].split('.')[0]
        print(f'Account name: {account_name}')
        print('')
        print('🔧 To fix this, you need to update the Key Vault secret with the full connection string:')
        print('Format: DefaultEndpointsProtocol=https;AccountName={};AccountKey=<KEY>;TableEndpoint={};'.format(account_name, conn_str))
        print('')
        print('Get the account key from Azure Portal > Storage Account > Access Keys')
        print('Then run:')
        print(f'az keyvault secret set --vault-name bookmanagement-kv --name cosmos-connection-string --value \"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey=<YOUR_KEY>;TableEndpoint={conn_str};\"')
    else:
        print('❌ Connection string format not recognized')
        print('Expected format: DefaultEndpointsProtocol=https;AccountName=<account>;AccountKey=<key>;TableEndpoint=https://<account>.table.core.windows.net/;')
        
except Exception as e:
    print(f'❌ Error accessing Key Vault: {e}')
"

echo ""
echo "🔄 Restarting services..."

# Kill existing backend processes
sudo pkill -f "uvicorn.*main:app" || true
sleep 2

# Start backend service
echo "🚀 Starting backend service..."
cd /opt/bookmanagement/backend
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
sleep 3

echo "✅ Backend service restarted"

# Check if service is running
if pgrep -f "uvicorn.*main:app" > /dev/null; then
    echo "✅ Backend service is running"
else
    echo "❌ Backend service failed to start"
    echo "Check logs: tail -f /tmp/backend.log"
fi

echo ""
echo "🏁 Fix attempt complete"
echo "Check application logs for any remaining issues"
