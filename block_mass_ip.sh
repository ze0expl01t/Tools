#!/bin/bash

# Block IPs from text file
BLOCKLIST="/etc/iptables/blocklist.txt"

# Check if file exists
if [ ! -f "$BLOCKLIST" ]; then
    echo "Blocklist file not found: $BLOCKLIST"
    exit 1
fi

# Read each IP and add to iptables
while IFS= read -r ip; do
    # Skip empty lines and comments
    if [[ -n "$ip" && ! "$ip" =~ ^# ]]; then
        echo "Blocking IP: $ip"
        iptables -A INPUT -s "$ip" -j DROP
    fi
done < "$BLOCKLIST"

echo "IP blocking completed"
