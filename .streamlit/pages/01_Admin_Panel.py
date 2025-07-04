import streamlit as st
import os
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from app.utils.auth import setup_authentication, is_authenticated, add_user, reset_password

st.set_page_config(page_title="MCP Admin", page_icon="🔐", layout="wide")

# Set up authentication
authenticated = setup_authentication()

# Only show the admin page if the user is authenticated
if authenticated:
    st.title("🔐 MCP Admin Panel")
    
    # Check if user is admin
    if st.session_state.get("username") != "admin":
        st.error("You don't have permission to access this page.")
        st.stop()
    
    # Admin tabs
    tab1, tab2, tab3 = st.tabs(["User Management", "Add User", "Reset Password"])
    
    # User Management Tab
    with tab1:
        st.header("User Management")
        
        # Load user data
        config_path = os.path.join("config", "auth.yaml")
        with open(config_path, 'r') as file:
            config = yaml.load(file, Loader=SafeLoader)
        
        # Display users
        st.subheader("Current Users")
        
        # Create a table of users
        users_data = []
        for username, user_info in config['credentials']['usernames'].items():
            users_data.append({
                "Username": username,
                "Name": user_info['name'],
                "Email": user_info['email']
            })
        
        st.table(users_data)
    
    # Add User Tab
    with tab2:
        st.header("Add New User")
        
        # Form to add a new user
        with st.form("add_user_form"):
            new_username = st.text_input("Username")
            new_name = st.text_input("Full Name")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            submit_button = st.form_submit_button("Add User")
            
            if submit_button:
                # Validate form
                if not new_username or not new_name or not new_email or not new_password:
                    st.error("All fields are required.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    # Add new user
                    success = add_user(new_username, new_name, new_email, new_password)
                    
                    if success:
                        st.success(f"User {new_username} added successfully!")
                    else:
                        st.error(f"Username {new_username} already exists.")
    
    # Reset Password Tab
    with tab3:
        st.header("Reset User Password")
        
        # Load user data for dropdown
        config_path = os.path.join("config", "auth.yaml")
        with open(config_path, 'r') as file:
            config = yaml.load(file, Loader=SafeLoader)
        
        # Get list of usernames
        usernames = list(config['credentials']['usernames'].keys())
        
        # Form to reset password
        with st.form("reset_password_form"):
            username = st.selectbox("Select User", usernames)
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            submit_button = st.form_submit_button("Reset Password")
            
            if submit_button:
                # Validate form
                if not new_password:
                    st.error("Password is required.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    # Reset password
                    success = reset_password(username, new_password)
                    
                    if success:
                        st.success(f"Password for {username} reset successfully!")
                    else:
                        st.error("Failed to reset password.") 