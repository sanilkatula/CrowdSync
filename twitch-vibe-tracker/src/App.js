import React, { useState, useEffect } from "react";
import "./styles.css"; // Importing the CSS file

const API_BASE_URL = "http://127.0.0.1:5000"; // Flask backend URL

const App = () => {
  const [channel, setChannel] = useState("");
  const [newChannel, setNewChannel] = useState("");
  const [vibe, setVibe] = useState("⚪ Waiting for messages...");
  const [messages, setMessages] = useState([]);
  const [isMonitoring, setIsMonitoring] = useState(false);

  // Fetch vibe and messages from Flask backend
  useEffect(() => {
    const fetchVibe = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/vibe`);
        if (!response.ok) throw new Error("Failed to fetch vibe");
        const data = await response.json();
        
        if (data?.vibe && Array.isArray(data.messages)) {
          setVibe(data.vibe);
          setMessages(data.messages);
        }
      } catch (error) {
        console.error("Error fetching vibe:", error);
      }
    };

    if (isMonitoring) {
      fetchVibe();
      const interval = setInterval(fetchVibe, 5000); // Auto-refresh every 5s
      return () => clearInterval(interval);
    }
  }, [isMonitoring]);

  // Update the Twitch channel
  const updateChannel = async () => {
    if (!newChannel) return;
    try {
      const response = await fetch(`${API_BASE_URL}/setchannel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ channel: newChannel }),
      });

      const data = await response.json();
      if (data?.message) {
        setChannel(newChannel);
        setNewChannel("");
        setIsMonitoring(true);
        alert(`✅ Now monitoring: ${newChannel}`);
      } else {
        alert("❌ Failed to update channel.");
      }
    } catch (error) {
      console.error("Error setting channel:", error);
    }
  };

  // Reset monitoring
  const resetMonitoring = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/reset`, {
        method: "POST",
      });

      const data = await response.json();
      if (data?.message) {
        setChannel("");
        setVibe("⚪ Waiting for messages...");
        setMessages([]);
        setIsMonitoring(false);
        alert("🔄 Monitoring has been reset. Select a new channel.");
      } else {
        alert("❌ Failed to reset monitoring.");
      }
    } catch (error) {
      console.error("Error resetting:", error);
    }
  };

  return (
    <div className="app-container">
      {/* Left Side - Mood Tracker */}
      <div className="mood-tracker">
        <h2>🌡️ Mood Tracker</h2>
        <p className="mood-status">{vibe}</p>
      </div>

      {/* Right Side - Live Chat Messages */}
      <div className="chat-panel">
        <h2>💬 Live Chat</h2>
        <div className="chat-messages">
          {messages.map((msg, index) => (
            <div key={index} className="message">
              <strong className="username">{msg?.user || "Unknown"}:</strong> {msg?.content || "No message"}{" "}
              <span className="mood-tag">({msg?.mood || "Neutral"})</span>
            </div>
          ))}
        </div>
      </div>

      {/* Channel Selector & Reset Button */}
      <div className="channel-controls">
        <input
          type="text"
          placeholder="Enter Twitch channel"
          value={newChannel}
          onChange={(e) => setNewChannel(e.target.value)}
          className="channel-input"
        />
        <button
          onClick={updateChannel}
          className="channel-button"
        >
          Set Channel
        </button>
        {isMonitoring && (
          <button
            onClick={resetMonitoring}
            className="channel-button"
            style={{ background: "linear-gradient(45deg, #ff416c, #ff4b2b)" }}
          >
            Reset
          </button>
        )}
      </div>
    </div>
  );
};

export default App;
