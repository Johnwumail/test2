#!/bin/bash
# System Diagnostics Script
# This script collects basic system diagnostic information.

# Exit on error
set -e

# Record start time
echo "=== System Diagnostics ==="
echo "Started at: $(date)"
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Warning: Not running as root. Some diagnostics may be limited."
fi

# Create a temporary directory for output
TEMP_DIR=$(mktemp -d)
REPORT_FILE="$TEMP_DIR/system_report.txt"

echo "Collecting system information in $REPORT_FILE"

# System information
echo "=== System Information ===" > "$REPORT_FILE"
echo "Date/Time: $(date)" >> "$REPORT_FILE"
echo "Hostname: $(hostname)" >> "$REPORT_FILE"
echo "Kernel: $(uname -r)" >> "$REPORT_FILE"
echo "Architecture: $(uname -m)" >> "$REPORT_FILE"
if command -v lsb_release &> /dev/null; then
  echo "Distribution: $(lsb_release -d | cut -f 2)" >> "$REPORT_FILE"
elif [ -f /etc/os-release ]; then
  echo "Distribution: $(grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '"')" >> "$REPORT_FILE"
fi
echo >> "$REPORT_FILE"

# CPU information
echo "=== CPU Information ===" >> "$REPORT_FILE"
if [ -f /proc/cpuinfo ]; then
  echo "CPU Model: $(grep "model name" /proc/cpuinfo | head -1 | cut -d: -f2 | sed 's/^[ \t]*//')" >> "$REPORT_FILE"
  echo "CPU Cores: $(grep -c "processor" /proc/cpuinfo)" >> "$REPORT_FILE"
fi
echo "Load Average: $(cat /proc/loadavg)" >> "$REPORT_FILE"
echo >> "$REPORT_FILE"

# Memory information
echo "=== Memory Information ===" >> "$REPORT_FILE"
if command -v free &> /dev/null; then
  free -h >> "$REPORT_FILE"
fi
echo >> "$REPORT_FILE"

# Disk information
echo "=== Disk Information ===" >> "$REPORT_FILE"
if command -v df &> /dev/null; then
  df -h >> "$REPORT_FILE"
fi
echo >> "$REPORT_FILE"

# Network information
echo "=== Network Information ===" >> "$REPORT_FILE"
if command -v ip &> /dev/null; then
  echo "Network Interfaces:" >> "$REPORT_FILE"
  ip addr show | grep -E "^[0-9]+:|inet " >> "$REPORT_FILE"
fi
echo >> "$REPORT_FILE"

# Process information
echo "=== Process Information ===" >> "$REPORT_FILE"
echo "Top 10 CPU-consuming processes:" >> "$REPORT_FILE"
if command -v ps &> /dev/null; then
  ps aux --sort=-%cpu | head -11 >> "$REPORT_FILE"
fi
echo >> "$REPORT_FILE"
echo "Top 10 memory-consuming processes:" >> "$REPORT_FILE"
if command -v ps &> /dev/null; then
  ps aux --sort=-%mem | head -11 >> "$REPORT_FILE"
fi
echo >> "$REPORT_FILE"

# Service status
echo "=== Service Status ===" >> "$REPORT_FILE"
if command -v systemctl &> /dev/null; then
  echo "Failed services:" >> "$REPORT_FILE"
  systemctl --failed >> "$REPORT_FILE"
fi
echo >> "$REPORT_FILE"

# Recent logs
echo "=== Recent System Logs ===" >> "$REPORT_FILE"
if [ -f /var/log/syslog ]; then
  echo "Last 20 syslog entries:" >> "$REPORT_FILE"
  tail -20 /var/log/syslog >> "$REPORT_FILE"
elif [ -f /var/log/messages ]; then
  echo "Last 20 messages entries:" >> "$REPORT_FILE"
  tail -20 /var/log/messages >> "$REPORT_FILE"
fi
echo >> "$REPORT_FILE"

# Security information
echo "=== Security Information ===" >> "$REPORT_FILE"
echo "Last 10 logins:" >> "$REPORT_FILE"
last -10 >> "$REPORT_FILE"
echo >> "$REPORT_FILE"

# Display report location
echo "Diagnostics completed."
echo "Report saved to: $REPORT_FILE"

# If a destination parameter was provided, copy the report there
if [ "$1" != "" ]; then
  cp "$REPORT_FILE" "$1"
  echo "Report copied to: $1"
fi

# Display diagnostic summary
echo
echo "=== Diagnostic Summary ==="
echo "CPU Load: $(cat /proc/loadavg | cut -d' ' -f1)"
if command -v free &> /dev/null; then
  echo "Memory: $(free -h | grep Mem | awk '{print $3 " used out of " $2}')"
fi
if command -v df &> /dev/null; then
  echo "Root Disk: $(df -h / | grep / | awk '{print $5 " used (" $3 " out of " $2 ")"}')"
fi

echo
echo "Run 'cat $REPORT_FILE' to view the full report." 