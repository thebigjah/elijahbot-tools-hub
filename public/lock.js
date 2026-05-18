// Simple password gate — SHA-256 client-side. Not bank-grade security; enough
// to keep casual snoopers out of a personal tool suite. Replace SECRET_HASH
// below with the hex digest of your chosen password.
//
// To generate a new hash, open browser console and run:
//   crypto.subtle.digest('SHA-256', new TextEncoder().encode('your-password'))
//     .then(b => console.log(Array.from(new Uint8Array(b)).map(x => x.toString(16).padStart(2, '0')).join('')))
//
// Default password is "purcell" — CHANGE THIS before sharing the URL with anyone.

const SECRET_HASH = 'e685b6be40952e8daf6c8aa347815677ff53c54f4bf6fdbd29307542ddec636e'; // sha256("purcell")

const UNLOCK_KEY = 'elijahbot-tools-unlocked';
const UNLOCK_EXPIRY_DAYS = 30; // re-prompt after N days for security

function _isUnlocked() {
  try {
    const data = JSON.parse(localStorage.getItem(UNLOCK_KEY) || 'null');
    if (!data || !data.ts) return false;
    const ageMs = Date.now() - data.ts;
    return ageMs < UNLOCK_EXPIRY_DAYS * 24 * 60 * 60 * 1000;
  } catch (e) {
    return false;
  }
}

async function _hash(s) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s));
  return Array.from(new Uint8Array(buf)).map(x => x.toString(16).padStart(2, '0')).join('');
}

function _lockUI() {
  document.body.innerHTML = `
    <div id="lock" style="position:fixed;inset:0;background:#0a0a14;color:#e8e8ea;display:flex;align-items:center;justify-content:center;font-family:-apple-system,system-ui,sans-serif;">
      <form id="unlock" style="background:#14141f;border:1px solid #2a2a3a;border-radius:12px;padding:2rem;max-width:340px;width:90%;text-align:center;">
        <div style="font-size:2rem;margin-bottom:0.5rem;color:#c2a173;">🔒</div>
        <h1 style="margin:0 0 0.4rem;font-size:1.3rem;">ElijahBot Tools</h1>
        <p style="color:#888;font-size:0.9rem;margin:0 0 1.5rem;">This is a private personal tool suite. Password required.</p>
        <input id="pw" type="password" autocomplete="current-password" placeholder="Password" style="width:100%;padding:0.7rem 1rem;border-radius:8px;border:1px solid #2a2a3a;background:#0a0a14;color:#e8e8ea;font-size:1rem;box-sizing:border-box;margin-bottom:0.6rem;" />
        <button type="submit" style="width:100%;padding:0.7rem 1rem;border:0;border-radius:8px;background:#c2a173;color:#0a0a14;font-weight:600;font-size:1rem;cursor:pointer;">Unlock</button>
        <p id="err" style="color:#c2453d;font-size:0.85rem;margin:0.8rem 0 0;min-height:1.2em;"></p>
      </form>
    </div>
  `;
  document.getElementById('unlock').addEventListener('submit', async (e) => {
    e.preventDefault();
    const pw = document.getElementById('pw').value;
    const h = await _hash(pw);
    if (h === SECRET_HASH) {
      localStorage.setItem(UNLOCK_KEY, JSON.stringify({ ts: Date.now() }));
      location.reload();
    } else {
      document.getElementById('err').textContent = 'Wrong password.';
      document.getElementById('pw').value = '';
      document.getElementById('pw').focus();
    }
  });
  document.getElementById('pw').focus();
}

if (!_isUnlocked()) {
  // Run the lock UI as soon as DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _lockUI);
  } else {
    _lockUI();
  }
}
