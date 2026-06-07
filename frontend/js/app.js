import { api } from "./api.js";
import { toast, modal, skillColor, skillLabel, fmtDate } from "./utils.js";

let state = {
  view: "tournaments",
  tournaments: [],
  players: [],
  currentTournament: null,
  tournamentPlayers: [],
  matches: [],
  leaderboard: [],
  leaderboardMode: "detailed", // "detailed" | "simple"
};

document.addEventListener("DOMContentLoaded", () => {
  setupNav();
  setupTheme();
  loadView("tournaments");
});

function setupTheme() {
  const btn = document.getElementById("theme-toggle");
  const apply = (theme) => {
    if (theme === "dark") {
      document.documentElement.setAttribute("data-theme", "dark");
      btn.textContent = "🌙";
    } else {
      document.documentElement.removeAttribute("data-theme");
      btn.textContent = "☀️";
    }
  };
  // Sync icon with saved preference
  apply(localStorage.getItem("theme") || "light");
  btn.addEventListener("click", () => {
    const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
    localStorage.setItem("theme", next);
    apply(next);
  });
}

function setupNav() {
  document.getElementById("nav-tournaments").addEventListener("click", () => loadView("tournaments"));
  document.getElementById("nav-players").addEventListener("click", () => loadView("players"));
  document.getElementById("brand-link").addEventListener("click", () => loadView("tournaments"));
}

async function loadView(view, tid) {
  state.view = view;
  document.querySelectorAll("nav button").forEach(b => b.classList.remove("active"));
  document.getElementById(`nav-${view === "tournament" ? "tournaments" : view}`)?.classList.add("active");

  const main = document.getElementById("main-content");

  if (view === "tournaments") {
    state.tournaments = await api.getTournaments();
    renderTournamentList(main);
  } else if (view === "tournament") {
    state.currentTournament = state.tournaments.find(t => t.id === tid)
      || await api.getTournaments().then(ts => { state.tournaments = ts; return ts.find(t => t.id === tid); });
    await refreshTournamentView(main);
  } else if (view === "players") {
    state.players = await api.getPlayers();
    renderPlayersView(main);
  }
}

async function refreshTournamentView(main) {
  if (!main) main = document.getElementById("main-content");
  const tid = state.currentTournament.id;
  [state.tournamentPlayers, state.matches, state.leaderboard] = await Promise.all([
    api.getTournamentPlayers(tid),
    api.getMatches(tid),
    api.getLeaderboard(tid),
  ]);
  renderTournamentView(main);
}

// ─── Tournament List ──────────────────────────────────────

function renderTournamentList(main) {
  main.innerHTML = `
    <div class="section-header">
      <h2>Tournaments</h2>
      <button class="btn btn-primary" id="btn-new-tournament">+ New Tournament</button>
    </div>
    ${state.tournaments.length === 0 ? `
      <div class="card">
        <div class="empty">
          <div class="empty-icon">🏸</div>
          No tournaments yet. Create one to get started.
        </div>
      </div>` : state.tournaments.map(t => `
      <div class="t-card" data-tid="${t.id}">
        <div class="t-card-icon">${t.status === "finished" ? "🏆" : "🏸"}</div>
        <div class="t-card-body">
          <div class="t-card-name">${t.name}</div>
          <div class="t-card-meta">
            <span>${t.num_courts} court${t.num_courts > 1 ? "s" : ""}</span>
            <span>${t.max_points} pts${t.deuce_enabled ? " · deuce" : ""}</span>
            <span>${fmtDate(t.created_at)}</span>
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:6px;flex-shrink:0" onclick="event.stopPropagation()">
          <span class="chip chip-${t.status === "finished" ? "finished-t" : "active-t"}">
            ${t.status === "finished" ? "Finished" : "Active"}
          </span>
          <button class="btn btn-ghost btn-xs t-rename-btn" data-tid="${t.id}" data-name="${t.name}" title="Rename">✏️</button>
          <button class="btn btn-ghost btn-xs t-delete-btn" data-tid="${t.id}" data-name="${t.name}" style="color:var(--red)" title="Delete">🗑</button>
        </div>
      </div>`).join("")}`;

  document.getElementById("btn-new-tournament").onclick = () => openNewTournamentModal();
  document.querySelectorAll(".t-card[data-tid]").forEach(el => {
    el.addEventListener("click", () => loadView("tournament", parseInt(el.dataset.tid)));
  });
  document.querySelectorAll(".t-rename-btn").forEach(btn => {
    btn.addEventListener("click", () => openRenameTournamentModal(parseInt(btn.dataset.tid), btn.dataset.name));
  });
  document.querySelectorAll(".t-delete-btn").forEach(btn => {
    btn.addEventListener("click", () => confirmDeleteTournament(parseInt(btn.dataset.tid), btn.dataset.name));
  });
}

function openNewTournamentModal() {
  const html = `
    <h2>New Tournament</h2>
    <div class="form-group" style="margin-bottom:16px">
      <label>Tournament Name</label>
      <input id="t-name" type="text" placeholder="e.g. Saturday Session" />
    </div>
    <div class="form-row" style="margin-bottom:16px">
      <div class="form-group">
        <label>Courts</label>
        <select id="t-courts">
          <option value="1">1 Court</option>
          <option value="2" selected>2 Courts</option>
          <option value="3">3 Courts</option>
          <option value="4">4 Courts</option>
        </select>
      </div>
      <div class="form-group">
        <label>Max Points</label>
        <input id="t-pts" type="number" value="21" min="11" max="99" />
      </div>
    </div>
    <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:.85rem;color:var(--text2)">
      <input id="t-deuce" type="checkbox" checked />
      Enable deuce (win by 2, cap at max+9)
    </label>`;

  modal(html, async () => {
    const name = document.getElementById("t-name").value.trim();
    if (!name) return toast("Name is required", "error");
    try {
      const t = await api.createTournament({
        name,
        num_courts: parseInt(document.getElementById("t-courts").value),
        max_points: parseInt(document.getElementById("t-pts").value),
        deuce_enabled: document.getElementById("t-deuce").checked,
      });
      state.tournaments.unshift(t);
      toast("Tournament created", "success");
      loadView("tournament", t.id);
    } catch (e) { toast(e.message, "error"); }
  }, "Create Tournament", "btn-success");
}

// ─── Tournament View ──────────────────────────────────────

function renderTournamentView(main) {
  const t = state.currentTournament;
  const active = state.tournamentPlayers.filter(p => p.status === "active");
  const rounds = [...new Set(state.matches.map(m => m.round_number))].sort((a,b) => b-a);
  const latestRound = rounds[0];
  const currentMatches = latestRound ? state.matches.filter(m => m.round_number === latestRound) : [];
  const hasOpenMatches = currentMatches.some(m => m.status !== "finished");

  main.innerHTML = `
    <div class="t-view-header" style="display:flex;align-items:center;gap:10px;margin-bottom:20px;flex-wrap:wrap">
      <div style="display:flex;align-items:center;gap:8px;flex:1;min-width:0">
        <button class="btn btn-ghost btn-sm" id="btn-back">←</button>
        <span style="font-size:1rem;font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${t.name}</span>
        <span class="chip chip-${t.status === "finished" ? "finished-t" : "active-t"}" style="flex-shrink:0">
          ${t.status === "finished" ? "Done" : "Active"}
        </span>
      </div>
      <div class="t-view-actions" style="display:flex;gap:6px;flex-wrap:wrap;flex-shrink:0">
        <button class="btn btn-ghost btn-sm" id="btn-rename-tournament">✏️</button>
        ${t.status !== "finished" ? `<button class="btn btn-ghost btn-sm" id="btn-finish-tournament">🏁 Finish</button>` : ""}
        <button class="btn btn-ghost btn-sm" id="btn-show-story">📸 Story</button>
      </div>
    </div>

    <div class="t-info-grid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin-bottom:16px">

      <div class="card">
        <div class="section-header">
          <h2>Players <span style="color:var(--text3);font-weight:400;font-size:.85rem">${active.length} active</span></h2>
          ${t.status !== "finished" ? `<button class="btn btn-ghost btn-sm" id="btn-add-player">+ Add Player</button>` : ""}
        </div>
        <div class="table-wrap">
          <table class="player-table">
            <thead><tr><th>Name</th><th>Skill</th><th>Status</th><th>GP</th>${t.status !== "finished" ? "<th></th>" : ""}</tr></thead>
            <tbody>
              ${state.tournamentPlayers.length === 0
                ? `<tr><td colspan="5"><div class="empty" style="padding:16px">No players yet</div></td></tr>`
                : state.tournamentPlayers.map(tp => {
                  const games = countGames(tp.player_id);
                  return `<tr>
                    <td style="font-weight:600">${tp.player_name}</td>
                    <td><span class="skill-badge" style="color:${skillColor(tp.skill)}">${tp.skill}</span></td>
                    <td><span class="chip chip-${tp.status}">${tp.status}</span></td>
                    <td style="color:var(--text2)">${games}</td>
                    ${t.status !== "finished" ? `<td>
                      <div style="display:flex;gap:4px">
                        ${tp.status === "active" ? `<button class="btn btn-ghost btn-xs" onclick="setPlayerStatus(${tp.id},'away')">Away</button>` : ""}
                        ${tp.status === "away"   ? `<button class="btn btn-success btn-xs" onclick="setPlayerStatus(${tp.id},'active')">Back</button>` : ""}
                        ${tp.status !== "left"   ? `<button class="btn btn-ghost btn-xs" style="color:var(--red)" onclick="setPlayerStatus(${tp.id},'left')">Leave</button>` : ""}
                      </div>
                    </td>` : ""}
                  </tr>`;
                }).join("")}
            </tbody>
          </table>
        </div>
      </div>

      <div class="card">
        <div class="card-title">Tournament Info</div>
        <div class="stat-row"><span class="stat-label">Courts</span><span class="stat-value">${t.num_courts}</span></div>
        <div class="stat-row"><span class="stat-label">Max Points</span><span class="stat-value">${t.max_points}${t.deuce_enabled ? " (deuce)" : ""}</span></div>
        <div class="stat-row"><span class="stat-label">Rounds</span><span class="stat-value">${rounds.length}</span></div>
        <div class="stat-row"><span class="stat-label">Matches finished</span><span class="stat-value">${state.matches.filter(m=>m.status==="finished").length} / ${state.matches.length}</span></div>
        <div class="stat-row"><span class="stat-label">Active players</span><span class="stat-value">${active.length}</span></div>
        <div class="stat-row" style="margin-top:12px;border-top:1px solid var(--border);padding-top:12px">
          <span class="stat-label" style="font-size:.75rem">Scoring: score earned per match (0–30)</span>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="section-header">
        <h2>${latestRound ? `Round ${latestRound}` : "Matches"}</h2>
        <div style="display:flex;gap:8px;align-items:center">
          ${latestRound ? `<span style="color:var(--text3);font-size:.8rem">${currentMatches.filter(m=>m.status==="finished").length}/${currentMatches.length} finished</span>` : ""}
          ${t.status !== "finished" && !hasOpenMatches
            ? `<button class="btn btn-primary btn-sm" id="btn-gen-matches">⚡ Next Round</button>`
            : ""}
        </div>
      </div>
      ${currentMatches.length === 0
        ? `<div class="empty"><div class="empty-icon">🎯</div>Click "Next Round" to generate matches.</div>`
        : `<div class="courts-grid" id="courts-grid">${currentMatches.map(m => renderCourtCard(m, t)).join("")}</div>`}
    </div>

    <div class="card" id="leaderboard-card">
      <div class="section-header">
        <h2>Leaderboard</h2>
        <div style="display:flex;gap:6px">
          <button class="btn btn-sm ${state.leaderboardMode === 'detailed' ? 'btn-primary' : 'btn-ghost'}" id="lb-tab-detailed">Detailed</button>
          <button class="btn btn-sm ${state.leaderboardMode === 'simple' ? 'btn-primary' : 'btn-ghost'}" id="lb-tab-simple">Simple</button>
        </div>
      </div>
      <div id="leaderboard-body">
        ${renderLeaderboard()}
      </div>
    </div>

    ${state.matches.length > 0 ? `
    <div class="card">
      <div class="section-header"><h2>Match History</h2></div>
      <div class="table-wrap">
        <table class="history-table">
          <thead><tr><th>Round</th><th>Court</th><th>Team A</th><th></th><th>Team B</th><th>Status</th></tr></thead>
          <tbody>
            ${[...state.matches].sort((a,b)=>b.round_number-a.round_number||a.court-b.court).map(m=>`
              <tr>
                <td><span class="round-badge">R${m.round_number}</span></td>
                <td style="color:var(--text2)">Court ${m.court}</td>
                <td>${playerNames(m.team_a)}</td>
                <td style="text-align:center;font-weight:700;font-variant-numeric:tabular-nums">
                  ${m.score_a??'—'} <span style="color:var(--text3)">:</span> ${m.score_b??'—'}
                </td>
                <td>${playerNames(m.team_b)}</td>
                <td><span class="chip chip-${m.status}">${m.status}</span></td>
              </tr>`).join("")}
          </tbody>
        </table>
      </div>
    </div>` : ""}
  `;

  document.getElementById("btn-back").onclick = () => loadView("tournaments");

  document.getElementById("lb-tab-detailed").onclick = () => {
    state.leaderboardMode = "detailed";
    document.getElementById("leaderboard-body").innerHTML = renderLeaderboard();
    document.getElementById("lb-tab-detailed").className = "btn btn-sm btn-primary";
    document.getElementById("lb-tab-simple").className   = "btn btn-sm btn-ghost";
  };
  document.getElementById("lb-tab-simple").onclick = () => {
    state.leaderboardMode = "simple";
    document.getElementById("leaderboard-body").innerHTML = renderLeaderboard();
    document.getElementById("lb-tab-detailed").className = "btn btn-sm btn-ghost";
    document.getElementById("lb-tab-simple").className   = "btn btn-sm btn-primary";
  };
  document.getElementById("btn-gen-matches")?.addEventListener("click", generateRound);
  document.getElementById("btn-add-player")?.addEventListener("click", () => openAddPlayerModal());
  document.getElementById("btn-rename-tournament").onclick = () =>
    openRenameTournamentModal(t.id, t.name, /* fromView */ true);
  document.getElementById("btn-finish-tournament")?.addEventListener("click", confirmFinishTournament);
  document.getElementById("btn-show-story").onclick = () => showStoryModal();

  window.startMatch    = (mid) => doStartMatch(mid);
  window.finishMatch   = (mid) => doFinishMatch(mid);
  window.saveScore     = (mid) => doSaveScore(mid);
  window.setPlayerStatus = (tpId, status) => doSetPlayerStatus(tpId, status);
  window.openTeamEditor = (mid) => doOpenTeamEditorModal(mid);
}

function countGames(playerId) {
  return state.matches.filter(m =>
    m.status === "finished" &&
    (m.team_a.includes(playerId) || m.team_b.includes(playerId))
  ).length;
}

function renderCourtCard(m, t) {
  const nameOf  = (id) => state.tournamentPlayers.find(p => p.player_id === id)?.player_name || `#${id}`;
  const skillOf = (id) => state.tournamentPlayers.find(p => p.player_id === id)?.skill || 0;
  const sumA    = m.team_a.reduce((s,id) => s + skillOf(id), 0);
  const sumB    = m.team_b.reduce((s,id) => s + skillOf(id), 0);
  const winA    = m.status === "finished" && m.score_a > m.score_b;
  const winB    = m.status === "finished" && m.score_b > m.score_a;
  const canScore = m.status === "ongoing" && t.status !== "finished";
  const canAct   = m.status !== "finished" && t.status !== "finished";

  return `
    <div class="court-card ${m.status}">
      <div class="court-header">
        <div style="display:flex;align-items:center;gap:8px">
          <span class="court-label">Court ${m.court}</span>
          <span class="round-badge">R${m.round_number}</span>
        </div>
        <span class="chip chip-${m.status}">${m.status}</span>
      </div>

      <div class="match-teams">
        <div class="team-row ${winA ? "winner" : ""}">
          <div class="team-info">
            ${m.team_a.map(id => `
              <span class="team-player">
                ${nameOf(id)}
                <span class="skill-badge" style="color:${skillColor(skillOf(id))}">${skillOf(id)}</span>
              </span>`).join("")}
            <span class="team-skill-sum">Σ ${sumA.toFixed(1)}</span>
          </div>
          <span class="team-score ${winA ? "winner" : ""}">${m.score_a ?? "—"}</span>
        </div>

        <div class="vs-row">VS</div>

        <div class="team-row ${winB ? "winner" : ""}">
          <div class="team-info">
            ${m.team_b.map(id => `
              <span class="team-player">
                ${nameOf(id)}
                <span class="skill-badge" style="color:${skillColor(skillOf(id))}">${skillOf(id)}</span>
              </span>`).join("")}
            <span class="team-skill-sum">Σ ${sumB.toFixed(1)}</span>
          </div>
          <span class="team-score ${winB ? "winner" : ""}">${m.score_b ?? "—"}</span>
        </div>
      </div>

      ${canScore ? `
      <div class="score-inputs">
        <input id="score-a-${m.id}" type="number" min="0" max="99" value="${m.score_a ?? ""}" placeholder="0" />
        <span class="score-sep">:</span>
        <input id="score-b-${m.id}" type="number" min="0" max="99" value="${m.score_b ?? ""}" placeholder="0" />
        <button class="btn btn-ghost btn-sm" onclick="saveScore(${m.id})">Save</button>
      </div>` : ""}
      ${canAct ? `
      <div class="match-actions">
        ${m.status === "pending" ? `<button class="btn btn-orange btn-sm" onclick="startMatch(${m.id})">▶ Start</button>` : ""}
        ${m.status === "ongoing" ? `<button class="btn btn-success btn-sm" onclick="finishMatch(${m.id})">✓ Finish</button>` : ""}
        <button class="btn btn-ghost btn-sm" onclick="openTeamEditor(${m.id})">✏️ Edit Teams</button>
      </div>` : ""}
    </div>`;
}

function renderLeaderboard() {
  if (state.leaderboard.length === 0)
    return `<div class="empty"><div class="empty-icon">📊</div>No finished matches yet.</div>`;

  return state.leaderboardMode === "simple"
    ? renderLeaderboardSimple()
    : renderLeaderboardDetailed();
}

function renderLeaderboardDetailed() {
  return `<div class="table-wrap"><table>
    <thead>
      <tr>
        <th style="width:40px">#</th>
        <th>Player</th>
        <th>Skill</th>
        <th>GP</th>
        <th>W</th>
        <th>L</th>
        <th title="Total score points earned across all matches">Score Pts</th>
        <th title="Total score points conceded across all matches" class="hide-mobile">Conceded</th>
        <th title="Score difference (scored − conceded)" class="hide-mobile">+/−</th>
      </tr>
    </thead>
    <tbody>
      ${state.leaderboard.map(e => {
        const diff = e.points_scored - e.points_conceded;
        return `
        <tr class="lb-row rank-${e.rank}">
          <td class="lb-rank" style="color:${e.rank===1?'var(--gold)':e.rank===2?'var(--silver)':e.rank===3?'var(--bronze)':'var(--text3)'}">
            ${e.rank === 1 ? "🥇" : e.rank === 2 ? "🥈" : e.rank === 3 ? "🥉" : e.rank}
          </td>
          <td style="font-weight:600">${e.player_name}</td>
          <td><span class="skill-badge" style="color:${skillColor(e.skill)}">${e.skill}</span></td>
          <td style="color:var(--text2)">${e.games_played}</td>
          <td style="color:var(--green);font-weight:700">${e.wins}</td>
          <td style="color:var(--text3)">${e.losses}</td>
          <td style="font-weight:800;font-size:.95rem">${e.total_points}</td>
          <td style="color:var(--text3)" class="hide-mobile">${e.points_conceded}</td>
          <td style="color:${diff>=0?'var(--green)':'var(--red)'};font-weight:600" class="hide-mobile">${diff >= 0 ? "+" : ""}${diff}</td>
        </tr>`;
      }).join("")}
    </tbody>
  </table></div>`;
}

function renderLeaderboardSimple() {
  const t = state.currentTournament;
  const rankColor = (r) => r === 1 ? 'var(--gold)' : r === 2 ? 'var(--silver)' : r === 3 ? 'var(--bronze)' : 'var(--text3)';
  const medal     = (r) => r === 1 ? "🥇" : r === 2 ? "🥈" : r === 3 ? "🥉" : `<span style="color:${rankColor(r)};font-weight:700">${r}</span>`;

  return `
    <div id="lb-simple-card" style="
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      max-width: 560px;
      margin: 0 auto;
    ">
      <!-- Brand header -->
      <div style="
        background: var(--accent);
        padding: 18px 24px;
        display: flex;
        align-items: center;
        gap: 14px;
      ">
        <img src="/assets/prunus-sport.png" alt="Prunus Sport"
             style="height:38px;object-fit:contain;filter:brightness(0) invert(1)"
             onerror="this.style.display='none'" />
        <div>
          <div style="font-weight:800;font-size:1rem;color:#fff;letter-spacing:.3px">Prunus Sport</div>
          <div style="font-size:.75rem;color:rgba(255,255,255,.75);margin-top:1px">Badminton Matchmaking</div>
        </div>
      </div>

      <!-- Tournament name -->
      <div style="padding:14px 24px 10px;border-bottom:1px solid var(--border)">
        <div style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.8px;color:var(--text3);margin-bottom:4px">Tournament</div>
        <div style="font-size:1.05rem;font-weight:800">${t.name}</div>
        <div style="font-size:.75rem;color:var(--text3);margin-top:3px">${new Date().toLocaleDateString('en-GB',{day:'numeric',month:'long',year:'numeric'})}</div>
      </div>

      <!-- Leaderboard rows -->
      <div style="padding:8px 0">
        ${state.leaderboard.map((e, i) => `
          <div style="
            display:flex;
            align-items:center;
            padding:10px 24px;
            gap:14px;
            background:${e.rank <= 3 ? 'var(--accent-bg)' : i % 2 === 0 ? 'transparent' : 'var(--bg3)'};
            border-bottom:1px solid var(--border);
          ">
            <span style="font-size:1.15rem;min-width:32px;text-align:center">${medal(e.rank)}</span>
            <span style="font-weight:700;flex:1;font-size:.95rem">${e.player_name}</span>
            <div style="display:flex;gap:16px;align-items:center;font-size:.82rem">
              <span style="color:var(--text3)">${e.wins}W · ${e.losses}L</span>
              <span style="
                font-weight:800;
                font-size:1rem;
                color:${e.rank===1?'var(--gold)':e.rank===2?'var(--silver)':e.rank===3?'var(--bronze)':'var(--text)'};
                min-width:40px;
                text-align:right;
              ">${e.total_points}</span>
            </div>
          </div>`).join("")}
      </div>

      <!-- Footer -->
      <div style="padding:12px 24px;display:flex;justify-content:space-between;align-items:center;border-top:1px solid var(--border)">
        <span style="font-size:.72rem;color:var(--text3)">Points = score earned per match</span>
        <span style="font-size:.72rem;font-weight:700;color:var(--accent)">prunus.sport</span>
      </div>
    </div>

    <p style="text-align:center;color:var(--text3);font-size:.75rem;margin-top:10px">
      📸 Switch to dark mode for a better screenshot
    </p>`;
}

function playerNames(ids) {
  return ids
    .map(id => state.tournamentPlayers.find(p => p.player_id === id)?.player_name || `#${id}`)
    .join(" & ");
}

// ─── Actions ──────────────────────────────────────────────

async function generateRound() {
  try {
    await api.generateMatches(state.currentTournament.id);
    toast("New round generated", "success");
    await refreshTournamentView();
  } catch (e) { toast(e.message, "error"); }
}

async function doStartMatch(mid) {
  try {
    await api.startMatch(state.currentTournament.id, mid);
    await refreshTournamentView();
  } catch (e) { toast(e.message, "error"); }
}

async function doSaveScore(mid) {
  const sa = parseInt(document.getElementById(`score-a-${mid}`)?.value);
  const sb = parseInt(document.getElementById(`score-b-${mid}`)?.value);
  if (isNaN(sa) || isNaN(sb)) return toast("Enter valid scores", "error");
  try {
    await api.updateScore(state.currentTournament.id, mid, { score_a: sa, score_b: sb });
    toast("Score saved", "success");
    await refreshTournamentView();
  } catch (e) { toast(e.message, "error"); }
}

async function doFinishMatch(mid) {
  const sa = parseInt(document.getElementById(`score-a-${mid}`)?.value);
  const sb = parseInt(document.getElementById(`score-b-${mid}`)?.value);
  if (isNaN(sa) || isNaN(sb)) return toast("Enter scores first", "error");
  try {
    await api.updateScore(state.currentTournament.id, mid, { score_a: sa, score_b: sb });
    await api.finishMatch(state.currentTournament.id, mid);
    toast("Match finished", "success");
    await refreshTournamentView();
  } catch (e) { toast(e.message, "error"); }
}

async function doSetPlayerStatus(tpId, status) {
  try {
    await api.updateTournamentPlayer(state.currentTournament.id, tpId, { status });
    const labels = { away: "Marked away", active: "Back in", left: "Left tournament" };
    toast(labels[status] || "Updated", "success");
    await refreshTournamentView();
  } catch (e) { toast(e.message, "error"); }
}

function doOpenTeamEditorModal(mid) {
  const m = state.matches.find(x => x.id === mid);
  if (!m) return;

  // All active players are eligible (team members can be rearranged freely)
  const activePlayers = state.tournamentPlayers.filter(p => p.status === "active");
  const nameOf = (id) => state.tournamentPlayers.find(p => p.player_id === id)?.player_name || `#${id}`;
  const skillOf = (id) => state.tournamentPlayers.find(p => p.player_id === id)?.skill ?? "";

  const playerOptions = (selectedId) => activePlayers.map(p =>
    `<option value="${p.player_id}" ${p.player_id === selectedId ? "selected" : ""}>
      ${p.player_name} · ${p.skill}
    </option>`
  ).join("");

  const [a1, a2] = m.team_a;
  const [b1, b2] = m.team_b;

  const html = `
    <h2>Edit Match Teams</h2>
    <p style="font-size:.8rem;color:var(--text3);margin-bottom:16px">
      Freely reassign all 4 slots — swap partners, swap opponents, or bring in a resting player.
    </p>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px">
      <div>
        <div style="font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.7px;color:var(--text3);margin-bottom:8px">Team A</div>
        <div class="form-group" style="margin-bottom:10px">
          <label>Player 1</label>
          <select id="te-a1">${playerOptions(a1)}</select>
        </div>
        <div class="form-group">
          <label>Player 2</label>
          <select id="te-a2">${playerOptions(a2)}</select>
        </div>
      </div>
      <div>
        <div style="font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.7px;color:var(--text3);margin-bottom:8px">Team B</div>
        <div class="form-group" style="margin-bottom:10px">
          <label>Player 1</label>
          <select id="te-b1">${playerOptions(b1)}</select>
        </div>
        <div class="form-group">
          <label>Player 2</label>
          <select id="te-b2">${playerOptions(b2)}</select>
        </div>
      </div>
    </div>`;

  modal(html, async () => {
    const newA = [
      parseInt(document.getElementById("te-a1").value),
      parseInt(document.getElementById("te-a2").value),
    ];
    const newB = [
      parseInt(document.getElementById("te-b1").value),
      parseInt(document.getElementById("te-b2").value),
    ];
    const all = [...newA, ...newB];
    if (new Set(all).size !== 4)
      return toast("All 4 players must be different", "error");
    try {
      await api.editMatchTeams(state.currentTournament.id, mid, newA, newB);
      toast("Teams updated", "success");
      await refreshTournamentView();
    } catch (e) { toast(e.message, "error"); }
  }, "Save Teams", "btn-primary");
}

async function openAddPlayerModal() {
  // Always fetch fresh — state.players may be empty if user hasn't visited the Players tab yet
  state.players = await api.getPlayers();

  const existing  = state.tournamentPlayers.map(tp => tp.player_id);
  const available = state.players.filter(p => !existing.includes(p.id));

  // Build the player list rows (checkboxes + inline skill slider per player)
  const playerRows = available.map(p => `
    <div class="add-player-row" data-pid="${p.id}" style="
      display:flex;align-items:center;gap:10px;
      padding:8px 10px;border-radius:6px;border:1px solid var(--border);
      margin-bottom:6px;background:var(--bg2);cursor:pointer;
    ">
      <input type="checkbox" class="ap-check" data-pid="${p.id}"
             style="width:16px;height:16px;cursor:pointer;flex-shrink:0" />
      <span style="font-weight:600;min-width:120px;flex:1">${p.name}</span>
      <div class="ap-skill-wrap" style="display:none;align-items:center;gap:6px;flex-shrink:0">
        <input type="range" class="ap-skill" data-pid="${p.id}"
               min="1" max="10" step="0.5" value="${p.default_skill}"
               style="width:100px" />
        <span class="ap-skill-val" style="min-width:28px;text-align:right;font-size:.82rem;color:var(--text2)">${p.default_skill}</span>
      </div>
    </div>`).join("");

  const html = `
    <h2>Add Players</h2>
    <div style="display:flex;gap:8px;margin-bottom:14px">
      <input id="new-player-name" type="text" placeholder="Quick-create new player…" style="flex:1" />
      <button class="btn btn-ghost btn-sm" id="quick-add-btn">＋ Create</button>
    </div>
    ${available.length === 0
      ? `<p style="color:var(--text3);font-size:.85rem;padding:8px 0">All players are already in this tournament.</p>`
      : `<p style="font-size:.78rem;color:var(--text3);margin-bottom:8px">
           Check players to add. Their default skill is pre-set — adjust with the slider if needed.
         </p>
         <div id="ap-list" style="max-height:340px;overflow-y:auto;padding-right:4px">
           ${playerRows}
         </div>`}`;

  const overlay = modal(html, async () => {
    const checks = overlay.querySelectorAll(".ap-check:checked");
    if (checks.length === 0) return toast("Select at least one player", "error");
    try {
      for (const cb of checks) {
        const pid   = parseInt(cb.dataset.pid);
        const skill = parseFloat(overlay.querySelector(`.ap-skill[data-pid="${pid}"]`)?.value ?? 5);
        await api.addTournamentPlayer(state.currentTournament.id, { player_id: pid, skill });
      }
      toast(`${checks.length} player${checks.length > 1 ? "s" : ""} added`, "success");
      state.players = await api.getPlayers();
      await refreshTournamentView();
    } catch (e) { toast(e.message, "error"); }
  }, "Add to Tournament", "btn-success");

  // Toggle skill slider when checkbox changes; clicking the row toggles the checkbox
  overlay.querySelectorAll(".add-player-row").forEach(row => {
    const cb   = row.querySelector(".ap-check");
    const wrap = row.querySelector(".ap-skill-wrap");
    const slider = row.querySelector(".ap-skill");
    const valEl  = row.querySelector(".ap-skill-val");

    const syncUI = () => {
      wrap.style.display = cb.checked ? "flex" : "none";
      row.style.borderColor = cb.checked ? "var(--accent)" : "var(--border)";
      row.style.background  = cb.checked ? "var(--accent-bg)" : "var(--bg2)";
    };

    cb.addEventListener("change", syncUI);

    // Clicking the row (but not the slider/checkbox itself) toggles selection
    row.addEventListener("click", e => {
      if (e.target === slider || e.target === cb) return;
      cb.checked = !cb.checked;
      syncUI();
    });

    // Live-update the displayed skill value
    slider?.addEventListener("input", () => {
      if (valEl) valEl.textContent = slider.value;
    });
  });

  // Quick-create: add to global player list AND inject a pre-checked row
  overlay.querySelector("#quick-add-btn").onclick = async () => {
    const name = overlay.querySelector("#new-player-name").value.trim();
    if (!name) return toast("Enter a name", "error");
    if (state.tournamentPlayers.some(tp => {
      const pl = state.players.find(p => p.id === tp.player_id);
      return pl?.name?.toLowerCase() === name.toLowerCase();
    })) return toast("Player already in tournament", "error");
    try {
      const player = await api.createPlayer({ name, default_skill: 5 });
      state.players.push(player);
      overlay.querySelector("#new-player-name").value = "";

      // Inject new row into the list, pre-checked
      const list = overlay.querySelector("#ap-list");
      if (!list) return toast("Player created — re-open Add Players to include them", "info");
      const div  = document.createElement("div");
      div.innerHTML = `
        <div class="add-player-row" data-pid="${player.id}" style="
          display:flex;align-items:center;gap:10px;
          padding:8px 10px;border-radius:6px;
          border:1px solid var(--accent);background:var(--accent-bg);
          margin-bottom:6px;cursor:pointer;
        ">
          <input type="checkbox" class="ap-check" data-pid="${player.id}" checked
                 style="width:16px;height:16px;cursor:pointer;flex-shrink:0" />
          <span style="font-weight:600;min-width:120px;flex:1">${player.name} <span style="font-size:.75rem;color:var(--text3)">(new)</span></span>
          <div class="ap-skill-wrap" style="display:flex;align-items:center;gap:6px;flex-shrink:0">
            <input type="range" class="ap-skill" data-pid="${player.id}"
                   min="1" max="10" step="0.5" value="5" style="width:100px" />
            <span class="ap-skill-val" style="min-width:28px;text-align:right;font-size:.82rem;color:var(--text2)">5</span>
          </div>
        </div>`;
      const row    = div.firstElementChild;
      const cb     = row.querySelector(".ap-check");
      const slider = row.querySelector(".ap-skill");
      const valEl  = row.querySelector(".ap-skill-val");

      row.addEventListener("click", e => {
        if (e.target === slider || e.target === cb) return;
        cb.checked = !cb.checked;
        row.style.borderColor = cb.checked ? "var(--accent)" : "var(--border)";
        row.style.background  = cb.checked ? "var(--accent-bg)" : "var(--bg2)";
      });
      slider.addEventListener("input", () => { valEl.textContent = slider.value; });

      list.prepend(row);
      toast(`${player.name} created`, "success");
    } catch (e) { toast(e.message, "error"); }
  };
}

function openRenameTournamentModal(tid, currentName, fromView = false) {
  const html = `
    <h2>Rename Tournament</h2>
    <div class="form-group">
      <label>New name</label>
      <input id="rename-input" type="text" value="${currentName}" />
    </div>`;

  modal(html, async () => {
    const name = document.getElementById("rename-input").value.trim();
    if (!name) return toast("Name cannot be empty", "error");
    if (name === currentName) return;
    try {
      const updated = await api.renameTournament(tid, name);
      const idx = state.tournaments.findIndex(t => t.id === tid);
      if (idx !== -1) state.tournaments[idx] = updated;
      if (state.currentTournament?.id === tid) state.currentTournament = updated;
      toast("Tournament renamed", "success");
      if (fromView) {
        await refreshTournamentView();
      } else {
        renderTournamentList(document.getElementById("main-content"));
      }
    } catch (e) { toast(e.message, "error"); }
  }, "Rename", "btn-primary");

  // Auto-select text for quick editing
  setTimeout(() => {
    const input = document.getElementById("rename-input");
    input?.select();
  }, 50);
}

function confirmDeleteTournament(tid, name) {
  modal(
    `<h2>Delete Tournament?</h2>
     <p style="color:var(--text2);font-size:.88rem;line-height:1.6">
       Delete <strong>${name}</strong>? This will permanently remove all matches and player data for this tournament. This cannot be undone.
     </p>`,
    async () => {
      try {
        await api.deleteTournament(tid);
        state.tournaments = state.tournaments.filter(t => t.id !== tid);
        toast("Tournament deleted", "success");
        // If we're currently viewing this tournament, go back to list
        if (state.currentTournament?.id === tid) {
          loadView("tournaments");
        } else {
          renderTournamentList(document.getElementById("main-content"));
        }
      } catch (e) { toast(e.message, "error"); }
    }, "Delete", "btn-danger"
  );
}

function confirmFinishTournament() {
  modal(
    `<h2>Finish Tournament?</h2>
     <p style="color:var(--text2);font-size:.88rem;line-height:1.6">
       This will lock the tournament. You can still view results and download the Instagram story afterwards.
     </p>`,
    async () => {
      try {
        await api.finishTournament(state.currentTournament.id);
        toast("Tournament finished!", "success");
        state.tournaments = await api.getTournaments();
        state.currentTournament = state.tournaments.find(t => t.id === state.currentTournament.id);
        await refreshTournamentView();
      } catch (e) { toast(e.message, "error"); }
    }, "Finish", "btn-danger"
  );
}

const STORY_FORMATS = [
  { id: "midnight", label: "🌙 Midnight",  desc: "Dark navy · Emerald" },
  { id: "daylight", label: "☀️ Daylight",  desc: "Clean white · Forest green" },
  { id: "neon",     label: "⚡ Neon Court", desc: "Black · Electric lime" },
  { id: "gold",     label: "🏆 Gold Trophy",desc: "Dark warm · Premium gold" },
];

function showStoryModal() {
  const tid = state.currentTournament.id;
  let activeFormat = "midnight";

  const buildUrl = (fmt) => api.getStoryUrl(tid, fmt) + "&t=" + Date.now();

  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.innerHTML = `
    <div class="modal" style="width:min(520px,96vw);max-height:92vh;overflow-y:auto">
      <h2>📸 Instagram Story</h2>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:18px">
        ${STORY_FORMATS.map(f => `
          <button class="story-fmt-btn btn btn-ghost btn-sm ${f.id === activeFormat ? "fmt-active" : ""}"
                  data-fmt="${f.id}"
                  style="flex-direction:column;align-items:flex-start;padding:10px 14px;height:auto;gap:2px;text-align:left">
            <span style="font-size:.84rem;font-weight:700">${f.label}</span>
            <span style="font-size:.72rem;color:var(--text3);font-weight:400">${f.desc}</span>
          </button>`).join("")}
      </div>

      <div id="story-preview-wrap" style="position:relative;min-height:160px;background:var(--bg3);border-radius:8px;overflow:hidden;margin-bottom:14px">
        <div id="story-loading" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:var(--text3);font-size:.85rem">
          Generating…
        </div>
        <img id="story-img" src="" alt="Story preview"
             style="width:100%;border-radius:8px;display:none" />
      </div>

      <p style="color:var(--text3);font-size:.78rem;margin-bottom:16px">
        Right-click the image to save, or use Download.
      </p>

      <div class="modal-actions">
        <button class="btn btn-ghost" id="story-close">Close</button>
        <a id="story-dl" href="#" download="leaderboard-story.png" class="btn btn-primary">⬇ Download</a>
      </div>
    </div>`;

  document.body.appendChild(overlay);

  // Style active format button
  const styleButtons = () => {
    overlay.querySelectorAll(".story-fmt-btn").forEach(b => {
      b.classList.toggle("fmt-active", b.dataset.fmt === activeFormat);
      b.style.borderColor = b.dataset.fmt === activeFormat ? "var(--accent)" : "";
      b.style.background  = b.dataset.fmt === activeFormat ? "var(--accent-bg)" : "";
    });
  };

  const loadPreview = () => {
    const img     = overlay.querySelector("#story-img");
    const loading = overlay.querySelector("#story-loading");
    const dlBtn   = overlay.querySelector("#story-dl");
    const url     = buildUrl(activeFormat);

    img.style.display   = "none";
    loading.style.display = "flex";

    const tmp    = new window.Image();
    tmp.onload   = () => {
      img.src           = url;
      img.style.display = "block";
      loading.style.display = "none";
      dlBtn.href        = url;
      dlBtn.download    = `prunus-sport-${activeFormat}.png`;
    };
    tmp.onerror  = () => {
      loading.textContent = "Failed to generate. Try again.";
    };
    tmp.src = url;
  };

  styleButtons();
  loadPreview();

  overlay.querySelectorAll(".story-fmt-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      activeFormat = btn.dataset.fmt;
      styleButtons();
      loadPreview();
    });
  });

  overlay.querySelector("#story-close").onclick = () => overlay.remove();
  overlay.addEventListener("click", e => { if (e.target === overlay) overlay.remove(); });
}

// ─── Players View ──────────────────────────────────────────

function renderPlayersView(main) {
  main.innerHTML = `
    <div class="section-header">
      <h2>Player Profiles</h2>
      <button class="btn btn-primary" id="btn-new-player">+ New Player</button>
    </div>
    <div class="card">
      ${state.players.length === 0
        ? `<div class="empty"><div class="empty-icon">👤</div>No players yet.</div>`
        : `<div class="table-wrap"><table class="player-table">
          <thead><tr><th>Name</th><th>Default Skill</th><th>Created</th><th></th></tr></thead>
          <tbody>
            ${state.players.map(p => `
              <tr>
                <td style="font-weight:600">${p.name}</td>
                <td>
                  <span class="skill-badge" style="color:${skillColor(p.default_skill)}">${p.default_skill}</span>
                  <span style="color:var(--text3);font-size:.78rem;margin-left:6px">${skillLabel(p.default_skill)}</span>
                </td>
                <td style="color:var(--text3);font-size:.8rem">${fmtDate(p.created_at)}</td>
                <td>
                  <div style="display:flex;gap:6px">
                    <button class="btn btn-ghost btn-sm" onclick="editPlayer(${p.id})">Edit</button>
                    <button class="btn btn-ghost btn-sm" style="color:var(--red)" onclick="deletePlayer(${p.id})">Delete</button>
                  </div>
                </td>
              </tr>`).join("")}
          </tbody>
        </table></div>`}
    </div>`;

  document.getElementById("btn-new-player").onclick = () => openNewPlayerModal();
  window.editPlayer   = (id) => openEditPlayerModal(id);
  window.deletePlayer = (id) => confirmDeletePlayer(id);
}

function openNewPlayerModal() {
  const html = `
    <h2>New Player</h2>
    <div class="form-group" style="margin-bottom:16px">
      <label>Name</label>
      <input id="np-name" type="text" placeholder="Player name" />
    </div>
    <div class="form-group">
      <label>Default Skill — <span id="np-skill-val">5</span> / 10</label>
      <input id="np-skill" type="range" min="1" max="10" step="0.5" value="5"
        oninput="document.getElementById('np-skill-val').textContent=this.value" />
    </div>`;

  modal(html, async () => {
    const name = document.getElementById("np-name").value.trim();
    if (!name) return toast("Name required", "error");
    try {
      const p = await api.createPlayer({ name, default_skill: parseFloat(document.getElementById("np-skill").value) });
      state.players.push(p);
      toast("Player created", "success");
      renderPlayersView(document.getElementById("main-content"));
    } catch (e) { toast(e.message, "error"); }
  }, "Create", "btn-success");
}

function openEditPlayerModal(id) {
  const p = state.players.find(x => x.id === id);
  if (!p) return;
  const html = `
    <h2>Edit Player</h2>
    <div class="form-group" style="margin-bottom:16px">
      <label>Name</label>
      <input id="ep-name" type="text" value="${p.name}" />
    </div>
    <div class="form-group">
      <label>Default Skill — <span id="ep-skill-val">${p.default_skill}</span> / 10</label>
      <input id="ep-skill" type="range" min="1" max="10" step="0.5" value="${p.default_skill}"
        oninput="document.getElementById('ep-skill-val').textContent=this.value" />
    </div>`;

  modal(html, async () => {
    try {
      const updated = await api.updatePlayer(id, {
        name: document.getElementById("ep-name").value.trim(),
        default_skill: parseFloat(document.getElementById("ep-skill").value),
      });
      state.players[state.players.findIndex(x => x.id === id)] = updated;
      toast("Player updated", "success");
      renderPlayersView(document.getElementById("main-content"));
    } catch (e) { toast(e.message, "error"); }
  }, "Save", "btn-primary");
}

function confirmDeletePlayer(id) {
  const p = state.players.find(x => x.id === id);
  modal(
    `<h2>Delete Player?</h2>
     <p style="color:var(--text2);font-size:.88rem">
       Delete <strong>${p?.name}</strong>? This cannot be undone.
     </p>`,
    async () => {
      try {
        await api.deletePlayer(id);
        state.players = state.players.filter(x => x.id !== id);
        toast("Player deleted", "success");
        renderPlayersView(document.getElementById("main-content"));
      } catch (e) { toast(e.message, "error"); }
    }, "Delete", "btn-danger"
  );
}
