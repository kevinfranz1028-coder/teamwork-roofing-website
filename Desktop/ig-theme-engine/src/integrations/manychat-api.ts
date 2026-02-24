import axios from 'axios';
import { CONFIG } from '../config/env.js';
import { getDb } from '../database/db.js';

const MANYCHAT_API = 'https://api.manychat.com/fb';

interface ManyChatFlow {
  name: string;
  triggerKeyword: string;
  messages: Array<{
    type: 'text' | 'image' | 'card';
    text?: string;
    imageUrl?: string;
    buttons?: Array<{ type: string; title: string; url?: string }>;
  }>;
}

/**
 * Create an automation rule triggered by a keyword.
 * If no ManyChat API key is configured, logs manual setup instructions.
 */
export async function createKeywordAutomation(flow: ManyChatFlow): Promise<any> {
  if (!CONFIG.manychat.apiKey) {
    console.log(`\nMANUAL MANYCHAT SETUP REQUIRED:`);
    console.log(`1. Go to ManyChat dashboard > Automation > Keywords`);
    console.log(`2. Add keyword trigger: "${flow.triggerKeyword}"`);
    console.log(`3. Set response message: "${flow.messages[0]?.text}"`);
    console.log(`4. Add email capture step if lead magnet flow\n`);
    return { manual: true, keyword: flow.triggerKeyword };
  }

  const response = await axios.post(`${MANYCHAT_API}/sending/sendContent`, {
    subscriber_id: 'all',
    data: {
      version: 'v2',
      content: {
        messages: flow.messages.map(m => ({
          type: m.type,
          text: m.text,
          ...(m.imageUrl ? { attachment: { type: 'image', payload: { url: m.imageUrl } } } : {}),
        })),
      },
    },
  }, {
    headers: { 'Authorization': `Bearer ${(CONFIG as any).manychat.apiKey}` }
  });

  return response.data;
}

/**
 * Sync all active DM flows from the database to ManyChat.
 */
export async function syncFlowsToManyChat(): Promise<{ synced: number; manual: number }> {
  const db = getDb();
  const flows = db.prepare('SELECT * FROM dm_flows WHERE is_active = 1').all() as any[];

  let synced = 0;
  let manual = 0;

  for (const flow of flows) {
    const steps = JSON.parse(flow.flow_steps_json);
    const result = await createKeywordAutomation({
      name: flow.flow_name,
      triggerKeyword: flow.trigger_keyword,
      messages: steps,
    });

    if (result.manual) {
      manual++;
    } else {
      synced++;
    }
  }

  return { synced, manual };
}
