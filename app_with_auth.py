import streamlit as st
import os
import requests
import json
import uuid
import hashlib
import base64
import io
from datetime import datetime, timedelta
from PIL import Image

# Configure page
st.set_page_config(
    page_title="AI-Powered Photography Assessment",
    page_icon="📸",
    layout="wide"
)

# ==============================
# Database utilities
# ==============================
class DB:
    """Database interface - adapts to PostgreSQL or JSON file storage"""
    
    @classmethod
    def _ensure_file(cls, file_path, default_content=None):
        """Ensure the file exists and has valid JSON content"""
        if not os.path.exists(file_path):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(default_content or {}, f)
        else:
            try:
                with open(file_path, 'r') as f:
                    json.load(f)
            except json.JSONDecodeError:
                with open(file_path, 'w') as f:
                    json.dump(default_content or {}, f)
    
    @classmethod
    def _load_data(cls, file_path):
        """Load data from a JSON file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    @classmethod
    def _save_data(cls, file_path, data):
        """Save data to a JSON file"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def save_user(cls, username, password_hash=None, email=None, name=None, google_id=None):
        """Save or update user information"""
        # Use simple JSON file storage as fallback
        users_file = 'data/users.json'
        cls._ensure_file(users_file, {"users": {}})
        
        users_data = cls._load_data(users_file)
        
        # Create or update user
        users_data.setdefault("users", {})
        users_data["users"][username] = {
            "username": username,
            "password_hash": password_hash,
            "email": email,
            "name": name,
            "google_id": google_id,
            "created_at": users_data["users"].get(username, {}).get("created_at", datetime.now().isoformat()),
            "updated_at": datetime.now().isoformat()
        }
        
        cls._save_data(users_file, users_data)
    
    @classmethod
    def get_user_by_google_id(cls, google_id):
        """Get user by Google ID"""
        users_file = 'data/users.json'
        cls._ensure_file(users_file, {"users": {}})
        
        users_data = cls._load_data(users_file)
        
        # Find user by Google ID
        for username, user_data in users_data.get("users", {}).items():
            if user_data.get("google_id") == google_id:
                return user_data
        
        return None
    
    @classmethod
    def get_user(cls, username):
        """Get user information"""
        users_file = 'data/users.json'
        cls._ensure_file(users_file, {"users": {}})
        
        users_data = cls._load_data(users_file)
        
        # Return user data if exists
        if username in users_data.get("users", {}):
            return users_data["users"][username]
        
        return None

    @classmethod
    def save_image_analysis(cls, image_id, username, image_data, analysis_results, 
                         enhancement_type=None, enhanced_image_data=None):
        """Save image analysis results to JSON file storage"""
        images_file = 'data/images.json'
        cls._ensure_file(images_file, {"images": {}})
        
        images_data = cls._load_data(images_file)
        images_data.setdefault("images", {})
        
        # Create a thumbnail of the image
        try:
            thumbnail_data = None
            if image_data:
                # Decode base64 image
                img_bytes = base64.b64decode(image_data)
                img = Image.open(io.BytesIO(img_bytes))
                
                # Create thumbnail
                img.thumbnail((100, 100))
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                thumbnail_data = base64.b64encode(buf.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"Thumbnail creation error: {str(e)}")
            thumbnail_data = None
        
        # Get current timestamp
        timestamp = datetime.now().isoformat()
        
        # Create entry if it doesn't exist
        if image_id not in images_data["images"]:
            images_data["images"][image_id] = {
                "id": image_id,
                "username": username,
                "upload_date": timestamp,
                "thumbnail": thumbnail_data,
                "analysis_history": []
            }
        
        # Add new analysis to history
        analysis_entry = {
            "timestamp": timestamp,
            "image_data": image_data,
            "analysis_results": analysis_results
        }
        
        # Add enhancement if available
        if enhancement_type and enhanced_image_data:
            analysis_entry["enhancement"] = {
                "type": enhancement_type,
                "image_data": enhanced_image_data
            }
        
        # Add to history
        images_data["images"][image_id]["analysis_history"].append(analysis_entry)
        
        # Update latest analysis reference
        images_data["images"][image_id]["latest_analysis"] = analysis_results
        
        # Save data
        cls._save_data(images_file, images_data)
        return True

    @classmethod
    def get_user_images(cls, username):
        """Get all images for a user"""
        images_file = 'data/images.json'
        cls._ensure_file(images_file, {"images": {}})
        
        images_data = cls._load_data(images_file)
        
        # Filter images by username
        user_images = []
        for image_id, image_data in images_data.get("images", {}).items():
            if image_data.get("username") == username:
                user_images.append(image_data)
        
        # Sort by upload date (newest first)
        user_images.sort(key=lambda x: x.get("upload_date", ""), reverse=True)
        
        return user_images

    @classmethod
    def get_image_details(cls, image_id):
        """Get detailed information for a specific image"""
        images_file = 'data/images.json'
        cls._ensure_file(images_file, {"images": {}})
        
        images_data = cls._load_data(images_file)
        
        # Return image data if exists
        if image_id in images_data.get("images", {}):
            return images_data["images"][image_id]
        
        return None

# ==============================
# Google OAuth Integration
# ==============================
def generate_random_state():
    """Generate a random state parameter for OAuth"""
    return str(uuid.uuid4())

def hash_password(password):
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_code_verifier():
    """Generate a random code verifier for PKCE"""
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8')
    code_verifier = code_verifier.replace('=', '')
    return code_verifier

def generate_code_challenge(code_verifier):
    """Generate code challenge from code verifier for PKCE"""
    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
    code_challenge = code_challenge.replace('=', '')
    return code_challenge

def generate_google_auth_url():
    """Generate Google OAuth authorization URL"""
    try:
        # Get OAuth credentials from environment
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        if not client_id:
            st.warning("Google OAuth credentials not configured.")
            return None
        
        # Generate state and code verifier
        state = generate_random_state()
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)
        
        # Store state and code verifier in session for later verification
        st.session_state.google_auth_state = state
        st.session_state.google_code_verifier = code_verifier
        
        # Define OAuth parameters
        redirect_uri = f"{os.getenv('BASE_URL', 'https://example-app.replit.app')}"
        scope = "openid email profile"
        
        # Construct authorization URL
        auth_url = (
            "https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
            f"&scope={scope}"
            f"&state={state}"
            f"&code_challenge={code_challenge}"
            f"&code_challenge_method=S256"
            f"&access_type=offline"
            f"&prompt=consent"
        )
        
        return auth_url
    except Exception as e:
        st.error(f"Error generating auth URL: {str(e)}")
        return None

def handle_google_auth_callback():
    """Handle the callback from Google OAuth"""
    try:
        # Get query parameters
        try:
            code = st.query_params["code"]
            state = st.query_params["state"]
        except:
            # Fallback for older Streamlit versions
            from urllib.parse import parse_qs
            query_string = st.experimental_get_query_params()
            code = query_string.get("code", [""])[0]
            state = query_string.get("state", [""])[0]
        
        # Verify state
        if state != st.session_state.google_auth_state:
            st.error("Invalid state parameter, authentication failed.")
            return False
        
        # Exchange code for token
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        redirect_uri = f"{os.getenv('BASE_URL', 'https://example-app.replit.app')}"
        code_verifier = st.session_state.google_code_verifier
        
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "code_verifier": code_verifier,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        
        if "error" in token_json:
            st.error(f"Token exchange error: {token_json['error']}")
            return False
        
        # Get user info
        access_token = token_json.get("access_token")
        userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        userinfo_response = requests.get(userinfo_url, headers=headers)
        userinfo = userinfo_response.json()
        
        # Process user information
        google_id = userinfo.get("sub")
        email = userinfo.get("email")
        name = userinfo.get("name")
        
        # Check if user exists by Google ID
        user = DB.get_user_by_google_id(google_id)
        
        if user:
            # Log in existing user
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
        st.error(f"Error during Google authentication: {str(e)}")
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
        from urllib.parse import parse_qs
        query_params = st.experimental_get_query_params()
        has_code = 'code' in query_params
        has_state = 'state' in query_params
    
    if has_code and has_state:
        if handle_google_auth_callback():
            st.success("Login with Google successful!")
            st.rerun()
            return True
    
    col1, col2 = st.columns(2)
    
    with col1:
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
                Login with Google
            </a>
            """
            st.markdown(google_login_html, unsafe_allow_html=True)
    
    return False

def logout():
    """Handle user logout"""
    if st.sidebar.button("Sign Out"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ==============================
# UI Components
# ==============================

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'username' not in st.session_state:
    st.session_state.username = None

if 'auth_type' not in st.session_state:
    st.session_state.auth_type = None

if 'google_auth_state' not in st.session_state:
    st.session_state.google_auth_state = None

if 'google_code_verifier' not in st.session_state:
    st.session_state.google_code_verifier = None

# Check if user is logged in
if not st.session_state.logged_in:
    # Title and description for login page
    st.title("Photography Assessment System")
    st.markdown("""
    This AI-powered system helps analyze and improve your photographs. 
    Please log in to continue.
    """)
    
    login()
    
    # Stop the app here if not logged in
    st.stop()

# Main app (when logged in)
st.title("Photography Assessment System")
st.markdown(f"""
Welcome to the Photography Assessment System. 
This application helps you analyze and improve your photographs with AI-powered tools.

Your account: **{st.session_state.username}**
""")

# Sidebar for user management
with st.sidebar:
    st.subheader(f"User: {st.session_state.username}")
    
    # Show authentication type
    if st.session_state.auth_type == 'google':
        st.write("Logged in with Google")
    
    logout()
    
    # Add other sidebar elements here

# Main content area with tabs
tab1, tab2, tab3 = st.tabs(["Photo Analysis", "Enhancement Tools", "Tip of the Day"])

with tab1:
    st.header("Photo Analysis")
    
    # Placeholder for Photo Analysis tab
    st.info("Photo analysis features will be implemented in the next phase")
    
    # Image upload section (placeholder)
    uploaded_file = st.file_uploader("Upload your photograph", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        # Display the uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded photograph", use_column_width=True)
        
        # Placeholder for analysis button
        if st.button("Analyze Photograph"):
            with st.spinner("Analyzing the image..."):
                # Placeholder for future analysis implementation
                st.success("Analysis will be implemented in the next phase")

with tab2:
    st.header("Enhancement Tools")
    
    # Placeholder for Enhancement Tools tab
    st.info("Enhancement tools will be implemented in the next phase")

with tab3:
    st.header("Tip of the Day")
    
    # Placeholder for Tip of the Day tab
    st.info("Photography tips will be implemented in the next phase")

# Footer
st.markdown("---")
st.markdown("### About this System")
st.markdown("""
This system provides AI-powered tools for photography assessment and enhancement.
Future versions will include advanced analysis algorithms and detailed feedback.
""")