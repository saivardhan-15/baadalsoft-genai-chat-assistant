document.addEventListener('DOMContentLoaded', () => {
    const messagesContainer = document.getElementById('messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const newChatBtn = document.getElementById('new-chat-btn');

    // Generate or retrieve session ID
    let sessionId = localStorage.getItem('chatSessionId');
    if (!sessionId) {
        sessionId = generateSessionId();
        localStorage.setItem('chatSessionId', sessionId);
    }

    function generateSessionId() {
        return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    }

    function formatTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    function addMessage(content, sender, metaInfo = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Parse markdown if assistant
        if (sender === 'assistant' && content !== `<div class="loading-dots"><span></span><span></span><span></span></div>`) {
            contentDiv.innerHTML = marked.parse(content);
        } else {
            contentDiv.innerHTML = content;
        }

        const metaDiv = document.createElement('div');
        metaDiv.className = 'message-meta';
        
        let metaHtml = `<span>${formatTime()}</span>`;
        if (metaInfo) {
            metaHtml += `<span class="debug-info">Tokens: ${metaInfo.tokensUsed} | Chunks: ${metaInfo.retrievedChunks}</span>`;
        }
        metaDiv.innerHTML = metaHtml;

        messageDiv.appendChild(contentDiv);
        if (content !== `<div class="loading-dots"><span></span><span></span><span></span></div>`) {
            messageDiv.appendChild(metaDiv);
        }

        messagesContainer.appendChild(messageDiv);
        scrollToBottom();
        
        return messageDiv;
    }

    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        // Clear input and disable button
        userInput.value = '';
        sendButton.disabled = true;

        // Add user message to UI
        addMessage(message, 'user');

        // Add loading indicator
        const loadingHtml = `<div class="loading-dots"><span></span><span></span><span></span></div>`;
        const loadingMsgNode = addMessage(loadingHtml, 'assistant');

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    sessionId: sessionId,
                    message: message
                })
            });

            const data = await response.json();
            
            // Remove loading msg
            messagesContainer.removeChild(loadingMsgNode);

            if (response.ok) {
                addMessage(data.reply, 'assistant', {
                    tokensUsed: data.tokensUsed,
                    retrievedChunks: data.retrievedChunks
                });
            } else {
                addMessage(`**Error:** ${data.error || 'Failed to get response'}`, 'assistant');
            }
        } catch (error) {
            messagesContainer.removeChild(loadingMsgNode);
            addMessage('**Error:** Connection failed. Make sure the server is running.', 'assistant');
            console.error('Chat error:', error);
        } finally {
            sendButton.disabled = false;
            userInput.focus();
        }
    }

    // Event Listeners
    sendButton.addEventListener('click', sendMessage);

    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    newChatBtn.addEventListener('click', () => {
        // Clear session ID to force a new one
        sessionId = generateSessionId();
        localStorage.setItem('chatSessionId', sessionId);
        
        // Clear UI except for the first greeting
        while (messagesContainer.children.length > 1) {
            messagesContainer.removeChild(messagesContainer.lastChild);
        }
        
        // Add a system notice
        const noticeDiv = document.createElement('div');
        noticeDiv.style.textAlign = 'center';
        noticeDiv.style.fontSize = '0.8rem';
        noticeDiv.style.color = '#9CA3AF';
        noticeDiv.style.margin = '10px 0';
        noticeDiv.innerText = 'Started a new conversation session.';
        messagesContainer.appendChild(noticeDiv);
        scrollToBottom();
    });

    // Focus input on load
    userInput.focus();
});
