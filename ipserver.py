#!/usr/bin/env python3
"""
ipserver.py - A simple web server that returns the current external IP address.

This script sets up a lightweight HTTP server on 127.0.0.1:8000 that returns
the current external IP address when queried. The IP address is fetched only
when a request is made to ensure it's always up-to-date.

Usage:
    python3 ipserver.py
    
    Then access http://{HOST}:{PORT} in your browser or use curl:
    curl http://{HOST}:{PORT}
"""

from dotenv import load_dotenv
import http.server
import os
from pathlib import Path
import socketserver
import subprocess
import sys
import logging
from urllib.error import URLError
import urllib.request
from typing import Optional

env_path = Path('/opt/myapp/.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ipserver')

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print("Environment variables loaded from /opt/myapp/.env")
else:
    logger.error("Failed to find .env file")

def send_gotify_notification(title: str, message: str, priority: int = 5) -> bool:
    """
    Send a notification to Gotify.
    
    Args:
        title (str): Notification title
        message (str): Notification message
        priority (int): Priority level (default 5)
        
    Returns:
        bool: True if notification was sent successfully, False otherwise
    """
    gotify_token = os.environ.get('GOTIFY_TOKEN')
    gotify_url = os.environ.get('GOTIFY_URL')
    
    if not gotify_token:
        logger.warning("GOTIFY_TOKEN environment variable not set, skipping notification")
        return False
    
    try:
        url = f"{gotify_url}?token={gotify_token}"
        data = urllib.parse.urlencode({
            'title': title,
            'message': message,
            'priority': str(priority)
        }).encode('utf-8')
        
        req = urllib.request.Request(url, data=data, method='POST')
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                logger.debug(f"Gotify notification sent: {title}")
                return True
            else:
                logger.warning(f"Gotify notification failed with status: {response.status}")
                return False
    except Exception as e:
        logger.warning(f"Failed to send Gotify notification: {e}")
        return False

class IPHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler that returns the external IP address."""
    
    def do_GET(self):
        """Handle GET requests by returning the current external IP."""
        ip_address = self.get_external_ip()
        
        if ip_address:
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"{ip_address}\n".encode('utf-8'))
            logger.info(f"Served IP address: {ip_address}")
        else:
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Error: Could not retrieve external IP address\n")
            logger.error("Failed to serve IP address")
            send_gotify_notification(
                title="IP Server Error",
                message="Failed to retrieve external IP address from all services",
                priority=6
            )            
    
    def log_message(self, format, *args):
        """Override log_message to use our logger instead."""
        logger.info(f"{self.client_address[0]} - {format%args}")
    
    def get_external_ip(self) -> Optional[str]:
        """
        Fetch the current external IP address using multiple methods.
        
        Returns:
            str or None: The external IP address if successful, None otherwise.
        """
        # List of services to try for fetching IP address
        ip_services = [
            "https://ifconfig.me/ip",
            "https://api.ipify.org",
            "https://icanhazip.com"
        ]
        
        # Try using urllib first (more reliable generally)
        for service in ip_services:
            try:
                logger.debug(f"Trying to fetch IP from {service}")
                with urllib.request.urlopen(service, timeout=5) as response:
                    ip_address = response.read().decode('utf-8').strip()
                    if ip_address and self.is_valid_ip(ip_address):
                        return ip_address
            except (URLError, TimeoutError) as e:
                logger.debug(f"Failed to fetch IP from {service}: {e}")
                continue
        
        # Fallback to curl if urllib methods failed
        try:
            logger.debug("Trying to fetch IP using curl")
            for service in ip_services:
                result = subprocess.run(
                    ["curl", "-s", service],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                ip_address = result.stdout.strip()
                if result.returncode == 0 and ip_address and self.is_valid_ip(ip_address):
                    return ip_address
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logger.debug(f"Curl method failed: {e}")
        
        logger.error("All methods to fetch external IP failed")
        return None
    
    def is_valid_ip(self, ip: str) -> bool:
        """
        Very basic validation for IP address format.
        
        Args:
            ip (str): The IP address to validate
            
        Returns:
            bool: True if the format looks valid, False otherwise
        """
        parts = ip.split('.')
        
        # Simple check for IPv4 format - could be enhanced for IPv6 support
        if len(parts) != 4:
            return False
            
        for part in parts:
            try:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            except ValueError:
                return False
                
        return True

def main():
    """Set up and start the IP address web server."""
    HOST=os.environ.get('HOST')
    PORT=os.environ.get('PORT')
    server_address = (HOST, PORT)
    
    try:
        with socketserver.TCPServer(server_address, IPHandler) as httpd:
            host, port = server_address
            logger.info(f"Starting IP server on {host}:{port}")
            logger.info(f"Access http://{host}:{port} to see your external IP")
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received, shutting down server")
                httpd.server_close()
                sys.exit(0)
    except OSError as e:
        error_msg = f"Could not start server: {e}"
        logger.error(error_msg)
        send_gotify_notification(
            title="IP Server Startup Failed",
            message=error_msg,
            priority=6
        )        
        sys.exit(1)

if __name__ == "__main__":
    main()