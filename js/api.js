const API = (() => {
  const BASE = window.API_BASE_URL || '';

  function getToken() {
    return localStorage.getItem('access_token');
  }

  function setToken(token) {
    localStorage.setItem('access_token', token);
  }

  function clearToken() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  }

  function getUser() {
    const raw = localStorage.getItem('user');
    return raw ? JSON.parse(raw) : null;
  }

  function setUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
  }

  async function request(path, options = {}) {
    const headers = { ...(options.headers || {}) };
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (!(options.body instanceof FormData) && options.body && typeof options.body === 'object') {
      headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(options.body);
    }
    const res = await fetch(`${BASE}/api/v1${path}`, { ...options, headers });
    if (res.status === 401) {
      clearToken();
      if (!window.location.pathname.includes('login.html') && !window.location.pathname.includes('register.html')) {
        window.location.href = 'login.html';
      }
      throw new Error('Unauthorized');
    }
    if (res.status === 204) return null;
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      let msg = data.detail || data.message || `Error ${res.status}`;
      if (Array.isArray(msg)) msg = msg.map((d) => d.msg || d).join(', ');
      throw new Error(msg);
    }
    return data;
  }

  return {
    getToken,
    setToken,
    clearToken,
    getUser,
    setUser,
    register: (body) => request('/auth/register', { method: 'POST', body }),
    login: (body) => request('/auth/login', { method: 'POST', body }),
    me: () => request('/auth/me'),
    getLibrary: () => request('/games/library'),
    addGame: (body) => request('/games/library', { method: 'POST', body }),
    removeGame: (id) => request(`/games/library/${id}`, { method: 'DELETE' }),
    uploadMemory: (formData) => request('/memories/upload', { method: 'POST', body: formData }),
    getGameMemories: (userGameId) => request(`/memories/game/${userGameId}`),
    getGameMemoriesFull: (userGameId) => request(`/memories/game/${userGameId}/full`),
    continueJourney: (userGameId) => request(`/memories/game/${userGameId}/continue`),
    deleteMemory: (id) => request(`/memories/${id}`, { method: 'DELETE' }),
    screenshotUrl: (path) => {
      if (!path) return null;
      if (path.startsWith('http')) return path;
      const name = path.replace(/\\/g, '/').split('/').pop();
      return `${BASE}/uploads/${name}`;
    },
  };
})();
