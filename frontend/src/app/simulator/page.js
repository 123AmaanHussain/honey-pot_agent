"use client";

import { useState, useRef, useEffect } from 'react';
import styles from './page.module.css';
import { sendMessage } from '../../lib/api';

export default function Simulator() {
  const [sessionId, setSessionId] = useState(`sim-${Math.floor(Math.random() * 10000)}`);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [lastResponse, setLastResponse] = useState(null);
  
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    const userText = inputText;
    setInputText('');
    setMessages(prev => [...prev, { role: 'scammer', text: userText }]);
    setIsLoading(true);

    const res = await sendMessage(sessionId, userText);
    
    if (res.error) {
      setMessages(prev => [...prev, { role: 'system', text: `Error: ${res.error}` }]);
    } else {
      setLastResponse(res);
      if (res.reply) {
        setMessages(prev => [...prev, { role: 'agent', text: res.reply }]);
      } else {
        setMessages(prev => [...prev, { role: 'system', text: '[Message passed through safely. Agent did not engage.]' }]);
      }
    }
    
    setIsLoading(false);
  };

  return (
    <div>
      <header className={styles.header}>
        <h1 className={styles.title}>Live Chat Simulator</h1>
        <p className={styles.subtitle}>Test the Honey-Pot agent by sending suspicious messages.</p>
      </header>

      <div className={styles.container}>
        {/* Chat Interface */}
        <div className={styles.chatPanel}>
          <div className={styles.chatHeader}>
            <div>
              Simulator Session: 
              <input 
                type="text" 
                className={styles.sessionInput} 
                value={sessionId} 
                onChange={(e) => setSessionId(e.target.value)} 
                style={{ marginLeft: '8px' }}
              />
            </div>
          </div>
          
          <div className={styles.chatMessages}>
            {messages.length === 0 && (
              <div style={{ textAlign: 'center', color: 'var(--text-secondary)', marginTop: '2rem' }}>
                Start typing below as a "Scammer" to see the Honey-Pot agent engage!
                <br/><br/>
                <em>Example: "URGENT: Your account is blocked. Send 500 to fraud@upi."</em>
              </div>
            )}
            
            {messages.map((msg, idx) => (
              <div 
                key={idx} 
                className={`${styles.message} ${
                  msg.role === 'scammer' ? styles.scammerMsg : 
                  msg.role === 'agent' ? styles.agentMsg : ''
                }`}
                style={msg.role === 'system' ? { alignSelf: 'center', color: 'var(--text-secondary)', fontStyle: 'italic', background: 'transparent', border: 'none' } : {}}
              >
                {msg.role !== 'system' && (
                  <div className={styles.msgRole}>
                    {msg.role === 'scammer' ? 'You (Scammer)' : 'Honey-Pot Agent'}
                  </div>
                )}
                <div>{msg.text}</div>
              </div>
            ))}
            
            {isLoading && (
              <div className={styles.typingIndicator}>Honey-Pot Agent is analyzing and typing...</div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form className={styles.inputArea} onSubmit={handleSend}>
            <input 
              type="text" 
              className={styles.input} 
              placeholder="Type a suspicious message..." 
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              disabled={isLoading}
            />
            <button type="submit" className={styles.sendBtn} disabled={isLoading || !inputText.trim()}>
              Send
            </button>
          </form>
        </div>

        {/* Real-time Status Panel */}
        <div>
          <div className={styles.infoPanel}>
            <h2 className={styles.panelTitle}>API Response Status</h2>
            {lastResponse ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Agent Engaged</span>
                  <div style={{ fontWeight: '600', color: lastResponse.agent_engaged ? 'var(--accent-safe)' : 'var(--text-secondary)' }}>
                    {lastResponse.agent_engaged ? 'Yes' : 'No'}
                  </div>
                </div>
                
                <div>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Scam Detected</span>
                  <div style={{ fontWeight: '600', color: lastResponse.scam_detected ? 'var(--accent-scam)' : 'var(--text-secondary)' }}>
                    {lastResponse.scam_detected ? 'Yes' : 'No'}
                  </div>
                </div>

                <div>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Confidence Level</span>
                  <div style={{ fontWeight: '600' }}>
                    {lastResponse.confidence ? Math.round(lastResponse.confidence * 100) : 0}%
                  </div>
                </div>
                
                <div style={{ marginTop: '1rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                  View full session transcript and extracted intelligence in the <strong>Session Logs</strong> page.
                </div>
              </div>
            ) : (
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', fontStyle: 'italic' }}>
                Send a message to see real-time detection metrics.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
