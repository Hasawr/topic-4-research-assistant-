import re
from ai.providers.factory import get_llm


def extract_keywords_fallback(query: str) -> str:
    """
    İstifadəçinin uzun sualından lazımsız sözləri təmizləyir 
    və axtarış üçün təmiz açar sözlər qaytarır.
    """
    stop_words = {
        "what", "is", "how", "does", "do", "are", "were", "was", "the", "a", "an", "in", "on", 
        "of", "for", "and", "or", "to", "with", "about", "impact", "role", "at", "level",
        "its", "main", "stages", "types", "current", "state", "properties",
        "nedir", "nece", "kimdir", "hansi", "ve", "ile", "ucun", "da", "de"
    }
 
    clean_query = re.sub(r'[^\w\s\-]', '', query.lower())
    
    words = clean_query.split()
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    
    return " ".join(keywords)





def extract_keywords(query: str) -> str:
    """
    LLM istifadə edərək sualdan ən təmiz açar sözləri çıxarır. 
    Əgər LLM xəta verərsə, avtomatik olaraq fallback (B planı) işə düşür.
    """
    # 1. LLM üçün sərt və dəqiq təlimat (Prompt)
    prompt = f"""
    Sən axtarış sistemləri üçün açar sözlər çıxaran bir agentsən.
    İstifadəçinin verdiyi aşağıdakı sualdan Wikipedia və ArXiv-də axtarış etmək üçün ən vacib 1-3 açar sözü çıxar.
    QAYDALAR:
    - Heç bir əlavə söz yazma (məsələn, "Açar sözlər bunlardır:" kimi cümlələr qurma).
    - Durğu işarələri (nöqtə, vergül) istifadə etmə.
    - YALNIZ və YALNIZ ingiliscə açar sözləri qaytar.
    
    Sual: "{query}"
    """
    
    try:
        llm = get_llm()
        llm_response = llm.complete(prompt)

        clean_keywords = llm_response.strip().replace('"', '').replace("'", "")

        if not clean_keywords:
            raise ValueError("LLM boş cavab qaytardı.")
            
        return clean_keywords
        
    except Exception as e:
        print(f"[XƏBƏRDARLIQ] Agentic keyword extraction uğursuz oldu: {e}. Ehtiyat (fallback) sistem işə düşür...")
        return extract_keywords_fallback(query)