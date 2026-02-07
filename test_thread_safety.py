#!/usr/bin/env python3
"""
Test script to verify thread-safety fixes in main.py
"""

import sys
import ast
from pathlib import Path

def test_thread_safe_methods():
    """Test that thread-safe methods are properly implemented"""
    print("Testing thread-safety implementation in main.py...\n")
    
    # Read main.py
    with open('main.py', 'r') as f:
        content = f.read()
    
    errors = []
    warnings = []
    successes = []
    
    # Check that log() uses self.after()
    if 'def log(self, message):' in content:
        if 'self.after(0, self._log_impl, message)' in content:
            successes.append("✓ log() method uses self.after() for thread-safety")
        else:
            errors.append("✗ log() method doesn't use self.after()")
        
        if 'def _log_impl(self, message):' in content:
            successes.append("✓ _log_impl() implementation method exists")
        else:
            errors.append("✗ _log_impl() implementation method missing")
        
        # Check that log() doesn't call update() directly
        if 'def log(self, message):' in content and 'self.update()' in content:
            # Need to check if update() is in log or _log_impl
            lines = content.split('\n')
            in_log = False
            in_log_impl = False
            for line in lines:
                if 'def log(self, message):' in line:
                    in_log = True
                    in_log_impl = False
                elif 'def _log_impl(self, message):' in line:
                    in_log_impl = True
                    in_log = False
                elif line.strip().startswith('def ') and (in_log or in_log_impl):
                    in_log = False
                    in_log_impl = False
                
                if in_log and 'self.update()' in line:
                    errors.append("✗ log() still calls self.update() directly")
                elif in_log_impl and 'self.update()' in line:
                    errors.append("✗ _log_impl() calls self.update()")
    
    # Check that update_progress() uses self.after()
    if 'def update_progress(self, value, text):' in content:
        if 'self.after(0, self._update_progress_impl, value, text)' in content:
            successes.append("✓ update_progress() method uses self.after() for thread-safety")
        else:
            errors.append("✗ update_progress() method doesn't use self.after()")
        
        if 'def _update_progress_impl(self, value, text):' in content:
            successes.append("✓ _update_progress_impl() implementation method exists")
        else:
            errors.append("✗ _update_progress_impl() implementation method missing")
    
    # Check that convert_log() uses self.after()
    if 'def convert_log(self, message):' in content:
        if 'self.after(0, self._convert_log_impl, message)' in content:
            successes.append("✓ convert_log() method uses self.after() for thread-safety")
        else:
            errors.append("✗ convert_log() method doesn't use self.after()")
        
        if 'def _convert_log_impl(self, message):' in content:
            successes.append("✓ _convert_log_impl() implementation method exists")
        else:
            errors.append("✗ _convert_log_impl() implementation method missing")
        
        # Check that convert_log doesn't call update() directly
        lines = content.split('\n')
        in_convert_log = False
        for line in lines:
            if 'def convert_log(self, message):' in line:
                in_convert_log = True
            elif line.strip().startswith('def ') and in_convert_log:
                in_convert_log = False
            
            if in_convert_log and 'self.update()' in line:
                errors.append("✗ convert_log() still calls self.update() directly")
    
    # Check conversion_thread for direct widget calls
    if 'def conversion_thread(self):' in content:
        lines = content.split('\n')
        in_conversion_thread = False
        direct_widget_calls = []
        
        for i, line in enumerate(lines):
            if 'def conversion_thread(self):' in line:
                in_conversion_thread = True
            elif line.strip().startswith('def ') and in_conversion_thread:
                in_conversion_thread = False
            
            if in_conversion_thread:
                # Check for direct widget calls that should be wrapped
                if 'self.convert_progress_bar.set(' in line and 'self.after(0,' not in line:
                    direct_widget_calls.append(f"Line {i+1}: direct convert_progress_bar.set()")
                if 'self.convert_progress_label.configure(' in line and 'self.after(0,' not in line:
                    direct_widget_calls.append(f"Line {i+1}: direct convert_progress_label.configure()")
                if 'self.convert_start_button.configure(' in line and 'self.after(0,' not in line:
                    direct_widget_calls.append(f"Line {i+1}: direct convert_start_button.configure()")
        
        if direct_widget_calls:
            errors.append(f"✗ conversion_thread() has {len(direct_widget_calls)} direct widget calls:")
            for call in direct_widget_calls[:3]:  # Show first 3
                errors.append(f"    {call}")
        else:
            successes.append("✓ conversion_thread() has no direct widget calls")
    
    # Check sort_textures_thread for direct widget calls
    if 'def sort_textures_thread(self):' in content:
        lines = content.split('\n')
        in_sort_thread = False
        direct_widget_calls = []
        
        for i, line in enumerate(lines):
            if 'def sort_textures_thread(self):' in line:
                in_sort_thread = True
            elif line.strip().startswith('def ') and in_sort_thread:
                in_sort_thread = False
            
            if in_sort_thread:
                # Check for direct widget calls in the finally block
                if 'self.start_button.configure(' in line and 'self.after(0,' not in line:
                    direct_widget_calls.append(f"Line {i+1}: direct start_button.configure()")
                if 'self.organize_button.configure(' in line and 'self.after(0,' not in line:
                    direct_widget_calls.append(f"Line {i+1}: direct organize_button.configure()")
                if 'self.pause_button.configure(' in line and 'self.after(0,' not in line:
                    direct_widget_calls.append(f"Line {i+1}: direct pause_button.configure()")
                if 'self.stop_button.configure(' in line and 'self.after(0,' not in line:
                    direct_widget_calls.append(f"Line {i+1}: direct stop_button.configure()")
        
        if direct_widget_calls:
            errors.append(f"✗ sort_textures_thread() has {len(direct_widget_calls)} direct widget calls:")
            for call in direct_widget_calls[:3]:  # Show first 3
                errors.append(f"    {call}")
        else:
            successes.append("✓ sort_textures_thread() has no direct widget calls")
    
    # Check for minsize() call
    if 'self.minsize(' in content:
        successes.append("✓ Window minimum size is set")
    else:
        warnings.append("⚠ Window minimum size not set")
    
    # Print results
    print("=" * 60)
    print("SUCCESSES:")
    for success in successes:
        print(f"  {success}")
    
    if warnings:
        print("\nWARNINGS:")
        for warning in warnings:
            print(f"  {warning}")
    
    if errors:
        print("\nERRORS:")
        for error in errors:
            print(f"  {error}")
    
    print("=" * 60)
    
    if errors:
        print(f"\n❌ TEST FAILED: {len(errors)} error(s) found")
        return False
    else:
        print(f"\n✅ TEST PASSED: All thread-safety checks passed!")
        return True

if __name__ == "__main__":
    success = test_thread_safe_methods()
    sys.exit(0 if success else 1)
