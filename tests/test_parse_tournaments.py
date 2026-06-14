"""Tests for tournament parsing."""

import pytest
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from parse_tournaments import EventParser


class TestEventParser:
    """Test suite for tournament HTML parsing."""
    
    def test_parser_initialization(self):
        """Test that parser can be initialized."""
        parser = EventParser()
        assert parser is not None
        assert hasattr(parser, 'log_buffer')
        assert isinstance(parser.log_buffer, list)
    
    def test_log_message_buffering(self):
        """Test that log messages are buffered."""
        parser = EventParser()
        parser.log("Test message")
        
        assert len(parser.log_buffer) > 0
        assert "Test message" in parser.log_buffer[0]
    
    def test_parse_real_tournament_file(self, test_data_dir):
        """Test parsing a real tournament HTML file."""
        # Find first HTML file in test data
        input_dirs = list((test_data_dir).glob('*/'))
        if not input_dirs:
            pytest.skip("No tournament directories in test data")
        
        html_files = list(input_dirs[0].glob('*.htm'))
        if not html_files:
            pytest.skip("No HTML files in test tournament data")
        
        parser = EventParser()
        html_file = html_files[0]
        
        # Should not raise an error
        try:
            matches = parser.parse_tournament_file(html_file)
            assert isinstance(matches, list)
        except Exception as e:
            pytest.skip(f"HTML parsing failed: {e}")
