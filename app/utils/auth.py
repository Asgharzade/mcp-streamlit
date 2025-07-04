import streamlit as st
import yaml
import os
import secrets
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import logging

logger = logging.getLogger("mcp-auth")

def load_auth_config():
    """Load authentication configuration from config file"""
    config_path = os.path.join("config", "auth.yaml")
    
    # Create default config if it doesn't exist
    if not os.path.exists(config_path):
        logger.info("Auth config not found, creating default config")
        
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Generate default hashed password (password: admin)
        hashed_password = stauth.Hasher(['admin']).generate()[0]
        
        # Get cookie key from environment or generate a secure one
        cookie_key = os.getenv("AUTH_COOKIE_KEY", secrets.token_hex(16))
        
        # Create default config
        default_config = {
            'credentials': {
                'usernames': {
                    'admin': {
                        'email': 'admin@example.com',
                        'name': 'Admin User',
                        'password': hashed_password
                    }
                }
            },
            'cookie': {
                'name': 'mcp_auth_cookie',
                'key': cookie_key,
                'expiry_days': 30
            }
        }
        
        # Save default config
        with open(config_path, 'w') as file:
            yaml.dump(default_config, file, default_flow_style=False)
        
        return default_config
    
    # Load existing config
    with open(config_path, 'r') as file:
        config = yaml.load(file, Loader=SafeLoader)
        logger.info("Auth config loaded successfully")
        
        # Update cookie key from environment if available
        if os.getenv("AUTH_COOKIE_KEY"):
            config['cookie']['key'] = os.getenv("AUTH_COOKIE_KEY")
        
        return config

def setup_authentication():
    """Set up Streamlit authentication"""
    # Load authentication configuration
    config = load_auth_config()
    
    # Create authenticator object
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )
    
    # Display login widget
    authenticator.login(location='main')
    
    # Check authentication status from session state
    if st.session_state.get('authentication_status'):
        # User is authenticated
        with st.sidebar:
            authenticator.logout(location='sidebar')
            st.write(f'Welcome *{st.session_state["name"]}*')
        return True
    elif st.session_state.get('authentication_status') is False:
        st.error('Username/password is incorrect')
        return False
    elif st.session_state.get('authentication_status') is None:
        st.warning('Please enter your username and password')
        return False
    
    return False

def is_authenticated():
    """Check if user is authenticated"""
    return st.session_state.get('authentication_status', False)

def reset_password(username, new_password):
    """Reset user password"""
    config_path = os.path.join("config", "auth.yaml")
    
    # Load config
    with open(config_path, 'r') as file:
        config = yaml.load(file, Loader=SafeLoader)
    
    # Hash new password
    hashed_password = stauth.Hasher([new_password]).generate()[0]
    
    # Update password
    config['credentials']['usernames'][username]['password'] = hashed_password
    
    # Save config
    with open(config_path, 'w') as file:
        yaml.dump(config, file, default_flow_style=False)
    
    logger.info(f"Password reset for user: {username}")
    return True

def add_user(username, name, email, password):
    """Add a new user"""
    config_path = os.path.join("config", "auth.yaml")
    
    # Load config
    with open(config_path, 'r') as file:
        config = yaml.load(file, Loader=SafeLoader)
    
    # Check if username already exists
    if username in config['credentials']['usernames']:
        logger.warning(f"User {username} already exists")
        return False
    
    # Hash password
    hashed_password = stauth.Hasher([password]).generate()[0]
    
    # Add new user
    config['credentials']['usernames'][username] = {
        'name': name,
        'email': email,
        'password': hashed_password
    }
    
    # Save config
    with open(config_path, 'w') as file:
        yaml.dump(config, file, default_flow_style=False)
    
    logger.info(f"Added new user: {username}")
    return True 