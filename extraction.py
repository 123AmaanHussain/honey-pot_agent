"""
Enhanced intelligence extraction module.
Extracts UPI IDs, phone numbers, URLs, and other intelligence from messages.
"""
import re
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


# Regex patterns for extraction
# Fixed UPI pattern - removed trailing \b to allow dots in domain (e.g., @fakebank.com)
UPI_PATTERN = re.compile(
    r'[\w\.\-]+@[\w\.\-]+',  # Matches user@paytm, scammer.fraud@fakebank, etc.
    re.IGNORECASE
)

# Enhanced phone pattern - captures +91-XXX, 91-XXX, and plain 10-digit
# Relaxed lookbehind to allow + sign before 91
PHONE_PATTERN = re.compile(
    r'(?:(?<!\d)\+91[\s\-]?|(?<!\d)91[\s\-]?|(?<!\d))[6-9]\d{9}(?!\d)',  # Indian phone numbers
    re.IGNORECASE
)

# Enhanced URL pattern - captures http://, www., and plain domains
URL_PATTERN = re.compile(
    r'(?:https?://)?(?:www\.)?[a-zA-Z0-9\-]+(?:\.[a-zA-Z0-9\-]+)*\.[a-z]{2,}(?:/[\w\-\./?%&=]*)?',
    re.IGNORECASE
)

# Enhanced bank account pattern - captures 11-18 digit numbers (avoiding phone numbers)
BANK_ACCOUNT_PATTERN = re.compile(
    r'\b\d{11,18}\b'  # Indian bank accounts are typically 11-18 digits
)

# Common UPI providers for validation
# Expanded UPI providers list
UPI_PROVIDERS = [
    'paytm', 'phonepe', 'googlepay', 'ybl', 'oksbi', 'okhdfcbank', 
    'okicici', 'okaxis', 'ibl', 'axl', 'upi', 'fakebank', 'fraud',
    'scam', 'bank', 'pay', 'wallet'
]


def extract_upi_ids(text: str) -> List[str]:
    """
    Extract UPI IDs from text.
    
    Args:
        text: Input text to extract from
        
    Returns:
        List of extracted UPI IDs
    """
    matches = UPI_PATTERN.findall(text)
    
    # Filter to only valid UPI IDs (must have known provider)
    valid_upis = []
    for match in matches:
        # Check if it's a valid UPI ID (has @ and known provider)
        if '@' in match:
            provider = match.split('@')[1].lower()
            # Check if provider is in known list or looks like a bank
            if any(p in provider for p in UPI_PROVIDERS) or 'bank' in provider:
                valid_upis.append(match)
                logger.info(f"Extracted UPI ID: {match}")
    
    return list(set(valid_upis))  # Remove duplicates


def extract_phone_numbers(text: str) -> List[str]:
    """
    Extract phone numbers from text.
    
    Args:
        text: Input text to extract from
        
    Returns:
        List of extracted phone numbers
    """
    matches = PHONE_PATTERN.findall(text)
    
    # Normalize phone numbers (remove spaces, dashes, country codes)
    normalized = []
    seen = set()
    
    for match in matches:
        # Remove spaces, dashes, and plus sign
        clean = re.sub(r'[\s\-\+]', '', match)
        
        # Remove country code if present
        if clean.startswith('91') and len(clean) >= 12:
            clean = clean[2:]  # Remove '91' prefix
        
        # Ensure it's exactly 10 digits and starts with 6-9
        if len(clean) == 10 and clean[0] in '6789' and clean not in seen:
            normalized.append(clean)
            seen.add(clean)
            logger.info(f"Extracted phone number: {clean}")
    
    return normalized


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text.
    
    Args:
        text: Input text to extract from
        
    Returns:
        List of extracted URLs
    """
    matches = URL_PATTERN.findall(text)
    
    # Filter out UPI IDs that might match URL pattern (e.g., scammer.fraud)
    # A valid URL should have a proper TLD (com, org, in, etc.) and not contain @
    common_tlds = ['com', 'org', 'net', 'in', 'io', 'co', 'gov', 'edu']
    filtered_urls = []
    for match in matches:
        # Skip if it looks like a UPI ID (contains @ or is part of email-like pattern)
        if '@' in match:
            continue
        # Check if it has a valid TLD
        parts = match.split('.')
        if len(parts) < 2:
            continue
        tld = parts[-1].lower().split('/')[0]  # Get TLD before any path
        if tld not in common_tlds and len(tld) > 3:
            continue
        # Skip very short matches (likely false positives)
        if len(match) < 8:
            continue
        filtered_urls.append(match)
    
    if filtered_urls:
        logger.info(f"Extracted {len(filtered_urls)} URLs")
    
    return list(set(filtered_urls))  # Remove duplicates


def extract_bank_accounts(text: str) -> List[str]:
    """
    Extract bank account numbers from text.
    Indian bank accounts are typically 9-18 digits.
    
    Args:
        text: Input text to extract from
        
    Returns:
        List of extracted bank account numbers
    """
    matches = BANK_ACCOUNT_PATTERN.findall(text)
    
    # Filter out phone numbers (10 digits) and common numbers
    valid_accounts = []
    for match in matches:
        # Skip if it's exactly 10 digits (likely a phone number)
        if len(match) == 10:
            continue
        # Skip very short numbers (likely not bank accounts)
        if len(match) < 9:
            continue
        # Skip numbers that are all the same digit
        if len(set(match)) == 1:
            continue
            
        valid_accounts.append(match)
        logger.info(f"Extracted bank account: {match[:4]}****{match[-4:]}")
    
    return list(set(valid_accounts))  # Remove duplicates


def extract_suspicious_keywords(text: str, detected_flags: List[str]) -> List[str]:
    """
    Extract suspicious keywords from detected flags.
    
    Args:
        text: Input text
        detected_flags: List of detection flags
        
    Returns:
        List of suspicious keywords found
    """
    keywords = []
    
    for flag in detected_flags:
        if flag.startswith("keyword:"):
            keyword = flag.replace("keyword:", "")
            keywords.append(keyword)
    
    return list(set(keywords))


def extract_all_intelligence(text: str, detection_flags: List[str] = None) -> Dict[str, List[str]]:
    """
    Extract all intelligence from a message.
    
    Args:
        text: Message text to extract from
        detection_flags: Optional detection flags for keyword extraction
        
    Returns:
        Dictionary containing all extracted intelligence
    """
    intelligence = {
        "upiIds": extract_upi_ids(text),
        "phoneNumbers": extract_phone_numbers(text),
        "phishingLinks": extract_urls(text),
        "bankAccounts": extract_bank_accounts(text),
        "suspiciousKeywords": extract_suspicious_keywords(text, detection_flags or [])
    }
    
    # Log summary
    total_items = sum(len(v) for v in intelligence.values())
    if total_items > 0:
        logger.info(
            f"Extracted intelligence summary",
            extra={
                "upi_ids": len(intelligence["upiIds"]),
                "phone_numbers": len(intelligence["phoneNumbers"]),
                "urls": len(intelligence["phishingLinks"]),
                "bank_accounts": len(intelligence["bankAccounts"]),
                "keywords": len(intelligence["suspiciousKeywords"]),
            }
        )
    
    return intelligence


def merge_intelligence(existing: Dict[str, List[str]], new: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Merge new intelligence with existing intelligence.
    
    Args:
        existing: Existing intelligence dictionary
        new: New intelligence to merge
        
    Returns:
        Merged intelligence dictionary
    """
    merged = {}
    
    for key in ["upiIds", "phoneNumbers", "phishingLinks", "bankAccounts", "suspiciousKeywords", "scannedText"]:
        # Combine and remove duplicates
        combined = list(set(existing.get(key, []) + new.get(key, [])))
        merged[key] = combined
    
    return merged
