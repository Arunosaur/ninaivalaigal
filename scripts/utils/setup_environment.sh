#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Ninaivalaigal Environment Setup Script

echo "🔧 Setting up Ninaivalaigal environment variables..."

# Generate a secure JWT secret for production
JWT_SECRET=$(openssl rand -base64 32)

# Set server-side JWT secret
export NINAIVALAIGAL_JWT_SECRET="$JWT_SECRET"
echo "✅ NINAIVALAIGAL_JWT_SECRET set (server secret)"

# For testing, create a user token
# In production, users get this from login API
echo "🔑 Generating test user token..."

python3 -c "
import jwt
from datetime import datetime, timedelta
import os

# Use the same secret
secret = os.environ['NINAIVALAIGAL_JWT_SECRET']

# Create test user payload
payload = {
    'user_id': 8,
    'email': 'durai@example.com',
    'account_type': 'individual',
    'role': 'user',
    'exp': int((datetime.utcnow() + timedelta(days=7)).timestamp())
}

# Generate token
token = jwt.encode(payload, secret, algorithm='HS256')
print(f'export NINAIVALAIGAL_USER_TOKEN=\"{token}\"')
" > /tmp/user_token.sh

# Source the user token
source /tmp/user_token.sh
rm /tmp/user_token.sh

echo "✅ NINAIVALAIGAL_USER_TOKEN set (test user)"
echo ""
echo "🚀 Environment ready! You can now:"
echo "   eM contexts"
echo "   eM start --context my-test"
echo "   eM remember '{\"data\": \"test\"}' --context my-test"
echo ""
echo "💡 To persist these variables, add them to your ~/.bashrc or ~/.zshrc"
echo "   echo 'export NINAIVALAIGAL_JWT_SECRET=\"$NINAIVALAIGAL_JWT_SECRET\"' >> ~/.zshrc"
echo "   echo 'export NINAIVALAIGAL_USER_TOKEN=\"$NINAIVALAIGAL_USER_TOKEN\"' >> ~/.zshrc"
