
// server.js — API-шлюз: обращается к Python LLM-сервису, при недоступности — фолбэк в OpenAI напрямую
import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import OpenAI from 'openai';

const app = express();
app.use(express.json({ limit: '1mb' }));
app.use(cors({
  origin: process.env.CORS_ORIGIN ? process.env.CORS_ORIGIN.split(',') : true,
  credentials: false,
}));

const PY_SERVICE_URL = process.env.PY_SERVICE_URL || 'http://localhost:8000';
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

function mapStyle(s) {
  if (!s) return 'simple';
  const x = String(s).toLowerCase();
  if (x.includes('егэ') || x.includes('ege')) return 'ege';
  if (x.includes('подроб') || x.includes('развер')) return 'expanded';
  if (x.includes('simple') || x.includes('просто')) return 'simple';
  return 'simple';
}

async function callPythonService(payload) {
  const res = await fetch(PY_SERVICE_URL + '/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('PY_SERVICE ' + res.status);
  return res.json();
}

// very simple fallback to keep MVP working without python
async function fallbackOpenAI({ question, subject, grade, settings }) {
  const sys = [
    'Ты — школьный тьютор.',
    `Предмет: ${subject}. Класс: ${grade}.`,
    `Стиль: ${settings?.explainLevel || 'простыми словами'}.`,
    'Структура: краткое объяснение → 1–2 примера → 3 тест-вопроса (с ответами, спрятанными после пустой строки).',
    'Если нужны формулы — используй KaTeX: $...$ или $$...$$.'
  ].join(' ');

  const resp = await openai.chat.completions.create({
    model: process.env.OPENAI_MODEL || 'gpt-4o-mini',
    messages: [
      { role: 'system', content: sys },
      { role: 'user', content: question }
    ],
  });

  const text = resp.choices?.[0]?.message?.content?.trim() || 'Не удалось получить ответ.';
  return { answer: text };
}

app.post('/api/answer', async (req, res) => {
  try {
    const { question, subject = 'Общий', grade = '7', settings = {}, history = [] } = req.body || {};
    if (!question || String(question).trim() === '') {
      return res.status(400).json({ error: 'Empty question' });
    }

    const payload = {
      subject: subject,
      grade: Number(grade) || 8,
      style: mapStyle(settings.explainLevel),
      query: question
    };

    try {
      const data = await callPythonService(payload);
      if (data?.markdown) {
        return res.json({ answer: data.markdown, meta: { normalized: data.payload } });
      }
      if (data?.output) {
        const o = data.output;
        const md = [
          '## Объяснение', o.explanation || '',
          '\n## Примеры', ...(o.examples || []).map(x => '- ' + x)
        ].join('\n');
        return res.json({ answer: md, meta: { normalized: data.payload } });
      }
      throw new Error('Bad payload from python');
    } catch (e) {
      if (!process.env.OPENAI_API_KEY) {
        console.error('Fallback requires OPENAI_API_KEY');
        return res.status(502).json({ error: 'LLM backend unavailable and no fallback key' });
      }
      const fb = await fallbackOpenAI({ question, subject, grade, settings });
      return res.json(fb);
    }
  } catch (err) {
    console.error('[ERROR /api/answer]', err);
    return res.status(500).json({ error: 'Internal error' });
  }
});

app.get('/health', async (_req, res) => {
  try {
    const r = await fetch(PY_SERVICE_URL + '/health').then(r => r.json()).catch(() => ({ ok: false }));
    res.json({ ok: true, py: r?.ok === true });
  } catch {
    res.json({ ok: true, py: false });
  }
});

const port = process.env.PORT || 8787;
app.listen(port, '0.0.0.0', () => {
  console.log('API gateway on http://0.0.0.0:' + port);
});
