#!/bin/bash

# LCW Fetch Service Thread Monitor
# Monitors thread counts and alerts on anomalies

CONTAINER_NAME="lcw-fetch-service"
LOG_FILE="thread-monitor.log"
ALERT_THRESHOLD_WARN=8
ALERT_THRESHOLD_CRITICAL=15
TOTAL_THREADS_CRITICAL=50

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Function to log with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') | $1" | tee -a "$LOG_FILE"
}

# Function to extract thread count from logs
# Function to extract thread count from logs
get_current_threads() {
    local temp_file="/tmp/thread_logs_$$"
    local thread_line
    local last_thread_log
    
    # Write logs to temp file to avoid piping issues
    docker logs "$CONTAINER_NAME" --tail 100 2>&1 | grep "📊 System Resources" > "$temp_file"
    
    # Get the last line from the temp file
    thread_line=$(tail -1 "$temp_file" 2>/dev/null)
    rm -f "$temp_file"
    
    if [ -z "$thread_line" ]; then
        echo "0 0"
        return
    fi
    
    # Extract just the "Threads: X/Y" part
    last_thread_log=$(echo "$thread_line" | grep -o "Threads: [0-9]\+/[0-9]\+")
    
    if [[ $last_thread_log =~ Threads:\ ([0-9]+)/([0-9]+) ]]; then
        echo "${BASH_REMATCH[1]} ${BASH_REMATCH[2]}"
    else
        echo "0 0"
    fi
}

# Function to check for errors
check_for_errors() {
    local error_count
    error_count=$(docker logs "$CONTAINER_NAME" --since "5m" 2>/dev/null | grep -i -c -E "(error|exception|failed)")
    echo "$error_count"
}

# Function to check for missing cleanup messages
check_cleanup_messages() {
    local recent_logs
    local cleanup_count
    recent_logs=$(docker logs "$CONTAINER_NAME" --since "5m" 2>/dev/null)
    
    # Count successful job completions vs cleanup messages
    local job_completions=$(echo "$recent_logs" | grep -c "Job.*executed successfully")
    local cleanup_messages=$(echo "$recent_logs" | grep -c "closed successfully")
    
    echo "$job_completions $cleanup_messages"
}

# Main monitoring function
monitor_threads() {
    log_message "🔍 Starting thread monitoring check"
    
    # Check if container is running
    if ! docker ps --format "table {{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
        log_message "🚨 CRITICAL: Container $CONTAINER_NAME is not running!"
        return 1
    fi
    
    # Get current thread counts
    read -r active_threads total_threads <<< "$(get_current_threads)"
    
    if [ "$active_threads" -eq 0 ] && [ "$total_threads" -eq 0 ]; then
        log_message "⚠️  WARNING: Could not extract thread information from logs"
        return 1
    fi
    
    # Check thread thresholds
    if [ "$active_threads" -gt "$ALERT_THRESHOLD_CRITICAL" ]; then
        log_message "🚨 CRITICAL: Active threads ($active_threads) exceeds critical threshold ($ALERT_THRESHOLD_CRITICAL)"
        return 2
    elif [ "$total_threads" -gt "$TOTAL_THREADS_CRITICAL" ]; then
        log_message "🚨 CRITICAL: Total threads ($total_threads) exceeds critical threshold ($TOTAL_THREADS_CRITICAL)"
        return 2
    elif [ "$active_threads" -gt "$ALERT_THRESHOLD_WARN" ]; then
        log_message "⚠️  WARNING: Active threads ($active_threads) exceeds warning threshold ($ALERT_THRESHOLD_WARN)"
        return 1
    fi
    
    # Check for errors
    local error_count
    error_count=$(check_for_errors)
    if [ "$error_count" -gt 0 ]; then
        log_message "⚠️  WARNING: Found $error_count errors in last 5 minutes"
    fi
    
    # Check cleanup messages
    read -r job_completions cleanup_count <<< "$(check_cleanup_messages)"
    if [ "$job_completions" -gt 0 ] && [ "$cleanup_count" -lt $((job_completions * 2)) ]; then
        log_message "⚠️  WARNING: Potential cleanup issue - $job_completions jobs completed but only $cleanup_count cleanup messages"
    fi
    
    # Log healthy status
    log_message "✅ Threads: $active_threads/$total_threads | Errors: $error_count | Cleanup OK"
    
    return 0
}

# Function to run continuous monitoring
continuous_monitor() {
    log_message "🚀 Starting continuous thread monitoring (checking every 30 seconds)"
    
    while true; do
        monitor_threads
        sleep 30
    done
}

# Function to show help
show_help() {
    echo "LCW Fetch Service Thread Monitor"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  check      Run a single monitoring check"
    echo "  monitor    Run continuous monitoring (every 30 seconds)"
    echo "  status     Show current thread status"
    echo "  help       Show this help message"
    echo ""
}

# Function to show current status
show_status() {
    echo -e "${GREEN}=== LCW Fetch Service Status ===${NC}"
    
    if ! docker ps --format "table {{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
        echo -e "${RED}❌ Container Status: NOT RUNNING${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ Container Status: RUNNING${NC}"
    
    read -r active_threads total_threads <<< "$(get_current_threads)"
    
    if [ "$active_threads" -gt "$ALERT_THRESHOLD_CRITICAL" ]; then
        echo -e "${RED}🚨 Thread Status: CRITICAL ($active_threads/$total_threads)${NC}"
    elif [ "$active_threads" -gt "$ALERT_THRESHOLD_WARN" ]; then
        echo -e "${YELLOW}⚠️  Thread Status: WARNING ($active_threads/$total_threads)${NC}"
    else
        echo -e "${GREEN}✅ Thread Status: HEALTHY ($active_threads/$total_threads)${NC}"
    fi
    
    local error_count
    error_count=$(check_for_errors)
    if [ "$error_count" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Recent Errors: $error_count in last 5 minutes${NC}"
    else
        echo -e "${GREEN}✅ No Recent Errors${NC}"
    fi
    
    echo ""
    echo "Last few thread measurements:"
    docker logs "$CONTAINER_NAME" --tail 20 2>/dev/null | grep "System Resources" | tail -3
}

# Main script logic
case "${1:-}" in
    "check")
        monitor_threads
        ;;
    "monitor")
        continuous_monitor
        ;;
    "status")
        show_status
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    "")
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
