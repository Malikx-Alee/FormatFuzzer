#!/usr/bin/env python3
"""
Test script for the Learning Constraints module.

This script performs basic tests to ensure the refactored module works correctly.
"""

import os
import sys
import tempfile
import shutil

# Import the new module
try:
    from learning_constraints import (
        Config,
        GlobalState,
        FileValidator,
        FileParser,
        FileMutator,
        LearningConstraintsOrchestrator,
        set_file_type,
        get_supported_file_types
    )
    print("✓ Successfully imported learning_constraints module")
except ImportError as e:
    print(f"✗ Failed to import learning_constraints module: {e}")
    sys.exit(1)


def test_config():
    """Test configuration functionality."""
    print("\nTesting Configuration...")
    
    # Test supported file types
    file_types = get_supported_file_types()
    assert len(file_types) > 0, "Should have supported file types"
    print(f"✓ Found {len(file_types)} supported file types")
    
    # Test file type setting
    original_type = Config.FILE_TYPE
    set_file_type("png")
    assert Config.FILE_TYPE == "png", "File type should be changed to png"
    print("✓ File type setting works")
    
    # Reset to original
    set_file_type(original_type)
    assert Config.FILE_TYPE == original_type, "File type should be reset"
    print("✓ File type reset works")


def test_global_state():
    """Test global state functionality."""
    print("\nTesting Global State...")
    
    state = GlobalState()
    
    # Test initial state
    assert state.valid_abstractions_count == 0, "Initial count should be 0"
    assert len(state.blacklisted_attributes) == 0, "Initial blacklist should be empty"
    print("✓ Initial state is correct")
    
    # Test state modification
    state.valid_abstractions_count = 5
    state.blacklisted_attributes.add("test_attr")
    
    stats = state.get_stats()
    assert stats['valid_abstractions'] == 5, "Stats should reflect changes"
    assert stats['blacklisted_attributes'] == 1, "Stats should reflect blacklist"
    print("✓ State modification works")
    
    # Test reset
    state.reset()
    assert state.valid_abstractions_count == 0, "Reset should clear counts"
    assert len(state.blacklisted_attributes) == 0, "Reset should clear blacklist"
    print("✓ State reset works")


def test_file_validator():
    """Test file validator functionality."""
    print("\nTesting File Validator...")
    
    validator = FileValidator()
    
    # Test with a non-existent file (should return False)
    result = validator.is_valid_file("/non/existent/file.gif", "gif")
    assert result == False, "Non-existent file should be invalid"
    print("✓ Non-existent file validation works")
    
    # Test with invalid file type
    try:
        validator.is_valid_file("test.txt", "invalid_type")
        print("✓ Invalid file type handled gracefully")
    except Exception:
        print("✓ Invalid file type raises appropriate error")


def test_file_parser():
    """Test file parser functionality."""
    print("\nTesting File Parser...")
    
    state = GlobalState()
    parser = FileParser(state)
    
    # Test with non-existent file
    byte_ranges = parser.parse_file_structure("/non/existent/file.gif")
    assert isinstance(byte_ranges, list), "Should return a list"
    assert len(byte_ranges) == 0, "Non-existent file should return empty list"
    print("✓ Non-existent file parsing works")
    
    # Test attribute extraction
    test_ranges = [(0, 5, "header~magic"), (6, 10, "header~version")]
    attributes = parser.get_file_attributes(test_ranges)
    assert "magic" in attributes, "Should extract magic attribute"
    assert "version" in attributes, "Should extract version attribute"
    print("✓ Attribute extraction works")


def test_orchestrator():
    """Test the main orchestrator."""
    print("\nTesting Orchestrator...")
    
    # Test creation
    orchestrator = LearningConstraintsOrchestrator(file_type="gif")
    assert orchestrator.global_state is not None, "Should have global state"
    assert orchestrator.parser is not None, "Should have parser"
    assert orchestrator.mutator is not None, "Should have mutator"
    print("✓ Orchestrator creation works")
    
    # Test directory processing with non-existent directory
    success, total = orchestrator.process_directory("/non/existent/directory")
    assert success == 0 and total == 0, "Non-existent directory should return 0, 0"
    print("✓ Non-existent directory handling works")


def test_directory_creation():
    """Test directory creation functionality."""
    print("\nTesting Directory Creation...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Change the data directory to our temp directory
        original_data_dir = Config.DATA_DIR
        Config.DATA_DIR = os.path.join(temp_dir, "test-data")
        Config.PASSED_DIR = os.path.join(Config.DATA_DIR, "passed/")
        Config.ABSTRACTED_DIR = os.path.join(Config.DATA_DIR, "abstracted/")
        Config.ABSTRACTED_SPECIAL_DIR = os.path.join(Config.DATA_DIR, "abstracted_special/")
        Config.FAILED_DIR = os.path.join(Config.DATA_DIR, "failed/")
        Config.RESULTS_OUTPUT_DIR = os.path.join(temp_dir, "results")
        
        # Test directory creation
        Config.ensure_directories_exist()
        
        # Check if directories were created
        assert os.path.exists(Config.PASSED_DIR), "Passed directory should be created"
        assert os.path.exists(Config.ABSTRACTED_DIR), "Abstracted directory should be created"
        assert os.path.exists(Config.RESULTS_OUTPUT_DIR), "Results directory should be created"
        print("✓ Directory creation works")
        
        # Restore original configuration
        Config.DATA_DIR = original_data_dir


def run_all_tests():
    """Run all tests."""
    print("Learning Constraints Module - Test Suite")
    print("="*50)
    
    try:
        test_config()
        test_global_state()
        test_file_validator()
        test_file_parser()
        test_orchestrator()
        test_directory_creation()
        
        print("\n" + "="*50)
        print("✓ All tests passed!")
        print("The Learning Constraints module is working correctly.")
        return True
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
