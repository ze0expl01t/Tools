#!/usr/bin/env python3
"""
Enhanced Linux Automation Script
Comprehensive automation tasks for Linux systems using Python
"""

import os
import sys
import subprocess
import time
import shutil
from datetime import datetime
import json
import re
import pwd
import grp
import stat
import socket
import platform


class LinuxAutomation:

  def __init__(self):
    self.log_file = "automation.log"
    self.ensure_log_directory()

  def ensure_log_directory(self):
    """Ensure log directory exists"""
    log_dir = os.path.dirname(os.path.abspath(
        self.log_file)) if os.path.dirname(self.log_file) else "."
    os.makedirs(log_dir, exist_ok=True)

  def log_message(self, message):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    with open(self.log_file, "a") as f:
      f.write(log_entry + "\n")

  def get_linux_distribution(self):
    """Get Linux distribution information"""
    try:
      # Try to read /etc/os-release
      if os.path.exists('/etc/os-release'):
        with open('/etc/os-release', 'r') as f:
          lines = f.readlines()
          info = {}
          for line in lines:
            if '=' in line:
              key, value = line.strip().split('=', 1)
              info[key] = value.strip('"')
          return info.get('PRETTY_NAME', 'Unknown Linux')

      # Fallback to platform module
      return platform.platform()
    except:
      return "Unknown Linux Distribution"

  def system_info(self):
    """Gather comprehensive system information"""
    self.log_message("=== System Information ===")

    # Get serial number from DMI
    serial_number = "Unknown"
    try:
      result = subprocess.run(['cat', '/sys/class/dmi/id/product_serial'],
                              capture_output=True,
                              text=True)
      if result.returncode == 0:
        serial_number = result.stdout.strip()
    except:
      try:
        result = subprocess.run(['dmidecode', '-s', 'system-serial-number'],
                                capture_output=True,
                                text=True)
        if result.returncode == 0:
          serial_number = result.stdout.strip()
      except:
        pass

    # Get full hostname with domain
    full_hostname = "Unknown"
    try:
      full_hostname = socket.getfqdn()
    except:
      full_hostname = os.uname().nodename

    # Get system uptime
    uptime = "Unknown"
    try:
      with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
        uptime = f"{uptime_seconds / 3600:.2f} hours"
    except:
      pass

    # Get load average
    load_avg = "Unknown"
    try:
      load_avg = os.getloadavg()
      load_avg = f"1min: {load_avg[0]:.2f}, 5min: {load_avg[1]:.2f}, 15min: {load_avg[2]:.2f}"
    except:
      pass

    # Get system info
    info = {
        "hostname": os.uname().nodename,
        "full_hostname": full_hostname,
        "serial_number": serial_number,
        "distribution": self.get_linux_distribution(),
        "kernel": os.uname().release,
        "architecture": os.uname().machine,
        "current_user": os.getenv("USER", "unknown"),
        "user_id": os.getuid() if hasattr(os, 'getuid') else "N/A",
        "group_id": os.getgid() if hasattr(os, 'getgid') else "N/A",
        "current_directory": os.getcwd(),
        "python_version": sys.version.split()[0],
        "system_uptime": uptime,
        "load_average": load_avg
    }

    for key, value in info.items():
      self.log_message(f"{key}: {value}")

    return info

  def check_services(self, services=None):
    """Check status of system services"""
    if services is None:
      services = ['ssh', 'cron', 'NetworkManager', 'systemd-resolved']

    self.log_message("=== Service Status Check ===")

    service_status = {}
    for service in services:
      try:
        result = subprocess.run(['systemctl', 'is-active', service],
                                capture_output=True,
                                text=True)
        status = result.stdout.strip()
        service_status[service] = status
        self.log_message(f"Service {service}: {status}")
      except Exception as e:
        service_status[service] = f"Error: {e}"
        self.log_message(f"Service {service}: Error checking - {e}")

    return service_status

  def disk_usage_check(self, paths=None):
    """Check disk usage for multiple paths"""
    if paths is None:
      paths = ["/", "/home", "/tmp", "/var"]

    self.log_message("=== Disk Usage Check ===")

    disk_info = {}
    for path in paths:
      if os.path.exists(path):
        try:
          total, used, free = shutil.disk_usage(path)

          # Convert to GB
          total_gb = total // (1024**3)
          used_gb = used // (1024**3)
          free_gb = free // (1024**3)
          usage_percent = (used / total) * 100

          disk_info[path] = {
              'total_gb': total_gb,
              'used_gb': used_gb,
              'free_gb': free_gb,
              'usage_percent': usage_percent
          }

          self.log_message(f"{path}: {total_gb}GB total, {used_gb}GB used, "
                           f"{free_gb}GB free ({usage_percent:.1f}%)")

          if usage_percent > 80:
            self.log_message(f"WARNING: {path} usage is above 80%!")

        except Exception as e:
          self.log_message(f"Error checking disk usage for {path}: {e}")

    return disk_info

  def memory_check(self):
    """Check memory usage"""
    self.log_message("=== Memory Usage Check ===")

    try:
      with open('/proc/meminfo', 'r') as f:
        meminfo = {}
        for line in f:
          key, value = line.split(':', 1)
          meminfo[key.strip()] = value.strip()

      total_kb = int(meminfo['MemTotal'].split()[0])
      available_kb = int(meminfo['MemAvailable'].split()[0])
      used_kb = total_kb - available_kb

      total_gb = total_kb / (1024 * 1024)
      available_gb = available_kb / (1024 * 1024)
      used_gb = used_kb / (1024 * 1024)
      usage_percent = (used_kb / total_kb) * 100

      self.log_message(
          f"Total: {total_gb:.2f}GB, Used: {used_gb:.2f}GB, "
          f"Available: {available_gb:.2f}GB ({usage_percent:.1f}%)")

      if usage_percent > 85:
        self.log_message("WARNING: Memory usage is above 85%!")

      return {
          'total_gb': total_gb,
          'used_gb': used_gb,
          'available_gb': available_gb,
          'usage_percent': usage_percent
      }

    except Exception as e:
      self.log_message(f"Error checking memory: {e}")
      return None

  def process_monitor(self, process_names=None):
    """Monitor multiple processes"""
    if process_names is None:
      process_names = ['python', 'ssh', 'cron']

    self.log_message("=== Process Monitoring ===")

    process_info = {}
    for process_name in process_names:
      try:
        result = subprocess.run(['pgrep', '-f', process_name],
                                capture_output=True,
                                text=True)

        if result.returncode == 0:
          pids = result.stdout.strip().split('\n')
          process_info[process_name] = {
              'running': True,
              'pids': pids,
              'count': len(pids)
          }
          self.log_message(
              f"Process '{process_name}': Running ({len(pids)} instances) - PIDs: {', '.join(pids)}"
          )
        else:
          process_info[process_name] = {
              'running': False,
              'pids': [],
              'count': 0
          }
          self.log_message(f"Process '{process_name}': Not running")

      except Exception as e:
        self.log_message(f"Error monitoring process '{process_name}': {e}")

    return process_info

  def network_interfaces(self):
    """Get network interface information"""
    self.log_message("=== Network Interfaces ===")

    interfaces = {}
    try:
      result = subprocess.run(['ip', 'addr', 'show'],
                              capture_output=True,
                              text=True)

      if result.returncode == 0:
        current_interface = None
        for line in result.stdout.split('\n'):
          if re.match(r'^\d+:', line):
            # New interface
            parts = line.split()
            if_name = parts[1].rstrip(':')
            current_interface = if_name
            interfaces[if_name] = {'addresses': []}
            self.log_message(f"Interface: {if_name}")
          elif 'inet ' in line and current_interface:
            # IPv4 address
            ip_match = re.search(r'inet (\S+)', line)
            if ip_match:
              interfaces[current_interface]['addresses'].append(
                  ip_match.group(1))
              self.log_message(f"  IPv4: {ip_match.group(1)}")

    except Exception as e:
      self.log_message(f"Error getting network interfaces: {e}")

    return interfaces

  def check_failed_logins(self, days=7):
    """Check for failed login attempts in the last N days"""
    self.log_message(f"=== Checking failed logins in last {days} days ===")

    # Common log files to check for failed logins
    log_files = [
        '/var/log/auth.log', '/var/log/secure', '/var/log/messages',
        '/var/log/faillog'
    ]

    failed_attempts = []

    for log_file in log_files:
      try:
        if os.path.exists(log_file) and os.access(log_file, os.R_OK):
          self.log_message(f"Checking {log_file}")

          with open(log_file, 'r') as f:
            for line in f:
              # Look for common failed login patterns
              if any(pattern in line.lower() for pattern in [
                  'failed password', 'authentication failure', 'invalid user',
                  'failed login', 'login incorrect',
                  'pam_unix(sshd:auth): authentication failure'
              ]):
                failed_attempts.append({
                    'log_file':
                    log_file,
                    'entry':
                    line.strip(),
                    'timestamp':
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

      except PermissionError:
        self.log_message(f"Permission denied accessing {log_file}")
      except Exception as e:
        self.log_message(f"Error reading {log_file}: {e}")

    # Alternative method using 'lastb' command for failed logins
    try:
      result = subprocess.run(['lastb', '-n', '20'],
                              capture_output=True,
                              text=True)
      if result.returncode == 0 and result.stdout.strip():
        self.log_message("Recent failed login attempts from 'lastb' command:")
        for line in result.stdout.strip().split('\n'):
          if line.strip() and not line.startswith('btmp begins'):
            failed_attempts.append({
                'source':
                'lastb',
                'entry':
                line.strip(),
                'timestamp':
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            self.log_message(f"Failed login: {line.strip()}")
    except Exception as e:
      self.log_message(f"Could not run 'lastb' command: {e}")

    # Summary
    if failed_attempts:
      self.log_message(
          f"ALERT: Found {len(failed_attempts)} failed login attempts")

      # Save detailed report
      report_file = f"failed_logins_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
      with open(report_file, 'w') as f:
        json.dump(failed_attempts, f, indent=2)
      self.log_message(f"Detailed report saved to: {report_file}")

      # Count unique IPs if possible
      unique_sources = set()
      for attempt in failed_attempts:
        entry = attempt['entry']
        ip_match = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', entry)
        if ip_match:
          unique_sources.add(ip_match.group())

      if unique_sources:
        self.log_message(
            f"Failed attempts from {len(unique_sources)} unique sources: {', '.join(list(unique_sources)[:5])}"
        )
    else:
      self.log_message(f"No failed login attempts found")

    return failed_attempts

  def list_users(self):
    """List system users and their information"""
    self.log_message("=== System Users ===")

    users_info = []
    try:
      # Read /etc/passwd to get user information
      with open('/etc/passwd', 'r') as f:
        for line in f:
          if line.strip():
            parts = line.strip().split(':')
            if len(parts) >= 7:
              user_info = {
                  'username': parts[0],
                  'uid': int(parts[2]),
                  'gid': int(parts[3]),
                  'description': parts[4],
                  'home_dir': parts[5],
                  'shell': parts[6]
              }
              
              # Check if user has login shell
              login_shells = ['/bin/bash', '/bin/sh', '/bin/zsh', '/bin/fish', '/usr/bin/bash']
              user_info['can_login'] = user_info['shell'] in login_shells
              
              # Check if home directory exists
              user_info['home_exists'] = os.path.exists(user_info['home_dir'])
              
              users_info.append(user_info)
              
              self.log_message(f"User: {user_info['username']} (UID: {user_info['uid']}, "
                             f"Shell: {user_info['shell']}, Home: {user_info['home_dir']})")

      # Count different types of users
      regular_users = [u for u in users_info if u['uid'] >= 1000 and u['can_login']]
      system_users = [u for u in users_info if u['uid'] < 1000]
      service_users = [u for u in users_info if u['uid'] >= 1000 and not u['can_login']]

      self.log_message(f"Total users: {len(users_info)}")
      self.log_message(f"Regular users: {len(regular_users)}")
      self.log_message(f"System users: {len(system_users)}")
      self.log_message(f"Service users: {len(service_users)}")

      # List users with login capabilities
      if regular_users:
        self.log_message("Users with login access:")
        for user in regular_users:
          self.log_message(f"  - {user['username']} (UID: {user['uid']})")

    except Exception as e:
      self.log_message(f"Error reading user information: {e}")

    return users_info

  def check_file_permissions(self, critical_files=None):
    """Check permissions on critical system files"""
    if critical_files is None:
      critical_files = [
          '/etc/passwd', '/etc/shadow', '/etc/sudoers', '/etc/ssh/sshd_config',
          '/etc/crontab'
      ]

    self.log_message("=== Critical File Permissions ===")

    permission_issues = []
    for file_path in critical_files:
      try:
        if os.path.exists(file_path):
          file_stat = os.stat(file_path)
          mode = stat.filemode(file_stat.st_mode)
          owner = pwd.getpwuid(file_stat.st_uid).pw_name
          group = grp.getgrgid(file_stat.st_gid).gr_name

          self.log_message(f"{file_path}: {mode} {owner}:{group}")

          # Check for potential security issues
          if file_path == '/etc/shadow' and (file_stat.st_mode & 0o077):
            permission_issues.append(f"{file_path} is readable by others")
          elif file_path == '/etc/passwd' and (file_stat.st_mode & 0o002):
            permission_issues.append(f"{file_path} is writable by others")

        else:
          self.log_message(f"{file_path}: File not found")

      except Exception as e:
        self.log_message(f"Error checking {file_path}: {e}")

    if permission_issues:
      self.log_message("SECURITY WARNINGS:")
      for issue in permission_issues:
        self.log_message(f"  - {issue}")

    return permission_issues

  def system_cleanup(self):
    """Perform system cleanup tasks"""
    self.log_message("=== System Cleanup ===")

    cleanup_tasks = {'old_logs': 0, 'temp_files': 0, 'package_cache': 0}

    # Clean old log files (older than 30 days)
    log_dirs = ['/var/log', '/tmp']
    for log_dir in log_dirs:
      if os.path.exists(log_dir):
        try:
          for root, dirs, files in os.walk(log_dir):
            for file in files:
              if file.endswith(('.log', '.old', '.1', '.2', '.3')):
                file_path = os.path.join(root, file)
                try:
                  file_stat = os.stat(file_path)
                  file_age = time.time() - file_stat.st_mtime
                  if file_age > 30 * 24 * 3600:  # 30 days
                    # Don't actually delete, just count
                    cleanup_tasks['old_logs'] += 1
                    self.log_message(f"Old log file found: {file_path}")
                except:
                  pass
        except Exception as e:
          self.log_message(f"Error checking {log_dir}: {e}")

    # Count temporary files
    temp_dirs = ['/tmp', '/var/tmp']
    for temp_dir in temp_dirs:
      if os.path.exists(temp_dir):
        try:
          for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            if os.path.isfile(item_path):
              try:
                file_stat = os.stat(item_path)
                file_age = time.time() - file_stat.st_mtime
                if file_age > 7 * 24 * 3600:  # 7 days
                  cleanup_tasks['temp_files'] += 1
              except:
                pass
        except Exception as e:
          self.log_message(f"Error checking {temp_dir}: {e}")

    self.log_message(f"Cleanup summary:")
    self.log_message(f"  Old log files: {cleanup_tasks['old_logs']}")
    self.log_message(f"  Old temp files: {cleanup_tasks['temp_files']}")

    return cleanup_tasks

  def generate_system_report(self):
        """Generate comprehensive system report"""
        self.log_message("=== Generating System Report ===")

        report = {
            'timestamp': datetime.now().isoformat(),
            'system_info': self.system_info(),
            'disk_usage': self.disk_usage_check(),
            'memory_usage': self.memory_check(),
            'network_interfaces': self.network_interfaces(),
            'process_status': self.process_monitor(),
            'service_status': self.check_services(),
            'users': self.list_users(),
            'security_check': {
                'failed_logins': len(self.check_failed_logins()),
                'permission_issues': self.check_file_permissions()
            },
            'cleanup_recommendations': self.system_cleanup()
        }

        # Save JSON report to file
        report_file = f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        self.log_message(f"System report saved to: {report_file}")

        # Save readable text report to report_monitoring.txt
        self.save_monitoring_report(report)

        return report

  def save_monitoring_report(self, report):
        """Save monitoring report to report_monitoring.txt"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open("report_monitoring.txt", "w") as f:
            f.write("=" * 80 + "\n")
            f.write(f"SYSTEM MONITORING REPORT - {timestamp}\n")
            f.write("=" * 80 + "\n\n")

            # System Information
            f.write("SYSTEM INFORMATION:\n")
            f.write("-" * 40 + "\n")
            sys_info = report['system_info']
            f.write(f"Hostname: {sys_info['hostname']}\n")
            f.write(f"Full Hostname: {sys_info['full_hostname']}\n")
            f.write(f"Serial Number: {sys_info['serial_number']}\n")
            f.write(f"Distribution: {sys_info['distribution']}\n")
            f.write(f"Kernel: {sys_info['kernel']}\n")
            f.write(f"Architecture: {sys_info['architecture']}\n")
            f.write(f"Current User: {sys_info['current_user']}\n")
            f.write(f"Python Version: {sys_info['python_version']}\n")
            f.write(f"System Uptime: {sys_info['system_uptime']}\n")
            f.write(f"Load Average: {sys_info['load_average']}\n\n")

            # Memory Usage
            f.write("MEMORY USAGE:\n")
            f.write("-" * 40 + "\n")
            mem = report['memory_usage']
            if mem:
                f.write(f"Total: {mem['total_gb']:.2f} GB\n")
                f.write(f"Used: {mem['used_gb']:.2f} GB\n")
                f.write(f"Available: {mem['available_gb']:.2f} GB\n")
                f.write(f"Usage: {mem['usage_percent']:.1f}%\n")
                if mem['usage_percent'] > 85:
                    f.write("âš ï¸  WARNING: High memory usage!\n")
            f.write("\n")

            # Disk Usage
            f.write("DISK USAGE:\n")
            f.write("-" * 40 + "\n")
            for path, disk_info in report['disk_usage'].items():
                f.write(f"{path}:\n")
                f.write(f"  Total: {disk_info['total_gb']} GB\n")
                f.write(f"  Used: {disk_info['used_gb']} GB\n")
                f.write(f"  Free: {disk_info['free_gb']} GB\n")
                f.write(f"  Usage: {disk_info['usage_percent']:.1f}%\n")
                if disk_info['usage_percent'] > 80:
                    f.write("  âš ï¸  WARNING: High disk usage!\n")
                f.write("\n")

            # Process Status
            f.write("PROCESS STATUS:\n")
            f.write("-" * 40 + "\n")
            for process, status in report['process_status'].items():
                f.write(f"{process}: ")
                if status['running']:
                    f.write(f"Running ({status['count']} instances) - PIDs: {', '.join(status['pids'])}\n")
                else:
                    f.write("Not running\n")
            f.write("\n")

            # Service Status
            f.write("SERVICE STATUS:\n")
            f.write("-" * 40 + "\n")
            for service, status in report['service_status'].items():
                f.write(f"{service}: {status}\n")
            f.write("\n")

            # Users
            f.write("SYSTEM USERS:\n")
            f.write("-" * 40 + "\n")
            users = report['users']
            if users:
                regular_users = [u for u in users if u['uid'] >= 1000 and u['can_login']]
                system_users = [u for u in users if u['uid'] < 1000]
                service_users = [u for u in users if u['uid'] >= 1000 and not u['can_login']]

                f.write(f"Total users: {len(users)}\n")
                f.write(f"Regular users: {len(regular_users)}\n")
                f.write(f"System users: {len(system_users)}\n")
                f.write(f"Service users: {len(service_users)}\n\n")

                if regular_users:
                    f.write("Regular users with login access:\n")
                    for user in regular_users:
                        f.write(f"  {user['username']} (UID: {user['uid']}, Home: {user['home_dir']})\n")
                        f.write(f"    Shell: {user['shell']}, Home exists: {user['home_exists']}\n")
                    f.write("\n")

                if service_users:
                    f.write("Service users (no login):\n")
                    for user in service_users[:10]:  # Show first 10 service users
                        f.write(f"  {user['username']} (UID: {user['uid']}, Shell: {user['shell']})\n")
                    if len(service_users) > 10:
                        f.write(f"  ... and {len(service_users) - 10} more service users\n")
                    f.write("\n")
            else:
                f.write("No user information available\n\n")

            # Security Check
            f.write("SECURITY CHECK:\n")
            f.write("-" * 40 + "\n")
            security = report['security_check']
            f.write(f"Failed login attempts: {security['failed_logins']}\n")

            if security['permission_issues']:
                f.write("âš ï¸  SECURITY WARNINGS:\n")
                for issue in security['permission_issues']:
                    f.write(f"  - {issue}\n")
            else:
                f.write("âœ… No permission issues found\n")
            f.write("\n")

            # Cleanup Recommendations
            f.write("CLEANUP RECOMMENDATIONS:\n")
            f.write("-" * 40 + "\n")
            cleanup = report['cleanup_recommendations']
            f.write(f"Old log files: {cleanup['old_logs']}\n")
            f.write(f"Old temp files: {cleanup['temp_files']}\n")
            f.write(f"Package cache: {cleanup['package_cache']}\n")
            f.write("\n")

            # Network Interfaces
            f.write("NETWORK INTERFACES:\n")
            f.write("-" * 40 + "\n")
            networks = report['network_interfaces']
            if networks:
                for interface, info in networks.items():
                    f.write(f"{interface}:\n")
                    for addr in info['addresses']:
                        f.write(f"  IP: {addr}\n")
            else:
                f.write("No network interface information available\n")
            f.write("\n")

            f.write("=" * 80 + "\n")
            f.write("Report generation completed\n")
            f.write("=" * 80 + "\n")

        self.log_message("Monitoring report saved to: report_monitoring.txt")

  def run_command(self, command, timeout=30):
    """Execute shell command with timeout"""
    self.log_message(f"=== Executing command: {command} ===")

    try:
      result = subprocess.run(command,
                              shell=True,
                              capture_output=True,
                              text=True,
                              timeout=timeout)

      if result.returncode == 0:
        self.log_message(f"Command output:\n{result.stdout}")
        return result.stdout
      else:
        self.log_message(
            f"Command failed (exit code {result.returncode}):\n{result.stderr}"
        )
        return None

    except subprocess.TimeoutExpired:
      self.log_message(f"Command timed out after {timeout} seconds")
      return None
    except Exception as e:
      self.log_message(f"Error executing command: {e}")
      return None


def main():
  """Main automation function"""
  automation = LinuxAutomation()

  print("Enhanced Linux Automation Script Starting...")
  print("=" * 60)

  # Generate comprehensive system report
  automation.generate_system_report()

  print("=" * 60)
  print("Linux automation script completed!")
  print(f"Check {automation.log_file} for detailed logs")
  print("System report files have been generated in the current directory")


if __name__ == "__main__":
  main()
