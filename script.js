// ===== コピー用テキスト（<pre id="..."> に流し込む） =====
const GUIDE_URL = "https://ryoya9595.github.io/vrew-telop-fix-manual/files/agent-guide.md";

const INSTALL_PROMPT = `Vrewで作った字幕の誤字を、AIが直してPremiere Proに戻せる仕組みを、私のPCに一緒に作ってください。

【手順書】
${GUIDE_URL}

【進め方】
1. 手順書をダウンロードして、全文を読んでください（WindowsはPowerShellのInvoke-WebRequest、Macはcurl）。
   ※ 要約して読むツールではなく、ファイルの原文を読んでください。
2. 手順書のフェーズA（今のやり方を聞く）→ B（置き場を作る）→ C（いつもの手順を保存）→ D（実際の字幕1本で確認）の順に進めてください。
3. 各フェーズの終わりに、何をやったかを短く報告してください。

【守ってほしいこと】
- インストールや設定を変える前は、何をするか説明して私に確認してください。
- 元の字幕ファイルは上書きしないでください。
- タイムコードは1文字も変えないでください。
- .env など認証情報のファイルは読まないでください。`;

const USE_PROMPT = `この字幕を直して：D:\\動画\\〇〇社_0923.srt
クライアント：〇〇社
台本：D:\\動画\\〇〇社_0923_台本.txt（無ければこの行は消す）`;

const TUNE_PROMPT = `今回わたしが直した言葉を、用語集に足しておいて。
（例：「〇〇」は「△△」と書く／数字は半角／このクライアントは「インスタ」ではなく「Instagram」）`;

const TEXTS = {
  installPrompt: INSTALL_PROMPT,
  usePrompt: USE_PROMPT,
  tunePrompt: TUNE_PROMPT,
};

// 各 <pre> に本文を流し込む
Object.entries(TEXTS).forEach(([id, text]) => {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
});

// ===== コピー処理 =====
async function copyText(text, target) {
  let ok = false;
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
      ok = true;
    }
  } catch { ok = false; }
  if (!ok && target) {
    const range = document.createRange();
    range.selectNodeContents(target);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
    try { ok = document.execCommand("copy"); } catch { ok = false; }
    sel.removeAllRanges();
  }
  return ok;
}

function showToast(msg) {
  let toast = document.getElementById("toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toast";
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 1800);
}

document.querySelectorAll(".copy-btn").forEach((button) => {
  button.addEventListener("click", async () => {
    const targetId = button.dataset.target;
    const target = document.getElementById(targetId);
    const text = TEXTS[targetId] || (target ? target.textContent : "");
    const ok = await copyText(text, target);
    const original = button.textContent;
    button.textContent = ok ? "コピーしました" : "手動でコピー";
    button.classList.toggle("done", ok);
    showToast(ok ? "📋 コピーしました" : "コピーできませんでした");
    setTimeout(() => {
      button.textContent = original;
      button.classList.remove("done");
    }, 2000);
  });
});

// ===== ナビ現在地ハイライト =====
const navLinks = Array.from(document.querySelectorAll(".topnav a[href^='#']"));
const sections = navLinks
  .map((a) => document.querySelector(a.getAttribute("href")))
  .filter(Boolean);
if ("IntersectionObserver" in window && sections.length) {
  const obs = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) {
        const id = "#" + e.target.id;
        navLinks.forEach((a) => a.classList.toggle("active", a.getAttribute("href") === id));
      }
    });
  }, { rootMargin: "-45% 0px -50% 0px" });
  sections.forEach((s) => obs.observe(s));
}
