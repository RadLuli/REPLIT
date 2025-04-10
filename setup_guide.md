# AI-Powered Photography Assessment System - Setup Guide

## Environment Setup

### 1. Required Environment Variables

Create a `.env` file in your project root with the following variables:

```
# Google OAuth Credentials (required for authentication)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
BASE_URL=your_app_url  # e.g., https://your-app.replit.app

# PostgreSQL Database (optional, will use JSON files if not provided)
DATABASE_URL=postgresql://username:password@host:port/database
```

### 2. Creating Google OAuth Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth client ID"
5. Configure the OAuth consent screen:
   - User Type: External
   - App Name: Photography Assessment System
   - User support email: your email
   - Developer contact information: your email
6. Add scopes:
   - `userinfo.email`
   - `userinfo.profile`
   - `openid`
7. Create OAuth client ID:
   - Application type: Web application
   - Name: Photography Assessment System
   - Authorized JavaScript origins: Your app URL (e.g., https://your-app.replit.app)
   - Authorized redirect URIs: Your app URL (e.g., https://your-app.replit.app)
8. Copy the Client ID and Client Secret to your `.env` file

### 3. Required Python Packages

Install the following required packages:

```
streamlit==1.22.0
pillow==9.5.0
requests==2.30.0
python-dotenv==1.0.0
```

Include optional packages based on features you want to implement:

```
# For advanced image processing
opencv-python==4.7.0.72

# For database support (PostgreSQL)
sqlalchemy==2.0.12
psycopg2-binary==2.9.6
```

## Application Structure

The application follows a modular architecture:

```
photography-assessment-system/
│
├── .env                    # Environment variables (not in version control)
├── .streamlit/
│   └── config.toml         # Streamlit configuration
├── app.py                  # Main application entry point
├── database.py             # Database utilities
├── auth/
│   ├── __init__.py
│   └── google_auth.py      # Google authentication 
├── image_processing/
│   ├── __init__.py
│   ├── analyzer.py         # Image analysis functions
│   └── enhancer.py         # Image enhancement functions
├── data/                   # Data directory (for JSON storage)
│   ├── users.json
│   └── images.json
└── utils/
    ├── __init__.py
    └── helpers.py          # Utility functions
```

## Streamlit Configuration

Create a `.streamlit/config.toml` file with the following content:

```toml
[server]
headless = true
address = "0.0.0.0"
port = 5000

[theme]
primaryColor = "#4285F4"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

## First-Time Setup

1. Clone the repository or create the project structure
2. Create and populate the `.env` file with your credentials
3. Install the required packages
4. Run the application using:
   ```
   streamlit run app.py
   ```

## Development Workflow

1. **Local Development**:
   - Run the application locally using `streamlit run app.py`
   - Test features with local JSON storage before deploying

2. **Database Migration**:
   - When moving to PostgreSQL, your data will be automatically migrated
   - Existing JSON data can be imported using provided utilities

3. **Google OAuth Testing**:
   - For local testing, add `http://localhost:5000` to your Google OAuth credentials
   - For production, use your Replit URL or custom domain

## Deployment to Replit

1. Create a new Replit project
2. Upload your code or clone from your repository
3. Set the required environment variables in Replit Secrets
4. Configure the run command to:
   ```
   streamlit run app.py --server.port 5000
   ```
5. Click Run to start your application

## Extending the System

### Adding New Image Analysis Algorithms

1. Create a new module in `image_processing/`
2. Implement your algorithm with proper documentation
3. Integrate it into the main analysis pipeline

### Adding Support for New Image Formats

1. Update the file upload widget in app.py to support the new format
2. Implement handlers for the new format in the image processing modules

### Integrating Future RAG Capabilities

The system is designed for future RAG integration:

1. Create a `documents/` directory with appropriate modules
2. Implement document storage and retrieval
3. Set up embedding generation and vector search
4. Connect to the image analysis pipeline through existing hooks

## Troubleshooting

### Common Issues

1. **Authentication Failures**:
   - Verify Google OAuth credentials
   - Check allowed redirect URIs
   - Ensure environment variables are set correctly

2. **Database Connection Issues**:
   - Verify PostgreSQL connection string
   - Check database server status
   - System will fall back to JSON storage if database is unavailable

3. **Image Processing Errors**:
   - Check supported image formats
   - Verify image file integrity
   - Check memory limitations for large images