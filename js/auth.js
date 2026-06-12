function requireAuth() {
  if (!API.getToken()) {
    window.location.href = 'login.html';
    return false;
  }
  return true;
}

function updateUserUI() {
  const user = API.getUser();
  if (!user) return;
  document.querySelectorAll('[data-user-name]').forEach((el) => {
    el.textContent = user.full_name;
  });
}

function logout() {
  API.clearToken();
  window.location.href = 'login.html';
}

function formatRelativeTime(dateStr) {
  if (!dateStr) return 'Never';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 48) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function showToast(message, isError = false) {
  let toast = document.getElementById('app-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'app-toast';
    toast.className = 'fixed bottom-6 right-6 z-[200] px-5 py-3 rounded-xl text-sm font-medium shadow-lg transition-all';
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.className = `fixed bottom-6 right-6 z-[200] px-5 py-3 rounded-xl text-sm font-medium shadow-lg transition-all ${isError ? 'bg-red-600 text-white' : 'bg-primary text-on-primary'}`;
  toast.style.opacity = '1';
  setTimeout(() => { toast.style.opacity = '0'; }, 4000);
}
