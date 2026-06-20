// Voice service for natural text-to-speech
// Supports multiple TTS backends

class VoiceService {
  constructor() {
    this.currentProvider = 'browser';
    this.elevenLabsApiKey = null;
    this.selectedVoice = null;
  }

  // Configure ElevenLabs API
  setElevenLabsApiKey(apiKey) {
    this.elevenLabsApiKey = apiKey;
    if (apiKey) {
      this.currentProvider = 'elevenlabs';
    }
  }

  // Get available browser voices
  getBrowserVoices() {
    if (!('speechSynthesis' in window)) {
      return [];
    }
    return speechSynthesis.getVoices();
  }

  // Find the best natural voice for a language
  findBestVoice(lang = 'en') {
    const voices = this.getBrowserVoices();

    // Prefer premium neural voices (Google, Microsoft, Apple)
    const preferredPrefixes = ['Google', 'Microsoft', 'Apple', 'Samantha', 'Daniel', 'Moira'];

    // Try to find a premium voice
    for (const prefix of preferredPrefixes) {
      const voice = voices.find(v =>
        v.name.includes(prefix) && v.lang.startsWith(lang)
      );
      if (voice) return voice;
    }

    // Fallback to any voice for the language
    return voices.find(v => v.lang.startsWith(lang)) || voices[0];
  }

  // Speak using browser speechSynthesis
  speakWithBrowser(text, options = {}) {
    return new Promise((resolve, reject) => {
      if (!('speechSynthesis' in window)) {
        reject(new Error('Speech synthesis not supported'));
        return;
      }

      speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);

      // Find best voice
      const lang = options.lang || 'en';
      const bestVoice = this.findBestVoice(lang);
      if (bestVoice) {
        utterance.voice = bestVoice;
        utterance.lang = bestVoice.lang;
      } else {
        utterance.lang = lang;
      }

      // Apply options
      utterance.rate = options.rate || 0.8;
      utterance.pitch = options.pitch || 1.0;
      utterance.volume = options.volume || 1.0;

      utterance.onend = () => resolve();
      utterance.onerror = (e) => reject(e);

      speechSynthesis.speak(utterance);
    });
  }

  // Speak using ElevenLabs API (more natural)
  async speakWithElevenLabs(text, options = {}) {
    if (!this.elevenLabsApiKey) {
      console.warn('ElevenLabs API key not set, falling back to browser');
      return this.speakWithBrowser(text, options);
    }

    const voiceId = options.voiceId || 'rachel'; // Default voice
    const stability = options.stability || 0.5;
    const similarityBoost = options.similarityBoost || 0.75;

    try {
      const response = await fetch(
        `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`,
        {
          method: 'POST',
          headers: {
            'Accept': 'audio/mpeg',
            'Content-Type': 'application/json',
            'xi-api-key': this.elevenLabsApiKey
          },
          body: JSON.stringify({
            text: text,
            model_id: 'eleven_monolingual_v1',
            voice_settings: {
              stability: stability,
              similarity_boost: similarityBoost
            }
          })
        }
      );

      if (!response.ok) {
        throw new Error(`ElevenLabs API error: ${response.status}`);
      }

      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);

      return new Promise((resolve, reject) => {
        const audio = new Audio(audioUrl);
        audio.onended = () => {
          URL.revokeObjectURL(audioUrl);
          resolve();
        };
        audio.onerror = (e) => {
          URL.revokeObjectURL(audioUrl);
          reject(e);
        };
        audio.play();
      });
    } catch (error) {
      console.error('ElevenLabs TTS error:', error);
      // Fallback to browser
      return this.speakWithBrowser(text, options);
    }
  }

  // Main speak function - chooses best available provider
  async speak(text, options = {}) {
    if (this.currentProvider === 'elevenlabs' && this.elevenLabsApiKey) {
      return this.speakWithElevenLabs(text, options);
    }
    return this.speakWithBrowser(text, options);
  }

  // Stop speaking
  stop() {
    if ('speechSynthesis' in window) {
      speechSynthesis.cancel();
    }
  }
}

export const voiceService = new VoiceService();
export default voiceService;
