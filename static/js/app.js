// @ts-nocheck

// ---------- Helpers ----------
async function getJSON(url) {
  const res = await fetch(url);
  return res.json();
}

async function postForm(url, formData) {
  const res = await fetch(url, { method: "POST", body: formData });
  return res.json();
}

async function postJSON(url, data) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

function toCSV(entries) {
  const headers = ["id", "created_at", "top_emotion", "top_score", "scores_json"];
  const rows = (entries || []).map((e) => [
    e.id,
    e.created_at,
    e.top_emotion,
    e.top_score,
    JSON.stringify(e.scores),
  ]);
  return [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
}

function download(filename, text) {
  const blob = new Blob([text], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// ---------- Emoji mapping (intensity-tiered) ----------
function emojiFor(label, score) {
  const L = String(label || "").toLowerCase();
  const s = Number(score) || 0;
  const low = s < 0.33;
  const mid = s < 0.66; // else high

  if (L.includes("joy") || L.includes("happy") || L.includes("happiness")) {
    if (low) return "🙂"; if (mid) return "😀"; return "🤣";
  }
  if (L.includes("sad") || L.includes("sadness")) {
    if (low) return "😕"; if (mid) return "😢"; return "😭";
  }
  if (L.includes("anger") || L.includes("angry") || L.includes("rage")) {
    if (low) return "😠"; if (mid) return "😡"; return "🤬";
  }
  if (L.includes("fear") || L.includes("anxious") || L.includes("scared") || L.includes("worried")) {
    if (low) return "😟"; if (mid) return "😨"; return "😱";
  }
  if (L.includes("love") || L.includes("grateful") || L.includes("thankful")) {
    if (low) return "😊"; if (mid) return "🥰"; return "😍";
  }
  if (L.includes("surprise")) {
    if (low) return "🙂"; if (mid) return "😮"; return "😲";
  }
  if (L.includes("neutral")) return "😐";
  return "❓";
}

function fontSizeFromScore(score) {
  const min = 14, max = 36;
  const s = Math.max(0, Math.min(1, Number(score) || 0));
  return Math.round(min + (max - min) * s);
}

// Draw emojis at data points
const EmojiPointsPlugin = {
  id: "emojiPoints",
  afterDatasetsDraw(chart) {
    const { ctx } = chart;
    const ds = chart.data.datasets[0];
    if (!ds || !ds._emojis || !ds._scores) return;
    const meta = chart.getDatasetMeta(0);

    ctx.save();
    for (let i = 0; i < meta.data.length; i++) {
      const pt = meta.data[i];
      if (!pt) continue;
      const emoji = ds._emojis[i] || "❓";
      const size = fontSizeFromScore(ds._scores[i]);
      ctx.font = `${size}px system-ui, Apple Color Emoji, Segoe UI Emoji, Noto Color Emoji, emoji`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(emoji, pt.x, pt.y);
    }
    ctx.restore();
  }
};

// ---------- UI state ----------
let chart;

async function refreshStatus() {
  const s = await getJSON("/user/status");
  const banner = document.getElementById("proBanner");
  if (banner) banner.style.display = s.is_pro ? "none" : "flex";
  return s;
}

// ---------- Chart with emojis ----------
async function refreshChart() {
  const data = await getJSON("/data");
  const entries = data.entries || [];

  const labels = entries.map((e) => new Date(e.created_at).toLocaleString());
  const values = entries.map((e) => e.top_score);
  const emojis = entries.map((e) => emojiFor(e.top_emotion, e.top_score));

  const canvas = document.getElementById("moodTrend");
  if (!canvas) return entries;
  const ctx = canvas.getContext("2d");

  if (chart) chart.destroy();
  chart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Top Emotion Score Over Time",
        data: values,
        tension: 0.35,
        pointRadius: 0,         // hide default dots; we draw emojis instead
        pointHoverRadius: 0,
        _emojis: emojis,        // expose to plugin
        _scores: values
      }]
    },
    options: {
      responsive: true,
      animation: { duration: 300 },
      scales: {
        y: { min: 0, max: 1, title: { display: true, text: "Intensity" } },
        x: { ticks: { maxRotation: 30, minRotation: 0 } }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const score = ctx.parsed.y;
              const emoji = emojis[ctx.dataIndex] || "❓";
              return `${emoji} ${(score * 100).toFixed(1)}%`;
            },
            title: (items) => items?.[0]?.label || ""
          }
        }
      }
    },
    plugins: [EmojiPointsPlugin]
  });

  if (entries.length) {
    const last = entries[entries.length - 1];
    const lastEl = document.getElementById("lastResult");
    if (lastEl) {
      const emoji = emojiFor(last.top_emotion, last.top_score);
      lastEl.textContent = `Last: ${emoji} ${last.top_emotion} (${(last.top_score * 100).toFixed(1)}%)`;
    }
  }

  return entries;
}

// ---------- Attach handlers ----------
function attachHandlers() {
  const entryForm = document.getElementById("entryForm");
  if (entryForm) {
    entryForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const box = document.getElementById("entryText");
      const text = (box?.value || "").trim();
      if (!text) return;
      const fd = new FormData();
      fd.append("text", text);
      try {
        const res = await postForm("/entry", fd);
        if (res.ok) {
          box.value = "";
          await refreshChart();
        } else {
          alert(res.error || "Failed to save entry");
        }
      } catch (err) {
        console.error(err);
        alert("Network error while saving entry.");
      }
    });
  }

  const saveEmailBtn = document.getElementById("saveEmail");
  if (saveEmailBtn) {
    saveEmailBtn.addEventListener("click", async () => {
      const emailEl = document.getElementById("email");
      const statusEl = document.getElementById("emailStatus");
      const email = (emailEl?.value || "").trim();
      if (!email) {
        if (statusEl) statusEl.textContent = "Please enter your email";
        return;
      }
      try {
        const fd = new FormData();
        fd.append("email", email);
        const res = await postForm("/user/email", fd);
        if (statusEl) {
          statusEl.textContent = res.ok ? `Saved: ${res.email}` : (res.error || "Could not save email");
        }
      } catch (err) {
        console.error(err);
        if (statusEl) statusEl.textContent = "Network error trying to save email";
      }
    });
  }

  const goProBtn = document.getElementById("goPro");
  if (goProBtn) {
    goProBtn.addEventListener("click", async () => {
      const statusEl = document.getElementById("emailStatus");
      const email = (document.getElementById("email")?.value || "").trim();

      if (typeof FlutterwaveCheckout !== "function") {
        alert("Payment library did not load. Check your internet and that the v3.js script tag is present.");
        console.error("FlutterwaveCheckout is not defined");
        return;
      }
      if (typeof FLW_PUBLIC_KEY === "undefined" || !FLW_PUBLIC_KEY?.length) {
        alert("Flutterwave public key is missing. Check your .env and index route variables.");
        console.error("FLW_PUBLIC_KEY missing");
        return;
      }
      if (!email) {
        if (statusEl) statusEl.textContent = "Please enter your email first, then click Save.";
        return;
      }

      // Persist email
      try {
        const fd = new FormData();
        fd.append("email", email);
        await postForm("/user/email", fd);
      } catch (e) {
        console.error(e);
        alert("Could not save email before payment start.");
        return;
      }

      // Get tx_ref
      let t;
      try {
        t = await getJSON("/subscribe/txref");
      } catch (e) {
        console.error(e);
        alert("Could not start payment (no tx_ref). Check server logs.");
        return;
      }
      if (!t?.ok || !t?.tx_ref) {
        alert("Could not start payment (no tx_ref).");
        return;
      }

      FlutterwaveCheckout({
        public_key: FLW_PUBLIC_KEY,
        tx_ref: t.tx_ref,
        amount: SUB_AMOUNT,
        currency: SUB_CURRENCY,
        payment_options: "card, banktransfer, ussd",
        customer: { email },
        customizations: {
          title: "Mood Journal PRO",
          description: "1-year access to PRO features",
        },
        callback: async function (payment) {
          try {
            const verify = await fetch("/payment/verify", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                transaction_id: payment.transaction_id,
                tx_ref: t.tx_ref,
              }),
            });
            const j = await verify.json();
            if (verify.ok && j.ok) {
              alert("Payment verified! PRO activated.");
              await refreshStatus();
            } else {
              alert("Verification failed. If you were charged, try refreshing. Check server logs.");
              console.error(j);
            }
          } catch (e) {
            console.error(e);
            alert("Network error while verifying payment.");
          }
        },
        onclose: function () {},
      });
    });
  }

  const exportBtn = document.getElementById("exportCsv");
  if (exportBtn) {
    exportBtn.addEventListener("click", async () => {
      const s = await refreshStatus();
      if (!s.is_pro) {
        alert("CSV export is a PRO feature.");
        return;
      }
      const data = await getJSON("/data");
      const csv = toCSV(data.entries || []);
      download("mood_journal.csv", csv);
    });
  }
}

// ---------- Init ----------
async function init() {
  await refreshStatus();
  await refreshChart();
  attachHandlers();
}

window.addEventListener("DOMContentLoaded", () => {
  init().catch((e) => console.error("Init failed:", e));
});
