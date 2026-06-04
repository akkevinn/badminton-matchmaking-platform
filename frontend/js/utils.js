export function toast(msg, type = "info") {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = msg;
  document.getElementById("toast-container").appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

export function modal(html, onConfirm, confirmLabel = "Confirm", confirmClass = "btn-primary") {
  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.innerHTML = `
    <div class="modal">
      ${html}
      <div class="modal-actions">
        <button class="btn btn-ghost" id="modal-cancel">Cancel</button>
        <button class="btn ${confirmClass}" id="modal-confirm">${confirmLabel}</button>
      </div>
    </div>`;
  document.body.appendChild(overlay);
  overlay.querySelector("#modal-cancel").onclick = () => overlay.remove();
  overlay.querySelector("#modal-confirm").onclick = () => { onConfirm(overlay); overlay.remove(); };
  return overlay;
}

export function skillColor(s) {
  if (s >= 8) return "#ef4444";
  if (s >= 6) return "#f97316";
  if (s >= 4) return "#facc15";
  return "#22c55e";
}

export function skillLabel(s) {
  if (s >= 8) return "Expert";
  if (s >= 6) return "Advanced";
  if (s >= 4) return "Intermediate";
  return "Beginner";
}

export function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString();
}
