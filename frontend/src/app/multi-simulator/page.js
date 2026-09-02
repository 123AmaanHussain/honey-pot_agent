"use client";

import { useState, useRef, useEffect } from 'react';
import styles from './page.module.css';

export default function MultiSimulator() {
  const [sessionId, setSessionId] = useState(`multi-${Math.floor(Math.random() * 10000)}`);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // Sender information for enhanced detection
  const [senderEmail, setSenderEmail] = useState('');
  const [senderPhone, setSenderPhone] = useState('');
  const [senderName, setSenderName] = useState('');
  const [senderProfile, setSenderProfile] = useState('');
  
  // Multiple model responses
  const [modelResponses, setModelResponses] = useState({
    'qwen/qwen3.6-27b': null,
    'qwen/qwen3.8-27b': null,
    'openai/gpt-oss-120b': null,
    'openai/gpt-oss-20b': null
  });
  
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [modelResponses, isLoading]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    const userText = inputText;
    setInputText('');
    setIsLoading(true);

    // Build sender information object
    const senderInfo = {};
    if (senderEmail.trim()) senderInfo.sender_email = senderEmail.trim();
    if (senderPhone.trim()) senderInfo.sender_phone = senderPhone.trim();
    if (senderName.trim()) senderInfo.sender_name = senderName.trim();
    if (senderProfile.trim()) senderInfo.sender_profile = senderProfile.trim();

    // Simulate responses from multiple models
    const models = Object.keys(modelResponses);
    const responses = {};
    
    // In a real implementation, this would call the API with different models
    // For now, we'll simulate the responses
    for (const model of models) {
      try {
        const response = await fetch('http://localhost:8000/honeypot/message', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'x-api-key': process.env.NEXT_PUBLIC_API_KEY || 'test-key'
          },
          body: JSON.stringify({
            sessionId: `${sessionId}-${model.replace('/', '-')}`,
            message: {
              sender: 'scammer',
              text: userText,
              ...senderInfo
            }
          })
        });
        
        const data = await response.json();
        responses[model] = data;
      } catch (error) {
        responses[model] = { error: error.message };
      }
    }
    
    setModelResponses(responses);
    setIsLoading(false);
  };

  const models = [
    { id: 'qwen/qwen3.6-27b', name: 'Qwen 3.6-27B', color: '#00d2d3' },
    { id: 'qwen/qwen3.8-27b', name: 'Qwen 3.8-27B', color: '#54a0ff' },
    { id: 'openai/gpt-oss-120b', name: 'GPT-OSS 120B', color: '#ff6b6b' },
    { id: 'openai/gpt-oss-20b', name: 'GPT-OSS 20B', color: '#feca57' }
  ];

  return (
    <div>
      <header className={styles.header}>
        <h1 className={styles.title}>Multi-Agent Model Comparison</h1>
        <p className={styles.subtitle}>Compare how different AI models respond to the same scammer message side-by-side</p>
      </header>

      <div className={styles.container}>
        {/* Input Section */}
        <div className={styles.inputSection}>
          <div className={styles.sessionInfo}>
            <span>Session ID: </span>
            <input 
              type="text" 
              className={styles.sessionInput} 
              value={sessionId} 
              onChange={(e) => setSessionId(e.target.value)} 
            />
          </div>
          
          <form className={styles.inputForm} onSubmit={handleSend}>
            <div className={styles.senderFields}>
              <input
                type="email"
                className={styles.senderInput}
                placeholder="Email"
                value={senderEmail}
                onChange={(e) => setSenderEmail(e.target.value)}
              />
              <input
                type="tel"
                className={styles.senderInput}
                placeholder="Phone"
                value={senderPhone}
                onChange={(e) => setSenderPhone(e.target.value)}
              />
              <input
                type="text"
                className={styles.senderInput}
                placeholder="Name"
                value={senderName}
                onChange={(e) => setSenderName(e.target.value)}
              />
              <input
                type="text"
                className={styles.senderInput}
                placeholder="Profile"
                value={senderProfile}
                onChange={(e) => setSenderProfile(e.target.value)}
              />
            </div>
            <div className={styles.messageInput}>
              <input 
                type="text" 
                className={styles.input} 
                placeholder="Type a suspicious message to test all models..." 
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                disabled={isLoading}
              />
              <button type="submit" className={styles.sendBtn} disabled={isLoading || !inputText.trim()}>
                {isLoading ? 'Testing All Models...' : 'Test All Models'}
              </button>
            </div>
          </form>
        </div>

        {/* Model Comparison Grid */}
        <div className={styles.modelsGrid}>
          {models.map((model) => (
            <div key={model.id} className={styles.modelCard}>
              <div className={styles.modelHeader} style={{ borderColor: model.color }}>
                <div className={styles.modelName}>{model.name}</div>
                <div className={styles.modelId}>{model.id}</div>
              </div>
              
              <div className={styles.modelContent}>
                {modelResponses[model.id] ? (
                  <div className={styles.responseDetails}>
                    {modelResponses[model.id].error ? (
                      <div className={styles.error}>
                        Error: {modelResponses[model.id].error}
                      </div>
                    ) : (
                      <>
                        <div className={styles.metric}>
                          <span className={styles.metricLabel}>Agent Engaged:</span>
                          <span className={styles.metricValue} style={{ 
                            color: modelResponses[model.id].agent_engaged ? '#00ff88' : '#ff6b6b' 
                          }}>
                            {modelResponses[model.id].agent_engaged ? 'Yes' : 'No'}
                          </span>
                        </div>
                        
                        <div className={styles.metric}>
                          <span className={styles.metricLabel}>Scam Detected:</span>
                          <span className={styles.metricValue} style={{ 
                            color: modelResponses[model.id].scam_detected ? '#ff6b6b' : '#00ff88' 
                          }}>
                            {modelResponses[model.id].scam_detected ? 'Yes' : 'No'}
                          </span>
                        </div>
                        
                        <div className={styles.metric}>
                          <span className={styles.metricLabel}>Confidence:</span>
                          <span className={styles.metricValue}>
                            {modelResponses[model.id].confidence ? Math.round(modelResponses[model.id].confidence * 100) : 0}%
                          </span>
                        </div>

                        {modelResponses[model.id].scam_type && (
                          <div className={styles.metric}>
                            <span className={styles.metricLabel}>Scam Type:</span>
                            <span className={styles.metricValue} style={{ color: '#ff6b6b' }}>
                              {modelResponses[model.id].scam_type}
                            </span>
                          </div>
                        )}

                        {modelResponses[model.id].reply && (
                          <div className={styles.agentResponse}>
                            <div className={styles.responseLabel}>Agent Response:</div>
                            <div className={styles.responseText}>
                              {modelResponses[model.id].reply}
                            </div>
                          </div>
                        )}

                        {modelResponses[model.id].flags && modelResponses[model.id].flags.length > 0 && (
                          <div className={styles.flags}>
                            <div className={styles.flagsLabel}>Detection Flags:</div>
                            <div className={styles.flagsList}>
                              {modelResponses[model.id].flags.map((flag, idx) => (
                                <span key={idx} className={styles.flag}>
                                  {flag}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                ) : (
                  <div className={styles.placeholder}>
                    Send a message to see how this model responds
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Comparison Summary */}
        {Object.values(modelResponses).some(r => r && !r.error) && (
          <div className={styles.summarySection}>
            <h2 className={styles.summaryTitle}>Model Comparison Summary</h2>
            <div className={styles.summaryGrid}>
              <div className={styles.summaryCard}>
                <div className={styles.summaryLabel}>Best Engagement</div>
                <div className={styles.summaryValue}>
                  {models.find(m => modelResponses[m.id]?.agent_engaged)?.name || 'None'}
                </div>
              </div>
              <div className={styles.summaryCard}>
                <div className={styles.summaryLabel}>Highest Confidence</div>
                <div className={styles.summaryValue}>
                  {models.reduce((best, m) => {
                    const conf = modelResponses[m.id]?.confidence || 0;
                    const bestConf = modelResponses[best.id]?.confidence || 0;
                    return conf > bestConf ? m : best;
                  }, models[0])?.name || 'None'}
                </div>
              </div>
              <div className={styles.summaryCard}>
                <div className={styles.summaryLabel}>Most Conservative</div>
                <div className={styles.summaryValue}>
                  {models.reduce((best, m) => {
                    const conf = modelResponses[m.id]?.confidence || 1;
                    const bestConf = modelResponses[best.id]?.confidence || 1;
                    return conf < bestConf ? m : best;
                  }, models[0])?.name || 'None'}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
