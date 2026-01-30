"""
Hinglish processing utilities for address parsing.
"""
from .hinglish_processor import process_hinglish_address

# Define the missing functions that the inference pipeline expects
def clean_text(text):
    """
    Clean text by removing extra spaces and normalizing
    """
    import re
    # Normalize spaces
    text = re.sub(r'\s+', ' ', text)
    # Remove extra punctuation
    text = re.sub(r'[^\w\s,.-]', ' ', text)
    return text.strip()

def expand_abbreviations(text):
    """
    Expand common abbreviations in address text
    """
    abbreviations = {
        'st': 'street',
        'ave': 'avenue', 
        'blvd': 'boulevard',
        'rd': 'road',
        'ln': 'lane',
        'dr': 'drive',
        'apt': 'apartment',
        'fl': 'floor',
        'no': 'number',
        'nr': 'near',
        'opp': 'opposite',
        'beh': 'behind',
        'b/h': 'behind',
        'dist': 'district'
    }
    
    words = text.split()
    expanded = []
    for word in words:
        clean_word = word.lower().strip('.,')
        if clean_word in abbreviations:
            expanded.append(abbreviations[clean_word])
        else:
            expanded.append(word)
    
    return ' '.join(expanded)

def translate_terms(text):
    """
    Translate common Hinglish terms to English
    """
    translations = {
        'gali': 'lane',
        'mohalla': 'area',
        'colony': 'colony',
        'nagar': 'nagar',
        'road': 'road',
        'marg': 'road',
        'path': 'road',
        'ka': '',
        'ki': '',
        'ke': ''
    }
    
    words = text.split()
    translated = []
    for word in words:
        clean_word = word.lower().strip('.,')
        if clean_word in translations and translations[clean_word]:
            translated.append(translations[clean_word])
        elif clean_word not in translations or translations[clean_word]:  # Keep word if no translation or translation is empty string
            translated.append(word)
    
    return ' '.join(translated)

def normalize_address(house_number, building_name, street, locality, landmark, city, state, pincode, country):
    """
    Normalize address components into a standard format
    """
    address_parts = []
    if house_number:
        address_parts.append(str(house_number))
    if building_name and building_name.lower() != 'nan':
        address_parts.append(str(building_name))
    if street and street.lower() != 'nan':
        address_parts.append(str(street))
    if locality and locality.lower() != 'nan':
        address_parts.append(str(locality))
    if landmark and landmark.lower() != 'nan':
        address_parts.append(str(landmark))
    if city and city.lower() != 'nan':
        address_parts.append(str(city))
    if state and state.lower() != 'nan':
        address_parts.append(str(state))
    if pincode:
        address_parts.append(str(pincode))
    if country and country.lower() != 'nan':
        address_parts.append(str(country))
    
    return ', '.join(address_parts)

__all__ = ['process_hinglish_address', 'clean_text', 'expand_abbreviations', 'translate_terms', 'normalize_address']

# This ensures the package is properly recognized
__version__ = '1.0.0'