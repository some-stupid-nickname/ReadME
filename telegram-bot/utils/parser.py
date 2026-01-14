"""Parser for LLM response text"""
import re
from typing import Dict, List, Tuple


def parse_llm_response(response: str, num_books: int) -> Dict[str, any]:
    """
    Parse LLM response to extract intro message and book recommendations
    
    Args:
        response: Raw LLM response text
        num_books: Number of books in the response
        
    Returns:
        Dictionary with:
        - 'intro': Introduction message (before first numbered recommendation)
        - 'recommendations': List of recommendation texts for each book
    """
    # Pattern to match numbered recommendations: \n\n1., \n\n2., etc.
    # Also handles cases like \n1., \n2. (without double newline)
    pattern = r'\n\n?\d+\.'
    
    # Find all matches
    matches = list(re.finditer(pattern, response))
    
    if not matches:
        # No numbered recommendations found, treat entire response as intro
        # and create empty recommendations
        return {
            'intro': clean_text(response),
            'recommendations': [''] * num_books
        }
    
    # Extract intro (text before first numbered recommendation)
    first_match = matches[0]
    intro = response[:first_match.start()].strip()
    
    # Extract recommendations
    recommendations = []
    
    for i, match in enumerate(matches):
        # Start position of current recommendation
        start = match.end()
        
        # End position (start of next recommendation or end of text)
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(response)
        
        # Extract recommendation text
        rec_text = response[start:end].strip()
        recommendations.append(clean_text(rec_text))
    
    # If we have fewer recommendations than books, pad with empty strings
    while len(recommendations) < num_books:
        recommendations.append('')
    
    # If we have more recommendations than books, truncate
    recommendations = recommendations[:num_books]
    
    return {
        'intro': clean_text(intro),
        'recommendations': recommendations
    }


def clean_text(text: str) -> str:
    """
    Clean text from formatting artifacts
    
    Args:
        text: Raw text with potential formatting issues
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove standalone \n1, \n2, etc. (not followed by space or text)
    text = re.sub(r'\\n\d+(?=\s|$)', '', text)
    
    # Replace literal \n with actual newlines (if present as string)
    text = text.replace('\\n', '\n')
    
    # Normalize multiple newlines to double newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text

