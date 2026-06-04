const BASE = "";

async function req(method, path, body) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(BASE + path, opts);
  if (res.status === 204) return null;
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

export const api = {
  // Players
  getPlayers: () => req("GET", "/api/players"),
  createPlayer: (data) => req("POST", "/api/players", data),
  updatePlayer: (id, data) => req("PATCH", `/api/players/${id}`, data),
  deletePlayer: (id) => req("DELETE", `/api/players/${id}`),

  // Tournaments
  getTournaments: () => req("GET", "/api/tournaments"),
  createTournament: (data) => req("POST", "/api/tournaments", data),
  updateTournament: (id, data) => req("PATCH", `/api/tournaments/${id}`, data),
  renameTournament: (id, name) => req("PATCH", `/api/tournaments/${id}`, { name }),
  deleteTournament: (id) => req("DELETE", `/api/tournaments/${id}`),
  finishTournament: (id) => req("POST", `/api/tournaments/${id}/finish`),

  // Tournament players
  getTournamentPlayers: (tid) => req("GET", `/api/tournaments/${tid}/players`),
  addTournamentPlayer: (tid, data) => req("POST", `/api/tournaments/${tid}/players`, data),
  updateTournamentPlayer: (tid, tpId, data) => req("PATCH", `/api/tournaments/${tid}/players/${tpId}`, data),

  // Matches
  getMatches: (tid) => req("GET", `/api/tournaments/${tid}/matches`),
  generateMatches: (tid) => req("POST", `/api/tournaments/${tid}/matches/generate`),
  startMatch: (tid, mid) => req("PATCH", `/api/tournaments/${tid}/matches/${mid}/start`),
  updateScore: (tid, mid, data) => req("PATCH", `/api/tournaments/${tid}/matches/${mid}/score`, data),
  finishMatch: (tid, mid) => req("PATCH", `/api/tournaments/${tid}/matches/${mid}/finish`),
  editMatchTeams: (tid, mid, teamA, teamB) =>
    req("PATCH", `/api/tournaments/${tid}/matches/${mid}/teams?team_a=${teamA.join(",")}&team_b=${teamB.join(",")}`),

  // Leaderboard
  getLeaderboard: (tid) => req("GET", `/api/tournaments/${tid}/matches/leaderboard`),

  // Story
  getStoryUrl: (tid, fmt = "midnight") => `/api/tournaments/${tid}/story?format=${fmt}`,
};
