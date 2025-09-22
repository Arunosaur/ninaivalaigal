#!/bin/bash

LOG_FILE="session_test.log"

# Start with a clean slate
rm -f $LOG_FILE .server.pid mem0_data.json

# Start the server
echo "--- STARTING SERVER ---" >> $LOG_FILE
./manage.sh start >> $LOG_FILE 2>&1
sleep 2 # Give the server a moment to start

# Start recording a new context
echo "\n--- STARTING RECORDING CONTEXT 'feature-x' ---" >> $LOG_FILE
./client/mem0 context start "feature-x" >> $LOG_FILE 2>&1

# Attempt to remember in a non-active context (should be ignored)
echo "\n--- REMEMBERING TO WRONG CONTEXT (SHOULD FAIL) ---" >> $LOG_FILE
./client/mem0 remember '{
    "type": "wrong_context",
    "source": "test_script",
    "data": {}
}' --context "feature-y" >> $LOG_FILE 2>&1

# Remember in the active context
echo "\n--- REMEMBERING TO CORRECT CONTEXT ---" >> $LOG_FILE
./client/mem0 remember '{
    "type": "correct_context",
    "source": "test_script",
    "data": {"value": "test"}
}' --context "feature-x" >> $LOG_FILE 2>&1

# Recall from the context to verify
echo "\n--- RECALLING FROM 'feature-x' ---" >> $LOG_FILE
./client/mem0 recall --context "feature-x" >> $LOG_FILE 2>&1

# Stop recording
echo "\n--- STOPPING RECORDING ---" >> $LOG_FILE
./client/mem0 context stop >> $LOG_FILE 2>&1

# Stop the server
echo "\n--- STOPPING SERVER ---" >> $LOG_FILE
./manage.sh stop >> $LOG_FILE 2>&1

echo "\n--- TEST COMPLETE ---" >> $LOG_FILE
