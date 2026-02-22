# ipserver

A simple, lightweight web server that returns your current external IP address.

`ipserver` is a Python script that sets up a local HTTP server to provide your machine's external IP address. It's useful for scenarios where you need to quickly check your public IP from a remote location, integrate with dynamic DNS updates, or simply monitor changes. The IP address is fetched dynamically upon each request, ensuring it's always up-to-date.

## Features

*   **Dynamic IP Retrieval:** Fetches the external IP address on demand from multiple reliable services (`ifconfig.me`, `api.ipify.org`, `icanhazip.com`).
*   **Fallback Mechanism:** Tries `urllib` first, then falls back to `curl` if `urllib` methods fail.
*   **Configurable Host and Port:** Uses environment variables to set the server's listening address and port.
*   **Gotify Notifications (Optional):** Can send notifications to a Gotify server on startup failures or IP retrieval errors.
*   **Lightweight:** Based on Python's built-in `http.server` module.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

*   Python 3.x
*   (Optional for `curl` fallback) `curl` command-line tool installed on your system.
*   (Optional for Gotify) A running Gotify server and an application token.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/peveleigh/ipserver.git
    cd ipserver
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

`ipserver` uses environment variables for configuration. You can set these directly in your shell or, more conveniently, using a `.env` file.

Create a file named `.env` in the project root directory with the following content:

```ini
# Server configuration
HOST=100.64.0.2  # Or 0.0.0.0 to listen on all interfaces
PORT=8000

# Optional: Gotify notification settings
# GOTIFY_URL=https://gotify.example.com
# GOTIFY_TOKEN=your_gotify_application_token
