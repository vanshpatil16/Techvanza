import re
from typing import Dict, Tuple

# Hinglish to English mappings
HINGLISH_DIR = {
    "paas": "near",
    "najdik": "near",
    "nazdeek": "near",
    "samne": "in front of",
    "saamne": "in front of",
    "peeche": "behind",
    "piche": "behind",
    "andar": "inside",
    "bahar": "outside",
    "side": "side",
    "baju": "beside",
    "bagal": "beside",
    "opposite": "opposite",
    "samip": "near"
}

HINGLISH_PLACE = {
    "mandir": "temple",
    "masjid": "mosque",
    "gurudwara": "gurdwara",
    "school": "school",
    "dawai": "pharmacy",
    "aspatal": "hospital",
    "hospital": "hospital",
    "chai": "tea",
    "tapri": "stall",
    "kirana": "grocery store",
    "bazaar": "market",
    "chowk": "square",
    "nagar": "nagar",
    "society": "society",
    "gali": "lane",
    "rasta": "road",
    "sadak": "road",
    "marg": "road",
    "road": "road"
}

CONNECTORS = {
    "ke paas": "near",
    "ke pass": "near",
    "ke samne": "in front of",
    "ke saamne": "in front of",
    "ke peeche": "behind",
    "ke piche": "behind",
    "ke andar": "inside",
    "ke bahar": "outside",
    "ke bagal mein": "beside",
    "ke baju mein": "beside",
    "wali gali": "lane",
    "wala rasta": "road",
    "wali sadak": "road",
    "wale raste": "road"
}

def normalize_text(text: str) -> str:
    """Normalize the input text by converting to lowercase, removing extra spaces, etc."""
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace common punctuation with commas
    text = re.sub(r'[\-\/\\]', ',', text)
    
    # Remove other special characters except alphanumeric, comma, and space
    text = re.sub(r'[^\w\s,]', ' ', text)
    
    # Normalize repeated characters (e.g., 'nooo' -> 'no')
    text = re.sub(r'(.)\1{2,}', r'\1', text)
    
    # Remove extra spaces and trim
    text = ' '.join(text.split())
    
    return text

def replace_phrases(text: str) -> str:
    """Replace common Hinglish phrases with their English equivalents."""
    # Process multi-word phrases first (longer ones first to avoid partial matches)
    for phrase in sorted(CONNECTORS.keys(), key=len, reverse=True):
        if phrase in text:
            text = text.replace(phrase, CONNECTORS[phrase])
    return text

def replace_words(text: str) -> str:
    """Replace individual Hinglish words with their English equivalents."""
    words = text.split()
    processed_words = []
    
    for word in words:
        # Check place names first
        if word in HINGLISH_PLACE:
            processed_words.append(HINGLISH_PLACE[word])
        # Then check direction words
        elif word in HINGLISH_DIR:
            processed_words.append(HINGLISH_DIR[word])
        else:
            processed_words.append(word)
    
    return ' '.join(processed_words)

def process_hinglish_address(address: str) -> Tuple[str, Dict]:
    """
    Process a Hinglish address and return the normalized English version.
    
    Returns:
        tuple: (normalized_address, metadata)
    """
    original = address.strip()
    
    # Step 1: Normalize text
    normalized = normalize_text(original)
    
    # Step 2: Replace phrases (multi-word patterns)
    processed = replace_phrases(normalized)
    
    # Step 3: Replace individual words
    processed = replace_words(processed)
    
    # Step 4: Clean up any remaining issues
    processed = ' '.join(processed.split())  # Remove extra spaces
    
    # Extract metadata
    metadata = {
        "original": original,
        "normalized": normalized,
        "is_hinglish": processed.lower() != normalized.lower(),
        "components": {
            "landmarks": [],
            "directions": [],
            "street_parts": []
        }
    }
    
    # Simple extraction of components (can be enhanced)
    for word in processed.split():
        if word in HINGLISH_PLACE.values():
            metadata["components"]["landmarks"].append(word)
        elif word in HINGLISH_DIR.values():
            metadata["components"]["directions"].append(word)
        elif word in ["lane", "road", "street"]:
            metadata["components"]["street_parts"].append(word)
    
    return processed, metadata
