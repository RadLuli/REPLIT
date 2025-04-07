import os
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
import requests
import urllib.parse

def get_google_translate_api():
    """Get Google Translate API key from environment variable"""
    return os.getenv("GOOGLE_TRANSLATE_API_KEY", "")

def translate_with_huggingface(text, target_lang="pt-br"):
    """
    Translate text using Hugging Face translation model
    
    Args:
        text: Text to translate
        target_lang: Target language code
    
    Returns:
        str: Translated text
    """
    try:
        # Load Helsinki-NLP's translation model
        model_name = "Helsinki-NLP/opus-mt-en-ROMANCE"
        
        # Initialize the tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        
        # Create translation pipeline
        translator = pipeline("translation", model=model, tokenizer=tokenizer)
        
        # Split the text into chunks to handle long texts
        max_length = 512
        chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
        
        # Translate each chunk
        translated_chunks = []
        for chunk in chunks:
            translation = translator(chunk, max_length=max_length*2)
            translated_chunks.append(translation[0]['translation_text'])
        
        # Join the translated chunks
        translated_text = ' '.join(translated_chunks)
        
        # Do some post-processing to ensure proper Brazilian Portuguese
        # Replace some common terms that might be translated to European Portuguese
        translated_text = translated_text.replace("tu ", "você ")
        
        return translated_text
    
    except Exception as e:
        print(f"Error in Hugging Face translation: {str(e)}")
        # Fallback to another method or return the original text
        return fallback_translation(text, target_lang)

def translate_with_google(text, target_lang="pt-BR"):
    """
    Translate text using Google Translate API (free tier)
    
    Args:
        text: Text to translate
        target_lang: Target language code
    
    Returns:
        str: Translated text
    """
    try:
        api_key = get_google_translate_api()
        
        # If no API key, use the free endpoint (limited usage)
        if not api_key:
            # URL encode the text
            encoded_text = urllib.parse.quote(text)
            
            # Create the URL for the free tier (no authentication required)
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target_lang}&dt=t&q={encoded_text}"
            
            # Make the request
            response = requests.get(url)
            
            # Check if the request was successful
            if response.status_code == 200:
                # Parse the response
                result = response.json()
                
                # Extract the translated text
                translated_text = ""
                for sentence in result[0]:
                    if sentence[0]:
                        translated_text += sentence[0]
                
                return translated_text
            else:
                raise Exception(f"Google Translate API returned status code {response.status_code}")
        else:
            # For the paid tier with API key (not implemented here)
            # This would use the official Google Cloud Translation API
            raise NotImplementedError("Paid Google Translate API not implemented")
    
    except Exception as e:
        print(f"Error in Google translation: {str(e)}")
        return text  # Return original text as fallback

def fallback_translation(text, target_lang="pt-br"):
    """
    Simple rule-based fallback translation for when all else fails
    This is a very limited implementation and should only be used as a last resort
    
    Args:
        text: Text to translate
        target_lang: Target language code
    
    Returns:
        str: Partially translated text
    """
    # This is a very simple dictionary-based translation for essential photography terms
    # Only meant as an absolute last resort
    en_to_pt = {
        "photograph": "fotografia",
        "photography": "fotografia",
        "exposure": "exposição",
        "brightness": "brilho",
        "contrast": "contraste",
        "sharpness": "nitidez",
        "composition": "composição",
        "color": "cor",
        "colors": "cores",
        "balance": "equilíbrio",
        "rating": "classificação",
        "stars": "estrelas",
        "improvement": "melhoria",
        "suggestions": "sugestões",
        "lighting": "iluminação",
        "focus": "foco",
        "depth": "profundidade",
        "field": "campo",
        "depth of field": "profundidade de campo",
        "aperture": "abertura",
        "shutter": "obturador",
        "speed": "velocidade",
        "ISO": "ISO",
        "white balance": "balanço de branco",
        "post-processing": "pós-processamento",
        "editing": "edição",
        "filter": "filtro",
        "filters": "filtros",
        "lens": "lente",
        "camera": "câmera",
        "digital": "digital",
        "sensor": "sensor",
        "image": "imagem",
        "picture": "imagem",
        "highlights": "destaques",
        "shadows": "sombras",
        "composition": "composição",
        "rule of thirds": "regra dos terços",
        "framing": "enquadramento",
        "perspective": "perspectiva",
        "angle": "ângulo",
        "background": "fundo",
        "foreground": "primeiro plano",
        "subject": "assunto",
        "portrait": "retrato",
        "landscape": "paisagem",
        "macro": "macro",
        "street photography": "fotografia de rua",
        "wildlife": "vida selvagem",
        "architecture": "arquitetura"
    }
    
    # Very simple word-by-word replacement
    for en_word, pt_word in en_to_pt.items():
        # Replace whole words only
        text = text.replace(f" {en_word} ", f" {pt_word} ")
        # Beginning of text
        text = text.replace(f"{en_word} ", f"{pt_word} ")
        # End of text or before punctuation
        text = text.replace(f" {en_word}.", f" {pt_word}.")
        text = text.replace(f" {en_word},", f" {pt_word},")
        text = text.replace(f" {en_word}!", f" {pt_word}!")
        text = text.replace(f" {en_word}?", f" {pt_word}?")
        text = text.replace(f" {en_word}:", f" {pt_word}:")
        text = text.replace(f" {en_word};", f" {pt_word};")
    
    return text

def translate_to_portuguese(text):
    """
    Translate text to Brazilian Portuguese using the best available method
    
    Args:
        text: Text to translate
    
    Returns:
        str: Translated text
    """
    try:
        # Try Hugging Face first
        result = translate_with_huggingface(text)
        
        # If the result is empty or unchanged, try Google Translate
        if not result or result == text:
            result = translate_with_google(text)
        
        # If still no translation, use the fallback
        if not result or result == text:
            result = fallback_translation(text)
        
        return result
    except Exception as e:
        print(f"Translation failed: {str(e)}")
        # If all translation methods fail, return the original text
        return text
