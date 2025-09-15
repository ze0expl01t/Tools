#!/bin/bash

# MySQL Server Manager for Ubuntu
# Interactive script for managing MySQL operations including deletion functions
#Jangan lupa setting password root

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
MYSQL_USER="root"
MYSQL_PASS=""
BACKUP_DIR="/var/backups/mysql"
LOG_FILE="/var/log/mysql_manager.log"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# Log function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Check if MySQL is running
check_mysql_status() {
    if systemctl is-active --quiet mysql; then
        echo -e "${GREEN}MySQL is running${NC}"
        return 0
    else
        echo -e "${RED}MySQL is not running${NC}"
        return 1
    fi
}

# Get MySQL password securely
get_mysql_password() {
    if [ -z "$MYSQL_PASS" ]; then
        read -sp "Enter MySQL root password: " MYSQL_PASS
        echo
    fi
}

# Execute MySQL command
mysql_execute() {
    get_mysql_password
    mysql -u "$MYSQL_USER" -p"$MYSQL_PASS" -e "$1" 2>/dev/null
}

# Execute MySQL command with database context
mysql_execute_db() {
    get_mysql_password
    mysql -u "$MYSQL_USER" -p"$MYSQL_PASS" "$1" -e "$2" 2>/dev/null
}

# Backup database
backup_database() {
    local db_name=$1
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/${db_name}_${timestamp}.sql"
    
    get_mysql_password
    
    echo -e "${BLUE}Backing up database: $db_name${NC}"
    mysqldump -u "$MYSQL_USER" -p"$MYSQL_PASS" "$db_name" > "$backup_file"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Backup completed: $backup_file${NC}"
        log "Backup created: $backup_file"
    else
        echo -e "${RED}Backup failed!${NC}"
        log "Backup failed for database: $db_name"
    fi
}

# Restore database
restore_database() {
    local backup_file=$1
    local db_name=$2
    
    get_mysql_password
    
    echo -e "${BLUE}Restoring database: $db_name${NC}"
    mysql -u "$MYSQL_USER" -p"$MYSQL_PASS" "$db_name" < "$backup_file"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Restore completed successfully${NC}"
        log "Database restored: $db_name from $backup_file"
    else
        echo -e "${RED}Restore failed!${NC}"
        log "Restore failed for database: $db_name"
    fi
}

# Show database list
show_databases() {
    echo -e "${YELLOW}Available databases:${NC}"
    mysql_execute "SHOW DATABASES;" | grep -v "Database" | nl
}

# Show tables in a database
show_tables() {
    local db_name=$1
    echo -e "${YELLOW}Tables in database '$db_name':${NC}"
    mysql_execute_db "$db_name" "SHOW TABLES;" | grep -v "Tables_in" | nl
}

# Show users
show_users() {
    echo -e "${YELLOW}MySQL users:${NC}"
    mysql_execute "SELECT user, host FROM mysql.user;" | grep -v "user" | nl
}

# Create database
create_database() {
    read -p "Enter new database name: " db_name
    mysql_execute "CREATE DATABASE $db_name;"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Database '$db_name' created successfully${NC}"
        log "Database created: $db_name"
    else
        echo -e "${RED}Failed to create database${NC}"
    fi
}

# Delete database with confirmation
delete_database() {
    show_databases
    read -p "Enter database number to delete: " db_num
    db_name=$(mysql_execute "SHOW DATABASES;" | grep -v "Database" | sed -n "${db_num}p")
    
    if [ -z "$db_name" ]; then
        echo -e "${RED}Invalid database selection${NC}"
        return
    fi
    
    echo -e "${RED}WARNING: This will permanently delete database '$db_name' and all its data!${NC}"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        # Backup before deletion
        echo -e "${YELLOW}Creating backup before deletion...${NC}"
        backup_database "$db_name"
        
        mysql_execute "DROP DATABASE $db_name;"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Database '$db_name' deleted successfully${NC}"
            log "Database deleted: $db_name"
        else
            echo -e "${RED}Failed to delete database${NC}"
        fi
    else
        echo -e "${YELLOW}Database deletion cancelled${NC}"
    fi
}

# Delete table with confirmation
delete_table() {
    show_databases
    read -p "Enter database number: " db_num
    db_name=$(mysql_execute "SHOW DATABASES;" | grep -v "Database" | sed -n "${db_num}p")
    
    if [ -z "$db_name" ]; then
        echo -e "${RED}Invalid database selection${NC}"
        return
    fi
    
    show_tables "$db_name"
    read -p "Enter table number to delete: " table_num
    table_name=$(mysql_execute_db "$db_name" "SHOW TABLES;" | grep -v "Tables_in" | sed -n "${table_num}p")
    
    if [ -z "$table_name" ]; then
        echo -e "${RED}Invalid table selection${NC}"
        return
    fi
    
    echo -e "${RED}WARNING: This will permanently delete table '$table_name' from database '$db_name'!${NC}"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        mysql_execute_db "$db_name" "DROP TABLE $table_name;"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Table '$table_name' deleted successfully${NC}"
            log "Table deleted: $table_name from database: $db_name"
        else
            echo -e "${RED}Failed to delete table${NC}"
        fi
    else
        echo -e "${YELLOW}Table deletion cancelled${NC}"
    fi
}

# Create user
create_user() {
    read -p "Enter new username: " username
    read -sp "Enter password for $username: " password
    echo
    read -p "Enter host (default: localhost): " host
    host=${host:-localhost}
    
    mysql_execute "CREATE USER '$username'@'$host' IDENTIFIED BY '$password';"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}User '$username' created successfully${NC}"
        log "User created: $username@$host"
    else
        echo -e "${RED}Failed to create user${NC}"
    fi
}

# Delete user with confirmation
delete_user() {
    show_users
    read -p "Enter user number to delete: " user_num
    user_info=$(mysql_execute "SELECT user, host FROM mysql.user;" | grep -v "user" | sed -n "${user_num}p")
    username=$(echo $user_info | awk '{print $1}')
    host=$(echo $user_info | awk '{print $2}')
    
    if [ -z "$username" ]; then
        echo -e "${RED}Invalid user selection${NC}"
        return
    fi
    
    echo -e "${RED}WARNING: This will permanently delete user '$username'@'$host'!${NC}"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        mysql_execute "DROP USER '$username'@'$host';"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}User '$username'@'$host' deleted successfully${NC}"
            log "User deleted: $username@$host"
        else
            echo -e "${RED}Failed to delete user${NC}"
        fi
    else
        echo -e "${YELLOW}User deletion cancelled${NC}"
    fi
}

# Grant privileges
grant_privileges() {
    show_databases
    read -p "Enter database number: " db_num
    db_name=$(mysql_execute "SHOW DATABASES;" | grep -v "Database" | sed -n "${db_num}p")
    
    show_users
    read -p "Enter user number: " user_num
    user_info=$(mysql_execute "SELECT user, host FROM mysql.user;" | grep -v "user" | sed -n "${user_num}p")
    username=$(echo $user_info | awk '{print $1}')
    host=$(echo $user_info | awk '{print $2}')
    
    echo -e "${YELLOW}Available privileges:${NC}"
    echo "1. ALL PRIVILEGES"
    echo "2. SELECT"
    echo "3. INSERT"
    echo "4. UPDATE"
    echo "5. DELETE"
    echo "6. Custom privileges"
    
    read -p "Choose option (1-6): " priv_opt
    
    case $priv_opt in
        1) privileges="ALL PRIVILEGES" ;;
        2) privileges="SELECT" ;;
        3) privileges="INSERT" ;;
        4) privileges="UPDATE" ;;
        5) privileges="DELETE" ;;
        6) read -p "Enter custom privileges: " privileges ;;
        *) privileges="ALL PRIVILEGES" ;;
    esac
    
    mysql_execute "GRANT $privileges ON $db_name.* TO '$username'@'$host';"
    mysql_execute "FLUSH PRIVILEGES;"
    
    echo -e "${GREEN}Privileges granted successfully${NC}"
    log "Privileges granted: $privileges on $db_name to $username@$host"
}

# Revoke privileges
revoke_privileges() {
    show_databases
    read -p "Enter database number: " db_num
    db_name=$(mysql_execute "SHOW DATABASES;" | grep -v "Database" | sed -n "${db_num}p")
    
    show_users
    read -p "Enter user number: " user_num
    user_info=$(mysql_execute "SELECT user, host FROM mysql.user;" | grep -v "user" | sed -n "${user_num}p")
    username=$(echo $user_info | awk '{print $1}')
    host=$(echo $user_info | awk '{print $2}')
    
    echo -e "${YELLOW}Available privileges to revoke:${NC}"
    echo "1. ALL PRIVILEGES"
    echo "2. SELECT"
    echo "3. INSERT"
    echo "4. UPDATE"
    echo "5. DELETE"
    echo "6. Custom privileges"
    
    read -p "Choose option (1-6): " priv_opt
    
    case $priv_opt in
        1) privileges="ALL PRIVILEGES" ;;
        2) privileges="SELECT" ;;
        3) privileges="INSERT" ;;
        4) privileges="UPDATE" ;;
        5) privileges="DELETE" ;;
        6) read -p "Enter custom privileges: " privileges ;;
        *) privileges="ALL PRIVILEGES" ;;
    esac
    
    mysql_execute "REVOKE $privileges ON $db_name.* FROM '$username'@'$host';"
    mysql_execute "FLUSH PRIVILEGES;"
    
    echo -e "${GREEN}Privileges revoked successfully${NC}"
    log "Privileges revoked: $privileges on $db_name from $username@$host"
}

# Show user privileges
show_user_privileges() {
    show_users
    read -p "Enter user number: " user_num
    user_info=$(mysql_execute "SELECT user, host FROM mysql.user;" | grep -v "user" | sed -n "${user_num}p")
    username=$(echo $user_info | awk '{print $1}')
    host=$(echo $user_info | awk '{print $2}')
    
    echo -e "${YELLOW}Privileges for '$username'@'$host':${NC}"
    mysql_execute "SHOW GRANTS FOR '$username'@'$host';"
}

# Main menu
main_menu() {
    while true; do
        echo -e "\n${BLUE}=== MySQL Server Manager ===${NC}"
        echo -e "${CYAN}Service Management:${NC}"
        echo "1. Check MySQL Status"
        echo "2. Start MySQL Service"
        echo "3. Stop MySQL Service"
        echo "4. Restart MySQL Service"
        echo -e "${CYAN}Database Operations:${NC}"
        echo "5. Show Databases"
        echo "6. Create Database"
        echo "7. Delete Database"
        echo -e "${CYAN}Table Operations:${NC}"
        echo "8. Show Tables"
        echo "9. Delete Table"
        echo -e "${CYAN}User Management:${NC}"
        echo "10. Show Users"
        echo "11. Create User"
        echo "12. Delete User"
        echo "13. Grant Privileges"
        echo "14. Revoke Privileges"
        echo "15. Show User Privileges"
        echo -e "${CYAN}Backup & Restore:${NC}"
        echo "16. Backup Database"
        echo "17. Restore Database"
        echo "18. Show Backup Files"
        echo -e "${CYAN}Other:${NC}"
        echo "19. View Logs"
        echo "20. Exit"
        echo -e "${YELLOW}===============================${NC}"
        
        read -p "Choose an option (1-20): " choice
        
        case $choice in
            1)
                check_mysql_status
                ;;
            2)
                sudo systemctl start mysql
                check_mysql_status
                ;;
            3)
                sudo systemctl stop mysql
                check_mysql_status
                ;;
            4)
                sudo systemctl restart mysql
                check_mysql_status
                ;;
            5)
                show_databases
                ;;
            6)
                create_database
                ;;
            7)
                delete_database
                ;;
            8)
                show_databases
                read -p "Enter database number: " db_num
                db_name=$(mysql_execute "SHOW DATABASES;" | grep -v "Database" | sed -n "${db_num}p")
                if [ -n "$db_name" ]; then
                    show_tables "$db_name"
                else
                    echo -e "${RED}Invalid database selection${NC}"
                fi
                ;;
            9)
                delete_table
                ;;
            10)
                show_users
                ;;
            11)
                create_user
                ;;
            12)
                delete_user
                ;;
            13)
                grant_privileges
                ;;
            14)
                revoke_privileges
                ;;
            15)
                show_user_privileges
                ;;
            16)
                show_databases
                read -p "Enter database number to backup: " db_num
                db_name=$(mysql_execute "SHOW DATABASES;" | grep -v "Database" | sed -n "${db_num}p")
                if [ -n "$db_name" ]; then
                    backup_database "$db_name"
                else
                    echo -e "${RED}Invalid database selection${NC}"
                fi
                ;;
            17)
                echo -e "${YELLOW}Available backup files:${NC}"
                ls -la "$BACKUP_DIR"/*.sql 2>/dev/null | nl || echo "No backup files found"
                read -p "Enter backup file number: " file_num
                backup_file=$(ls "$BACKUP_DIR"/*.sql 2>/dev/null | sed -n "${file_num}p")
                
                show_databases
                read -p "Enter target database number: " db_num
                db_name=$(mysql_execute "SHOW DATABASES;" | grep -v "Database" | sed -n "${db_num}p")
                
                if [ -f "$backup_file" ] && [ -n "$db_name" ]; then
                    restore_database "$backup_file" "$db_name"
                else
                    echo -e "${RED}Invalid selection${NC}"
                fi
                ;;
            18)
                echo -e "${YELLOW}Backup files:${NC}"
                ls -la "$BACKUP_DIR"/*.sql 2>/dev/null || echo "No backup files found"
                ;;
            19)
                echo -e "${YELLOW}Last 20 log entries:${NC}"
                tail -20 "$LOG_FILE"
                ;;
            20)
                echo -e "${GREEN}Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid option!${NC}"
                ;;
        esac
        
        read -p "Press Enter to continue..."
        clear
    done
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

# Check if MySQL is installed
if ! command -v mysql &> /dev/null; then
    echo -e "${RED}MySQL is not installed. Please install it first:${NC}"
    echo "sudo apt update && sudo apt install mysql-server"
    exit 1
fi

# Start the main menu
clear
echo -e "${GREEN}MySQL Server Manager Started${NC}"
echo -e "${YELLOW}Including database, table, and user deletion functions${NC}"
main_menu
