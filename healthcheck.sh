#!/bin/bash
# Lightweight health check script
# Priority: Check metrics endpoint first, fallback to HTTP check

# Method 1: Check metrics endpoint (fastest)
if curl -f -s http://localhost:9099/metrics >/dev/null 2>&1; then
    exit 0
fi

# Method 2: Check if the application is responsive with a minimal HTTP request
if curl -f -s --max-time 5 http://localhost:9099/ >/dev/null 2>&1; then
    exit 0
fi

# If both fail, health check fails
exit 1
