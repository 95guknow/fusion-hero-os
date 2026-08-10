import express from 'express';
import { createServer as createViteServer } from 'vite';
import { GoogleGenAI, ThinkingLevel, Modality, GenerateVideosOperation } from '@google/genai';
import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/** Env truthy helper (1/true/yes/on). */
function envFlag(name: string, defaultValue = false): boolean {
  const raw = process.env[name];
  if (raw == null || raw === '') return defaultValue;
  return /^(1|true|yes|on)$/i.test(String(raw).trim());
}

/** Comma-separated env list → trimmed non-empty unique models. */
function envModelList(name: string, fallback: string[]): string[] {
  const raw = process.env[name];
  const parts = (raw && raw.trim() ? raw.split(',') : fallback)
    .map((s) => s.trim())
    .filter(Boolean);
  return [...new Set(parts)];
}

/**
 * Model matrix for AscensionOS / Fusionista Lab.
 * Free-tier keys often return limit:0 for gemini-*-pro* — prefer flash + fallbacks.
 *
 * Env:
 *   GEMINI_PREFER_FREE_TIER=1     — skip Pro first; use flash as primary (recommended free tier)
 *   GEMINI_MODEL_PRO              — primary high-reasoning model
 *   GEMINI_MODEL_FLASH            — free-tier / fast model
 *   GEMINI_MODEL_LITE             — low-latency model
 *   GEMINI_MODEL_REASONING_CHAIN  — ordered fallbacks after primary (comma-separated)
 *   GEMINI_ENABLE_THINKING=1      — attach ThinkingLevel.HIGH on pro-like models only
 */
const PREFER_FREE_TIER = envFlag('GEMINI_PREFER_FREE_TIER', true);
const ENABLE_THINKING = envFlag('GEMINI_ENABLE_THINKING', true);

const MODEL_PRO = process.env.GEMINI_MODEL_PRO || 'gemini-3.1-pro-preview';
const MODEL_FLASH =
  process.env.GEMINI_MODEL_FLASH ||
  process.env.FUSION_GEMINI_MODEL ||
  'gemini-2.5-flash';
const MODEL_LITE = process.env.GEMINI_MODEL_LITE || 'gemini-2.0-flash-lite';
const MODEL_IMAGE = process.env.GEMINI_MODEL_IMAGE || 'gemini-3.1-flash-image';
const MODEL_TTS = process.env.GEMINI_MODEL_TTS || 'gemini-3.1-flash-tts-preview';

const REASONING_PRIMARY = PREFER_FREE_TIER ? MODEL_FLASH : MODEL_PRO;
const REASONING_CHAIN = envModelList(
  'GEMINI_MODEL_REASONING_CHAIN',
  PREFER_FREE_TIER
    ? [MODEL_FLASH, 'gemini-2.0-flash', MODEL_LITE, MODEL_PRO]
    : [MODEL_PRO, MODEL_FLASH, 'gemini-2.0-flash', MODEL_LITE]
);

function isProLikeModel(model: string): boolean {
  return /pro/i.test(model) && !/flash/i.test(model);
}

function isQuotaOrRateLimitError(err: any): boolean {
  const msg = String(err?.message || err || '');
  const status = err?.status ?? err?.code ?? err?.error?.code;
  return (
    status === 429 ||
    status === 'RESOURCE_EXHAUSTED' ||
    /RESOURCE_EXHAUSTED|exceeded your current quota|Quota exceeded|rate.?limit|limit:\s*0/i.test(msg)
  );
}

function formatGeminiError(err: any): string {
  const msg = String(err?.message || err || 'Unknown Gemini error');
  if (isQuotaOrRateLimitError(err)) {
    return (
      'Gemini quota exhausted (429 RESOURCE_EXHAUSTED). ' +
      'Free-tier Pro models often report limit:0 — set GEMINI_PREFER_FREE_TIER=1 (default), ' +
      'use GEMINI_MODEL_FLASH=gemini-2.5-flash / gemini-2.0-flash, or enable billing on the API key project. ' +
      'Details: ' + msg.slice(0, 500)
    );
  }
  return msg;
}

type GenerateArgs = {
  contents: any;
  config?: Record<string, any>;
};

/**
 * Try models in order; on 429/quota, drop thinking and continue chain.
 * Returns { response, modelUsed }.
 */
async function generateWithFallback(
  ai: GoogleGenAI,
  models: string[],
  args: GenerateArgs,
  label = 'gemini'
): Promise<{ response: any; modelUsed: string }> {
  const chain = [...new Set(models.filter(Boolean))];
  if (!chain.length) {
    throw new Error('No Gemini models configured for generateWithFallback');
  }

  let lastError: any;
  for (const model of chain) {
    const config: Record<string, any> = { ...(args.config || {}) };

    // ThinkingLevel.HIGH is Pro-oriented; strip on flash/lite to avoid hard failures.
    if (config.thinkingConfig && !(ENABLE_THINKING && isProLikeModel(model))) {
      delete config.thinkingConfig;
    }

    try {
      console.log(`[${label}] generateContent model=${model}`);
      const response = await ai.models.generateContent({
        model,
        contents: args.contents,
        config,
      });
      return { response, modelUsed: model };
    } catch (err: any) {
      lastError = err;
      if (isQuotaOrRateLimitError(err)) {
        console.warn(`[${label}] quota/rate-limit on ${model}, trying next fallback…`);
        continue;
      }
      console.error(`[${label}] non-quota error on ${model}:`, err?.message || err);
      throw err;
    }
  }

  throw new Error(formatGeminiError(lastError));
}

async function startServer() {
  const app = express();
  const port = 3000;

  app.use(express.json({ limit: '50mb' }));
  app.use(express.urlencoded({ limit: '50mb', extended: true }));

  // Initialize Gemini Client
  const apiKey = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;
  const ai = new GoogleGenAI({
    apiKey: apiKey || '',
    httpOptions: {
      headers: {
        'User-Agent': 'aistudio-build',
      },
    },
  });

  // Helper to verify API Key
  const checkApiKey = () => {
    if (!process.env.GEMINI_API_KEY && !process.env.GOOGLE_API_KEY) {
      throw new Error('GEMINI_API_KEY is not configured. Please add your key in the Secrets panel in AI Studio.');
    }
  };

  // Telemetry: active model matrix (no secrets)
  app.get('/api/gemini/models', (_req, res) => {
    res.json({
      preferFreeTier: PREFER_FREE_TIER,
      enableThinking: ENABLE_THINKING,
      reasoningPrimary: REASONING_PRIMARY,
      reasoningChain: REASONING_CHAIN,
      flash: MODEL_FLASH,
      lite: MODEL_LITE,
      pro: MODEL_PRO,
      image: MODEL_IMAGE,
      tts: MODEL_TTS,
    });
  });

  // Endpoint: High-Thinking Recipe Fusion (FusionIsta)
  app.post('/api/gemini/recipe', async (req, res) => {
    try {
      checkApiKey();
      const { itemA, itemB, fusionType } = req.body;
      
      const prompt = `Develop an extremely detailed and highly creative fusion recipe combining: "${itemA}" and "${itemB}" (Type of fusion: ${fusionType}).
The recipe must be innovative, visually stunning, and physically plausible.
Provide the response in structured JSON format with the following schema:
{
  "name": "Creative name for the fusion dish",
  "tagline": "Short poetic culinary tagline",
  "difficulty": "Easy" | "Medium" | "Hard",
  "prepTime": "Prep time (e.g. 20 mins)",
  "cookTime": "Cook time (e.g. 45 mins)",
  "fusionRatio": "Brief description of the balance (e.g. 60% Japanese, 40% Italian)",
  "flavorProfile": ["flavor1", "flavor2", ...],
  "ingredients": [
    { "item": "Ingredient with amount", "category": "Base" | "Fusion Twist" | "Garnish" }
  ],
  "steps": [
    { "number": 1, "title": "Step Title", "text": "Step instructions detailing the physical combination technique" }
  ],
  "chefSecrets": "A pro tip explaining why this chemical/culinary combination actually works."
}`;

      const { response, modelUsed } = await generateWithFallback(
        ai,
        REASONING_CHAIN,
        {
          contents: prompt,
          config: {
            systemInstruction:
              'You are FusionIsta, a molecular gastronomy chef who specializes in creating physical, delicious, and ground-breaking fusion recipes. You always answer in strict, valid JSON matching the requested schema.',
            responseMimeType: 'application/json',
            thinkingConfig: {
              thinkingLevel: ThinkingLevel.HIGH,
            },
          },
        },
        'recipe'
      );

      const responseText = response.text || '{}';
      const recipe = JSON.parse(responseText.trim());
      res.json({ ...recipe, _meta: { modelUsed, preferFreeTier: PREFER_FREE_TIER } });
    } catch (error: any) {
      console.error('Recipe Fusion Error:', error);
      res.status(500).json({ error: formatGeminiError(error) || 'An error occurred during recipe generation.' });
    }
  });

  // Endpoint: High-Thinking AI Assistant (Intelligence Core)
  app.post('/api/gemini/thinking', async (req, res) => {
    try {
      checkApiKey();
      const { message, history } = req.body;

      const systemInstruction = `You are the Fusion Hero OS Intelligence Core.
You run in a futuristic, cybernetic, operating system cockpit environment.
You help the user solve their most complex logical, technical, or creative queries.
Since you are in Thinking Mode (HIGH), you explain your detailed line of reasoning and then present a brilliant, clear, structured solution.
Keep your final output highly technical, clean, and styled in neat markdown with terminal-like telemetry references where appropriate.`;

      const { response, modelUsed } = await generateWithFallback(
        ai,
        REASONING_CHAIN,
        {
          contents: message,
          config: {
            systemInstruction: systemInstruction,
            thinkingConfig: {
              thinkingLevel: ThinkingLevel.HIGH,
            },
          },
        },
        'thinking'
      );

      res.json({ text: response.text, modelUsed });
    } catch (error: any) {
      console.error('Intelligence Core Error:', error);
      res.status(500).json({ error: formatGeminiError(error) || 'An error occurred during high-reasoning query.' });
    }
  });

  // Endpoint: Versatile Chat with groundings, thinking level toggles, etc.
  app.post('/api/gemini/chat', async (req, res) => {
    try {
      checkApiKey();
      const { message, mode, latitude, longitude } = req.body;

      let modelChain = [MODEL_FLASH, 'gemini-2.0-flash', MODEL_LITE];
      let config: any = {
        systemInstruction: 'You are the Fusion Hero OS Chat Intelligence Core. Answer the user accurately and beautifully in Markdown format.',
      };

      if (mode === 'high-thinking') {
        modelChain = REASONING_CHAIN;
        config.thinkingConfig = {
          thinkingLevel: ThinkingLevel.HIGH,
        };
      } else if (mode === 'low-latency') {
        modelChain = [MODEL_LITE, MODEL_FLASH, 'gemini-2.0-flash'];
      } else if (mode === 'search-grounding') {
        modelChain = [MODEL_FLASH, 'gemini-2.0-flash'];
        config.tools = [{ googleSearch: {} }];
      } else if (mode === 'maps-grounding') {
        modelChain = [MODEL_FLASH, 'gemini-2.0-flash'];
        config.tools = [{ googleMaps: {} }];
        if (latitude && longitude) {
          config.toolConfig = {
            retrievalConfig: {
              latLng: {
                latitude: Number(latitude),
                longitude: Number(longitude)
              }
            }
          };
        }
      }

      const { response, modelUsed } = await generateWithFallback(
        ai,
        modelChain,
        { contents: message, config },
        'chat'
      );

      const groundingChunks = response.candidates?.[0]?.groundingMetadata?.groundingChunks;

      res.json({
        text: response.text || '',
        groundingChunks: groundingChunks || null,
        modelUsed,
      });
    } catch (error: any) {
      console.error('Chat endpoint error:', error);
      res.status(500).json({ error: formatGeminiError(error) || 'Error occurred during chat operation.' });
    }
  });

  // Endpoint: Generate high-quality images with size and aspect ratio controls
  app.post('/api/gemini/generate-image', async (req, res) => {
    try {
      checkApiKey();
      const { prompt, aspectRatio, imageSize } = req.body;

      const response = await ai.models.generateContent({
        model: 'gemini-3.1-flash-image',
        contents: {
          parts: [{ text: prompt || 'A futuristic cybernetic interface' }]
        },
        config: {
          imageConfig: {
            aspectRatio: aspectRatio || '1:1',
            imageSize: imageSize || '1K'
          }
        }
      });

      let base64Image = '';
      const parts = response.candidates?.[0]?.content?.parts;
      if (parts) {
        for (const part of parts) {
          if (part.inlineData) {
            base64Image = part.inlineData.data;
            break;
          }
        }
      }

      if (!base64Image) {
        throw new Error('No image was returned from the Gemini image model.');
      }

      res.json({ imageUrl: `data:image/png;base64,${base64Image}` });
    } catch (error: any) {
      console.error('Image Gen error:', error);
      res.status(500).json({ error: error.message || 'Image generation failed.' });
    }
  });

  // Endpoint: Analyze Image / Media
  app.post('/api/gemini/analyze-media', async (req, res) => {
    try {
      checkApiKey();
      const { fileBase64, mimeType, prompt } = req.body;

      if (!fileBase64) {
        throw new Error('Please upload an image/media file first.');
      }

      const { response, modelUsed } = await generateWithFallback(
        ai,
        REASONING_CHAIN,
        {
          contents: {
            parts: [
              { inlineData: { data: fileBase64, mimeType: mimeType || 'image/png' } },
              {
                text:
                  prompt ||
                  'Identify and analyze the details of this image or video screenshot inside a cyber OS telemetry report.',
              },
            ],
          },
        },
        'analyze-media'
      );

      res.json({ text: response.text || '', modelUsed });
    } catch (error: any) {
      console.error('Analyze Media error:', error);
      res.status(500).json({ error: formatGeminiError(error) || 'Media analysis failed.' });
    }
  });

  // Endpoint: Audio Transcription
  app.post('/api/gemini/transcribe-audio', async (req, res) => {
    try {
      checkApiKey();
      const { fileBase64, mimeType } = req.body;

      if (!fileBase64) {
        throw new Error('No audio data received.');
      }

      const { response, modelUsed } = await generateWithFallback(
        ai,
        [MODEL_FLASH, 'gemini-2.0-flash', MODEL_LITE],
        {
          contents: {
            parts: [
              { inlineData: { data: fileBase64, mimeType: mimeType || 'audio/wav' } },
              { text: 'Transcribe this audio precisely. Return only the transcription text.' },
            ],
          },
        },
        'transcribe'
      );

      res.json({ text: response.text || '', modelUsed });
    } catch (error: any) {
      console.error('Transcription error:', error);
      res.status(500).json({ error: formatGeminiError(error) || 'Audio transcription failed.' });
    }
  });

  // Endpoint: Text to Speech (TTS)
  app.post('/api/gemini/tts', async (req, res) => {
    try {
      checkApiKey();
      const { text, voice } = req.body;

      const response = await ai.models.generateContent({
        model: 'gemini-3.1-flash-tts-preview',
        contents: [{ parts: [{ text: `Say clearly: ${text || 'System ready.'}` }] }],
        config: {
          responseModalities: [Modality.AUDIO],
          speechConfig: {
            voiceConfig: {
              prebuiltVoiceConfig: { voiceName: voice || 'Zephyr' }
            }
          }
        }
      });

      const base64Audio = response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
      if (!base64Audio) {
        throw new Error('TTS model failed to output voice data.');
      }

      res.json({ audioBase64: base64Audio });
    } catch (error: any) {
      console.error('TTS error:', error);
      res.status(500).json({ error: error.message || 'TTS generation failed.' });
    }
  });

  // Endpoint: Lyria Music Generation
  app.post('/api/gemini/generate-music', async (req, res) => {
    try {
      checkApiKey();
      const { prompt, length } = req.body;

      const model = length === 'full' ? 'lyria-3-pro-preview' : 'lyria-3-clip-preview';
      const stream = await ai.models.generateContentStream({
        model: model,
        contents: prompt || 'Generate a short neon cyberpunk synth ambient loop.',
        config: {
          responseModalities: [Modality.AUDIO]
        }
      });

      let audioBase64 = '';
      let lyrics = '';
      let mimeType = 'audio/wav';

      for await (const chunk of stream) {
        const parts = chunk.candidates?.[0]?.content?.parts;
        if (!parts) continue;
        for (const part of parts) {
          if (part.inlineData?.data) {
            if (!audioBase64 && part.inlineData.mimeType) {
              mimeType = part.inlineData.mimeType;
            }
            audioBase64 += part.inlineData.data;
          }
          if (part.text && !lyrics) {
            lyrics = part.text;
          }
        }
      }

      if (!audioBase64) {
        throw new Error('Lyria model failed to generate any music audio stream.');
      }

      res.json({ audioBase64, lyrics, mimeType });
    } catch (error: any) {
      console.error('Music generation error:', error);
      res.status(500).json({ error: error.message || 'Music generation failed.' });
    }
  });

  // Endpoint: Veo Video Generation (3-Step Post Setup)
  app.post('/api/gemini/generate-video', async (req, res) => {
    try {
      checkApiKey();
      const { prompt, aspectRatio, resolution, fileBase64, mimeType } = req.body;

      const payload: any = {
        model: 'veo-3.1-lite-generate-preview',
        prompt: prompt || 'Futuristic wireframe digital code waterfall in cyber cockpit',
        config: {
          numberOfVideos: 1,
          resolution: resolution || '720p',
          aspectRatio: aspectRatio || '16:9'
        }
      };

      if (fileBase64) {
        payload.image = {
          imageBytes: fileBase64,
          mimeType: mimeType || 'image/png'
        };
      }

      const operation = await ai.models.generateVideos(payload);
      res.json({ operationName: operation.name });
    } catch (error: any) {
      console.error('Generate video error:', error);
      res.status(500).json({ error: error.message || 'Video generation initialization failed.' });
    }
  });

  app.post('/api/gemini/video-status', async (req, res) => {
    try {
      checkApiKey();
      const { operationName } = req.body;

      const op = new GenerateVideosOperation();
      op.name = operationName;
      const updated = await ai.operations.getVideosOperation({ operation: op });
      res.json({ done: updated.done });
    } catch (error: any) {
      console.error('Video status error:', error);
      res.status(500).json({ error: error.message || 'Failed to poll video generation operation.' });
    }
  });

  app.post('/api/gemini/video-download', async (req, res) => {
    try {
      checkApiKey();
      const { operationName } = req.body;

      const op = new GenerateVideosOperation();
      op.name = operationName;
      const updated = await ai.operations.getVideosOperation({ operation: op });

      const uri = updated.response?.generatedVideos?.[0]?.video?.uri;
      if (!uri) {
        throw new Error('Video URI not found. Ensure generation has completed successfully.');
      }

      const videoRes = await fetch(uri, {
        headers: { 'x-goog-api-key': process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY || '' },
      });

      res.setHeader('Content-Type', 'video/mp4');
      const buffer = await videoRes.arrayBuffer();
      res.send(Buffer.from(buffer));
    } catch (error: any) {
      console.error('Video download error:', error);
      res.status(500).json({ error: error.message || 'Video download extraction failed.' });
    }
  });

  // Endpoint: Live Workspace Files
  app.get('/api/workspace/files', async (req, res) => {
    try {
      const files = ['src/App.tsx', 'server.ts', 'package.json', 'index.html', 'metadata.json', '.env.example'];
      const fileData = await Promise.all(
        files.map(async (file) => {
          try {
            const filePath = path.join(process.cwd(), file);
            const content = await fs.promises.readFile(filePath, 'utf-8');
            const stats = await fs.promises.stat(filePath);
            const kbSize = (stats.size / 1024).toFixed(1) + ' KB';
            return { name: path.basename(file), path: '/' + file, size: kbSize, content };
          } catch (e) {
            return { name: path.basename(file), path: '/' + file, size: '0.0 KB', content: '// Error loading file' };
          }
        })
      );
      res.json(fileData);
    } catch (error: any) {
      res.status(500).json({ error: error.message || 'Failed to read workspace files.' });
    }
  });

  // Static serving or Dev environment middleware
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    // Serve static files in production
    app.use(express.static(path.join(__dirname, 'dist')));
    app.get('*', (req, res) => {
      res.sendFile(path.join(__dirname, 'dist', 'index.html'));
    });
  }

  app.listen(port, '0.0.0.0', () => {
    console.log(`Fusion Hero OS server running on http://0.0.0.0:${port}`);
  });
}

startServer();
