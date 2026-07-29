/**
 * 🍯 Honey-Pot — WhatsApp Local Monitor
 * ========================================
 * Runs silently in background. Monitors YOUR WhatsApp account.
 * When a scam is detected, auto-replies on YOUR behalf.
 *
 * Uses whatsapp-web.js (connects to WhatsApp Web as you).
 * 
 * Requirements:
 *   npm install whatsapp-web.js qrcode-terminal axios dotenv
 *
 * Setup:
 *   1. Copy .env.whatsapp → .env  (fill in your HONEYPOT_API_KEY)
 *   2. Run: node whatsapp_monitor.js
 *   3. Scan the QR code with your phone's WhatsApp → "Linked Devices"
 *   4. Done — it runs silently from now on (no need to scan again)
 */

require("dotenv").config();
const fs = require("fs");
const { Client, LocalAuth } = require("whatsapp-web.js");
const qrcode = require("qrcode-terminal");
const axios = require("axios");

// ─── Config ────────────────────────────────────────────────────────────────────
const HONEYPOT_URL = process.env.HONEYPOT_URL || "https://honey-pot-agent.onrender.com/honeypot/message";
const HONEYPOT_KEY = process.env.HONEYPOT_API_KEY || "";

// Phone numbers to NEVER auto-reply to (add trusted contacts here)
// Format: country code + number, e.g. "919876543210@c.us"
const WHITELISTED = new Set([]);

// In-memory conversation history per session
const conversationHistory = {};

// ─── Multi-Browser Auto-Detection ─────────────────────────────────────────────
// whatsapp-web.js requires a Chromium-based browser (Chrome, Edge, Brave, Opera).
// We auto-detect whichever is installed and prefer an already-running one.
const os = require("os");
const path = require("path");
const { execSync } = require("child_process");

function fileExists(p) {
    try { fs.accessSync(p, fs.constants.F_OK); return true; } catch { return false; }
}

function findBrowsers() {
    const candidates = [];
    const progFiles = process.env["ProgramFiles(x86)"] || process.env.ProgramFiles || "C:\\Program Files (x86)";
    const progFiles64 = process.env.ProgramFiles || "C:\\Program Files";
    const localAppData = process.env.LOCALAPPDATA || path.join(os.homedir(), "AppData", "Local");

    // 1. Puppeteer-downloaded Chrome (most reliable)
    const puppeteerCache = path.join(os.homedir(), ".cache", "puppeteer", "chrome");
    if (fs.existsSync(puppeteerCache)) {
        const entries = fs.readdirSync(puppeteerCache);
        for (const entry of entries) {
            const p = path.join(puppeteerCache, entry, "chrome-win64", "chrome.exe");
            if (fileExists(p)) candidates.push({ name: "Puppeteer Chrome", path: p });
        }
    }

    // 2. Google Chrome (system)
    const chromePaths = [
        path.join(progFiles64, "Google", "Chrome", "Application", "chrome.exe"),
        path.join(progFiles, "Google", "Chrome", "Application", "chrome.exe"),
        path.join(localAppData, "Google", "Chrome", "Application", "chrome.exe"),
    ];
    for (const p of chromePaths) if (fileExists(p)) candidates.push({ name: "Google Chrome", path: p });

    // 3. Microsoft Edge (system)
    const edgePaths = [
        path.join(progFiles64, "Microsoft", "Edge", "Application", "msedge.exe"),
        path.join(progFiles, "Microsoft", "Edge", "Application", "msedge.exe"),
        path.join(localAppData, "Microsoft", "Edge", "Application", "msedge.exe"),
    ];
    for (const p of edgePaths) if (fileExists(p)) candidates.push({ name: "Microsoft Edge", path: p });

    // 4. Brave
    const bravePaths = [
        path.join(progFiles64, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
        path.join(localAppData, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
    ];
    for (const p of bravePaths) if (fileExists(p)) candidates.push({ name: "Brave", path: p });

    // 5. Opera / Opera GX
    const operaPaths = [
        path.join(progFiles64, "Opera", "opera.exe"),
        path.join(progFiles, "Opera", "opera.exe"),
        path.join(localAppData, "Programs", "Opera", "opera.exe"),
        path.join(progFiles64, "Opera GX", "opera.exe"),
        path.join(localAppData, "Programs", "Opera GX", "opera.exe"),
    ];
    for (const p of operaPaths) if (fileExists(p)) candidates.push({ name: "Opera", path: p });

    // 6. Vivaldi
    const vivaldiPaths = [
        path.join(progFiles64, "Vivaldi", "Application", "vivaldi.exe"),
        path.join(localAppData, "Vivaldi", "Application", "vivaldi.exe"),
    ];
    for (const p of vivaldiPaths) if (fileExists(p)) candidates.push({ name: "Vivaldi", path: p });

    // 7. Env override
    const envPath = process.env.PUPPETEER_EXECUTABLE_PATH;
    if (envPath && fileExists(envPath)) candidates.push({ name: "ENV override", path: envPath });

    return candidates;
}

function isBrowserRunning(exeName) {
    try {
        execSync(`tasklist /FI "IMAGENAME eq ${exeName}" 2>nul | findstr /I "${exeName}"`, { shell: "cmd.exe" });
        return true;
    } catch { return false; }
}

function killStaleBrowsers() {
    const names = ["chrome.exe", "msedge.exe", "brave.exe", "opera.exe", "vivaldi.exe"];
    for (const n of names) {
        try {
            // Use double slashes for Git Bash compatibility on Windows
            execSync(`taskkill //F //IM ${n}`, { stdio: "ignore", shell: "cmd.exe" });
        } catch { /* ignore */ }
    }
}

const browsers = findBrowsers();
let selectedBrowser = null;

if (browsers.length > 0) {
    // Prefer a browser that is already running (user likely has WhatsApp open there)
    for (const b of browsers) {
        const exe = path.basename(b.path);
        if (isBrowserRunning(exe)) {
            selectedBrowser = b;
            break;
        }
    }
    // Fallback to first available
    if (!selectedBrowser) selectedBrowser = browsers[0];
    console.log(`🔍 Found ${browsers.length} browser(s). Using: ${selectedBrowser.name} (${selectedBrowser.path})`);
} else {
    console.log("⚠️  No Chromium browser found. Will let Puppeteer download Chrome automatically.");
}

// ─── WhatsApp Client Setup ─────────────────────────────────────────────────────
const client = new Client({
    authStrategy: new LocalAuth({ clientId: "honeypot" }),  // Saves session — no QR next time
    puppeteer: {
        headless: true,
        executablePath: selectedBrowser ? selectedBrowser.path : undefined,
        args: [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-accelerated-2d-canvas",
            "--disable-gpu",
            "--disable-extensions",
            "--disable-infobars",
            "--window-size=1920,1080",
            "--disable-features=IsolateOrigins,site-per-process",
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ]
    }
});

// ─── QR Code (first-time login) ────────────────────────────────────────────────
client.on("qr", (qr) => {
    console.log("\n🍯 Scan this QR code with WhatsApp → Linked Devices:\n");
    qrcode.generate(qr, { small: true });
});

client.on("ready", () => {
    console.log("✅ WhatsApp connected — Honey-Pot monitor active!");
    console.log("👁️  Watching all incoming messages silently...\n");
});

client.on("auth_failure", (msg) => {
    console.error("❌ Authentication failed:", msg);
});

client.on("disconnected", (reason) => {
    console.log("⚠️  WhatsApp disconnected:", reason);
    console.log("   Restarting in 10 seconds...");
    setTimeout(() => {
        client.initialize().catch((err) => {
            console.error("   Restart failed:", err.message);
        });
    }, 10000);
});

process.on("uncaughtException", (err) => {
    console.error("❌ Uncaught Exception:", err.message);
    console.error("   Restarting in 15 seconds...");
    setTimeout(() => {
        client.initialize().catch((e) => {
            console.error("   Restart failed:", e.message);
        });
    }, 15000);
});

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
                metadata: { channel: "WhatsApp" }
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
client.on("message", async (msg) => {
    // Only private (1-on-1) messages, skip group chats
    if (msg.fromMe) return;
    // Skip groups: group IDs end with @g.us
    if (msg.from && msg.from.endsWith("@g.us")) return;

    const sender = msg.from;  // e.g. "919876543210@c.us"
    const text = msg.body?.trim();

    if (!text || WHITELISTED.has(sender)) return;

    const sessionId = `wa_${sender.replace("@c.us", "")}`;
    console.log(`📩 Message from ${sender}: ${text.substring(0, 60)}...`);

    const reply = await checkMessage(sessionId, text);

    if (reply) {
        console.warn(`⚠️  SCAM DETECTED — auto-replying as you`);
        await msg.reply(reply);   // Sends as YOUR WhatsApp account
        console.log(`✅ Reply sent: ${reply.substring(0, 80)}...`);
    } else {
        console.log(`✅ Safe message — no action taken`);
    }
});

// ─── Start ──────────────────────────────────────────────────────────────────────
if (!HONEYPOT_KEY) {
    console.error("❌ HONEYPOT_API_KEY not set in .env");
    process.exit(1);
}

// ─── Robust Initialization with Retry ──────────────────────────────────────────
async function startWithRetry(retries = 3) {
    for (let i = 0; i < retries; i++) {
        try {
            console.log(`🍯 Starting Honey-Pot WhatsApp Monitor (attempt ${i + 1}/${retries})...`);
            await client.initialize();
            return; // Success
        } catch (err) {
            console.error(`❌ Attempt ${i + 1} failed:`, err.message);
            // Kill any hanging browser processes
            console.log("   Killing stale browser processes...");
            killStaleBrowsers();
            // Clear possibly corrupted auth cache before retry
            const authDir = path.join(__dirname, ".wwebjs_auth", "session-honeypot");
            if (fs.existsSync(authDir)) {
                console.log("   Clearing auth cache...");
                try {
                    fs.rmSync(authDir, { recursive: true, force: true });
                } catch (e) {
                    // ignore
                }
            }
            if (i < retries - 1) {
                console.log(`   Retrying in 5 seconds...`);
                await new Promise((r) => setTimeout(r, 5000));
            }
        }
    }
    console.error("❌ WhatsApp monitor failed after all retries.");
    console.error("   Make sure a Chromium browser is installed (Chrome, Edge, Brave, Opera).");
    console.error("   Or install Chrome: https://google.com/chrome");
    process.exit(1);
}

startWithRetry();
