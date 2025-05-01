import os
import pytest
import time
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor
from memory_profiler import profile
from src.actions.keystrokes import send_keystrokes, send_keystroke_sequence
from src.cli import load_config, validate_config
from unittest.mock import patch, MagicMock
import logging

def test_concurrent_operations():
    """Test concurrent operations performance."""
    def run_keystrokes():
        sequence = [
            {'keys': 'a', 'delay_ms': 100},
            {'keys': 'command+a', 'delay_ms': 100},
            {'keys': 'shift+enter', 'delay_ms': 100}
        ]
        return send_keystroke_sequence(sequence)
    
    # Test with multiple threads
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(run_keystrokes) for _ in range(4)]
        results = [f.result() for f in futures]
    
    duration = time.time() - start_time
    assert duration < 2.0  # Should complete within 2 seconds
    assert all(results)  # All operations should succeed

def test_resource_usage():
    """Test resource usage during operations."""
    process = psutil.Process()
    
    # Test memory usage
    initial_memory = process.memory_info().rss
    sequence = [
        {'keys': 'a', 'delay_ms': 100},
        {'keys': 'command+a', 'delay_ms': 100},
        {'keys': 'shift+enter', 'delay_ms': 100}
    ]
    
    for _ in range(100):
        send_keystroke_sequence(sequence)
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    assert memory_increase < 10 * 1024 * 1024  # Should use less than 10MB
    
    # Test CPU usage
    initial_cpu = process.cpu_percent()
    for _ in range(100):
        send_keystroke_sequence(sequence)
    final_cpu = process.cpu_percent()
    assert final_cpu - initial_cpu < 50  # Should use less than 50% CPU

def test_response_times():
    """Test response times for different operations."""
    # Test keystroke response time
    start_time = time.time()
    send_keystrokes('a')
    duration = time.time() - start_time
    assert duration < 0.1  # Should complete within 100ms
    
    # Test sequence response time
    sequence = [
        {'keys': 'a', 'delay_ms': 100},
        {'keys': 'command+a', 'delay_ms': 100},
        {'keys': 'shift+enter', 'delay_ms': 100}
    ]
    start_time = time.time()
    send_keystroke_sequence(sequence)
    duration = time.time() - start_time
    assert duration < 0.5  # Should complete within 500ms
    
    # Test configuration loading time
    start_time = time.time()
    config = load_config("config.yaml")
    validate_config(config)
    duration = time.time() - start_time
    assert duration < 1.0  # Should complete within 1 second

def test_scalability():
    """Test system scalability."""
    def run_operations(count):
        sequence = [
            {'keys': 'a', 'delay_ms': 100},
            {'keys': 'command+a', 'delay_ms': 100},
            {'keys': 'shift+enter', 'delay_ms': 100}
        ]
        for _ in range(count):
            send_keystroke_sequence(sequence)
    
    # Test with increasing load
    for count in [10, 100, 1000]:
        start_time = time.time()
        run_operations(count)
        duration = time.time() - start_time
        assert duration < count * 0.1  # Should scale linearly

def test_stress_test():
    """Test system under stress conditions."""
    def stress_operation():
        sequence = [
            {'keys': 'a', 'delay_ms': 100},
            {'keys': 'command+a', 'delay_ms': 100},
            {'keys': 'shift+enter', 'delay_ms': 100}
        ]
        while True:
            send_keystroke_sequence(sequence)
    
    # Test with multiple stress threads
    threads = []
    for _ in range(4):
        thread = threading.Thread(target=stress_operation)
        thread.daemon = True
        threads.append(thread)
    
    # Run stress test for 5 seconds
    for thread in threads:
        thread.start()
    
    time.sleep(5)
    
    # Check system stability
    process = psutil.Process()
    assert process.memory_info().rss < 100 * 1024 * 1024  # Should use less than 100MB
    assert process.cpu_percent() < 80  # Should use less than 80% CPU 