const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';

async function fetchWithAuth(endpoint) {
  try {
    const res = await fetch(`${API_URL}${endpoint}`, {
      headers: {
        'x-api-key': API_KEY,
        'Content-Type': 'application/json',
      },
      // In Next.js App router, we can control caching here. Let's revalidate every 5 seconds for dashboard freshness.
      next: { revalidate: 5 } 
    });
    
    if (!res.ok) {
      throw new Error(`API Error: ${res.status}`);
    }
    
    return await res.json();
  } catch (error) {
    console.error(`Error fetching ${endpoint}:`, error);
    return null;
  }
}

export async function getMetrics() {
  return fetchWithAuth('/metrics');
}

export async function getIntelligence() {
  return fetchWithAuth('/intelligence');
}

export async function getSession(sessionId) {
  return fetchWithAuth(`/sessions/${sessionId}`);
}

export async function listSessions() {
  return fetchWithAuth('/sessions');
}

export async function sendMessage(sessionId, text) {
  try {
    const res = await fetch(`${API_URL}/honeypot/message`, {
      method: 'POST',
      headers: {
        'x-api-key': API_KEY,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sessionId,
        message: {
          sender: 'scammer',
          text
        }
      })
    });
    
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return await res.json();
  } catch (error) {
    console.error('Error sending message:', error);
    return { error: error.message };
  }
}

// WhatsApp Monitor Control
export async function startWhatsAppMonitor() {
  try {
    const res = await fetch(`${API_URL}/monitor/whatsapp/start`, {
      method: 'POST',
      headers: {
        'x-api-key': API_KEY,
        'Content-Type': 'application/json',
      },
    });
    
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return await res.json();
  } catch (error) {
    console.error('Error starting monitor:', error);
    return { error: error.message };
  }
}

export async function stopWhatsAppMonitor() {
  try {
    const res = await fetch(`${API_URL}/monitor/whatsapp/stop`, {
      method: 'POST',
      headers: {
        'x-api-key': API_KEY,
        'Content-Type': 'application/json',
      },
    });
    
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return await res.json();
  } catch (error) {
    console.error('Error stopping monitor:', error);
    return { error: error.message };
  }
}

export async function getWhatsAppStatus() {
  try {
    const res = await fetch(`${API_URL}/monitor/whatsapp/status`, {
      headers: {
        'x-api-key': API_KEY,
        'Content-Type': 'application/json',
      },
      cache: 'no-store'
    });
    
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return await res.json();
  } catch (error) {
    console.error('Error getting status:', error);
    return { error: error.message };
  }
}

export async function getWhatsAppOutput(lines = 20) {
  try {
    const res = await fetch(`${API_URL}/monitor/whatsapp/output?lines=${lines}`, {
      headers: {
        'x-api-key': API_KEY,
        'Content-Type': 'application/json',
      },
      cache: 'no-store'
    });
    
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return await res.json();
  } catch (error) {
    console.error('Error getting output:', error);
    return { error: error.message };
  }
}
