import requests
import time
import threading

# Configuration
# Use port-forward: kubectl port-forward -n python-demo-app svc/demo-flask-app-for-autoscaling-service 8080:80
URL = "http://localhost:8080/api/hello" # Replace with your service URL
TOTAL_THREADS = 50  # Increase this to scale higher

def send_requests():
    print(f"Thread started...")
    while True:
        try:
            # Mimic 20 requests per second per thread
            response = requests.get(URL, timeout=1)
            time.sleep(0.05) 
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    print(f"Starting load test on {URL}...")
    threads = []
    
    # Ramp up: Add 5 threads every 10 seconds
    for i in range(0, TOTAL_THREADS, 5):
        for _ in range(5):
            t = threading.Thread(target=send_requests)
            t.daemon = True
            t.start()
            threads.append(t)
        
        print(f"Current Load: {len(threads)} threads active...")
        time.sleep(10)

    # Keep the script running
    while True:
        time.sleep(1)