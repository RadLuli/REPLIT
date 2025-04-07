import os
import streamlit as st

def get_file_extension(filename):
    """
    Get the extension of a file
    
    Args:
        filename: Name of the file
    
    Returns:
        str: Extension of the file without the dot
    """
    return os.path.splitext(filename)[1][1:].lower()

def display_rating_stars(rating):
    """
    Display star rating in Streamlit
    
    Args:
        rating: Rating value (1-5)
    """
    # Ensure the rating is valid
    if rating is None:
        rating = 0
    rating = max(0, min(5, rating))
    
    # Display stars
    stars = "★" * int(rating) + "☆" * (5 - int(rating))
    
    # Display as HTML to get nice formatting
    st.markdown(f"""
    <div style="font-size: 24px; color: gold;">
        {stars} ({rating}/5)
    </div>
    """, unsafe_allow_html=True)

def create_photography_terms_glossary():
    """
    Create a glossary of photography terms in Brazilian Portuguese
    
    Returns:
        dict: Photography terms glossary
    """
    return {
        "aperture": {
            "pt": "abertura",
            "definition": "Abertura do diafragma da lente que controla a quantidade de luz que entra na câmera."
        },
        "shutter speed": {
            "pt": "velocidade do obturador",
            "definition": "Tempo durante o qual o obturador da câmera permanece aberto, expondo o sensor à luz."
        },
        "ISO": {
            "pt": "ISO",
            "definition": "Medida da sensibilidade do sensor da câmera à luz."
        },
        "depth of field": {
            "pt": "profundidade de campo",
            "definition": "Área da foto que aparece nítida e em foco."
        },
        "composition": {
            "pt": "composição",
            "definition": "Arranjo dos elementos visuais dentro do quadro da fotografia."
        },
        "rule of thirds": {
            "pt": "regra dos terços",
            "definition": "Princípio de composição que divide a imagem em nove partes iguais, com quatro pontos de interseção."
        },
        "exposure": {
            "pt": "exposição",
            "definition": "Quantidade de luz que atinge o sensor da câmera."
        },
        "white balance": {
            "pt": "balanço de branco",
            "definition": "Ajuste da câmera para representar corretamente as cores brancas e, consequentemente, todas as outras cores."
        },
        "bokeh": {
            "pt": "bokeh",
            "definition": "Qualidade estética das áreas desfocadas de uma fotografia."
        },
        "focal length": {
            "pt": "distância focal",
            "definition": "Característica da lente que determina o ângulo de visão e a ampliação da imagem."
        }
    }

def format_bytes(size):
    """
    Format file size in bytes to a human-readable format
    
    Args:
        size: Size in bytes
    
    Returns:
        str: Formatted size
    """
    # Define the suffixes
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
    
    # Determine the appropriate suffix
    suffix_index = 0
    while size > 1024 and suffix_index < len(suffixes) - 1:
        size /= 1024
        suffix_index += 1
    
    # Format the size
    if suffix_index == 0:
        return f"{size} {suffixes[suffix_index]}"
    else:
        return f"{size:.2f} {suffixes[suffix_index]}"
