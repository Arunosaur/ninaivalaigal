#!/bin/bash

LOG_FILE="context_test.log"

# Start with a clean slate
rm -f $LOG_FILE .server.pid mem0_data.json

# Start the server
echo "--- STARTING SERVER ---" >> $LOG_FILE
./manage.sh start >> $LOG_FILE 2>&1
sleep 2 # Give the server a moment to start

# Remember a memory without specifying context
echo "\n--- REMEMBERING MEMORY (IMPLICIT CONTEXT) ---" >> $LOG_FILE
./client/mem0 remember '{
    "type": "context_test",
    "source": "run_context_test.sh",
    "data": {
        "test_id": "implicit_context_test"
    }
}' >> $LOG_FILE 2>&1

# Recall from the implicit context
echo "\n--- RECALLING MEMORY (IMPLICIT CONTEXT) ---" >> $LOG_FILE
./client/mem0 recall >> $LOG_FILE 2>&1

# Stop the server
echo "\n--- STOPPING SERVER ---" >> $LOG_FILE
./manage.sh stop >> $LOG_FILE 2>&1

echo "\n--- TEST COMPLETE ---" >> $LOG_FILE

