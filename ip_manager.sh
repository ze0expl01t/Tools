#!/bin/bash

# Script: ipmanager.sh
# Description: Interactive menu to Block, Unblock, or Check an IP address in iptables.
# Usage: sudo ./ipmanager.sh

# Text Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if run as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root. Use sudo.${NC}" 
   exit 1
fi

# Function to validate IP address
validate_ip() {
    local ip=$1
    if [[ $ip =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        return 0
    else
        echo -e "${RED}Error: '$ip' is not a valid IP address.${NC}"
        return 1
    fi
}

# Function to check if IP is already blocked
check_ip() {
    local ip=$1
    echo -e "${YELLOW}Checking for IP: $ip in iptables rules...${NC}"
    local found=0

    # Check filter table (INPUT and FORWARD)
    if iptables -L INPUT -n --line-numbers | grep -q "DROP.*$ip\|$ip.*DROP"; then
        echo -e "${RED}>>> FOUND in INPUT chain (filter table):${NC}"
        iptables -L INPUT -n --line-numbers | grep --color=auto -n "DROP.*$ip\|$ip.*DROP"
        found=1
    fi

    if iptables -L FORWARD -n --line-numbers | grep -q "DROP.*$ip\|$ip.*DROP"; then
        echo -e "${RED}>>> FOUND in FORWARD chain (filter table):${NC}"
        iptables -L FORWARD -n --line-numbers | grep --color=auto -n "DROP.*$ip\|$ip.*DROP"
        found=1
    fi

    # Check nat table (PREROUTING)
    if iptables -t nat -L PREROUTING -n --line-numbers | grep -q "$ip"; then
        echo -e "${RED}>>> FOUND in PREROUTING chain (nat table):${NC}"
        iptables -t nat -L PREROUTING -n --line-numbers | grep --color=auto -n "$ip"
        found=1
    fi

    if [[ $found -eq 0 ]]; then
        echo -e "${GREEN}IP $ip is NOT currently blocked.${NC}"
    fi
    echo ""
}

# Function to block an IP address
block_ip() {
    local ip=$1
    echo -e "${YELLOW}Attempting to block IP: $ip${NC}"

    # Check if already blocked first
    if iptables -L INPUT -n | grep -q "DROP.*$ip\|$ip.*DROP" || \
       iptables -L FORWARD -n | grep -q "DROP.*$ip\|$ip.*DROP"; then
        echo -e "${RED}IP $ip is already blocked!${NC}"
        check_ip "$ip"
        return 1
    fi

    # Add blocking rules
    iptables -A INPUT -s "$ip" -j DROP
    iptables -A FORWARD -s "$ip" -j DROP
    echo -e "${GREEN}Successfully added DROP rules for IP $ip in INPUT and FORWARD chains.${NC}"

    # Optional: Add a rule to log the blocked attempt (comment out if not needed)
    # iptables -I INPUT 1 -s "$ip" -m limit --limit 2/min -j LOG --log-prefix "IPTables-Blocked: " --log-level 4

    echo -e "${GREEN}IP $ip has been blocked.${NC}"
}

# Function to unblock an IP address
unblock_ip() {
    local ip=$1
    echo -e "${YELLOW}Attempting to unblock IP: $ip${NC}"
    local removed=0

    # Remove rules from INPUT chain (from highest line number to lowest)
    while true; do
        local line_num
        line_num=$(iptables -L INPUT -n --line-numbers | grep "DROP.*$ip" | tail -1 | awk '{print $1}')
        if [[ -n "$line_num" ]]; then
            iptables -D INPUT "$line_num"
            echo -e "${BLUE}Removed rule from INPUT chain, line #$line_num${NC}"
            removed=1
        else
            break
        fi
    done

    # Remove rules from FORWARD chain
    while true; do
        local line_num
        line_num=$(iptables -L FORWARD -n --line-numbers | grep "DROP.*$ip" | tail -1 | awk '{print $1}')
        if [[ -n "$line_num" ]]; then
            iptables -D FORWARD "$line_num"
            echo -e "${BLUE}Removed rule from FORWARD chain, line #$line_num${NC}"
            removed=1
        else
            break
        fi
    done

    # Remove rules from nat table PREROUTING chain
    while true; do
        local line_num
        line_num=$(iptables -t nat -L PREROUTING -n --line-numbers | grep "$ip" | tail -1 | awk '{print $1}')
        if [[ -n "$line_num" ]]; then
            iptables -t nat -D PREROUTING "$line_num"
            echo -e "${BLUE}Removed rule from PREROUTING (nat), line #$line_num${NC}"
            removed=1
        else
            break
        fi
    done

    if [[ $removed -eq 1 ]]; then
        echo -e "${GREEN}Finished. All rules for IP $ip have been removed.${NC}"
    else
        echo -e "${YELLOW}No active rules found for IP $ip. Nothing to remove.${NC}"
    fi
}

# Main Interactive Menu
while true; do
    clear
    echo -e "${BLUE}=================================${NC}"
    echo -e "${BLUE}    ze0expl01t ~ IPTABLES IP MANAGER${NC}"
    echo -e "${BLUE}=================================${NC}"
    echo -e "1) ${GREEN}Block an IP address${NC}"
    echo -e "2) ${RED}Unblock an IP address${NC}"
    echo -e "3) ${YELLOW}Check if an IP is blocked${NC}"
    echo -e "4) ${RED}Exit${NC}"
    echo -e "${BLUE}=================================${NC}"
    read -p "Please choose an option [1-4]: " choice

    case $choice in
        1)
            # Block IP
            read -p "Enter the IP address to BLOCK: " ip
            if validate_ip "$ip"; then
                check_ip "$ip" # Show current status first
                read -p "Are you sure you want to BLOCK this IP? (y/N): " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    block_ip "$ip"
                else
                    echo -e "${YELLOW}Block operation cancelled.${NC}"
                fi
            fi
            read -p "Press [Enter] to return to menu..."
            ;;
        2)
            # Unblock IP
            read -p "Enter the IP address to UNBLOCK: " ip
            if validate_ip "$ip"; then
                check_ip "$ip" # Show what will be removed
                read -p "Are you sure you want to UNBLOCK this IP? (y/N): " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    unblock_ip "$ip"
                else
                    echo -e "${YELLOW}Unblock operation cancelled.${NC}"
                fi
            fi
            read -p "Press [Enter] to return to menu..."
            ;;
        3)
            # Check IP
            read -p "Enter the IP address to CHECK: " ip
            if validate_ip "$ip"; then
                check_ip "$ip"
            fi
            read -p "Press [Enter] to return to menu..."
            ;;
        4)
            echo -e "${BLUE}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option. Please choose 1, 2, 3, or 4.${NC}"
            sleep 2
            ;;
    esac
done
