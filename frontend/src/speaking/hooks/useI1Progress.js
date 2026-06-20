import { useState, useEffect, useCallback } from 'react';

const API_BASE = 'http://localhost:5000/api/i1';

/**
 * useI1Progress - Hook for i+1 adaptive learning state management
 *
 * Provides:
 * - User proficiency levels per language
 * - Spaced repetition review items
 * - i+1 passage selection
 * - Review recording
 */
export function useI1Progress(userId, language = 'es') {
  const [proficiency, setProficiency] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch user proficiency on mount or language change
  useEffect(() => {
    if (!userId) {
      setLoading(false);
      return;
    }
    fetchProficiency();
  }, [userId, language]);

  const fetchProficiency = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/proficiency/${userId}?language=${language}`);
      if (!response.ok) throw new Error('Failed to fetch proficiency');
      const data = await response.json();
      setProficiency(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching proficiency:', err);
    } finally {
      setLoading(false);
    }
  };

  const updateProficiency = async (scores) => {
    try {
      const response = await fetch(`${API_BASE}/proficiency/${userId}?language=${language}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scores })
      });
      const data = await response.json();
      setProficiency(prev => ({
        ...prev,
        updated_levels: data.updated_levels,
        i_label: data.i_label
      }));
      return data;
    } catch (err) {
      console.error('Error updating proficiency:', err);
      throw err;
    }
  };

  const selectI1Passage = async (scenario = null, reviewDueOnly = false) => {
    try {
      let url = `${API_BASE}/select/${userId}?language=${language}`;
      if (scenario) url += `&scenario=${scenario}`;
      if (reviewDueOnly) url += `&review_due_only=true`;

      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to select passage');
      return await response.json();
    } catch (err) {
      console.error('Error selecting i+1 passage:', err);
      throw err;
    }
  };

  return {
    proficiency,
    loading,
    error,
    updateProficiency,
    selectI1Passage,
    refreshProficiency: fetchProficiency
  };
}

/**
 * useSpacedReview - Hook for spaced repetition review management
 */
export function useSpacedReview(userId, language = null) {
  const [dueItems, setDueItems] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchDueReviews = useCallback(async () => {
    setLoading(true);
    try {
      let url = `${API_BASE}/review/due/${userId}`;
      if (language) url += `?language=${language}`;

      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch reviews');
      const data = await response.json();
      setDueItems(data.items || []);
      return data;
    } catch (err) {
      setError(err.message);
      console.error('Error fetching due reviews:', err);
      return { due_count: 0, items: [] };
    } finally {
      setLoading(false);
    }
  }, [userId, language]);

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/review/stats/${userId}`);
      if (!response.ok) throw new Error('Failed to fetch stats');
      const data = await response.json();
      setStats(data);
      return data;
    } catch (err) {
      console.error('Error fetching review stats:', err);
      setError(err.message);
      return null;
    }
  }, [userId]);

  const recordReview = async (itemId, quality) => {
    try {
      const response = await fetch(`${API_BASE}/review/${itemId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quality })
      });
      const data = await response.json();

      // Remove reviewed item from due list
      setDueItems(prev => prev.filter(item => item.id !== itemId));

      return data;
    } catch (err) {
      console.error('Error recording review:', err);
      throw err;
    }
  };

  // Initial fetch
  useEffect(() => {
    if (userId) {
      fetchDueReviews();
      fetchStats();
    }
  }, [userId, language, fetchDueReviews, fetchStats]);

  return {
    dueItems,
    stats,
    loading,
    error,
    fetchDueReviews,
    fetchStats,
    recordReview
  };
}

/**
 * useLevelProgress - Hook for level/difficulty tracking
 */
export function useLevelProgress(userId) {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/proficiency/${userId}/analytics`);
      if (!response.ok) throw new Error('Failed to fetch analytics');
      const data = await response.json();
      setAnalytics(data);
      return data;
    } catch (err) {
      console.error('Error fetching analytics:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    if (userId) {
      fetchAnalytics();
    }
  }, [userId, fetchAnalytics]);

  return {
    analytics,
    loading,
    fetchAnalytics
  };
}
