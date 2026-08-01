/**
 * Email Monitor - IMAP-based email monitoring for scam detection
 * Monitors an email inbox, detects scam emails, and auto-replies
 */

const Imap = require('imap');
const { simpleParser } = require('mailparser');
const axios = require('axios');

// Configuration from command line arguments
const IMAP_HOST = process.argv[2];
const IMAP_PORT = parseInt(process.argv[3]) || 993;
const IMAP_USER = process.argv[4];
const IMAP_PASS = process.argv[5];
const HONEYPOT_URL = process.env.HONEYPOT_URL || 'http://localhost:8000/honeypot/message';
const HONEYPOT_API_KEY = process.env.HONEYPOT_API_KEY || 'test_secret_key_12345';

// Track processed emails to avoid duplicates
const processedEmails = new Set();
const CHECK_INTERVAL = 30000; // Check every 30 seconds

console.log('📧 Email Monitor Starting...');
console.log(`IMAP Host: ${IMAP_HOST}:${IMAP_PORT}`);
console.log(`User: ${IMAP_USER}`);
console.log(`Honeypot URL: ${HONEYPOT_URL}`);

// IMAP configuration
const imapConfig = {
    user: IMAP_USER,
    password: IMAP_PASS,
    host: IMAP_HOST,
    port: IMAP_PORT,
    tls: true,
    tlsOptions: { rejectUnauthorized: false }
};

let imap = null;
let isMonitoring = false;

/**
 * Initialize IMAP connection
 */
function connectImap() {
    return new Promise((resolve, reject) => {
        imap = new Imap(imapConfig);
        
        imap.once('ready', () => {
            console.log('✅ Connected to IMAP server');
            resolve(imap);
        });
        
        imap.once('error', (err) => {
            console.error('❌ IMAP connection error:', err);
            reject(err);
        });
        
        imap.once('end', () => {
            console.log('⚠️  IMAP connection ended');
            isMonitoring = false;
        });
        
        imap.connect();
    });
}

/**
 * Fetch unseen emails from INBOX
 */
function fetchUnseenEmails() {
    return new Promise((resolve, reject) => {
        imap.openBox('INBOX', false, (err, box) => {
            if (err) {
                console.error('❌ Error opening INBOX:', err);
                return reject(err);
            }
            
            // Search for unseen emails
            imap.search(['UNSEEN'], (err, results) => {
                if (err) {
                    console.error('❌ Error searching emails:', err);
                    return reject(err);
                }
                
                if (results.length === 0) {
                    console.log('📭 No new emails');
                    return resolve([]);
                }
                
                console.log(`📬 Found ${results.length} new emails`);
                
                const fetch = imap.fetch(results, {
                    bodies: '',
                    markSeen: false
                });
                
                const emails = [];
                
                fetch.on('message', (msg, seqno) => {
                    let emailBuffer = '';
                    
                    msg.on('body', (stream, info) => {
                        stream.on('data', (chunk) => {
                            emailBuffer += chunk.toString('utf8');
                        });
                        
                        stream.once('end', async () => {
                            try {
                                const parsed = await simpleParser(emailBuffer);
                                const emailId = parsed.messageId || `${seqno}-${Date.now()}`;
                                
                                if (!processedEmails.has(emailId)) {
                                    processedEmails.add(emailId);
                                    emails.push({
                                        id: emailId,
                                        from: parsed.from.text,
                                        subject: parsed.subject,
                                        text: parsed.text || '',
                                        html: parsed.html || '',
                                        date: parsed.date
                                    });
                                }
                            } catch (err) {
                                console.error('❌ Error parsing email:', err);
                            }
                        });
                    });
                });
                
                fetch.once('error', (err) => {
                    console.error('❌ Fetch error:', err);
                    reject(err);
                });
                
                fetch.once('end', () => {
                    resolve(emails);
                });
            });
        });
    });
}

/**
 * Check email for scam using Honey-Pot API
 */
async function checkScam(email) {
    try {
        const emailContent = `
From: ${email.from}
Subject: ${email.subject}
Date: ${email.date}
Body: ${email.text}
        `.trim();
        
        const response = await axios.post(HONEYPOT_URL, {
            message: emailContent,
            sender: email.from,
            metadata: {
                type: 'email',
                subject: email.subject,
                date: email.date
            }
        }, {
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': HONEYPOT_API_KEY
            }
        });
        
        return response.data;
    } catch (error) {
        console.error('❌ Error checking scam:', error.message);
        return null;
    }
}

/**
 * Send auto-reply to scam email
 */
async function sendAutoReply(email, replyText) {
    console.log(`📤 Would send auto-reply to: ${email.from}`);
    console.log(`   Reply: ${replyText.substring(0, 100)}...`);
    // Note: Actual email sending requires SMTP configuration
    // This is a placeholder for the auto-reply functionality
}

/**
 * Process new emails
 */
async function processEmails() {
    try {
        const emails = await fetchUnseenEmails();
        
        for (const email of emails) {
            console.log(`\n📧 Processing email from: ${email.from}`);
            console.log(`   Subject: ${email.subject}`);
            
            const scamResult = await checkScam(email);
            
            if (scamResult) {
                console.log(`   Scam Confidence: ${(scamResult.confidence * 100).toFixed(0)}%`);
                
                if (scamResult.confidence > 0.4) {
                    console.log('   🚨 SCAM DETECTED!');
                    
                    if (scamResult.reply) {
                        await sendAutoReply(email, scamResult.reply);
                    }
                    
                    if (scamResult.intelligence) {
                        console.log('   📊 Intelligence extracted:');
                        if (scamResult.intelligence.upiIds?.length) console.log(`      UPIs: ${scamResult.intelligence.upiIds.join(', ')}`);
                        if (scamResult.intelligence.phoneNumbers?.length) console.log(`      Phones: ${scamResult.intelligence.phoneNumbers.join(', ')}`);
                        if (scamResult.intelligence.phishingLinks?.length) console.log(`      Links: ${scamResult.intelligence.phishingLinks.join(', ')}`);
                    }
                } else {
                    console.log('   ✅ Not a scam (below threshold)');
                }
            }
        }
    } catch (error) {
        console.error('❌ Error processing emails:', error.message);
    }
}

/**
 * Main monitoring loop
 */
async function startMonitoring() {
    try {
        await connectImap();
        isMonitoring = true;
        
        console.log('🔄 Starting email monitoring loop...');
        
        const monitorInterval = setInterval(async () => {
            if (!isMonitoring) {
                clearInterval(monitorInterval);
                return;
            }
            
            try {
                await processEmails();
            } catch (error) {
                console.error('❌ Error in monitoring loop:', error.message);
            }
        }, CHECK_INTERVAL);
        
        // Graceful shutdown
        process.on('SIGINT', () => {
            console.log('\n🛑 Shutting down email monitor...');
            isMonitoring = false;
            if (imap) {
                imap.end();
            }
            process.exit(0);
        });
        
    } catch (error) {
        console.error('❌ Fatal error starting monitor:', error);
        process.exit(1);
    }
}

// Start the monitor
startMonitoring();
