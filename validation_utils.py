"""
validation_utils.py

Comprehensive validation utilities for land registration data.
Includes NRC, TPIN, phone, email, and document content validation.
"""
import re
from typing import Tuple, Dict, Optional


def validate_nrc(nrc: str) -> Tuple[bool, Optional[str]]:
    """
    Validate Zambian National Registration Card (NRC) number.
    
    Format: XXXXXX/XX/X (6 digits, 2 digits, 1 digit)
    Example: 123456/12/1
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not nrc:
        return False, "NRC number is required"
    
    nrc = nrc.strip()
    
    # Check format: 6 digits / 2 digits / 1 digit
    pattern = r'^\d{6}/\d{2}/\d$'
    if not re.match(pattern, nrc):
        return False, "NRC must be in format XXXXXX/XX/X (e.g., 123456/12/1)"
    
    # Additional validation: check if district code (middle 2 digits) is valid (01-72)
    parts = nrc.split('/')
    district_code = int(parts[1])
    if district_code < 1 or district_code > 72:
        return False, f"Invalid district code {district_code}. Must be between 01-72"
    
    return True, None


def validate_passport(passport: str) -> Tuple[bool, Optional[str]]:
    """
    Validate passport number.
    Format: Alphanumeric, 6-20 characters
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not passport:
        return False, "Passport number is required"
    
    passport = passport.strip().upper()
    
    # Must be alphanumeric and 6-20 characters
    if not re.match(r'^[A-Z0-9]{6,20}$', passport):
        return False, "Passport must be 6-20 alphanumeric characters"
    
    return True, None


def validate_tpin(tpin: str) -> Tuple[bool, Optional[str]]:
    """
    Validate Zambian Tax Payer Identification Number (TPIN).
    Format: 10 digits (1000000000 - 9999999999)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not tpin:
        return False, "TPIN is required"
    
    tpin = tpin.strip()
    
    # Must be exactly 10 digits
    if not re.match(r'^\d{10}$', tpin):
        return False, "TPIN must be exactly 10 digits"
    
    # Check if it's a reasonable number (not all zeros or ones)
    if tpin == '0000000000' or tpin == '1111111111':
        return False, "TPIN appears to be invalid (all same digits)"
    
    # TPIN should start with 1-9
    if tpin[0] == '0':
        return False, "TPIN cannot start with 0"
    
    return True, None


def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
    """
    Validate Zambian phone number.
    Formats accepted:
    - +260XXXXXXXXX (with country code)
    - 0XXXXXXXXX (local format)
    - 09XXXXXXXX or 07XXXXXXXX (common mobile)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not phone:
        return False, "Phone number is required"
    
    # Remove spaces, hyphens, parentheses
    phone = re.sub(r'[\s\-\(\)]', '', phone.strip())
    
    # Check for international format +260
    if phone.startswith('+260'):
        # Should be +260 followed by 9 digits
        if not re.match(r'^\+260\d{9}$', phone):
            return False, "International format must be +260 followed by 9 digits"
        return True, None
    
    # Check for local format starting with 0
    if phone.startswith('0'):
        # Should be 10 digits total (0 + 9 digits)
        if not re.match(r'^0\d{9}$', phone):
            return False, "Local format must be 10 digits starting with 0"
        
        # Most common Zambian mobile prefixes: 095, 096, 097, 076, 077
        prefix = phone[0:3]
        valid_prefixes = ['095', '096', '097', '076', '077', '075', '078']
        if prefix not in valid_prefixes:
            return False, f"Phone prefix {prefix} is not a common Zambian mobile operator"
        
        return True, None
    
    return False, "Phone must start with +260 or 0"


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate email address.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email:
        return False, "Email address is required"
    
    email = email.strip().lower()
    
    # RFC 5322 compliant regex (simplified)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    # Check for common typos
    if email.count('@') != 1:
        return False, "Email must contain exactly one @ symbol"
    
    # Check domain part
    domain = email.split('@')[1]
    if domain.count('.') < 1:
        return False, "Email domain must contain at least one period"
    
    # Check for suspicious patterns
    if '..' in email or email.startswith('.') or email.endswith('.'):
        return False, "Email contains invalid characters or format"
    
    return True, None


def validate_land_size(size: float, min_size: float = 0.01, max_size: float = 100000) -> Tuple[bool, Optional[str]]:
    """
    Validate land size in hectares.
    
    Args:
        size: Land size in hectares
        min_size: Minimum acceptable size (default 0.01 ha = 100 sq meters)
        max_size: Maximum acceptable size (default 100,000 ha)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if size is None:
        return False, "Land size is required"
    
    try:
        size = float(size)
    except (TypeError, ValueError):
        return False, "Land size must be a number"
    
    if size < min_size:
        return False, f"Land size too small. Minimum is {min_size} hectares"
    
    if size > max_size:
        return False, f"Land size too large. Maximum is {max_size} hectares"
    
    return True, None


def validate_coordinates(coordinates: str) -> Tuple[bool, Optional[str]]:
    """
    Validate GPS coordinates format.
    Format: latitude,longitude (e.g., -12.989159,28.653111)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not coordinates:
        return False, "Coordinates are required"
    
    try:
        parts = coordinates.split(',')
        if len(parts) != 2:
            return False, "Coordinates must be in format: latitude,longitude"
        
        lat = float(parts[0].strip())
        lon = float(parts[1].strip())
        
        # Zambia coordinates approximately:
        # Latitude: -8° to -18° (southern hemisphere)
        # Longitude: 21° to 34° (eastern hemisphere)
        if lat < -18 or lat > -8:
            return False, "Latitude out of range for Zambia (-18° to -8°)"
        
        if lon < 21 or lon > 34:
            return False, "Longitude out of range for Zambia (21° to 34°)"
        
        return True, None
    except (ValueError, AttributeError):
        return False, "Invalid coordinate format. Use: latitude,longitude"


def normalize_identifier(identifier: str, identifier_type: str) -> str:
    """
    Normalize an identifier for comparison.
    
    Args:
        identifier: The identifier string (NRC, TPIN, phone, etc.)
        identifier_type: Type of identifier ('nrc', 'tpin', 'phone', 'email')
    
    Returns:
        Normalized identifier string
    """
    if not identifier:
        return ""
    
    identifier = identifier.strip()
    
    if identifier_type == 'nrc':
        # Remove spaces, convert to uppercase
        return identifier.upper().replace(' ', '')
    
    elif identifier_type == 'tpin':
        # Remove spaces and non-digits
        return re.sub(r'\D', '', identifier)
    
    elif identifier_type == 'phone':
        # Remove spaces, hyphens, parentheses
        phone = re.sub(r'[\s\-\(\)]', '', identifier)
        # Normalize to +260 format
        if phone.startswith('0'):
            phone = '+260' + phone[1:]
        return phone
    
    elif identifier_type == 'email':
        # Lowercase and trim
        return identifier.lower().strip()
    
    return identifier


def validate_all_application_data(data: Dict) -> Tuple[bool, Dict[str, str]]:
    """
    Validate all application data at once.
    
    Args:
        data: Dictionary containing application data
    
    Returns:
        Tuple of (all_valid, error_dict)
        error_dict maps field names to error messages
    """
    errors = {}
    
    # Validate NRC or Passport
    if 'nrc_number' in data and data['nrc_number']:
        nrc_valid, nrc_error = validate_nrc(data['nrc_number'])
        if not nrc_valid:
            # Try passport validation
            passport_valid, passport_error = validate_passport(data['nrc_number'])
            if not passport_valid:
                errors['nrc_number'] = f"{nrc_error}. Or provide valid passport: {passport_error}"
    
    # Validate TPIN
    if 'tpin_number' in data and data['tpin_number']:
        tpin_valid, tpin_error = validate_tpin(data['tpin_number'])
        if not tpin_valid:
            errors['tpin_number'] = tpin_error
    
    # Validate Phone
    if 'phone_number' in data and data['phone_number']:
        phone_valid, phone_error = validate_phone(data['phone_number'])
        if not phone_valid:
            errors['phone_number'] = phone_error
    
    # Validate Email
    if 'email' in data and data['email']:
        email_valid, email_error = validate_email(data['email'])
        if not email_valid:
            errors['email'] = email_error
    
    # Validate Land Size
    if 'land_size' in data:
        size_valid, size_error = validate_land_size(data['land_size'])
        if not size_valid:
            errors['land_size'] = size_error
    
    return len(errors) == 0, errors


# Quick validation functions for AJAX requests
def quick_validate(field: str, value: str) -> Dict:
    """
    Quick validation for AJAX requests.
    Returns JSON-compatible dict.
    """
    validators = {
        'nrc': validate_nrc,
        'nrc_number': validate_nrc,
        'tpin': validate_tpin,
        'tpin_number': validate_tpin,
        'phone': validate_phone,
        'phone_number': validate_phone,
        'email': validate_email,
    }
    
    validator = validators.get(field.lower())
    if not validator:
        return {'valid': False, 'message': 'Unknown field type'}
    
    is_valid, error_msg = validator(value)
    return {
        'valid': is_valid,
        'message': error_msg if not is_valid else 'Valid'
    }
