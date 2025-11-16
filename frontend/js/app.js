/**
 * FinSight Frontend Application
 * Main application logic for WebSocket communication and UI management
 */

class FinSightApp {
    constructor() {
        this.ws = null;
        this.chartParser = new ChartParser();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.isDarkTheme = false;
        
        this.initializeElements();
        this.attachEventListeners();
        this.connectWebSocket();
        this.loadThemePreference();
    }

    /**
     * Initialize DOM elements
     */
    initializeElements() {
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.chatMessages = document.getElementById('chatMessages');
        this.clearBtn = document.getElementById('clearBtn');
        this.connectionStatus = document.getElementById('connectionStatus');
        this.themeToggle = document.getElementById('themeToggle');
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Send message on button click
        this.sendBtn.addEventListener('click', () => this.sendMessage());

        // Send message on Enter (but allow Shift+Enter for new line)
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Enable/disable send button based on input
        this.messageInput.addEventListener('input', () => {
            this.sendBtn.disabled = !this.messageInput.value.trim();
            this.autoResizeTextarea();
        });

        // Clear chat
        this.clearBtn.addEventListener('click', () => this.clearChat());

        // Theme toggle
        this.themeToggle.addEventListener('click', () => this.toggleTheme());
    }

    /**
     * Connect to WebSocket server
     */
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        this.updateConnectionStatus('connecting', 'Connecting...');

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('✅ WebSocket connected');
                this.updateConnectionStatus('connected', 'Connected');
                this.reconnectAttempts = 0;
            };

            this.ws.onmessage = (event) => {
                this.handleMessage(event.data);
            };

            this.ws.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
                this.updateConnectionStatus('disconnected', 'Connection error');
            };

            this.ws.onclose = () => {
                console.log('🔌 WebSocket disconnected');
                this.updateConnectionStatus('disconnected', 'Disconnected');
                this.attemptReconnect();
            };

        } catch (error) {
            console.error('Failed to connect:', error);
            this.updateConnectionStatus('disconnected', 'Connection failed');
        }
    }

    /**
     * Attempt to reconnect to WebSocket
     */
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);
            
            this.updateConnectionStatus('connecting', `Reconnecting in ${delay/1000}s...`);
            
            setTimeout(() => {
                console.log(`🔄 Reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
                this.connectWebSocket();
            }, delay);
        } else {
            this.updateConnectionStatus('disconnected', 'Connection failed. Refresh to retry.');
        }
    }

    /**
     * Update connection status UI
     */
    updateConnectionStatus(status, text) {
        this.connectionStatus.className = `connection-status ${status}`;
        this.connectionStatus.querySelector('.status-text').textContent = text;
    }

    /**
     * Send message to agent
     */
    sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || !this.ws || this.ws.readyState !== WebSocket.OPEN) return;

        // Add user message to chat
        this.addMessage('user', message);

        // Send to backend
        this.ws.send(JSON.stringify({
            type: 'message',
            content: message
        }));

        // Clear input
        this.messageInput.value = '';
        this.sendBtn.disabled = true;
        this.autoResizeTextarea();

        // Show thinking indicator
        this.showThinkingIndicator();
    }

    /**
     * Handle incoming WebSocket message
     */
    handleMessage(data) {
        const message = JSON.parse(data);

        // Remove thinking indicator
        this.removeThinkingIndicator();

        switch (message.type) {
            case 'message':
                this.addMessage('assistant', message.content);
                break;

            case 'thinking':
                // Thinking indicator already shown
                break;

            case 'error':
                this.addMessage('error', message.content);
                break;

            case 'system':
                this.showSystemMessage(message.content);
                break;

            default:
                console.warn('Unknown message type:', message.type);
        }
    }

    /**
     * Add message to chat
     */
    addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;

        // Create avatar
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        
        if (role === 'user') {
            avatar.textContent = 'U';
        } else if (role === 'assistant') {
            avatar.innerHTML = `
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" fill="url(#gradient-${Date.now()})"/>
                    <path d="M8 14C8 14 9.5 16 12 16C14.5 16 16 14 16 14M9 9H9.01M15 9H15.01" stroke="white" stroke-width="2" stroke-linecap="round"/>
                    <defs>
                        <linearGradient id="gradient-${Date.now()}" x1="0" y1="0" x2="24" y2="24" gradientUnits="userSpaceOnUse">
                            <stop stop-color="#6366F1"/>
                            <stop offset="1" stop-color="#8B5CF6"/>
                        </linearGradient>
                    </defs>
                </svg>
            `;
        } else if (role === 'error') {
            avatar.innerHTML = `
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="#EF4444" stroke-width="2"/>
                    <path d="M12 8V12M12 16H12.01" stroke="#EF4444" stroke-width="2" stroke-linecap="round"/>
                </svg>
            `;
        }

        // Create content container
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';

        // Parse for charts/images
        const parsed = this.chartParser.parseResponse(content);

        // Add formatted text
        if (parsed.text) {
            textDiv.innerHTML = this.chartParser.formatText(parsed.text);
        }

        contentDiv.appendChild(textDiv);

        // Add charts if any
        parsed.images.forEach(imageData => {
            const chartElement = this.chartParser.createChartElement(imageData);
            contentDiv.appendChild(chartElement);
        });

        // Assemble message
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);

        // Add to chat
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    /**
     * Show thinking indicator
     */
    showThinkingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'message assistant-message thinking-message';
        indicator.id = 'thinkingIndicator';

        indicator.innerHTML = `
            <div class="message-avatar">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" fill="url(#gradient-thinking)"/>
                    <defs>
                        <linearGradient id="gradient-thinking" x1="0" y1="0" x2="24" y2="24" gradientUnits="userSpaceOnUse">
                            <stop stop-color="#6366F1"/>
                            <stop offset="1" stop-color="#8B5CF6"/>
                        </linearGradient>
                    </defs>
                </svg>
            </div>
            <div class="message-content">
                <div class="message-text">
                    <div class="thinking-indicator">
                        <div class="thinking-dot"></div>
                        <div class="thinking-dot"></div>
                        <div class="thinking-dot"></div>
                    </div>
                </div>
            </div>
        `;

        this.chatMessages.appendChild(indicator);
        this.scrollToBottom();
    }

    /**
     * Remove thinking indicator
     */
    removeThinkingIndicator() {
        const indicator = document.getElementById('thinkingIndicator');
        if (indicator) {
            indicator.remove();
        }
    }

    /**
     * Show system message
     */
    showSystemMessage(content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'system-message';
        messageDiv.style.cssText = `
            text-align: center;
            padding: 12px;
            margin: 16px 0;
            background: var(--bg-secondary);
            border-radius: 8px;
            color: var(--text-secondary);
            font-size: 14px;
        `;
        messageDiv.textContent = content;
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    /**
     * Clear chat history
     */
    clearChat() {
        if (!confirm('Are you sure you want to clear the chat history?')) return;

        // Send clear message to backend
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'clear'
            }));
        }

        // Clear UI (keep welcome message)
        const messages = this.chatMessages.querySelectorAll('.message:not(.welcome-message)');
        messages.forEach(msg => msg.remove());

        this.showSystemMessage('Chat history cleared');
    }

    /**
     * Toggle dark/light theme
     */
    toggleTheme() {
        this.isDarkTheme = !this.isDarkTheme;
        document.body.classList.toggle('dark-theme', this.isDarkTheme);
        localStorage.setItem('finsight-theme', this.isDarkTheme ? 'dark' : 'light');
    }

    /**
     * Load theme preference
     */
    loadThemePreference() {
        const savedTheme = localStorage.getItem('finsight-theme');
        if (savedTheme === 'dark') {
            this.isDarkTheme = true;
            document.body.classList.add('dark-theme');
        }
    }

    /**
     * Auto-resize textarea
     */
    autoResizeTextarea() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = this.messageInput.scrollHeight + 'px';
    }

    /**
     * Scroll chat to bottom
     */
    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }
}

/**
 * Quick query function for sidebar buttons
 */
function sendQuickQuery(query) {
    const app = window.finsightApp;
    if (app && app.messageInput) {
        app.messageInput.value = query;
        app.sendBtn.disabled = false;
        app.messageInput.focus();
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.finsightApp = new FinSightApp();
});