#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#

LOG_FILE="test.log"
EXPORT_FILE="export_test.md"

# Start with a clean slate
rm -f $LOG_FILE $EXPORT_FILE .server.pid ninaivalaigal_data.json

# Start the server
echo "--- STARTING SERVER ---" >> $LOG_FILE
./manage.sh start >> $LOG_FILE 2>&1
sleep 2 # Give the server a moment to start

# Remember a memory
echo "\n--- REMEMBERING MEMORY ---" >> $LOG_FILE
./client/mem0 remember '{
    "type": "test_data",
    "source": "run_test.sh",
    "data": {
        "status": "success"
    }
}' >> $LOG_FILE 2>&1

# Export the memory
echo "\n--- EXPORTING MEMORY ---" >> $LOG_FILE
./client/mem0 export $EXPORT_FILE >> $LOG_FILE 2>&1

# Stop the server
echo "\n--- STOPPING SERVER ---" >> $LOG_FILE
./manage.sh stop >> $LOG_FILE 2>&1

echo "\n--- TEST COMPLETE ---" >> $LOG_FILE
