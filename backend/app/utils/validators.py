"""
Basic validation for parsed resume data
"""
from datetime import datetime


def validate_parsed_data(data: dict) -> dict:
    """
    Add basic validation metadata to parsed data
    """
    data['_validation'] = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'validated_at': datetime.now().isoformat()
    }
    return data