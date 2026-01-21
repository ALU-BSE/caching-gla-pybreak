#!/usr/bin/env python
"""
Load test script for cache performance comparison.

This script measures the performance difference between cached and non-cached
API calls, demonstrating the benefits of Redis caching.

Usage:
    python test_cache_performance.py
    python test_cache_performance.py --url http://localhost:8000/api/users/
    python test_cache_performance.py --iterations 10
"""
import argparse
import time
import statistics
from typing import List, Tuple
try:
    import requests
except ImportError:
    print("Please install requests: pip install requests")
    exit(1)


def make_request(url: str) -> Tuple[float, int]:
    """
    Make a single request and return response time and status code.
    
    Returns:
        Tuple of (response_time_seconds, status_code)
    """
    start = time.time()
    response = requests.get(url)
    elapsed = time.time() - start
    return elapsed, response.status_code


def run_load_test(url: str, iterations: int = 5, clear_cache_url: str = None) -> dict:
    """
    Run load test comparing first call (potential cache miss) vs subsequent calls (cache hits).
    
    Args:
        url: The API endpoint to test
        iterations: Number of iterations for cache hit testing
        clear_cache_url: Optional URL to clear cache before testing
        
    Returns:
        Dictionary with test results
    """
    print(f"\n{'='*60}")
    print(f"Cache Performance Load Test")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"Iterations: {iterations}")
    print(f"{'='*60}\n")
    
    # Clear cache if endpoint provided
    if clear_cache_url:
        print("Clearing cache...")
        try:
            requests.post(clear_cache_url)
            print("Cache cleared.\n")
        except Exception as e:
            print(f"Could not clear cache: {e}\n")
    
    # First call (cache miss - should be slower)
    print("Making first call (potential cache miss)...")
    first_time, first_status = make_request(url)
    print(f"  Time: {first_time:.4f}s | Status: {first_status}")
    
    # Subsequent calls (cache hits - should be faster)
    print(f"\nMaking {iterations} subsequent calls (cache hits)...")
    subsequent_times: List[float] = []
    
    for i in range(iterations):
        elapsed, status = make_request(url)
        subsequent_times.append(elapsed)
        print(f"  Call {i+1}: {elapsed:.4f}s | Status: {status}")
    
    # Calculate statistics
    avg_subsequent = statistics.mean(subsequent_times)
    min_subsequent = min(subsequent_times)
    max_subsequent = max(subsequent_times)
    
    if len(subsequent_times) > 1:
        std_subsequent = statistics.stdev(subsequent_times)
    else:
        std_subsequent = 0.0
    
    # Calculate speedup
    if avg_subsequent > 0:
        speedup = first_time / avg_subsequent
    else:
        speedup = float('inf')
    
    results = {
        'first_call_time': first_time,
        'first_call_status': first_status,
        'average_cached_time': avg_subsequent,
        'min_cached_time': min_subsequent,
        'max_cached_time': max_subsequent,
        'std_cached_time': std_subsequent,
        'speedup_factor': speedup,
        'iterations': iterations,
    }
    
    # Print summary
    print(f"\n{'='*60}")
    print("RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"First call (cache miss):     {first_time:.4f}s")
    print(f"Average cached call:         {avg_subsequent:.4f}s")
    print(f"Min cached call:             {min_subsequent:.4f}s")
    print(f"Max cached call:             {max_subsequent:.4f}s")
    print(f"Std deviation:               {std_subsequent:.4f}s")
    print(f"{'='*60}")
    print(f"SPEEDUP:                     {speedup:.2f}x faster with cache")
    print(f"{'='*60}\n")
    
    if speedup > 1.5:
        print("✅ Caching is working effectively!")
    elif speedup > 1.0:
        print("⚠️  Caching provides modest improvement. Consider:")
        print("   - Checking Redis connection")
        print("   - Increasing cache timeout")
        print("   - Testing with more data")
    else:
        print("❌ Caching may not be working. Check:")
        print("   - Redis server is running")
        print("   - Cache configuration in settings.py")
        print("   - View-level caching is implemented")
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Cache performance load test')
    parser.add_argument(
        '--url',
        default='http://localhost:8000/api/users/',
        help='API endpoint URL to test'
    )
    parser.add_argument(
        '--iterations',
        type=int,
        default=5,
        help='Number of iterations for cache hit testing'
    )
    parser.add_argument(
        '--clear-cache-url',
        default=None,
        help='Optional URL to POST to for clearing cache'
    )
    
    args = parser.parse_args()
    
    try:
        results = run_load_test(
            url=args.url,
            iterations=args.iterations,
            clear_cache_url=args.clear_cache_url
        )
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Error: Could not connect to {args.url}")
        print("Make sure the Django development server is running:")
        print("  python manage.py runserver")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
