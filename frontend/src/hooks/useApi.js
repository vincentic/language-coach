// Custom hooks for API calls
import { useState, useEffect } from 'react';
import * as api from '../services/api';

export function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      const data = await api.authAPI.getMe();
      setUser(data);
    } catch (error) {
      console.error('Failed to load user:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateProfile = async (data) => {
    const updated = await api.authAPI.updateProfile(data);
    setUser(updated);
    return updated;
  };

  return { user, loading, updateProfile, reload: loadUser };
}

export function usePractice() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadRecords = async () => {
    try {
      const data = await api.practiceAPI.getRecords();
      setRecords(data);
    } catch (error) {
      console.error('Failed to load practice records:', error);
    }
  };

  const analyzeAudio = async (audio, language, type) => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('audio', audio);
      formData.append('language', language);
      formData.append('type', type);
      const result = await api.practiceAPI.analyzeAudio(formData);
      setRecords(prev => [result, ...prev]);
      return result;
    } finally {
      setLoading(false);
    }
  };

  return { records, loading, loadRecords, analyzeAudio };
}

export function useConversation() {
  const [conversations, setConversations] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadConversations();
    loadScenarios();
  }, []);

  const loadConversations = async () => {
    try {
      const data = await api.conversationAPI.getConversations();
      setConversations(data);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const loadScenarios = async () => {
    try {
      const data = await api.conversationAPI.getScenarios();
      setScenarios(data);
    } catch (error) {
      console.error('Failed to load scenarios:', error);
    }
  };

  const startConversation = async (language, scenario) => {
    setLoading(true);
    try {
      const conv = await api.conversationAPI.startConversation({ language, scenario });
      setConversations(prev => [conv, ...prev]);
      setCurrentConversation(conv);
      return conv;
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async (conversationId, content) => {
    setLoading(true);
    try {
      const result = await api.conversationAPI.sendMessage(conversationId, content);
      setCurrentConversation(result.conversation);
      return result;
    } finally {
      setLoading(false);
    }
  };

  return {
    conversations,
    scenarios,
    currentConversation,
    loading,
    loadConversations,
    startConversation,
    sendMessage,
    setCurrentConversation
  };
}

export function useProgress() {
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProgress();
  }, []);

  const loadProgress = async () => {
    setLoading(true);
    try {
      const data = await api.progressAPI.getAll();
      setProgress(data);
    } catch (error) {
      console.error('Failed to load progress:', error);
    } finally {
      setLoading(false);
    }
  };

  return { progress, loading, reload: loadProgress };
}

export function useSettings() {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const data = await api.settingsAPI.getSettings();
      setSettings(data);
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateSettings = async (section, data) => {
    const apiMap = {
      profile: api.settingsAPI.updateProfile,
      preferences: api.settingsAPI.updatePreferences,
      voice: api.settingsAPI.updateVoice,
      privacy: api.settingsAPI.updatePrivacy,
    };

    const updated = await apiMap[section](data);
    setSettings(prev => ({ ...prev, [section]: updated }));
    return updated;
  };

  return { settings, loading, reload: loadSettings, updateSettings };
}
