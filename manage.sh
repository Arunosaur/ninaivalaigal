#!/bin/bash

PID_FILE=".server.pid"

start() {
    if [ -f "$PID_FILE" ]; then
        echo "Server is already running. PID: $(cat $PID_FILE)"
        exit 1
    fi
    echo "Starting mem0 server..."
    /opt/homebrew/anaconda3/bin/python -m uvicorn server.main:app --host 127.0.0.1 --port 13370 & echo $! > $PID_FILE
    echo "Server started with PID: $(cat $PID_FILE)"
}

stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat $PID_FILE)
        echo "Stopping mem0 server with PID: $PID..."
        kill $PID
        rm $PID_FILE
        echo "Server stopped."
    else
        echo "Server is not running."
    fi
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    *)
        echo "Usage: $0 {start|stop}"
        exit 1
esac
