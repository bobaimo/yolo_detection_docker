#!/usr/bin/env python

import requests
import time
import json
import threading


class DetectionReader:
    """Class to continuously read detections from the HTTP server as a background thread."""

    def __init__(self, server_url, poll_interval=1.0, auto_start=True):
        """
        Initialize the detection reader and optionally start it as a thread.

        Args:
            server_url: The URL of the detection server (e.g., 'http://localhost:8080')
            poll_interval: Time in seconds between GET requests (default: 1.0)
            auto_start: Whether to automatically start the reader thread (default: True)
        """
        self.server_url = server_url.rstrip('/')
        self.endpoint = f"{self.server_url}/api/detections"
        self.poll_interval = poll_interval
        self.running = False
        self.last_detection = None
        self.thread = None
        self.pathname=""
        self.lock = threading.Lock()

        if auto_start:
            self.start_reading()

    def get_detection(self):
        """
        Perform a GET request to retrieve the newest detection.

        Returns:
            dict: The detection data, or None if request fails
        """
        try:
            response = requests.get(self.endpoint, timeout=5)

            if response.status_code == 200:
                data = response.json()

                if data.get('status') == 'success':
                    if 'detection' in data:
                        return data['detection']
                    else:
                        print("No detections available")
                        return None
                else:
                    print("Server returned error status")
                    return None
            else:
                print(f"HTTP error: {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            return None

    def extract_pathname(self, detection):
        """
        Extract the pathname from a detection object.

        Args:
            detection: The detection dictionary

        Returns:
            str: The pathname if found, None otherwise
        """
        if detection is None:
            return None

        # Adjust this based on your actual detection structure
        # Common patterns:
        self.pathname = detection.get('InPathName')

        return self.pathname

    def _reading_loop(self):
        """Internal method that runs the continuous reading loop."""
        print(f"Detection reader thread started. Polling {self.endpoint} every {self.poll_interval}s")

        try:
            while self.running:
                detection = self.get_detection()

                if detection:
                    pathname = self.extract_pathname(detection)

                    if pathname:
                        #print(f"Pathname: {pathname}")
                        # Store the detection for further processing if needed
                        with self.lock:
                            self.last_detection = detection
                    else:
                        print("Detection received but no pathname found")
                        print(f"Detection data: {detection}")

                time.sleep(self.poll_interval)

        except Exception as e:
            print(f"Error in reading loop: {e}")
        finally:
            print("Detection reader thread stopped")

    def start_reading(self):
        """Start continuously reading detections from the server in a background thread."""
        if self.running:
            print("Detection reader is already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._reading_loop, daemon=True)
        self.thread.start()
        print("Detection reader started as background thread")

    def stop_reading(self):
        """Stop the continuous reading."""
        if not self.running:
            return

        print("Stopping detection reader...")
        self.running = False

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

    def get_last_detection(self):
        """
        Get the last stored detection in a thread-safe manner.

        Returns:
            dict: The last detection, or None if no detections yet
        """
        with self.lock:
            return self.last_detection

    def cleanup(self):
        """Clean up resources."""
        self.stop_reading()
        print("Detection reader cleaned up")


def main():
    # Configure your server URL here
    SERVER_URL = "http://43.199.222.97:8081"
    POLL_INTERVAL = 1.0  # seconds

    # Create reader - it will automatically start as a thread
    reader = DetectionReader(SERVER_URL, POLL_INTERVAL, auto_start=True)

    try:
        # Keep the main thread alive
        print("Main thread running. Press Ctrl+C to stop")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        reader.cleanup()


if __name__ == '__main__':
    main()
