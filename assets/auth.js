/* Google sign-in + cloud sync of wordbook & progress via Firebase.
 * Loaded only when site.json contains a "firebase" config.
 * Data model: users/{uid} = { words: [{z,p,e}], done: {slug: "YYYY-MM-DD"},
 *                             plan: "free", updated: ISO }
 * Merge strategy on login: union of local + cloud, then write back both ways.
 * Every local change (reader.js dispatches "rcd-changed") uploads debounced. */
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import {
  getAuth, GoogleAuthProvider, signInWithPopup, signInWithRedirect,
  onAuthStateChanged, signOut
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
import {
  getFirestore, doc, getDoc, setDoc
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";

const cfg = window.RCD_FB;
if (cfg && cfg.apiKey) {
  const app = initializeApp(cfg);
  const auth = getAuth(app);
  const db = getFirestore(app);
  const btn = document.getElementById("t-auth");

  const localWords = () => { try { return JSON.parse(localStorage.getItem("rcd-words")) || []; } catch (e) { return []; } };
  const localProg = () => { try { return JSON.parse(localStorage.getItem("rcd-progress")) || { done: {} }; } catch (e) { return { done: {} }; } };

  function mergedState(cloud) {
    const words = localWords();
    const seen = new Set(words.map((w) => w.z));
    (cloud.words || []).forEach((w) => { if (!seen.has(w.z)) { words.push(w); seen.add(w.z); } });
    const done = Object.assign({}, cloud.done || {}, localProg().done || {});
    return { words, done };
  }

  let user = null;
  let pushTimer = null;

  async function pushState() {
    if (!user) return;
    const state = { words: localWords(), done: localProg().done || {},
                    updated: new Date().toISOString() };
    try {
      await setDoc(doc(db, "users", user.uid), state, { merge: true });
    } catch (e) { console.warn("sync push failed", e); }
  }
  function schedulePush() {
    if (!user) return;
    clearTimeout(pushTimer);
    pushTimer = setTimeout(pushState, 2000);
  }
  document.addEventListener("rcd-changed", schedulePush);

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

  function renderBtn() {
    if (!btn) return;
    btn.hidden = false;
    if (user) {
      const label = (user.displayName || user.email || "?").trim();
      btn.textContent = "👤 " + label.split(" ")[0];
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
      const provider = new GoogleAuthProvider();
      try { await signInWithPopup(auth, provider); }
      catch (e) {
        if (e && (e.code === "auth/popup-blocked" || e.code === "auth/operation-not-supported-in-this-environment")) {
          signInWithRedirect(auth, provider);
        } else if (e && e.code !== "auth/popup-closed-by-user") {
          alert("Sign-in failed: " + (e.message || e));
        }
      }
    });
  }

  let firstAuth = true;
  onAuthStateChanged(auth, async (u) => {
    user = u;
    renderBtn();
    if (u) {
      await pullAndMerge();
      // refresh page once after first login so streak/wordbook show merged data
      if (firstAuth && sessionStorage.getItem("rcd-just-signed") !== u.uid) {
        sessionStorage.setItem("rcd-just-signed", u.uid);
        location.reload();
      }
    }
    firstAuth = false;
  });
}
