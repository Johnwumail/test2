#!/usr/bin/env python3
"""
Network Diagnostics Script

This script performs various network diagnostic tests and generates a report.
"""
import os
import sys
import socket
import subprocess
import platform
import argparse
import json
import time
from datetime import datetime
import ipaddress
from typing import Dict, Any, List, Optional, Tuple

def get_os_info() -> Dict[str, str]:
    """Get operating system information."""
    return {
        "system": platform.system(),
        "node": platform.node(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor()
    }

def get_ip_addresses() -> Dict[str, List[str]]:
    """Get IP addresses of the local machine."""
    hostname = socket.gethostname()
    ip_addresses = {
        "hostname": hostname,
        "ipv4": [],
        "ipv6": []
    }
    
    try:
        # Get all addresses for this hostname
        addr_info = socket.getaddrinfo(hostname, None)
        
        for addr in addr_info:
            family, _, _, _, sockaddr = addr
            ip = sockaddr[0]
            
            # Classify as IPv4 or IPv6
            if family == socket.AF_INET and ip not in ip_addresses["ipv4"]:
                ip_addresses["ipv4"].append(ip)
            elif family == socket.AF_INET6 and ip not in ip_addresses["ipv6"]:
                ip_addresses["ipv6"].append(ip)
                
        # Also add localhost addresses
        localhost_info = socket.getaddrinfo('localhost', None)
        for addr in localhost_info:
            family, _, _, _, sockaddr = addr
            ip = sockaddr[0]
            
            if family == socket.AF_INET and ip not in ip_addresses["ipv4"]:
                ip_addresses["ipv4"].append(ip)
            elif family == socket.AF_INET6 and ip not in ip_addresses["ipv6"]:
                ip_addresses["ipv6"].append(ip)
                
    except Exception as e:
        print(f"Error getting IP addresses: {e}")
    
    return ip_addresses

def ping_test(hosts: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Perform ping test to multiple hosts.
    
    Args:
        hosts: List of hosts to ping
        
    Returns:
        Dictionary with ping results for each host
    """
    results = {}
    
    for host in hosts:
        print(f"Pinging {host}...")
        ping_param = "-n" if platform.system().lower() == "windows" else "-c"
        ping_count = "4"
        
        try:
            # Execute ping command
            output = subprocess.check_output(
                ["ping", ping_param, ping_count, host],
                universal_newlines=True,
                stderr=subprocess.STDOUT,
                timeout=10
            )
            
            # Parse ping results
            packet_loss = "100%"
            min_time = max_time = avg_time = "N/A"
            
            if platform.system().lower() == "windows":
                # Parse Windows ping output
                for line in output.split("\n"):
                    if "loss" in line:
                        packet_loss = line.split("%")[0].split(" ")[-1] + "%"
                    if "Minimum" in line:
                        times = line.split(",")
                        min_time = times[0].split("=")[1].strip()
                        max_time = times[2].split("=")[1].strip()
                        avg_time = times[1].split("=")[1].strip()
            else:
                # Parse Linux/Unix ping output
                for line in output.split("\n"):
                    if "packet loss" in line:
                        packet_loss = line.split("%")[0].split(" ")[-1] + "%"
                    if "min/avg/max" in line:
                        times = line.split("=")[1].strip().split("/")
                        min_time = times[0] + " ms"
                        avg_time = times[1] + " ms"
                        max_time = times[2].split("/")[0] + " ms"
            
            results[host] = {
                "success": True,
                "packet_loss": packet_loss,
                "min_time": min_time,
                "max_time": max_time,
                "avg_time": avg_time,
                "output": output
            }
            
        except subprocess.CalledProcessError as e:
            results[host] = {
                "success": False,
                "error": "Ping failed",
                "output": e.output
            }
        except subprocess.TimeoutExpired:
            results[host] = {
                "success": False,
                "error": "Ping timed out",
                "output": "Command timed out after 10 seconds"
            }
        except Exception as e:
            results[host] = {
                "success": False,
                "error": str(e),
                "output": f"Unexpected error: {str(e)}"
            }
    
    return results

def traceroute_test(host: str) -> Dict[str, Any]:
    """
    Perform traceroute to a host.
    
    Args:
        host: Host to trace
        
    Returns:
        Dictionary with traceroute results
    """
    print(f"Tracing route to {host}...")
    
    # Determine the command to use based on the platform
    if platform.system().lower() == "windows":
        cmd = ["tracert", "-d", "-w", "1000", host]
    else:
        cmd = ["traceroute", "-n", "-w", "1", host]
    
    try:
        # Execute traceroute command
        output = subprocess.check_output(
            cmd,
            universal_newlines=True,
            stderr=subprocess.STDOUT,
            timeout=30
        )
        
        return {
            "success": True,
            "output": output
        }
        
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "error": "Traceroute failed",
            "output": e.output
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Traceroute timed out",
            "output": "Command timed out after 30 seconds"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "output": f"Unexpected error: {str(e)}"
        }

def dns_lookup(hosts: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Perform DNS lookup for multiple hosts.
    
    Args:
        hosts: List of hosts to look up
        
    Returns:
        Dictionary with DNS lookup results for each host
    """
    results = {}
    
    for host in hosts:
        print(f"Looking up DNS for {host}...")
        
        try:
            # Get address info
            addr_info = socket.getaddrinfo(host, None)
            
            ipv4_addresses = []
            ipv6_addresses = []
            
            for addr in addr_info:
                family, _, _, _, sockaddr = addr
                ip = sockaddr[0]
                
                if family == socket.AF_INET and ip not in ipv4_addresses:
                    ipv4_addresses.append(ip)
                elif family == socket.AF_INET6 and ip not in ipv6_addresses:
                    ipv6_addresses.append(ip)
            
            results[host] = {
                "success": True,
                "ipv4_addresses": ipv4_addresses,
                "ipv6_addresses": ipv6_addresses
            }
            
        except socket.gaierror as e:
            results[host] = {
                "success": False,
                "error": f"DNS lookup failed: {e}"
            }
        except Exception as e:
            results[host] = {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    return results

def port_scan(host: str, ports: List[int]) -> Dict[int, bool]:
    """
    Scan ports on a host.
    
    Args:
        host: Host to scan
        ports: List of ports to scan
        
    Returns:
        Dictionary with scan results for each port
    """
    print(f"Scanning ports on {host}...")
    results = {}
    
    for port in ports:
        print(f"  Checking port {port}...", end="")
        sys.stdout.flush()
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        
        try:
            result = sock.connect_ex((host, port))
            if result == 0:
                print(" Open")
                results[port] = True
            else:
                print(" Closed")
                results[port] = False
        except Exception as e:
            print(f" Error: {e}")
            results[port] = False
        finally:
            sock.close()
    
    return results

def http_check(urls: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Check HTTP status for multiple URLs.
    
    Args:
        urls: List of URLs to check
        
    Returns:
        Dictionary with HTTP check results for each URL
    """
    results = {}
    
    try:
        import requests
        
        for url in urls:
            print(f"Checking HTTP status for {url}...")
            
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                elapsed_time = time.time() - start_time
                
                results[url] = {
                    "success": True,
                    "status_code": response.status_code,
                    "reason": response.reason,
                    "elapsed_seconds": round(elapsed_time, 3),
                    "content_type": response.headers.get("Content-Type", ""),
                    "content_length": len(response.content)
                }
                
            except requests.RequestException as e:
                results[url] = {
                    "success": False,
                    "error": str(e)
                }
                
    except ImportError:
        print("Warning: 'requests' library not found. HTTP checks skipped.")
        for url in urls:
            results[url] = {
                "success": False,
                "error": "Requests library not available"
            }
    
    return results

def run_diagnostics(args):
    """
    Run network diagnostics and generate a report.
    
    Args:
        args: Command line arguments
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "os_info": get_os_info(),
        "local_ip_addresses": get_ip_addresses()
    }
    
    # Ping tests
    ping_hosts = args.ping_hosts.split(",") if args.ping_hosts else ["8.8.8.8", "1.1.1.1", "www.google.com"]
    report["ping_tests"] = ping_test(ping_hosts)
    
    # Traceroute
    if args.traceroute_host:
        report["traceroute"] = traceroute_test(args.traceroute_host)
    
    # DNS lookup
    dns_hosts = args.dns_hosts.split(",") if args.dns_hosts else ["www.google.com", "www.github.com", "www.microsoft.com"]
    report["dns_lookup"] = dns_lookup(dns_hosts)
    
    # Port scan
    if args.scan_host and args.scan_ports:
        ports = [int(p) for p in args.scan_ports.split(",")]
        report["port_scan"] = {
            "host": args.scan_host,
            "results": port_scan(args.scan_host, ports)
        }
    
    # HTTP check
    http_urls = args.http_urls.split(",") if args.http_urls else ["https://www.google.com", "https://www.github.com"]
    report["http_checks"] = http_check(http_urls)
    
    # Generate report
    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to {args.output}")
    else:
        # Print a summary to stdout
        print("\n=== Network Diagnostics Summary ===")
        
        print("\nLocal IP Addresses:")
        for ipv4 in report["local_ip_addresses"]["ipv4"]:
            print(f"  IPv4: {ipv4}")
        for ipv6 in report["local_ip_addresses"]["ipv6"]:
            print(f"  IPv6: {ipv6}")
        
        print("\nPing Results:")
        for host, result in report["ping_tests"].items():
            status = "Success" if result.get("success") else f"Failed: {result.get('error', 'Unknown error')}"
            if result.get("success"):
                print(f"  {host}: {status} (Packet Loss: {result.get('packet_loss')}, Avg Time: {result.get('avg_time')})")
            else:
                print(f"  {host}: {status}")
        
        print("\nDNS Lookup Results:")
        for host, result in report["dns_lookup"].items():
            if result.get("success"):
                ipv4 = ", ".join(result.get("ipv4_addresses", []))
                print(f"  {host}: Success (IPv4: {ipv4 or 'None'})")
            else:
                print(f"  {host}: Failed: {result.get('error', 'Unknown error')}")
        
        print("\nHTTP Check Results:")
        for url, result in report["http_checks"].items():
            if result.get("success"):
                print(f"  {url}: Status {result.get('status_code')} in {result.get('elapsed_seconds')}s")
            else:
                print(f"  {url}: Failed: {result.get('error', 'Unknown error')}")
    
    print("\nDiagnostics completed.")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Network Diagnostics Tool")
    
    parser.add_argument("--ping-hosts", type=str, help="Comma-separated list of hosts to ping")
    parser.add_argument("--traceroute-host", type=str, help="Host to run traceroute against")
    parser.add_argument("--dns-hosts", type=str, help="Comma-separated list of hosts for DNS lookup")
    parser.add_argument("--scan-host", type=str, help="Host to scan ports on")
    parser.add_argument("--scan-ports", type=str, help="Comma-separated list of ports to scan")
    parser.add_argument("--http-urls", type=str, help="Comma-separated list of URLs to check")
    parser.add_argument("--output", type=str, help="Output file for diagnostic report (JSON format)")
    
    args = parser.parse_args()
    
    try:
        run_diagnostics(args)
    except KeyboardInterrupt:
        print("\nDiagnostics interrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError running diagnostics: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 