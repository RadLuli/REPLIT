import streamlit as st

# Set page configuration first
st.set_page_config(
    page_title="Avaliação Fotográfica com IA",
    page_icon="📸",
    layout="wide"
)

# Import Google Fonts and set custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;500;600;700&family=Montserrat:wght@300;400;500;600&display=swap');
    /* Modern dark theme customization */
    .stApp {
        background-color: #1A1C1E;
    }

    /* Card-like containers */
    .element-container {
        background-color: #232527;
        border-radius: 8px;
        padding: 1.25rem;
        margin: 0.75rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Text elements */
    h1, h2, h3 {
        color: white !important;
        font-family: 'Barlow Condensed', sans-serif !important;
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    /* Body text */
    body, p, div, span {
        font-family: 'Montserrat', sans-serif !important;
        color: rgba(255, 255, 255, 0.87);
    }

    /* Streamlit elements */
    .stMarkdown, .stText {
        font-family: 'Montserrat', sans-serif !important;
        color: rgba(255, 255, 255, 0.87);
    }

    /* File uploader */
    .stFileUploader {
        border-radius: 8px;
        border: 1px dashed rgba(255, 255, 255, 0.2);
        padding: 1rem;
        background-color: #232527;
    }

    /* Selectbox and other inputs */
    .stSelectbox, .stTextInput {
        background-color: #232527;
        border-radius: 6px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Buttons */
    .stButton button {
        background-color: #28a745; /* Green */
        color: white;
        border: none;
        padding: 0.7rem 1.5rem;
        border-radius: 6px;
        cursor: pointer;
    }

    .stButton button:hover {
        background-color: #218838; /* Darker green on hover */
    }

    /* Image containers */
    .stImage {
        border-radius: 8px;
        overflow: hidden;
    }

</style>
""", unsafe_allow_html=True)

# Rest of your existing app.py code...

import streamlit as st
import os
import tempfile
import base64
import uuid
import secrets
import json
from datetime import datetime
from PIL import Image
import io
from io import BytesIO
from urllib.parse import urlencode

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
from database import DB
from google_auth import get_auth_url, exchange_code_for_token, get_user_info, validate_state, GoogleAuthError
from photography_tips import get_tip_of_the_day, get_tip_by_topic

# Helper functions for authentication
def hash_password(password):
    """Simple password hashing"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def generate_google_auth_url():
    """Generate Google OAuth authorization URL"""
    # Create a redirect URI that Streamlit can handle
    # Get the base URL for the Streamlit app
    base_url = '/'
    redirect_uri = f"{base_url}google-auth-callback"

    try:
        # Get the authorization URL from the Google Auth module
        auth_url, auth_state = get_auth_url(redirect_uri)

        # Store the state in session
        st.session_state.google_auth_state = auth_state

        return auth_url
    except Exception as e:
        st.error(f"Erro ao gerar URL de autenticação Google: {str(e)}")
        return None

def handle_google_auth_callback():
    """Handle the callback from Google OAuth"""
    # Get query parameters
    try:
        code = st.query_params.get('code', None)
        state = st.query_params.get('state', None)
        error = st.query_params.get('error', None)
    except:
        # Fallback for older Streamlit versions
        code = st.experimental_get_query_params().get('code', [None])[0] if 'code' in st.experimental_get_query_params() else None
        state = st.experimental_get_query_params().get('state', [None])[0] if 'state' in st.experimental_get_query_params() else None
        error = st.experimental_get_query_params().get('error', [None])[0] if 'error' in st.experimental_get_query_params() else None

    # Check for errors
    if error:
        st.error(f"Erro de autenticação Google: {error}")
        return False

    # Check if code and state are present
    if not code or not state:
        st.warning("Parâmetros de autenticação incompletos")
        return False

    # Check if we have stored state
    if 'google_auth_state' not in st.session_state:
        st.error("Estado de autenticação perdido. Por favor, tente novamente.")
        return False

    try:
        # Validate state
        stored_state = st.session_state.google_auth_state.get('state')
        validate_state(state, stored_state)

        # Get code verifier and redirect URI from stored state
        code_verifier = st.session_state.google_auth_state.get('code_verifier')
        redirect_uri = st.session_state.google_auth_state.get('redirect_uri')

        # Exchange code for token
        token_response = exchange_code_for_token(code, code_verifier, redirect_uri)
        access_token = token_response.get('access_token')

        # Get user info
        user_info = get_user_info(access_token)

        # Extract user data
        google_id = user_info.get('id')
        email = user_info.get('email')
        name = user_info.get('name')

        # Check if user exists by Google ID
        user = DB.get_user_by_google_id(google_id)

        if user:
            # User exists, log them in
        st.session_state.logged_in = True
        st.session_state.username = user.get('username')
        st.session_state.auth_type = 'google'

            # Clear the URL parameters
            try:
                st.query_params.clear()
            except:
                # Fallback for older Streamlit versions
                try:
                    st.experimental_set_query_params()
                except:
                    pass
            return True
        else:
            # Create a new username based on email
            username_base = email.split('@')[0]
            username = username_base
            counter = 1

            # Check if username exists
            while DB.get_user(username):
                username = f"{username_base}{counter}"
                counter += 1

            # Save the new user
            DB.save_user(username, None, email, name, google_id)

            # Log them in
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.auth_type = 'google'

            # Clear the URL parameters
            try:
                st.query_params.clear()
            except:
                # Fallback for older Streamlit versions
                try:
                    st.experimental_set_query_params()
                except:
                    pass
            return True
    except Exception as e:
        st.error(f"Erro durante a autenticação Google: {str(e)}")
        return False

def login():
    """Handle user login"""
    st.header("Login")

    # Check if we're in a callback from Google OAuth
    try:
        has_code = 'code' in st.query_params
        has_state = 'state' in st.query_params
    except:
        # Fallback for older Streamlit versions
        has_code = 'code' in st.experimental_get_query_params()
        has_state = 'state' in st.experimental_get_query_params()

    if has_code and has_state:
        if handle_google_auth_callback():
            st.success("Login com Google realizado com sucesso!")
            st.rerun()
            return True

    username = st.text_input("Nome de Usuário")
    password = st.text_input("Senha", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Entrar"):
            if not username or not password:
                st.error("Por favor, preencha todos os campos")
                return False

            # Hash the password
            hashed_password = hash_password(password)

            # Authenticate user
            if DB.authenticate_user(username, hashed_password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.auth_type = 'local'
                st.rerun()
                return True
            else:
                st.error("Nome de usuário ou senha incorretos")
                return False

    with col2:
        # Add Google login button
        google_auth_url = generate_google_auth_url()
        if google_auth_url:
            google_login_html = f"""
            <a href="{google_auth_url}" style="display: inline-block; 
                background-color: #4285F4; color: white; 
                padding: 10px 20px; text-align: center; 
                text-decoration: none; font-size: 16px; 
                margin: 4px 2px; cursor: pointer; 
                border-radius: 4px;">
                Entrar com Google
            </a>
            """
            st.markdown(google_login_html, unsafe_allow_html=True)

    return False

def register():
    """Handle user registration"""
    st.header("Registrar")

    username = st.text_input("Nome de Usuário", key="reg_username")
    password = st.text_input("Senha", type="password", key="reg_password")
    confirm_password = st.text_input("Confirmar Senha", type="password")
    email = st.text_input("Email (opcional)")
    name = st.text_input("Nome Completo (opcional)")

    if st.button("Registrar"):
        if not username or not password:
            st.error("Nome de usuário e senha são obrigatórios")
            return False

        if password != confirm_password:
            st.error("As senhas não coincidem")
            return False

        # Check if user already exists
        existing_user = DB.get_user(username)
        if existing_user:
            st.error("Nome de usuário já existe, escolha outro")
            return False

        # Hash the password
        hashed_password = hash_password(password)

        # Save user
        DB.save_user(username, hashed_password, email, name)
        st.success("Registro bem-sucedido! Faça login para continuar.")
        return True

    return False

# No longer needed - removed logout function since authentication was removed

def save_analysis_to_db():
    """Save current analysis to database"""
    if 'processed_image' in st.session_state and st.session_state.processed_image:
        if 'image_id' not in st.session_state:
            # Generate a unique ID for the image
            st.session_state.image_id = str(uuid.uuid4())

        # Convert image to base64
        buffer = BytesIO()
        st.session_state.processed_image.save(buffer, format="PNG")
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # Get analysis results
        analysis_results = {
            'rating': st.session_state.rating if 'rating' in st.session_state else None,
            'analysis': st.session_state.rag_response if 'rag_response' in st.session_state else None,
            'technical_data': st.session_state.image_analysis if 'image_analysis' in st.session_state else None,
            'timestamp': datetime.now().isoformat()
        }

        # Get enhancement data if available
        enhancement_type = st.session_state.enhancement_type if 'enhancement_type' in st.session_state else None
        enhanced_image_data = None

        if 'enhanced_image' in st.session_state and st.session_state.enhanced_image:
            buffer = BytesIO()
            st.session_state.enhanced_image.save(buffer, format="PNG")
            enhanced_image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # Save to database
        DB.save_image_analysis(
            st.session_state.image_id,
            st.session_state.username,
            image_data,
            analysis_results,
            enhancement_type,
            enhanced_image_data
        )
        return True

    return False



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

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'username' not in st.session_state:
    st.session_state.username = None

if 'auth_type' not in st.session_state:
    st.session_state.auth_type = None

if 'google_auth_state' not in st.session_state:
    st.session_state.google_auth_state = None

if 'image_id' not in st.session_state:
    st.session_state.image_id = None

if 'user_gallery' not in st.session_state:
    st.session_state.user_gallery = []

if 'photo_tip' not in st.session_state:
    st.session_state.photo_tip = None

# Set default user (no login required)
if not st.session_state.logged_in:
    st.session_state.logged_in = True
    st.session_state.username = "usuario_padrao"
    st.session_state.auth_type = "local"

# Sidebar for document upload and image history
with st.sidebar:
    st.header("Materiais de Referência")
    st.markdown("Faça upload dos materiais de referência para análise fotográfica (PDF, EPUB, MOBI, AZW)")

uploaded_docs = st.file_uploader(
"Fazer upload de documentos", 
type=["pdf", "epub", "mobi", "azw"], 
accept_multiple_files=True
)
# Placeholder for additional sidebar content
st.header("Histórico de Análises")
# Load user's image history
try:
user_images = DB.get_user_images(st.session_state.username)
st.session_state.user_gallery = user_images
if user_images:
st.write(f"Você tem {len(user_images)} imagens analisadas")
for i, img_data in enumerate(user_images):
st.markdown(f"**{i+1}. Imagem analisada em {img_data['upload_date'][:10]}**")
                    if img_data['thumbnail']:
                        # Display a smaller thumbnail
                        st.image(f"data:image/png;base64,{img_data['thumbnail']}", width=100)
    
                    if img_data['latest_analysis'] and 'rating' in img_data['latest_analysis']:
                        st.write(f"Classificação: {img_data['latest_analysis']['rating']}/5")
    
                    # Button to load this image and its analysis
                    if st.button(f"Carregar análise #{i+1}", key=f"load_img_{img_data['id']}"):
                        # Get full image details
                        image_details = DB.get_image_details(img_data['id'])
    
                        if image_details and image_details['analysis_history']:
                            # Get the first entry with image data
                            first_entry = image_details['analysis_history'][0]
                            if 'image_data' in first_entry:
                                # Convert base64 back to image
                                import base64
                                from io import BytesIO
                                img_bytes = base64.b64decode(first_entry['image_data'])
                                img = Image.open(BytesIO(img_bytes))
    
                                # Update session state
                                st.session_state.processed_image = img
                                st.session_state.image_id = img_data['id']
    
                                # Get the most recent analysis
                                latest_analysis = image_details['analysis_history'][-1]
                                if 'analysis_results' in latest_analysis:
                                    results = latest_analysis['analysis_results']
    
                                    if 'rating' in results:
                                        st.session_state.rating = results['rating']
    
                                    if 'analysis' in results:
                                        st.session_state.rag_response = results['analysis']
    
                                    if 'technical_data' in results:
                                        st.session_state.image_analysis = results['technical_data']
    
                                # Check if there's an enhancement
                                if 'enhancement' in latest_analysis:
                                    enhancement = latest_analysis['enhancement']
                                    st.session_state.enhancement_type = enhancement['type']
    
                                    # Load enhanced image if available
                                    if 'image_data' in enhancement:
                                        enhanced_img_bytes = base64.b64decode(enhancement['image_data'])
                                        enhanced_img = Image.open(BytesIO(enhanced_img_bytes))
                                        st.session_state.enhanced_image = enhanced_img
    
                                st.success("Análise carregada com sucesso!")
                                st.rerun()
            else:
                st.info("Você ainda não tem análises salvas.")
        except Exception as e:
            st.error(f"Erro ao carregar histórico: {str(e)}")

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
# Main content area with tabs
tab1, tab2, tab3 = st.tabs(["Análise de Fotografia", "Melhorias Sugeridas", "Dica do Dia"])

with tab1:
    st.header("Upload e Análise de Fotografia")

    # Image upload section
    uploaded_file = st.file_uploader("Faça upload da sua fotografia", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # Display the uploaded image
        image = Image.open(uploaded_file)
        st.session_state.processed_image = image
        st.image(image, caption="Fotografia enviada", use_container_width=True)

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

                # Save analysis to database
                try:
                    if save_analysis_to_db():
                    st.success("Análise salva no banco de dados!")
                except Exception as e:
                    st.warning(f"Não foi possível salvar a análise no banco de dados: {str(e)}")

            display_rating_stars(st.session_state.rating)
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
                st.image(st.session_state.enhanced_image, caption=f"Imagem com ajuste de {st.session_state.enhancement_type} aplicado", use_container_width=True)

                # Save enhanced image button
                buf = io.BytesIO()
                st.session_state.enhanced_image.save(buf, format="PNG")
                byte_im = buf.getvalue()

                # Save to database button
                if st.button("Salvar no Sistema", key="save_enhanced"):
                    try:
                        # Update enhancement in session state
                        st.session_state.enhancement_type = enhancement_type

                        # Save to database
                        if save_analysis_to_db():
                        st.success("Imagem melhorada salva no banco de dados!")
                    except Exception as e:
                        st.warning(f"Não foi possível salvar a imagem melhorada: {str(e)}")

                # Download button
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

# Tip of the Day tab
with tab3:
    st.header("Dica de Fotografia do Dia")

    # Initialize tip in session state if not already there
    if 'photo_tip' not in st.session_state:
        with st.spinner('Gerando dica de fotografia...'):
            st.session_state.photo_tip = get_tip_of_the_day(st.session_state.model)

    # Display the tip
    if st.session_state.photo_tip:
        st.subheader(st.session_state.photo_tip["title"])
        st.write(st.session_state.photo_tip["content"])
        st.caption(f"Tópico: {st.session_state.photo_tip['topic']}")
        st.caption(f"Data: {st.session_state.photo_tip['date']}")

    # Get a different tip
    if st.button("Nova Dica"):
        with st.spinner('Gerando nova dica de fotografia...'):
            st.session_state.photo_tip = get_tip_of_the_day(st.session_state.model, force_refresh=True)
            st.rerun()

    # Get a tip on a specific topic
    st.subheader("Buscar Dica por Tópico")
    from photography_tips import PHOTOGRAPHY_TIP_TOPICS

    topic = st.selectbox("Selecione um tópico de fotografia:", PHOTOGRAPHY_TIP_TOPICS)

    if st.button("Buscar Dica por Tópico"):
        with st.spinner(f'Gerando dica sobre {topic}...'):
            topic_tip = get_tip_by_topic(st.session_state.model, topic)
            st.subheader(topic_tip["title"])
            st.write(topic_tip["content"])
            st.caption(f"Tópico: {topic_tip['topic']}")

