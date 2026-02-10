def clean_original_text(text: str) -> str:
    """
    텍스트의 앞뒤 공백과 개행문자를 제거합니다.
    
    Args:
        text: 정리할 텍스트
        
    Returns:
        앞뒤 공백과 개행문자가 제거된 텍스트
    """
    if not text:
        return ""
    return str(text).strip()
