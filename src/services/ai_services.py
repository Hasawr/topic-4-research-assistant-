# def extract_arxiv_keywords(query: str) -> str:
#     """
#     İstifadəçinin uzun sualından arXiv üçün lazımsız sözləri (stop-words) təmizləyir 
#     və axtarış üçün təmiz açar sözlər (keywords) qaytarır.
#     """
#     # Lazımsız bağlayıcılar və sual əvəzlikləri (həm İngiliscə, həm Azərbaycanca)
#     stop_words = {
#         "what", "is", "how", "does", "do", "are", "the", "a", "an", "in", "on", 
#         "of", "for", "and", "or", "to", "with", "about", "impact", "role",
#         "nedir", "nece", "kimdir", "hansi", "ve", "ile", "ucun", "da", "de"
#     }
 
#     clean_query = re.sub(r'[^\w\s]', '', query.lower())
    
#     words = clean_query.split()
#     keywords = [word for word in words if word not in stop_words and len(word) > 2]
    
#     return " AND ".join(keywords[:4])
# import re

# def extract_keywords(query: str) -> str:
#     """
#     İstifadəçinin uzun sualından lazımsız sözləri təmizləyir 
#     və axtarış üçün təmiz açar sözlər qaytarır.
#     """
#     stop_words = {
#         "what", "is", "how", "does", "do", "are", "the", "a", "an", "in", "on", 
#         "of", "for", "and", "or", "to", "with", "about", "impact", "role", "at", "level",
#         "nedir", "nece", "kimdir", "hansi", "ve", "ile", "ucun", "da", "de"
#     }

#     clean_query = re.sub(r'[^\w\s\-]', '', query.lower())
    
#     words = clean_query.split()
#     keywords = [word for word in words if word not in stop_words and len(word) > 2]
    
#     return " ".join(keywords[:3])





import re

def extract_keywords(query: str) -> str:
    """
    İstifadəçinin uzun sualından lazımsız sözləri təmizləyir 
    və axtarış üçün təmiz açar sözlər qaytarır.
    """
    stop_words = {
        "what", "is", "how", "does", "do", "are", "were", "was", "the", "a", "an", "in", "on", 
        "of", "for", "and", "or", "to", "with", "about", "impact", "role", "at", "level",
        "nedir", "nece", "kimdir", "hansi", "ve", "ile", "ucun", "da", "de"
    }
 
    clean_query = re.sub(r'[^\w\s\-]', '', query.lower())
    
    words = clean_query.split()
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    
    return " ".join(keywords)