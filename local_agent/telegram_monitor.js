/**
 * 🍯 Honey-Pot — Telegram Local Monitor
 * ========================================
 * Runs silently in background. Monitors YOUR Telegram bot.
 * When a scam is detected, auto-replies on behalf of the bot.
 *
 * Uses node-telegram-bot-api (Telegram Bot API).
 *
 * Requirements:
 *   npm install node-telegram-bot-api axios dotenv
 *
 * Setup:
 *   1. Create a bot via @BotFather on Telegram
 *   2. Get your bot token (format: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)
 *   3. Run: node telegram_monitor.js <BOT_TOKEN>
 *   4. Done — it runs silently monitoring for scam messages
 */

require("dotenv").config();
const TelegramBot = require("node-telegram-bot-api");
const axios = require("axios");

// ─── Config ────────────────────────────────────────────────────────────────────
// Get bot token from command line argument
const TELEGRAM_BOT_TOKEN = process.argv[2] || process.env.TELEGRAM_BOT_TOKEN || "";
const HONEYPOT_URL = process.env.HONEYPOT_URL || "https://honey-pot-agent.onrender.com/honeypot/message";
const HONEYPOT_KEY = process.env.HONEYPOT_API_KEY || "";

// User IDs to NEVER auto-reply to (add trusted contacts here)
const WHITELISTED = new Set([]);

// In-memory conversation history per session
const conversationHistory = {};

// ─── Telegram Bot Setup ─────────────────────────────────────────────────────────
if (!TELEGRAM_BOT_TOKEN) {
    console.error("❌ TELEGRAM_BOT_TOKEN not set in .env");
    console.error("   Get your token from @BotFather on Telegram");
    process.exit(1);
}

if (!HONEYPOT_KEY) {
    console.error("❌ HONEYPOT_API_KEY not set in .env");
    process.exit(1);
}

const bot = new TelegramBot(TELEGRAM_BOT_TOKEN, { polling: true });

console.log("🍯 Starting Honey-Pot Telegram Monitor...");
console.log("👁️  Watching all incoming messages silently...\n");

// ─── Conversation History Helpers ──────────────────────────────────────────────
function addHistory(sessionId, sender, text) {
    if (!conversationHistory[sessionId]) {
        conversationHistory[sessionId] = [];
    }
    conversationHistory[sessionId].push({ sender, text });
    // Keep last 20 messages
    if (conversationHistory[sessionId].length > 20) {
        conversationHistory[sessionId] = conversationHistory[sessionId].slice(-20);
    }
}

function getHistory(sessionId) {
    return conversationHistory[sessionId] || [];
}

// ─── Honey-Pot API Call ─────────────────────────────────────────────────────────
async function checkMessage(sessionId, text) {
    try {
        addHistory(sessionId, "scammer", text);
        const history = getHistory(sessionId).slice(0, -1); // exclude current
        const response = await axios.post(
            HONEYPOT_URL,
            {
                sessionId: sessionId,
                message: { sender: "scammer", text: text },
                conversationHistory: history,
                metadata: { channel: "Telegram" }
            },
            {
                headers: {
                    "x-api-key": HONEYPOT_KEY,
                    "Content-Type": "application/json"
                },
                timeout: 10000
            }
        );
        const reply = response.data.reply || null;
        if (reply) {
            addHistory(sessionId, "agent", reply);
        }
        return reply;
    } catch (err) {
        console.error("⚠️  API error:", err.message);
        return null;  // On error, do NOT auto-reply (safe default)
    }
}

// ─── Message Handler ───────────────────────────────────────────────────────────
bot.on('message', async (msg) => {
    // Skip messages from the bot itself
    if (msg.from.id === bot.id) return;
    
    // Skip group chats (only monitor private messages)
    if (msg.chat.type !== 'private') return;

    const userId = msg.from.id.toString();
    const text = msg.text?.trim();

    if (!text || WHITELISTED.has(userId)) return;

    const sessionId = `tg_${userId}`;
    const username = msg.from.username ? `@${msg.from.username}` : `User ${userId}`;
    
    console.log(`📩 Message from ${username} (${userId}): ${text.substring(0, 60)}...`);

    const reply = await checkMessage(sessionId, text);

    if (reply) {
        console.warn(`⚠️  SCAM DETECTED — auto-replying as bot`);
        await bot.sendMessage(msg.chat.id, reply);
        console.log(`✅ Reply sent: ${reply.substring(0, 80)}...`);
    } else {
        console.log(`✅ Safe message — no action taken`);
    }
});

// ─── Error Handling ─────────────────────────────────────────────────────────────
bot.on('polling_error', (error) => {
    console.error('❌ Polling error:', error.message);
});

process.on('uncaughtException', (err) => {
    console.error('❌ Uncaught Exception:', err.message);
});

process.on('SIGINT', () => {
    console.log('\n🍯 Stopping Telegram Monitor...');
    bot.stopPolling();
    process.exit(0);
});

console.log('✅ Telegram Monitor started successfully');
console.log('📱 Bot is now listening for messages...\n');
