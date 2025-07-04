# MCP Chatbot with OpenAI Intent Detection

A Streamlit-based chatbot that uses OpenAI's API for intelligent intent detection and Serper API for real-time web search capabilities.

## Features

- 🤖 AI-powered chatbot using OpenAI's GPT-3.5-turbo
- 🧠 Intelligent intent detection - automatically determines when to search vs. chat
- 🔍 Real-time web search using Serper API
- 🌐 Streamlit web interface for easy interaction
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
   ```
   - Get your Serper API key from [https://serper.dev/](https://serper.dev/)
   - Get your OpenAI API key from [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

4. Run the application:
   ```
   streamlit run app.py
   ```
   
5. Open your browser and navigate to the URL shown in the terminal (usually `http://localhost:8501`)

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
   ```

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

## Development

This project uses:

- Streamlit for the web interface
- OpenAI API for AI capabilities and intent detection
- Serper API for web search
- httpx for async HTTP requests
- python-dotenv for environment variable management

## License

MIT
