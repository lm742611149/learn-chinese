/* Multi-provider sign-in (Google / Facebook / email) + cloud sync of
 * wordbook & progress via Firebase. Loaded only when site.json has "firebase".
 * users/{uid} = { words:[{z,p,e}], done:{slug:"YYYY-MM-DD"}, plan, updated } */
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import {
  getAuth, GoogleAuthProvider, FacebookAuthProvider,
  signInWithPopup, signInWithRedirect, onAuthStateChanged, signOut,
  signInWithEmailAndPassword, createUserWithEmailAndPassword,
  sendPasswordResetEmail
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
import {
  getFirestore, doc, getDoc, setDoc
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";

const cfg = window.RCD_FB;
const PROVIDERS = window.RCD_PROVIDERS || ["google"];

if (cfg && cfg.apiKey) {
  const app = initializeApp(cfg);
  const auth = getAuth(app);
  const db = getFirestore(app);
  const btn = document.getElementById("t-auth");
  let user = null;
  let pushTimer = null;

  /* ---------- local stores ---------- */
  const localWords = () => { try { return JSON.parse(localStorage.getItem("rcd-words")) || []; } catch (e) { return []; } };
  const localProg = () => { try { return JSON.parse(localStorage.getItem("rcd-progress")) || { done: {} }; } catch (e) { return { done: {} }; } };

  /* ---------- sync ---------- */
  function mergedState(cloud) {
    const words = localWords();
    const seen = new Set(words.map((w) => w.z));
    (cloud.words || []).forEach((w) => { if (!seen.has(w.z)) { words.push(w); seen.add(w.z); } });
    const done = Object.assign({}, cloud.done || {}, localProg().done || {});
    return { words, done };
  }
  async function pushState() {
    if (!user) return;
    try {
      await setDoc(doc(db, "users", user.uid),
        { words: localWords(), done: localProg().done || {},
          updated: new Date().toISOString() }, { merge: true });
    } catch (e) { console.warn("sync push failed", e); }
  }
  document.addEventListener("rcd-changed", () => {
    if (!user) return;
    clearTimeout(pushTimer);
    pushTimer = setTimeout(pushState, 2000);
  });
  async function pullAndMerge() {
    try {
      const snap = await getDoc(doc(db, "users", user.uid));
      const cloud = snap.exists() ? snap.data() : {};
      const m = mergedState(cloud);
      localStorage.setItem("rcd-words", JSON.stringify(m.words));
      localStorage.setItem("rcd-progress", JSON.stringify({ done: m.done }));
      await setDoc(doc(db, "users", user.uid),
        { words: m.words, done: m.done, plan: cloud.plan || "free",
          updated: new Date().toISOString() }, { merge: true });
    } catch (e) { console.warn("sync pull failed", e); }
  }

  /* ---------- sign-in modal ---------- */
  const FB_ICON = '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M13.4 21v-8.2h2.8l.4-3.2h-3.2V7.5c0-.9.3-1.6 1.7-1.6h1.7V3.1c-.3 0-1.3-.1-2.5-.1-2.5 0-4.2 1.5-4.2 4.3v2.3H7.3v3.2h2.8V21h3.3z"/></svg>';
  const G_ICON = '<svg viewBox="0 0 24 24" width="16" height="16"><path fill="#4285F4" d="M22.6 12.3c0-.8-.1-1.6-.2-2.3H12v4.4h5.9a5 5 0 0 1-2.2 3.3v2.8h3.6c2.1-2 3.3-4.9 3.3-8.2z"/><path fill="#34A853" d="M12 23c3 0 5.5-1 7.3-2.7l-3.6-2.8c-1 .7-2.3 1.1-3.7 1.1-2.9 0-5.3-1.9-6.2-4.6H2.1v2.9A11 11 0 0 0 12 23z"/><path fill="#FBBC05" d="M5.8 14a6.6 6.6 0 0 1 0-4.2V6.9H2.1a11 11 0 0 0 0 10l3.7-2.9z"/><path fill="#EA4335" d="M12 5.4c1.6 0 3.1.6 4.2 1.7L19.4 4A11 11 0 0 0 2.1 6.9L5.8 9.8c.9-2.7 3.3-4.4 6.2-4.4z"/></svg>';

  function errText(e) {
    const m = {
      "auth/account-exists-with-different-credential":
        "This email is already registered with another sign-in method. Try that method instead.",
      "auth/invalid-credential": "Wrong email or password.",
      "auth/wrong-password": "Wrong email or password.",
      "auth/user-not-found": "No account with this email — tap “Create account”.",
      "auth/email-already-in-use": "This email is already registered — sign in instead.",
      "auth/weak-password": "Password needs at least 6 characters.",
      "auth/invalid-email": "That doesn't look like a valid email.",
    };
    return (e && m[e.code]) || (e && e.message) || String(e);
  }

  function buildModal() {
    const wrap = document.createElement("div");
    wrap.id = "auth-modal";
    let inner = '<div class="am-box"><button class="am-close" id="am-close">✕</button>' +
      '<h3>Sign in to <span>' + document.title.split("—")[0].split("|")[0].trim() + "</span></h3>" +
      '<p class="am-sub">Keep your wordbook & streak on every device.</p>';
    if (PROVIDERS.includes("google"))
      inner += '<button class="am-btn am-g" id="am-google">' + G_ICON + " Continue with Google</button>";
    if (PROVIDERS.includes("facebook"))
      inner += '<button class="am-btn am-f" id="am-fb">' + FB_ICON + " Continue with Facebook</button>";
    if (PROVIDERS.includes("email")) {
      inner += '<div class="am-div"><span>or with email</span></div>' +
        '<input class="am-in" id="am-email" type="email" placeholder="Email" autocomplete="email">' +
        '<input class="am-in" id="am-pass" type="password" placeholder="Password (6+ characters)" autocomplete="current-password">' +
        '<div class="am-err" id="am-err" hidden></div>' +
        '<button class="am-btn am-e" id="am-signin">Sign in</button>' +
        '<div class="am-links"><button id="am-create">Create account</button>' +
        '<button id="am-forgot">Forgot password?</button></div>';
    }
    inner += "</div>";
    wrap.innerHTML = inner;
    document.body.appendChild(wrap);

    const close = () => wrap.classList.remove("show");
    wrap.addEventListener("click", (e) => { if (e.target === wrap) close(); });
    document.getElementById("am-close").addEventListener("click", close);

    async function oauth(provider) {
      try { await signInWithPopup(auth, provider); close(); }
      catch (e) {
        if (e.code === "auth/popup-blocked" ||
            e.code === "auth/operation-not-supported-in-this-environment") {
          signInWithRedirect(auth, provider);
        } else if (e.code !== "auth/popup-closed-by-user" &&
                   e.code !== "auth/cancelled-popup-request") {
          showErr(e);
        }
      }
    }
    const g = document.getElementById("am-google");
    if (g) g.addEventListener("click", () => oauth(new GoogleAuthProvider()));
    const f = document.getElementById("am-fb");
    if (f) f.addEventListener("click", () => oauth(new FacebookAuthProvider()));

    function showErr(e) {
      const el = document.getElementById("am-err");
      if (el) { el.hidden = false; el.textContent = errText(e); }
    }
    const em = () => (document.getElementById("am-email") || {}).value || "";
    const pw = () => (document.getElementById("am-pass") || {}).value || "";
    const si = document.getElementById("am-signin");
    if (si) si.addEventListener("click", async () => {
      try { await signInWithEmailAndPassword(auth, em().trim(), pw()); close(); }
      catch (e) { showErr(e); }
    });
    const cr = document.getElementById("am-create");
    if (cr) cr.addEventListener("click", async () => {
      try { await createUserWithEmailAndPassword(auth, em().trim(), pw()); close(); }
      catch (e) { showErr(e); }
    });
    const fg = document.getElementById("am-forgot");
    if (fg) fg.addEventListener("click", async () => {
      if (!em().trim()) { showErr({ message: "Enter your email above first." }); return; }
      try {
        await sendPasswordResetEmail(auth, em().trim());
        showErr({ message: "Reset link sent — check your inbox." });
      } catch (e) { showErr(e); }
    });
    return wrap;
  }
  let modal = null;

  function openSignin() {
    if (!modal) modal = buildModal();
    modal.classList.add("show");
  }

  /* ---------- header button ---------- */
  function renderBtn() {
    if (!btn) return;
    btn.hidden = false;
    btn.classList.toggle("signed", !!user);
    if (user) {
      const label = (user.displayName || user.email || "?").trim();
      btn.textContent = "👤 " + label.split(" ")[0].split("@")[0];
      btn.title = "Signed in as " + label + " — click to sign out";
    } else {
      btn.textContent = "Sign in";
      btn.title = "Sign in to sync your wordbook and streak";
    }
  }
  if (btn) {
    btn.addEventListener("click", async () => {
      if (user) {
        if (confirm("Sign out? Your data stays saved in the cloud.")) await signOut(auth);
        return;
      }
      openSignin();
    });
  }

  /* ---------- members-only gate (progress / wordbook pages) ---------- */
  const gateBtn = document.getElementById("gate-signin");
  if (gateBtn) gateBtn.addEventListener("click", openSignin);
  function applyGate() {
    const panel = document.getElementById("gate-panel");
    const content = document.getElementById("gated");
    if (!panel || !content) return;
    panel.hidden = !!user;
    content.hidden = !user;
  }

  let firstAuth = true;
  onAuthStateChanged(auth, async (u) => {
    user = u;
    renderBtn();
    applyGate();
    if (u) {
      await pullAndMerge();
      if (firstAuth && sessionStorage.getItem("rcd-just-signed") !== u.uid) {
        sessionStorage.setItem("rcd-just-signed", u.uid);
        location.reload();
      }
    }
    firstAuth = false;
  });
}
