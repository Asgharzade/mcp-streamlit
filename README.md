# MCP Chatbot with OpenAI Intent Detection

A Streamlit-based chatbot that uses OpenAI's API for intelligent intent detection and Serper API for real-time web search capabilities.

## Features

- 🤖 AI-powered chatbot using OpenAI's GPT-3.5-turbo
- 🧠 Intelligent intent detection - automatically determines when to search vs. chat
- 🔍 Real-time web search using Serper API
- 🌐 Streamlit web interface for easy interaction
- 🔐 User authentication system with admin panel
- 🔄 MCP (Model Context Protocol) compliant tool integration
- 💾 Chat history persistence
- 🐛 Debug mode to see AI decision-making
- 🔄 Fallback to keyword detection if OpenAI is unavailable

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with the following variables:
   ```
   SERPER_API_KEY=your_serper_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   AUTH_COOKIE_KEY=your_secure_random_string_here
   ```
   - Get your Serper API key from [https://serper.dev/](https://serper.dev/)
   - Get your OpenAI API key from [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
   - Generate a secure random string for AUTH_COOKIE_KEY (e.g., using `openssl rand -hex 32`)

4. Run the application:
   ```
   streamlit run app.py
   ```
   
5. Open your browser and navigate to the URL shown in the terminal (usually `http://localhost:8501`)

6. Login with the default credentials:
   - Username: `admin`
   - Password: `admin`

7. For admin panel access, run:
   ```
   streamlit run admin.py
   ```

## Release History

### Version 1.1.0 (May 29, 2024)
- Added user authentication system
- Added admin panel for user management
- Implemented secure cookie-based authentication
- Added multi-page Streamlit app structure

### Version 1.0.0 (May 15, 2024)
- Initial release with OpenAI intent detection
- Serper API integration for web search
- Streamlit web interface

For detailed release notes, see the [CHANGELOG.md](CHANGELOG.md) file.

### Release Process

To create a new release:

1. Run the release script:
   ```
   # On Linux/Mac
   ./scripts/release.py 1.2.0
   
   # On Windows
   scripts\release.bat 1.2.0
   ```

2. Follow the prompts to enter changes for each category
3. Review the updated VERSION and CHANGELOG.md files
4. Commit and push the changes
5. Create a new GitHub release (optional)

## Authentication System

The application includes a user authentication system with the following features:

- **Login/Logout**: Secure access to the chatbot interface
- **User Management**: Admin panel for managing users
- **Password Reset**: Admin can reset user passwords
- **Role-Based Access**: Admin-specific features and pages

### Default Credentials

- **Username**: admin
- **Password**: admin

### Admin Panel

Access the admin panel by:
1. Running `streamlit run admin.py`
2. Clicking the "Admin Panel" link in the sidebar (admin users only)

The admin panel allows you to:
- View all registered users
- Add new users
- Reset user passwords

### Authentication Configuration

Authentication settings are stored in `config/auth.yaml`. This file is automatically created with default settings if it doesn't exist.

## Heroku Deployment

### Prerequisites
- A Heroku account
- Heroku CLI installed on your machine
- Git installed on your machine

### Deployment Steps

1. **Login to Heroku**
   ```
   heroku login
   ```

2. **Create a new Heroku app**
   ```
   heroku create your-app-name
   ```
   Replace `your-app-name` with a unique name for your application.

3. **Set environment variables**
   ```
   heroku config:set OPENAI_API_KEY=your_openai_api_key
   heroku config:set SERPER_API_KEY=your_serper_api_key
   heroku config:set AUTH_COOKIE_KEY=your_secure_random_string
   ```
   Generate a secure random string for AUTH_COOKIE_KEY (e.g., using `openssl rand -hex 32`)

4. **Deploy the application**
   ```
   git push heroku main
   ```

5. **Scale the application**
   ```
   heroku ps:scale web=1
   ```

6. **Open the application**
   ```
   heroku open
   ```

### Authentication on Heroku

When deploying to Heroku, note that:

1. The authentication config file (`config/auth.yaml`) will be created automatically on first run
2. The `AUTH_COOKIE_KEY` environment variable will be used for secure cookie encryption
3. User data will be reset when the Heroku dyno restarts, as Heroku has an ephemeral filesystem

For persistent user data on Heroku, consider:
- Using a database add-on to store user credentials
- Using Heroku's config vars to store initial admin credentials

### Updating Your Deployed App

To update your deployed application after making changes:

1. Commit your changes to git
   ```
   git add .
   git commit -m "Your update message"
   ```

2. Push the changes to Heroku
   ```
   git push heroku main
   ```

### Troubleshooting

- **View logs**
  ```
  heroku logs --tail
  ```

- **Restart the application**
  ```
  heroku restart
  ```

- **Check build status**
  ```
  heroku builds
  ```

## How It Works

The chatbot uses OpenAI's GPT-3.5-turbo to intelligently analyze user messages and determine:

1. **Intent Detection**: Whether the user needs current information that requires a web search
2. **Query Optimization**: What the optimal search query should be
3. **Response Generation**: Whether to provide a conversational response or search results

### Examples

- "What's the weather like today?" → Triggers search for current weather
- "Hello, how are you?" → Provides conversational response
- "Tell me about quantum computing" → Triggers search for latest quantum computing info
- "What's 2+2?" → Provides conversational response (no search needed)
- "Latest news about AI" → Triggers search for recent AI news

## Features

### Intelligent Intent Detection
The AI analyzes each message to determine if it needs current, factual, or specific information that would benefit from a web search.

### Optimized Search Queries
Instead of using the exact user message, the AI generates optimized search queries for better results.

### Fallback System
If OpenAI is unavailable, the system falls back to keyword-based detection to ensure reliability.

### Debug Mode
Toggle debug information to see the AI's decision-making process, including:
- Whether a search was triggered
- The optimized search query
- The reasoning behind the decision

## Architecture

- **Streamlit**: Web interface and session management
- **OpenAI API**: Intent detection and conversational responses
- **Serper API**: Web search capabilities
- **MCP Protocol**: Tool integration framework
- **Async/await**: Non-blocking API calls
- **Streamlit Authenticator**: User authentication system

## Development

This project uses:

- Streamlit for the web interface
- OpenAI API for AI capabilities and intent detection
- Serper API for web search
- httpx for async HTTP requests
- python-dotenv for environment variable management
- streamlit-authenticator for user authentication
- PyYAML for configuration management

## License

MIT
