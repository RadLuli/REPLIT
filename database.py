import os
import json
import datetime
import base64
from io import BytesIO
from pathlib import Path

# Create a data directory if it doesn't exist
data_dir = Path('./data')
data_dir.mkdir(exist_ok=True)

# File paths for JSON storage
IMAGE_DATA_FILE = data_dir / 'image_data.json'
USER_DATA_FILE = data_dir / 'user_data.json'

class SimpleDB:
    """
    A simple file-based JSON database for storing
    images and analysis results when a SQL database is not available
    """
    
    @staticmethod
    def _ensure_file(file_path, default_content=None):
        """Ensure the file exists and has valid JSON content"""
        if not file_path.exists():
            with open(file_path, 'w') as f:
                json.dump(default_content or {}, f)
    
    @staticmethod
    def load_data(file_path):
        """Load data from a JSON file"""
        SimpleDB._ensure_file(file_path, {})
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    @staticmethod
    def save_data(file_path, data):
        """Save data to a JSON file"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def save_image_analysis(cls, image_id, username, image_data, analysis_results, 
                          enhancement_type=None, enhanced_image_data=None):
        """
        Save image analysis results
        
        Args:
            image_id: Unique ID for the image
            username: User who uploaded the image
            image_data: Base64 encoded image data
            analysis_results: Analysis results dictionary
            enhancement_type: Type of enhancement applied (optional)
            enhanced_image_data: Base64 encoded enhanced image data (optional)
        """
        # Load existing data
        data = cls.load_data(IMAGE_DATA_FILE)
        
        # Create entry if it doesn't exist
        if image_id not in data:
            data[image_id] = {
                'id': image_id,
                'username': username,
                'upload_date': datetime.datetime.now().isoformat(),
                'analysis_history': []
            }
        
        # Add the new analysis to the history
        analysis_entry = {
            'date': datetime.datetime.now().isoformat(),
            'analysis_results': analysis_results,
        }
        
        # Add image data to the first entry only (to save space)
        if not data[image_id]['analysis_history']:
            analysis_entry['image_data'] = image_data
        
        # Add enhancement data if provided
        if enhancement_type and enhanced_image_data:
            analysis_entry['enhancement'] = {
                'type': enhancement_type,
                'image_data': enhanced_image_data
            }
        
        # Append to history
        data[image_id]['analysis_history'].append(analysis_entry)
        
        # Save the updated data
        cls.save_data(IMAGE_DATA_FILE, data)
    
    @classmethod
    def get_user_images(cls, username):
        """
        Get all images for a user
        
        Args:
            username: Username to fetch images for
            
        Returns:
            List of image data dictionaries
        """
        data = cls.load_data(IMAGE_DATA_FILE)
        user_images = []
        
        for image_id, image_data in data.items():
            if image_data['username'] == username:
                # Create a summary object without the full image data
                summary = {
                    'id': image_id,
                    'upload_date': image_data['upload_date'],
                    'latest_analysis': None,
                    'thumbnail': None
                }
                
                # Get the most recent analysis
                if image_data['analysis_history']:
                    latest = image_data['analysis_history'][-1]
                    summary['latest_analysis'] = latest['analysis_results']
                    
                    # Use the first entry which has the image data for the thumbnail
                    first_entry = image_data['analysis_history'][0]
                    if 'image_data' in first_entry:
                        summary['thumbnail'] = first_entry['image_data']
                
                user_images.append(summary)
        
        return user_images
    
    @classmethod
    def get_image_details(cls, image_id):
        """
        Get detailed information for a specific image
        
        Args:
            image_id: ID of the image to retrieve
            
        Returns:
            Dictionary with image details or None if not found
        """
        data = cls.load_data(IMAGE_DATA_FILE)
        return data.get(image_id)
    
    @classmethod
    def save_user(cls, username, password_hash=None, email=None, name=None, google_id=None):
        """
        Save or update user information
        
        Args:
            username: Username (unique identifier)
            password_hash: Hashed password (None for OAuth users)
            email: User's email (optional)
            name: User's name (optional)
            google_id: Google user ID for OAuth users (optional)
        """
        data = cls.load_data(USER_DATA_FILE)
        
        # Create or update user entry
        if username not in data:
            data[username] = {
                'username': username,
                'created_at': datetime.datetime.now().isoformat(),
            }
            
            # Set password hash only if provided (regular users)
            if password_hash:
                data[username]['password_hash'] = password_hash
                
            # Set OAuth data if provided
            if google_id:
                data[username]['google_id'] = google_id
                data[username]['auth_type'] = 'google'
            else:
                data[username]['auth_type'] = 'local'
        else:
            # Update existing user
            data[username]['updated_at'] = datetime.datetime.now().isoformat()
            
            # Update password if provided
            if password_hash:
                data[username]['password_hash'] = password_hash
                
            # Update OAuth data if provided
            if google_id:
                data[username]['google_id'] = google_id
                data[username]['auth_type'] = 'google'
        
        # Add optional fields if provided
        if email:
            data[username]['email'] = email
        if name:
            data[username]['name'] = name
        
        cls.save_data(USER_DATA_FILE, data)
        return data[username]
    
    @classmethod
    def get_user_by_google_id(cls, google_id):
        """
        Get user by Google ID
        
        Args:
            google_id: Google ID to look up
            
        Returns:
            User dictionary or None if not found
        """
        data = cls.load_data(USER_DATA_FILE)
        
        for username, user_data in data.items():
            if user_data.get('google_id') == google_id:
                return user_data
                
        return None
    
    @classmethod
    def get_user(cls, username):
        """
        Get user information
        
        Args:
            username: Username to retrieve
            
        Returns:
            User dictionary or None if not found
        """
        data = cls.load_data(USER_DATA_FILE)
        return data.get(username)
    
    @classmethod
    def authenticate_user(cls, username, password_hash=None, google_id=None):
        """
        Verify user credentials
        
        Args:
            username: Username to authenticate
            password_hash: Hashed password to verify (None for OAuth users)
            google_id: Google ID to verify (None for regular users)
            
        Returns:
            Boolean indicating if authentication was successful
        """
        user = cls.get_user(username)
        if not user:
            return False
        
        # Check authentication type
        if google_id and user.get('auth_type') == 'google':
            return user.get('google_id') == google_id
        elif password_hash and user.get('auth_type', 'local') == 'local':
            return user.get('password_hash') == password_hash
        
        return False

# Try to import PostgreSQL libraries if available
try:
    import psycopg2
    from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime, ForeignKey, Text, LargeBinary
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship
    
    # Define if we have database access
    HAS_DATABASE = True
    
    # Create the base class for declarative models
    Base = declarative_base()
    
    # Define database models
    class User(Base):
        """User model for PostgreSQL"""
        __tablename__ = 'users'
        
        id = Column(Integer, primary_key=True)
        username = Column(String(50), unique=True, nullable=False)
        password_hash = Column(String(100), nullable=True)  # Can be null for OAuth users
        email = Column(String(100))
        name = Column(String(100))
        google_id = Column(String(100), nullable=True, unique=True)  # Google OAuth ID
        auth_type = Column(String(20), default='local')  # 'local' or 'google'
        created_at = Column(DateTime, default=datetime.datetime.utcnow)
        updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
        
        images = relationship("Image", back_populates="user")
    
    class Image(Base):
        """Image model for PostgreSQL"""
        __tablename__ = 'images'
        
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey('users.id'))
        upload_date = Column(DateTime, default=datetime.datetime.utcnow)
        image_data = Column(LargeBinary)  # Store the image as binary data
        
        user = relationship("User", back_populates="images")
        analyses = relationship("Analysis", back_populates="image")
    
    class Analysis(Base):
        """Analysis model for PostgreSQL"""
        __tablename__ = 'analyses'
        
        id = Column(Integer, primary_key=True)
        image_id = Column(Integer, ForeignKey('images.id'))
        analysis_date = Column(DateTime, default=datetime.datetime.utcnow)
        results = Column(JSON)  # Store analysis results as JSON
        
        image = relationship("Image", back_populates="analyses")
        enhancements = relationship("Enhancement", back_populates="analysis")
    
    class Enhancement(Base):
        """Enhancement model for PostgreSQL"""
        __tablename__ = 'enhancements'
        
        id = Column(Integer, primary_key=True)
        analysis_id = Column(Integer, ForeignKey('analyses.id'))
        enhancement_type = Column(String(50))
        enhanced_image_data = Column(LargeBinary)  # Store the enhanced image
        
        analysis = relationship("Analysis", back_populates="enhancements")
    
    class PostgresDB:
        """PostgreSQL database interface"""
        
        @staticmethod
        def get_engine():
            """Get SQLAlchemy engine from environment variables"""
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                raise ValueError("DATABASE_URL environment variable not set")
            
            return create_engine(database_url)
        
        @classmethod
        def setup_database(cls):
            """Create tables if they don't exist"""
            engine = cls.get_engine()
            Base.metadata.create_all(engine)
        
        @classmethod
        def get_session(cls):
            """Get a new database session"""
            engine = cls.get_engine()
            Session = sessionmaker(bind=engine)
            return Session()
        
        @classmethod
        def save_user(cls, username, password_hash=None, email=None, name=None, google_id=None):
            """Save or update a user"""
            session = cls.get_session()
            
            try:
                # Check if user exists
                user = session.query(User).filter_by(username=username).first()
                
                # Also check if a user with this google_id already exists
                if google_id:
                    google_user = session.query(User).filter_by(google_id=google_id).first()
                    if google_user and (not user or google_user.id != user.id):
                        # User already exists with this Google ID but different username
                        return False
                
                if not user:
                    # Create new user
                    user = User(
                        username=username,
                        password_hash=password_hash,
                        email=email,
                        name=name,
                        google_id=google_id,
                        auth_type='google' if google_id else 'local'
                    )
                    session.add(user)
                else:
                    # Update existing user
                    if password_hash:
                        user.password_hash = password_hash
                    if email:
                        user.email = email
                    if name:
                        user.name = name
                    if google_id:
                        user.google_id = google_id
                        user.auth_type = 'google'
                
                session.commit()
                
                # Convert to dictionary for response
                user_dict = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'name': user.name,
                    'auth_type': user.auth_type,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'updated_at': user.updated_at.isoformat() if user.updated_at else None
                }
                return user_dict
            except Exception as e:
                session.rollback()
                print(f"Database error saving user: {str(e)}")
                return False
            finally:
                session.close()
        
        @classmethod
        def get_user_by_google_id(cls, google_id):
            """Get user by Google ID"""
            session = cls.get_session()
            
            try:
                user = session.query(User).filter_by(google_id=google_id).first()
                if not user:
                    return None
                
                # Convert to dictionary
                return {
                    'id': user.id,
                    'username': user.username,
                    'password_hash': user.password_hash,
                    'email': user.email,
                    'name': user.name,
                    'google_id': user.google_id,
                    'auth_type': user.auth_type,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'updated_at': user.updated_at.isoformat() if user.updated_at else None
                }
            except Exception as e:
                print(f"Database error getting user by Google ID: {str(e)}")
                return None
            finally:
                session.close()
        
        @classmethod
        def get_user(cls, username):
            """Get user information"""
            session = cls.get_session()
            
            try:
                user = session.query(User).filter_by(username=username).first()
                if not user:
                    return None
                
                # Convert to dictionary
                return {
                    'id': user.id,
                    'username': user.username,
                    'password_hash': user.password_hash,
                    'email': user.email,
                    'name': user.name,
                    'google_id': user.google_id,
                    'auth_type': user.auth_type,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'updated_at': user.updated_at.isoformat() if user.updated_at else None
                }
            except Exception as e:
                print(f"Database error getting user: {str(e)}")
                return None
            finally:
                session.close()
        
        @classmethod
        def authenticate_user(cls, username, password_hash=None, google_id=None):
            """Verify user credentials"""
            user = cls.get_user(username)
            if not user:
                return False
            
            # Check authentication type
            if google_id and user.get('auth_type') == 'google':
                return user.get('google_id') == google_id
            elif password_hash and user.get('auth_type', 'local') == 'local':
                return user.get('password_hash') == password_hash
            
            return False
        
        @classmethod
        def save_image_analysis(cls, image_id, username, image_data, analysis_results, 
                              enhancement_type=None, enhanced_image_data=None):
            """Save image analysis results"""
            session = cls.get_session()
            
            try:
                # Get or create user
                user = session.query(User).filter_by(username=username).first()
                if not user:
                    # If the user doesn't exist, we can't save their image
                    print(f"User {username} not found")
                    return False
                
                # Check if this is a new image or existing one
                image = None
                if image_id and image_id.isdigit():
                    # Try to find existing image
                    image = session.query(Image).filter_by(id=int(image_id)).first()
                
                if not image:
                    # Create new image
                    image = Image(
                        user_id=user.id,
                        image_data=base64.b64decode(image_data) if image_data else None
                    )
                    session.add(image)
                    session.flush()  # To get the image ID
                
                # Create analysis
                analysis = Analysis(
                    image_id=image.id,
                    results=analysis_results
                )
                session.add(analysis)
                session.flush()  # To get the analysis ID
                
                # Add enhancement if provided
                if enhancement_type and enhanced_image_data:
                    enhancement = Enhancement(
                        analysis_id=analysis.id,
                        enhancement_type=enhancement_type,
                        enhanced_image_data=base64.b64decode(enhanced_image_data) if enhanced_image_data else None
                    )
                    session.add(enhancement)
                
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                print(f"Database error saving image analysis: {str(e)}")
                return False
            finally:
                session.close()
        
        @classmethod
        def get_user_images(cls, username):
            """Get all images for a user"""
            session = cls.get_session()
            
            try:
                # Get user
                user = session.query(User).filter_by(username=username).first()
                if not user:
                    return []
                
                # Get images with their most recent analysis
                images = session.query(Image).filter_by(user_id=user.id).all()
                result = []
                
                for image in images:
                    # Get the most recent analysis
                    latest_analysis = (session.query(Analysis)
                                     .filter_by(image_id=image.id)
                                     .order_by(Analysis.analysis_date.desc())
                                     .first())
                    
                    # Create summary object
                    summary = {
                        'id': str(image.id),
                        'upload_date': image.upload_date.isoformat(),
                        'latest_analysis': latest_analysis.results if latest_analysis else None,
                        'thumbnail': base64.b64encode(image.image_data).decode('utf-8') if image.image_data else None
                    }
                    
                    result.append(summary)
                
                return result
            except Exception as e:
                print(f"Database error getting user images: {str(e)}")
                return []
            finally:
                session.close()
        
        @classmethod
        def get_image_details(cls, image_id):
            """Get detailed information for a specific image"""
            session = cls.get_session()
            
            try:
                # Get image
                image = session.query(Image).filter_by(id=int(image_id)).first()
                if not image:
                    return None
                
                # Get all analyses for this image
                analyses = (session.query(Analysis)
                          .filter_by(image_id=image.id)
                          .order_by(Analysis.analysis_date)
                          .all())
                
                # Get user info
                user = session.query(User).filter_by(id=image.user_id).first()
                
                # Build the response object
                result = {
                    'id': str(image.id),
                    'username': user.username if user else None,
                    'upload_date': image.upload_date.isoformat(),
                    'analysis_history': []
                }
                
                # Add each analysis
                for analysis in analyses:
                    # Get enhancements for this analysis
                    enhancements = (session.query(Enhancement)
                                  .filter_by(analysis_id=analysis.id)
                                  .all())
                    
                    analysis_entry = {
                        'date': analysis.analysis_date.isoformat(),
                        'analysis_results': analysis.results,
                    }
                    
                    # Add image data to the first entry only
                    if not result['analysis_history']:
                        analysis_entry['image_data'] = base64.b64encode(image.image_data).decode('utf-8') if image.image_data else None
                    
                    # Add enhancement if available
                    if enhancements:
                        enhancement = enhancements[0]  # Just get the first one
                        analysis_entry['enhancement'] = {
                            'type': enhancement.enhancement_type,
                            'image_data': base64.b64encode(enhancement.enhanced_image_data).decode('utf-8') if enhancement.enhanced_image_data else None
                        }
                    
                    result['analysis_history'].append(analysis_entry)
                
                return result
            except Exception as e:
                print(f"Database error getting image details: {str(e)}")
                return None
            finally:
                session.close()

except ImportError:
    # If PostgreSQL libraries are not available, we'll use the simple JSON database
    HAS_DATABASE = False
    print("PostgreSQL libraries not available, using simple JSON database instead")

# Choose which database implementation to use
if HAS_DATABASE:
    print("Using PostgreSQL database")
    DB = PostgresDB
    try:
        # Setup database tables
        PostgresDB.setup_database()
    except Exception as e:
        print(f"Error setting up PostgreSQL database: {str(e)}")
        print("Falling back to simple JSON database")
        DB = SimpleDB
else:
    print("Using simple JSON database")
    DB = SimpleDB