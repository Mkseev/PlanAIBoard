/* Traduzioni: legge /lingue e /lingua?c=xx. Chi manca in una lingua ricade sull'italiano (it.json).
   Per aggiungere una lingua basta un file lingue/xx.json con "_nome" e le stesse chiavi di it.json. */
(function () {
  let base = {}, dic = {}, cod = "it";
  const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  // testo con **grassetto** e `codice`, tutto il resto è scritto come testo semplice (sicuro anche con file tradotti a mano)
  const ric = s => esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/`(.+?)`/g, "<code>$1</code>");
  const t = k => (k in dic ? dic[k] : k in base ? base[k] : k);
  async function init(pref) {
    const disp = await (await fetch("/lingue")).json(), ha = c => disp.some(x => x.codice === c);
    cod = pref && pref !== "auto" && ha(pref) ? pref : null;
    for (const n of cod ? [] : navigator.languages || [navigator.language]) { const c = String(n).slice(0, 2).toLowerCase(); if (ha(c)) { cod = c; break; } }
    cod = cod || (ha("en") ? "en" : "it");
    base = await (await fetch("/lingua?c=it")).json();
    dic = cod === "it" ? base : await (await fetch("/lingua?c=" + cod)).json();
    document.documentElement.lang = cod;
    return { codice: cod, disponibili: disp };
  }
  function applica(r) {
    r = r || document;
    r.querySelectorAll("[data-tr]").forEach(e => { e.textContent = t(e.dataset.tr); });
    r.querySelectorAll("[data-tr-r]").forEach(e => { e.innerHTML = ric(t(e.dataset.trR)); });
    r.querySelectorAll("[data-tr-ph]").forEach(e => { e.placeholder = t(e.dataset.trPh); });
    r.querySelectorAll("[data-tr-title]").forEach(e => { e.title = t(e.dataset.trTitle); });
  }
  window.I18N = { init, applica, t, ric, codice: () => cod };
})();
