import React, { useState, useRef, useEffect } from "react";
import { MessageCircle, X, Send, Loader, HelpCircle } from "lucide-react";
import "./ChatbotWidget.css";

const ChatbotWidget = ({ diagnosis, confidence }) => {
    const [isChatOpen, setIsChatOpen] = useState(false);
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    const API_BASE_URL = "http://localhost:5000/api";

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        if (isChatOpen && inputRef.current) {
            inputRef.current.focus();
        }
    }, [isChatOpen]);

    // Fetch welcome message when chat opens
    useEffect(() => {
        if (isChatOpen && messages.length === 0) {
            fetchWelcomeMessage();
        }
    }, [isChatOpen]);

    const fetchWelcomeMessage = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/welcome`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ diagnosis, confidence }),
            });

            if (response.ok) {
                const data = await response.json();
                setMessages([{ type: "bot", content: data.message }]);
            }
        } catch (error) {
            console.error("Error fetching welcome message:", error);
            setMessages([
                {
                    type: "bot",
                    content: `👋 Hi! I can help explain your diagnosis of ${diagnosis} (${confidence.toFixed(
                        2
                    )}% confidence). Ask me anything!`,
                },
            ]);
        }
    };

    const handleSendMessage = async () => {
        const question = inputValue.trim();
        if (!question) return;

        // Add user message
        const userMessage = { type: "user", content: question };
        setMessages((prev) => [...prev, userMessage]);
        setInputValue("");
        setIsLoading(true);

        try {
            const response = await fetch(`${API_BASE_URL}/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    question,
                    diagnosis,
                    confidence,
                }),
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }

            const data = await response.json();
            setMessages((prev) => [
                ...prev,
                { type: "bot", content: data.answer },
            ]);
        } catch (error) {
            console.error("Chat error:", error);
            setMessages((prev) => [
                ...prev,
                {
                    type: "bot",
                    content: `❌ ${error.message}\n\nPlease make sure the backend server is running on port 5000.`,
                },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const formatMessage = (content) => {
        // Split by ** for bold text
        const parts = content.split("**");
        return parts.map((part, i) =>
            i % 2 === 0 ? part : <strong key={i}>{part}</strong>
        );
    };

    return (
        <>
            {/* Floating Action Button */}
            <button
                className="chat-fab"
                onClick={() => setIsChatOpen(!isChatOpen)}
                aria-label={isChatOpen ? "Close chat" : "Open chat"}
            >
                {isChatOpen ? <X size={24} /> : <MessageCircle size={24} />}
            </button>

            {/* Chat Window */}
            {isChatOpen && (
                <div className="chat-window">
                    {/* Header */}
                    <div className="chat-header">
                        <div className="chat-header-content">
                            <MessageCircle size={24} />
                            <div>
                                <h3>AI Assistant</h3>
                                <p>Ask about your diagnosis</p>
                            </div>
                        </div>
                    </div>

                    {/* Messages Area */}
                    <div className="chat-messages">
                        {messages.map((msg, idx) => (
                            <div
                                key={idx}
                                className={`message ${msg.type === "user" ? "user-message" : "bot-message"}`}
                            >
                                <div className="message-bubble">
                                    {formatMessage(msg.content)}
                                </div>
                            </div>
                        ))}
                        {isLoading && (
                            <div className="message bot-message">
                                <div className="message-bubble loading-bubble">
                                    <Loader size={16} className="spin-icon" />
                                    <span>Thinking...</span>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input Area */}
                    <div className="chat-input-area">
                        <div className="chat-input-container">
                            <button
                                className="help-button"
                                onClick={() => setInputValue("help")}
                                title="Get help"
                            >
                                <HelpCircle size={20} />
                            </button>
                            <input
                                ref={inputRef}
                                type="text"
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder="Ask about your diagnosis..."
                                disabled={isLoading}
                                className="chat-input"
                            />
                            <button
                                onClick={handleSendMessage}
                                disabled={isLoading || !inputValue.trim()}
                                className="send-button"
                            >
                                <Send size={18} />
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default ChatbotWidget;