import streamlit as st
import os
import tempfile
from PIL import Image
import io

from image_processor import (
    analyze_image, 
    enhance_image_brightness,
    enhance_image_contrast,
    enhance_image_sharpness,
    enhance_image_color
)
from document_processor import process_document
from rag_system import generate_rag_response
from llm_integration import load_llama_model
from translation import translate_to_portuguese
from utils import get_file_extension, display_rating_stars

# Set page configuration
st.set_page_config(
    page_title="Avaliação Fotográfica com IA",
    page_icon="📸",
    layout="wide"
)

# Initialize session state variables if they don't exist
if 'model' not in st.session_state:
    try:
        with st.spinner('Carregando modelo LLM...'):
            st.session_state.model = load_llama_model()
    except Exception as e:
        st.warning(f"Não foi possível carregar o modelo LLM: {str(e)}")
        # Create a simple mock model
        from langchain.llms.fake import FakeListLLM
        
        responses = [
            """
            Rating: 3/5 stars
            
            Technical Assessment:
            The photograph shows reasonable technical quality with adequate sharpness and a balanced exposure. The composition follows basic principles but could be improved for greater visual impact.
            
            Strengths:
            - Appropriate exposure for the main subject
            - Decent color balance
            - Clear subject identification
            
            Areas for Improvement:
            - Consider applying the rule of thirds more deliberately
            - Increase the contrast slightly to add visual impact
            - Pay attention to the background elements that may distract from the subject
            
            Post-processing Tips:
            - Try enhancing contrast by about 10-15%
            - Slightly increase saturation for more vibrant colors
            - Consider a subtle vignette to direct attention to the subject
            """
        ]
        
        st.session_state.model = FakeListLLM(responses=responses)
        st.session_state.model_status = "fallback"

if 'documents' not in st.session_state:
    st.session_state.documents = []

if 'document_embeddings' not in st.session_state:
    st.session_state.document_embeddings = None

if 'processed_image' not in st.session_state:
    st.session_state.processed_image = None

if 'image_analysis' not in st.session_state:
    st.session_state.image_analysis = None

if 'rag_response' not in st.session_state:
    st.session_state.rag_response = None

if 'rating' not in st.session_state:
    st.session_state.rating = None

if 'enhanced_image' not in st.session_state:
    st.session_state.enhanced_image = None

if 'enhancement_type' not in st.session_state:
    st.session_state.enhancement_type = None

if 'model_status' not in st.session_state:
    st.session_state.model_status = "normal"


# Title and description
st.title("Avaliação Fotográfica com IA")
st.markdown("""
Este sistema utiliza Inteligência Artificial para analisar e avaliar fotografias, 
fornecendo feedback e sugestões de melhoria com base em materiais de referência.
""")

# Sidebar for document upload and management
with st.sidebar:
    st.header("Materiais de Referência")
    st.markdown("Faça upload dos materiais de referência para análise fotográfica (PDF, EPUB, MOBI, AZW)")
    
    uploaded_docs = st.file_uploader(
        "Fazer upload de documentos", 
        type=["pdf", "epub", "mobi", "azw"], 
        accept_multiple_files=True
    )
    
    if uploaded_docs:
        for doc in uploaded_docs:
            # Check if document is already processed
            doc_already_processed = any(processed_doc['name'] == doc.name for processed_doc in st.session_state.documents)
            
            if not doc_already_processed:
                with st.spinner(f"Processando {doc.name}..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{get_file_extension(doc.name)}") as tmp:
                        tmp.write(doc.getvalue())
                        tmp_path = tmp.name
                    
                    # Process document and get text content
                    try:
                        doc_content = process_document(tmp_path)
                        st.session_state.documents.append({
                            'name': doc.name,
                            'content': doc_content,
                            'type': get_file_extension(doc.name)
                        })
                        st.success(f"Documento '{doc.name}' processado com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao processar '{doc.name}': {str(e)}")
                    finally:
                        # Clean up the temporary file
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
    
    # Display uploaded documents
    if st.session_state.documents:
        st.subheader("Documentos Processados:")
        for i, doc in enumerate(st.session_state.documents):
            st.write(f"{i+1}. {doc['name']} ({doc['type'].upper()})")
        
        if st.button("Limpar Todos os Documentos"):
            st.session_state.documents = []
            st.session_state.document_embeddings = None
            st.success("Todos os documentos foram removidos!")
            st.rerun()
    else:
        st.info("Nenhum documento de referência foi carregado ainda.")

# Main content area with tabs
tab1, tab2 = st.tabs(["Análise de Fotografia", "Melhorias Sugeridas"])

with tab1:
    st.header("Upload e Análise de Fotografia")
    
    # Image upload section
    uploaded_file = st.file_uploader("Faça upload da sua fotografia", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        # Display the uploaded image
        image = Image.open(uploaded_file)
        st.session_state.processed_image = image
        st.image(image, caption="Fotografia enviada", use_column_width=True)
        
        # Option to analyze the image
        if st.button("Analisar Fotografia"):
            if not st.session_state.documents:
                st.warning("Por favor, faça upload de pelo menos um documento de referência para uma análise completa.")
            
            with st.spinner("Analisando a imagem..."):
                # Get image analysis
                image_analysis = analyze_image(image)
                st.session_state.image_analysis = image_analysis
                
                # Generate RAG response based on image analysis and documents
                rag_response = generate_rag_response(
                    image_analysis,
                    st.session_state.documents,
                    st.session_state.model
                )
                
                # Translate response to Portuguese
                portuguese_response = translate_to_portuguese(rag_response)
                st.session_state.rag_response = portuguese_response
                
                # Extract rating from the response (assuming the model includes a rating)
                # In a real implementation, you might want a more robust way to extract this
                try:
                    # Very simple rating extraction for demo purposes
                    if "classificação: 5" in portuguese_response.lower() or "rating: 5" in portuguese_response.lower():
                        st.session_state.rating = 5
                    elif "classificação: 4" in portuguese_response.lower() or "rating: 4" in portuguese_response.lower():
                        st.session_state.rating = 4
                    elif "classificação: 3" in portuguese_response.lower() or "rating: 3" in portuguese_response.lower():
                        st.session_state.rating = 3
                    elif "classificação: 2" in portuguese_response.lower() or "rating: 2" in portuguese_response.lower():
                        st.session_state.rating = 2
                    else:
                        st.session_state.rating = 1
                except:
                    st.session_state.rating = 3  # Default rating if extraction fails
            
            # Display the results
            st.subheader("Resultados da Análise")
            st.markdown("### Avaliação")
            display_rating_stars(st.session_state.rating)
            
            st.markdown("### Feedback Detalhado")
            st.write(st.session_state.rag_response)

with tab2:
    st.header("Melhorias Sugeridas")
    
    if st.session_state.processed_image is not None and st.session_state.rag_response is not None:
        st.subheader("Sugestões para Melhoria da Fotografia")
        st.write(st.session_state.rag_response)
        
        st.subheader("Aplicar Melhorias Básicas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            enhancement_type = st.selectbox(
                "Selecione o tipo de melhoria:",
                ["Brilho", "Contraste", "Nitidez", "Cor"]
            )
            
            if enhancement_type == "Brilho":
                brightness_factor = st.slider("Ajuste de Brilho", 0.5, 2.0, 1.0, 0.1)
                if st.button("Aplicar Ajuste de Brilho"):
                    with st.spinner("Aplicando ajuste de brilho..."):
                        st.session_state.enhanced_image = enhance_image_brightness(st.session_state.processed_image, brightness_factor)
                        st.session_state.enhancement_type = "Brilho"
            
            elif enhancement_type == "Contraste":
                contrast_factor = st.slider("Ajuste de Contraste", 0.5, 2.0, 1.0, 0.1)
                if st.button("Aplicar Ajuste de Contraste"):
                    with st.spinner("Aplicando ajuste de contraste..."):
                        st.session_state.enhanced_image = enhance_image_contrast(st.session_state.processed_image, contrast_factor)
                        st.session_state.enhancement_type = "Contraste"
            
            elif enhancement_type == "Nitidez":
                sharpness_factor = st.slider("Ajuste de Nitidez", 0.0, 3.0, 1.0, 0.1)
                if st.button("Aplicar Ajuste de Nitidez"):
                    with st.spinner("Aplicando ajuste de nitidez..."):
                        st.session_state.enhanced_image = enhance_image_sharpness(st.session_state.processed_image, sharpness_factor)
                        st.session_state.enhancement_type = "Nitidez"
            
            elif enhancement_type == "Cor":
                color_factor = st.slider("Ajuste de Saturação de Cor", 0.0, 2.0, 1.0, 0.1)
                if st.button("Aplicar Ajuste de Cor"):
                    with st.spinner("Aplicando ajuste de cor..."):
                        st.session_state.enhanced_image = enhance_image_color(st.session_state.processed_image, color_factor)
                        st.session_state.enhancement_type = "Cor"
        
        with col2:
            if st.session_state.enhanced_image is not None:
                st.image(st.session_state.enhanced_image, caption=f"Imagem com ajuste de {st.session_state.enhancement_type} aplicado", use_column_width=True)
                
                # Save enhanced image button
                buf = io.BytesIO()
                st.session_state.enhanced_image.save(buf, format="PNG")
                byte_im = buf.getvalue()
                
                st.download_button(
                    label="Baixar Imagem Melhorada",
                    data=byte_im,
                    file_name="imagem_melhorada.png",
                    mime="image/png"
                )
            else:
                st.info("Selecione e aplique um tipo de melhoria para visualizar o resultado.")
    else:
        st.info("Por favor, primeiro faça upload e analise uma fotografia na aba 'Análise de Fotografia'.")

# Footer
st.markdown("---")
st.markdown("### Sobre este Sistema")
st.markdown("""
Este sistema utiliza o modelo Llama para análise de imagens e recuperação aumentada por geração (RAG) 
para fornecer feedback sobre fotografias com base em documentos de referência. Todos os resultados e sugestões 
são apresentados em Português Brasileiro.
""")
