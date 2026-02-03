"""
Unit tests for bank account extraction.
"""
import pytest
from extraction import extract_bank_accounts, extract_all_intelligence


class TestBankAccountExtraction:
    """Test suite for bank account extraction."""
    
    def test_extract_valid_bank_accounts(self):
        """Test extraction of various valid bank account number formats."""
        text = "Please deposit the funds to my account: 123456789012. It's safe."
        accounts = extract_bank_accounts(text)
        assert "123456789012" in accounts
        assert len(accounts) == 1
    
    def test_extract_multiple_accounts(self):
        """Test extraction of multiple account numbers."""
        text = "Account 1: 987654321000, Account 2: 1212121212121"
        accounts = extract_bank_accounts(text)
        assert "987654321000" in accounts
        assert "1212121212121" in accounts
        assert len(accounts) == 2
    
    def test_filter_phone_numbers(self):
        """Test that 10-digit numbers (potential phone numbers) are filtered out."""
        text = "My account is 1234567890123. Call me at 9876543210 if any issues."
        accounts = extract_bank_accounts(text)
        assert "1234567890123" in accounts
        assert "9876543210" not in accounts  # Should be ignored by bank account extractor
        assert len(accounts) == 1
    
    def test_filter_short_numbers(self):
        """Test that too short numbers are ignored."""
        text = "Code is 1234 or 5678."
        accounts = extract_bank_accounts(text)
        assert len(accounts) == 0
    
    def test_filter_invalid_patterns(self):
        """Test that numbers with same digits are ignored (likely dummy data)."""
        text = "Account: 999999999999"
        accounts = extract_bank_accounts(text)
        assert len(accounts) == 0
    
    def test_extract_all_with_bank_accounts(self):
        """Test that aggregate extraction includes bank accounts."""
        text = "Pay to 987654321012. UPI: boss@paytm"
        intelligence = extract_all_intelligence(text, [])
        assert "987654321012" in intelligence["bankAccounts"]
        assert "boss@paytm" in intelligence["upiIds"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
