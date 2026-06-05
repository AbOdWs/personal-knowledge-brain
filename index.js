/**
 * WhatsApp Bot
 * Connects your WhatsApp number to the n8n knowledge pipeline.
 * Messages are forwarded to the n8n webhook for processing.
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const fs = require('fs');

const config = JSON.parse(fs.readFileSync('/root/config.json', 'utf8'));

// n8n webhook URL — update this to match your n8n setup
const N8N_WEBHOOK = 'http://x.x.x.x:xxxx/webhook/whatsapp';

const client = new Client({
  authStrategy: new LocalAuth({ dataPath: '/root/whatsapp-bot/.wwebjs_auth' }),
  puppeteer: {
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
    executablePath: '/usr/bin/chromium-browser',
    headless: true
  }
});

client.on('qr', qr => {
  console.log('Scan this QR code with your WhatsApp:');
  qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
  console.log('WhatsApp bot is ready!');
});

client.on('message', async msg => {
  // Ignore group messages — only handle private chats
  if (msg.from.includes('@g.us')) return;

  const senderId = msg.from.replace('@c.us', '').replace('@lid', '');
  const text = msg.body || '';

  try {
    const response = await axios.post(N8N_WEBHOOK, {
      sender: senderId,
      message: text,
      platform: 'whatsapp'
    });

    const reply = response.data?.answer || response.data?.text || '';
    if (reply) await msg.reply(reply);
  } catch(e) {
    console.error('Error sending to n8n:', e.message);
  }
});

client.initialize();
