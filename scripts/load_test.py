#!/usr/bin/env python3
import argparse
import concurrent.futures
import json
import time
import uuid
from datetime import datetime
import requests
import statistics

class LoadTester:
    def __init__(self, base_url, concurrent_users=50, test_duration=300):
        self.base_url = base_url.rstrip('/')
        self.concurrent_users = concurrent_users
        self.test_duration = test_duration
        self.response_times = []
        self.success_count = 0
        self.error_count = 0
        self.total_requests = 0

    def make_request(self):
        """Make a single TTS request and measure response time"""
        request_id = str(uuid.uuid4())
        payload = {
            "text": "This is a load test request " + request_id,
            "voice": "en-US-JennyNeural",
            "pitch": 0,
            "speed": 1.0,
            "volume_envelope": 1.0,
            "clean_audio": True
        }

        start_time = time.time()
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/tts",
                json=payload,
                timeout=30
            )
            end_time = time.time()
            duration = end_time - start_time

            if response.status_code == 200:
                self.response_times.append(duration)
                self.success_count += 1
            else:
                self.error_count += 1
                print(f"Error: {response.status_code} - {response.text}")

        except Exception as e:
            self.error_count += 1
            print(f"Request failed: {str(e)}")

        self.total_requests += 1

    def run_test(self):
        """Run the load test with concurrent users"""
        print(f"Starting load test with {self.concurrent_users} concurrent users for {self.test_duration} seconds")
        print(f"Target: {self.base_url}/api/v1/tts")

        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrent_users) as executor:
            futures = []
            while time.time() - start_time < self.test_duration:
                if len(futures) < self.concurrent_users:
                    futures.append(executor.submit(self.make_request))

                # Clean up completed futures
                futures = [f for f in futures if not f.done()]

            # Wait for remaining requests to complete
            concurrent.futures.wait(futures)

    def generate_report(self):
        """Generate test results report"""
        if not self.response_times:
            print("No successful requests to generate report")
            return

        avg_response_time = statistics.mean(self.response_times)
        p95_response_time = statistics.quantiles(self.response_times, n=20)[18]  # 95th percentile
        p99_response_time = statistics.quantiles(self.response_times, n=100)[98]  # 99th percentile

        requests_per_second = self.total_requests / self.test_duration
        requests_per_hour = requests_per_second * 3600

        report = {
            "timestamp": datetime.now().isoformat(),
            "test_duration": self.test_duration,
            "concurrent_users": self.concurrent_users,
            "total_requests": self.total_requests,
            "successful_requests": self.success_count,
            "failed_requests": self.error_count,
            "requests_per_second": round(requests_per_second, 2),
            "requests_per_hour": int(requests_per_hour),
            "average_response_time": round(avg_response_time, 2),
            "p95_response_time": round(p95_response_time, 2),
            "p99_response_time": round(p99_response_time, 2),
            "min_response_time": round(min(self.response_times), 2),
            "max_response_time": round(max(self.response_times), 2)
        }

        print("\nLoad Test Report")
        print("===============")
        print(f"Test Duration: {report['test_duration']} seconds")
        print(f"Concurrent Users: {report['concurrent_users']}")
        print(f"\nRequest Statistics:")
        print(f"Total Requests: {report['total_requests']}")
        print(f"Successful Requests: {report['successful_requests']}")
        print(f"Failed Requests: {report['failed_requests']}")
        print(f"Requests/Second: {report['requests_per_second']}")
        print(f"Requests/Hour: {report['requests_per_hour']}")
        print(f"\nResponse Times (seconds):")
        print(f"Average: {report['average_response_time']}")
        print(f"95th Percentile: {report['p95_response_time']}")
        print(f"99th Percentile: {report['p99_response_time']}")
        print(f"Min: {report['min_response_time']}")
        print(f"Max: {report['max_response_time']}")

        # Save report to file
        report_file = f"load_test_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nDetailed report saved to: {report_file}")

def main():
    parser = argparse.ArgumentParser(description='Load test the TTS API')
    parser.add_argument('url', help='Base URL of the API')
    parser.add_argument('--users', type=int, default=50,
                      help='Number of concurrent users (default: 50)')
    parser.add_argument('--duration', type=int, default=300,
                      help='Test duration in seconds (default: 300)')

    args = parser.parse_args()

    tester = LoadTester(args.url, args.users, args.duration)
    tester.run_test()
    tester.generate_report()

if __name__ == '__main__':
    main()
