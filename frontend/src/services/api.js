// API service for communicating with backend
const API_BASE = 'http://localhost:5003/api';

async function fetchAPI(endpoint, options = {}) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  return response.json();
}

// Auth API
export const authAPI = {
  getMe: () => fetchAPI('/auth/me'),
  updateProfile: (data) => fetchAPI('/auth/me', {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  register: (data) => fetchAPI('/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  login: (data) => fetchAPI('/auth/login', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
};

// Practice API
export const practiceAPI = {
  getRecords: () => fetchAPI('/practice/'),
  analyzeAudio: async (formData) => {
    const response = await fetch(`${API_BASE}/practice/analyze`, {
      method: 'POST',
      body: formData,
    });
    return response.json();
  },
  getRecord: (id) => fetchAPI(`/practice/${id}`),
  getCoreLoop: (language, theme) => fetchAPI(`/practice/core-loop?language=${language}&theme=${theme}`),
  getImitatePrompt: (language, sentence) => fetchAPI(`/practice/imitate?language=${language}&sentence=${encodeURIComponent(sentence)}`),
  postCorrection: (language, userInput, targetSentence) => fetchAPI('/practice/correction', {
    method: 'POST',
    body: JSON.stringify({ language, user_input: userInput, target_sentence: targetSentence }),
  }),
  postApplication: (language, userVariation, originalSentence) => fetchAPI('/practice/apply', {
    method: 'POST',
    body: JSON.stringify({ language, user_variation: userVariation, original_sentence: originalSentence }),
  }),
  getScenarios: () => fetchAPI('/practice/scenarios'),
};

// Conversation API
export const conversationAPI = {
  getConversations: () => fetchAPI('/conversation/'),
  getScenarios: () => fetchAPI('/conversation/scenarios'),
  startConversation: (data) => fetchAPI('/conversation/start', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  sendMessage: (id, content) => fetchAPI(`/conversation/${id}/message`, {
    method: 'POST',
    body: JSON.stringify({ content }),
  }),
  getConversation: (id) => fetchAPI(`/conversation/${id}`),
  deleteConversation: (id) => fetchAPI(`/conversation/${id}`, {
    method: 'DELETE',
  }),
};

// Progress API
export const progressAPI = {
  getAll: () => fetchAPI('/progress/'),
  getWeekly: () => fetchAPI('/progress/weekly'),
  getMonthly: () => fetchAPI('/progress/monthly'),
  getSkills: () => fetchAPI('/progress/skills'),
  getAchievements: () => fetchAPI('/progress/achievements'),
  getStatistics: () => fetchAPI('/progress/statistics'),
  updateProgress: (data) => fetchAPI('/progress/update', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
};

// Settings API
export const settingsAPI = {
  getSettings: () => fetchAPI('/settings/'),
  updateProfile: (data) => fetchAPI('/settings/profile', {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  updatePreferences: async (data) => {
    const params = new URLSearchParams();
    if (data.native_language) params.append('native_language', data.native_language);
    if (data.target_language) params.append('target_language', data.target_language);
    if (data.theme) params.append('theme', data.theme);
    if (data.notifications) params.append('notifications', JSON.stringify(data.notifications));
    const response = await fetch(`${API_BASE}/settings/preferences?${params}`, {
      method: 'PUT',
    });
    return response.json();
  },
  updateVoice: (data) => fetchAPI('/settings/voice', {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  updatePrivacy: async (data) => {
    const params = new URLSearchParams();
    if (data.save_recordings !== undefined) params.append('save_recordings', data.save_recordings);
    if (data.share_progress !== undefined) params.append('share_progress', data.share_progress);
    if (data.anonymous_analytics !== undefined) params.append('anonymous_analytics', data.anonymous_analytics);
    const response = await fetch(`${API_BASE}/settings/privacy?${params}`, {
      method: 'PUT',
    });
    return response.json();
  },
  deleteAccount: () => fetchAPI('/settings/account', {
    method: 'DELETE',
  }),
};
