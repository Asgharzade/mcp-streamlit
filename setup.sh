mkdir -p ~/.streamlit/

echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
[browser]\n\
serverAddress = \"0.0.0.0\"\n\
serverPort = $PORT\n\
\n\
[theme]\n\
primaryColor = \"#7792E3\"\n\
backgroundColor = \"#273346\"\n\
secondaryBackgroundColor = \"#B9F1C0\"\n\
textColor = \"#FFFFFF\"\n\
\n\
" > ~/.streamlit/config.toml 