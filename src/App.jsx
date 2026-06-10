import { useState, useMemo } from "react";
import _ from "lodash";

const ALL_MODELS = [
  { name: "gemini-2.5-pro", org: "Google", elo: 1207, rank: 1, votes: 6954, sets: { 80: [1,5], 85: [1,6], 90: [1,8], 95: [1,9] }, boot95: [1,2], codeRank: 1, noncodeRank: 1 },
  { name: "chatgpt-4o-latest-20250326", org: "OpenAI", elo: 1137, rank: 2, votes: 5635, sets: { 80: [1,10], 85: [1,11], 90: [1,12], 95: [1,14] }, boot95: [2,10], codeRank: 3, noncodeRank: 3 },
  { name: "grok-4-0709", org: "xAI", elo: 1131, rank: 3, votes: 1153, sets: { 80: [1,8], 85: [1,8], 90: [1,10], 95: [1,12] }, boot95: [1,9], codeRank: 5, noncodeRank: 2 },
  { name: "gemini-2.5-pro-preview-03-25", org: "Google", elo: 1125, rank: 4, votes: 1029, sets: { 80: [1,8], 85: [1,8], 90: [1,10], 95: [1,12] }, boot95: [1,7], codeRank: 7, noncodeRank: 4 },
  { name: "gemini-2.5-flash", org: "Google", elo: 1114, rank: 5, votes: 6920, sets: { 80: [4,13], 85: [4,14], 90: [2,16], 95: [1,17] }, boot95: [4,13], codeRank: 8, noncodeRank: 5 },
  { name: "o3-2025-04-16", org: "OpenAI", elo: 1112, rank: 6, votes: 6411, sets: { 80: [1,10], 85: [1,11], 90: [1,12], 95: [1,14] }, boot95: [2,11], codeRank: 4, noncodeRank: 7 },
  { name: "gemini-2.5-pro-preview-05-06", org: "Google", elo: 1106, rank: 7, votes: 2382, sets: { 80: [1,10], 85: [1,10], 90: [1,12], 95: [1,14] }, boot95: [2,12], codeRank: 9, noncodeRank: 6 },
  { name: "deepseek-r1-0528", org: "DeepSeek", elo: 1093, rank: 8, votes: 4783, sets: { 80: [1,11], 85: [1,12], 90: [1,13], 95: [1,14] }, boot95: [2,11], codeRank: 6, noncodeRank: 8 },
  { name: "grok-3-preview-02-24", org: "xAI", elo: 1078, rank: 9, votes: 4435, sets: { 80: [2,11], 85: [1,12], 90: [1,14], 95: [1,15] }, boot95: [2,12], codeRank: 2, noncodeRank: 10 },
  { name: "llama-4-maverick-03-26-exp", org: "Meta", elo: 1077, rank: 10, votes: 4313, sets: { 80: [4,13], 85: [3,14], 90: [1,15], 95: [1,17] }, boot95: [3,13], codeRank: 12, noncodeRank: 9 },
  { name: "mistral-medium-2505", org: "Mistral", elo: 1067, rank: 11, votes: 6454, sets: { 80: [13,23], 85: [13,23], 90: [11,25], 95: [9,26] }, boot95: [11,27], codeRank: 15, noncodeRank: 11 },
  { name: "o4-mini-2025-04-16", org: "OpenAI", elo: 1042, rank: 12, votes: 4649, sets: { 80: [14,23], 85: [13,24], 90: [12,26], 95: [9,27] }, boot95: [11,27], codeRank: 22, noncodeRank: 15 },
  { name: "gemini-2.5-flash-preview-04-17", org: "Google", elo: 1042, rank: 13, votes: 3665, sets: { 80: [9,18], 85: [9,20], 90: [7,21], 95: [5,23] }, boot95: [10,25], codeRank: 20, noncodeRank: 14 },
  { name: "hunyuan-turbos-20250416", org: "Tencent", elo: 1039, rank: 14, votes: 1111, sets: { 80: [11,21], 85: [10,22], 90: [9,24], 95: [8,25] }, boot95: [9,26], codeRank: 21, noncodeRank: 13 },
  { name: "deepseek-v3-0324", org: "DeepSeek", elo: 1037, rank: 15, votes: 4354, sets: { 80: [12,21], 85: [11,21], 90: [9,23], 95: [8,25] }, boot95: [10,26], codeRank: 24, noncodeRank: 12 },
  { name: "kimi-k2-0711-preview", org: "Moonshot", elo: 1034, rank: 16, votes: 2028, sets: { 80: [11,19], 85: [10,20], 90: [9,22], 95: [6,24] }, boot95: [10,27], codeRank: 14, noncodeRank: 17 },
  { name: "qwen3-235b-a22b-no-thinking", org: "Alibaba", elo: 1014, rank: 17, votes: 6497, sets: { 80: [8,17], 85: [7,17], 90: [5,19], 95: [4,21] }, boot95: [7,21], codeRank: 13, noncodeRank: 18 },
  { name: "gpt-4.1-2025-04-14", org: "OpenAI", elo: 1010, rank: 18, votes: 4656, sets: { 80: [11,21], 85: [11,21], 90: [9,23], 95: [8,26] }, boot95: [10,25], codeRank: 25, noncodeRank: 19 },
  { name: "gemma-3-27b-it", org: "Google", elo: 1010, rank: 19, votes: 5256, sets: { 80: [17,27], 85: [16,27], 90: [15,29], 95: [13,31] }, boot95: [13,30], codeRank: 35, noncodeRank: 16 },
  { name: "claude-opus-4-thinking-16k", org: "Anthropic", elo: 1005, rank: 20, votes: 4582, sets: { 80: [19,29], 85: [19,29], 90: [17,31], 95: [15,32] }, boot95: [14,32], codeRank: 10, noncodeRank: 24 },
  { name: "qwen3-235b-a22b", org: "Alibaba", elo: 1004, rank: 21, votes: 3614, sets: { 80: [12,22], 85: [12,22], 90: [10,24], 95: [8,25] }, boot95: [10,26], codeRank: 16, noncodeRank: 22 },
  { name: "claude-opus-4", org: "Anthropic", elo: 1002, rank: 22, votes: 7337, sets: { 80: [20,29], 85: [19,30], 90: [18,32], 95: [16,33] }, boot95: [14,32], codeRank: 11, noncodeRank: 28 },
  { name: "gemini-flash-lite-think", org: "Google", elo: 1002, rank: 23, votes: 3738, sets: { 80: [14,24], 85: [13,24], 90: [12,26], 95: [10,27] }, boot95: [11,28], codeRank: 27, noncodeRank: 23 },
  { name: "gemini-2.0-flash-001", org: "Google", elo: 1001, rank: 24, votes: 4305, sets: { 80: [26,35], 85: [25,36], 90: [24,37], 95: [23,39] }, boot95: [21,36], codeRank: 31, noncodeRank: 26 },
  { name: "qwen-max-2025-01-25", org: "Alibaba", elo: 994, rank: 25, votes: 3080, sets: { 80: [14,22], 85: [13,23], 90: [11,25], 95: [9,27] }, boot95: [10,26], codeRank: 30, noncodeRank: 20 },
  { name: "mistral-small-2506", org: "Mistral", elo: 994, rank: 26, votes: 1669, sets: { 80: [25,34], 85: [25,35], 90: [23,37], 95: [21,39] }, boot95: [23,37], codeRank: 18, noncodeRank: 32 },
  { name: "qwen3-30b-a3b", org: "Alibaba", elo: 991, rank: 27, votes: 3862, sets: { 80: [28,37], 85: [28,38], 90: [26,40], 95: [24,41] }, boot95: [26,39], codeRank: 23, noncodeRank: 33 },
  { name: "minimax-m1", org: "MiniMax", elo: 987, rank: 28, votes: 3972, sets: { 80: [18,27], 85: [18,27], 90: [16,29], 95: [15,31] }, boot95: [13,30], codeRank: 33, noncodeRank: 21 },
  { name: "qwq-32b", org: "Alibaba", elo: 986, rank: 29, votes: 3053, sets: { 80: [25,35], 85: [24,35], 90: [23,37], 95: [21,39] }, boot95: [23,36], codeRank: 28, noncodeRank: 27 },
  { name: "grok-3-mini-beta", org: "xAI", elo: 984, rank: 30, votes: 4300, sets: { 80: [19,28], 85: [18,28], 90: [17,31], 95: [15,32] }, boot95: [14,33], codeRank: 19, noncodeRank: 29 },
  { name: "gpt-4.1-mini-2025-04-14", org: "OpenAI", elo: 982, rank: 31, votes: 4347, sets: { 80: [26,36], 85: [26,36], 90: [24,38], 95: [22,40] }, boot95: [21,37], codeRank: 32, noncodeRank: 25 },
  { name: "grok-3-mini-high", org: "xAI", elo: 975, rank: 32, votes: 1982, sets: { 80: [21,30], 85: [21,31], 90: [19,33], 95: [17,35] }, boot95: [17,32], codeRank: 26, noncodeRank: 30 },
  { name: "claude-sonnet-4-thinking-32k", org: "Anthropic", elo: 975, rank: 33, votes: 4124, sets: { 80: [24,34], 85: [24,34], 90: [22,36], 95: [20,37] }, boot95: [20,35], codeRank: 17, noncodeRank: 34 },
  { name: "gemma-3n-e4b-it", org: "Google", elo: 955, rank: 34, votes: 1893, sets: { 80: [32,41], 85: [32,42], 90: [30,44], 95: [28,46] }, boot95: [31,42], codeRank: 41, noncodeRank: 31 },
  { name: "claude-sonnet-4", org: "Anthropic", elo: 951, rank: 35, votes: 6081, sets: { 80: [28,37], 85: [27,38], 90: [25,40], 95: [24,42] }, boot95: [26,39], codeRank: 29, noncodeRank: 36 },
  { name: "o3-mini", org: "OpenAI", elo: 946, rank: 36, votes: 4807, sets: { 80: [32,41], 85: [31,42], 90: [30,44], 95: [28,46] }, boot95: [32,42], codeRank: 34, noncodeRank: 37 },
  { name: "command-a-03-2025", org: "Cohere", elo: 945, rank: 37, votes: 4787, sets: { 80: [29,38], 85: [28,39], 90: [26,40], 95: [24,42] }, boot95: [27,38], codeRank: 38, noncodeRank: 35 },
  { name: "nova-experimental-chat", org: "Amazon", elo: 940, rank: 38, votes: 2313, sets: { 80: [31,42], 85: [31,42], 90: [29,44], 95: [28,45] }, boot95: [32,42], codeRank: 36, noncodeRank: 39 },
  { name: "llama-4-scout-17b", org: "Meta", elo: 913, rank: 39, votes: 2028, sets: { 80: [37,46], 85: [36,47], 90: [35,48], 95: [33,48] }, boot95: [36,45], codeRank: 40, noncodeRank: 40 },
  { name: "llama-4-maverick-17b", org: "Meta", elo: 910, rank: 40, votes: 3900, sets: { 80: [36,45], 85: [36,46], 90: [34,48], 95: [32,48] }, boot95: [36,44], codeRank: 46, noncodeRank: 38 },
  { name: "claude-3.7-sonnet", org: "Anthropic", elo: 907, rank: 41, votes: 5110, sets: { 80: [36,45], 85: [35,46], 90: [34,48], 95: [32,48] }, boot95: [36,45], codeRank: 39, noncodeRank: 42 },
  { name: "claude-3.5-sonnet", org: "Anthropic", elo: 907, rank: 42, votes: 5054, sets: { 80: [37,46], 85: [36,47], 90: [35,48], 95: [33,48] }, boot95: [36,45], codeRank: 37, noncodeRank: 44 },
  { name: "claude-3.7-sonnet-thinking", org: "Anthropic", elo: 894, rank: 43, votes: 5344, sets: { 80: [35,44], 85: [34,45], 90: [33,47], 95: [31,48] }, boot95: [35,44], codeRank: 42, noncodeRank: 43 },
  { name: "llama-3.3-70b-instruct", org: "Meta", elo: 888, rank: 44, votes: 3604, sets: { 80: [40,48], 85: [40,48], 90: [38,48], 95: [36,48] }, boot95: [40,48], codeRank: 48, noncodeRank: 41 },
  { name: "claude-3.5-haiku", org: "Anthropic", elo: 873, rank: 45, votes: 4694, sets: { 80: [42,48], 85: [41,48], 90: [40,48], 95: [38,48] }, boot95: [43,48], codeRank: 45, noncodeRank: 46 },
  { name: "mistral-small-3.1-24b", org: "Mistral", elo: 869, rank: 46, votes: 2331, sets: { 80: [41,48], 85: [40,48], 90: [38,48], 95: [37,48] }, boot95: [41,48], codeRank: 44, noncodeRank: 47 },
  { name: "magistral-medium-2506", org: "Mistral", elo: 863, rank: 47, votes: 1993, sets: { 80: [42,48], 85: [41,48], 90: [40,48], 95: [38,48] }, boot95: [43,48], codeRank: 43, noncodeRank: 48 },
  { name: "amazon-nova-pro-v1", org: "Amazon", elo: 857, rank: 48, votes: 4580, sets: { 80: [40,48], 85: [40,48], 90: [38,48], 95: [36,48] }, boot95: [40,48], codeRank: 47, noncodeRank: 45 },
];

const N = 48;
const OC = { Google: "#4285f4", OpenAI: "#10a37f", Anthropic: "#d97706", xAI: "#a855f7", DeepSeek: "#06b6d4", Meta: "#3b82f6", Mistral: "#f97316", Tencent: "#22c55e", Moonshot: "#ec4899", Alibaba: "#ef4444", MiniMax: "#8b5cf6", Cohere: "#14b8a6", Amazon: "#f59e0b" };

function bc(w) { return w <= 8 ? "#22c55e" : w <= 12 ? "#84cc16" : w <= 14 ? "#eab308" : w <= 16 ? "#f97316" : "#ef4444"; }

function Pill({ children, active, onClick }) {
  return <button onClick={onClick} style={{ padding: "5px 12px", fontSize: 12, borderRadius: 6, cursor: "pointer", fontWeight: active ? 600 : 400, border: `1px solid ${active ? "#3b82f6" : "rgba(255,255,255,0.1)"}`, background: active ? "rgba(59,130,246,0.15)" : "rgba(255,255,255,0.03)", color: active ? "#93c5fd" : "#6b7280" }}>{children}</button>;
}

function Badge({ children, color = "#6b7280" }) {
  return <span style={{ fontSize: 10, padding: "2px 6px", borderRadius: 4, background: `${color}18`, color, border: `1px solid ${color}30`, fontWeight: 500 }}>{children}</span>;
}

const ss = { padding: "6px 10px", fontSize: 13, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 6, color: "#e5e7eb", outline: "none", minWidth: 200, cursor: "pointer" };

function CompareView({ alpha }) {
  const [a, setA] = useState("gemini-2.5-pro");
  const [b, setB] = useState("grok-4-0709");
  const mA = ALL_MODELS.find(m => m.name === a) || ALL_MODELS[0];
  const mB = ALL_MODELS.find(m => m.name === b) || ALL_MODELS[2];
  const sA = mA.sets[alpha], sB = mB.sets[alpha];
  const overlap = sA[0] <= sB[1] && sB[0] <= sA[1];
  const oRange = overlap ? [Math.max(sA[0], sB[0]), Math.min(sA[1], sB[1])] : null;
  const lo = Math.min(sA[0], sB[0]) - 1, hi = Math.max(sA[1], sB[1]) + 1, range = hi - lo;

  return (
    <div style={{ background: "rgba(255,255,255,0.02)", borderRadius: 8, padding: 20, border: "1px solid rgba(255,255,255,0.06)" }}>
      <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" }}>
        <select value={a} onChange={e => setA(e.target.value)} style={ss}>{ALL_MODELS.map(m => <option key={m.name} value={m.name}>#{m.rank} {m.name}</option>)}</select>
        <span style={{ color: "#6b7280", alignSelf: "center", fontWeight: 600 }}>vs</span>
        <select value={b} onChange={e => setB(e.target.value)} style={ss}>{ALL_MODELS.map(m => <option key={m.name} value={m.name}>#{m.rank} {m.name}</option>)}</select>
      </div>
      {[mA, mB].map((m, idx) => {
        const s = m.sets[alpha]; const c = idx === 0 ? "#3b82f6" : "#f97316";
        return (
          <div key={m.name} style={{ marginBottom: 10 }}>
            <div style={{ fontSize: 12, color: "#9ca3af", marginBottom: 4, display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: c, fontWeight: 600 }}>#{m.rank} {m.name}</span>
              <span>Elo {m.elo} · [{s[0]}-{s[1]}] · Width {s[1]-s[0]+1}</span>
            </div>
            <div style={{ height: 28, background: "rgba(255,255,255,0.04)", borderRadius: 4, position: "relative" }}>
              <div style={{ position: "absolute", left: `${((s[0]-lo)/range)*100}%`, width: `${((s[1]-s[0]+1)/range)*100}%`, height: "100%", background: c, opacity: 0.35, borderRadius: 4 }} />
              <div style={{ position: "absolute", left: `${((m.rank-lo)/range)*100}%`, top: "50%", transform: "translate(-50%,-50%)", width: 10, height: 10, background: c, borderRadius: "50%", border: "2px solid #fff", zIndex: 2 }} />
            </div>
          </div>
        );
      })}
      {oRange && <div style={{ height: 20, background: "rgba(255,255,255,0.04)", borderRadius: 4, position: "relative", marginTop: 4 }}>
        <div style={{ position: "absolute", left: `${((oRange[0]-lo)/range)*100}%`, width: `${((oRange[1]-oRange[0]+1)/range)*100}%`, height: "100%", background: "rgba(239,68,68,0.3)", borderRadius: 4, border: "1px dashed rgba(239,68,68,0.5)" }} />
        <span style={{ position: "absolute", left: "50%", top: "50%", transform: "translate(-50%,-50%)", fontSize: 10, color: "#ef4444", fontWeight: 600 }}>OVERLAP [{oRange[0]}-{oRange[1]}]</span>
      </div>}
      <div style={{ padding: 14, borderRadius: 6, textAlign: "center", fontSize: 14, fontWeight: 600, marginTop: 12, background: overlap ? "rgba(239,68,68,0.08)" : "rgba(34,197,94,0.08)", border: `1px solid ${overlap ? "rgba(239,68,68,0.2)" : "rgba(34,197,94,0.2)"}`, color: overlap ? "#fca5a5" : "#86efac" }}>
        {overlap ? `Statistically indistinguishable at ${alpha}% coverage.` : `Distinguishable! ${mA.rank < mB.rank ? mA.name : mB.name} is confidently ranked higher.`}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 1, marginTop: 16, fontSize: 12, background: "rgba(255,255,255,0.06)", borderRadius: 6, overflow: "hidden" }}>
        {[["", mA.name, mB.name], ["Elo", mA.elo, mB.elo], ["Rank", `#${mA.rank}`, `#${mB.rank}`], ["CP Set", `[${sA[0]}-${sA[1]}]`, `[${sB[0]}-${sB[1]}]`], ["Width", sA[1]-sA[0]+1, sB[1]-sB[0]+1], ["Votes", mA.votes.toLocaleString(), mB.votes.toLocaleString()], ["Code Rank", `#${mA.codeRank}`, `#${mB.codeRank}`], ["Non-Code", `#${mA.noncodeRank}`, `#${mB.noncodeRank}`]].map((row, i) => row.map((cell, j) => <div key={`${i}-${j}`} style={{ padding: "8px 10px", background: i === 0 ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.3)", color: i === 0 ? "#9ca3af" : j === 0 ? "#6b7280" : "#e5e7eb", fontWeight: i === 0 || j === 0 ? 600 : 400 }}>{cell}</div>))}
      </div>
    </div>
  );
}

function CIView({ alpha }) {
  const top = ALL_MODELS.slice(0, 25);
  return (
    <div>
      <p style={{ fontSize: 13, color: "#6b7280", marginBottom: 16 }}>Red: Arena bootstrap 95% CI. Blue: Conformal {alpha}%. Blue wider = Arena overconfident.</p>
      {top.map(m => {
        const s = m.sets[alpha], b = m.boot95, cpW = (s[1]-s[0]) > (b[1]-b[0]);
        return (
          <div key={m.name} style={{ display: "flex", alignItems: "center", marginBottom: 3 }}>
            <div style={{ width: 155, fontSize: 11, color: "#9ca3af", textAlign: "right", marginRight: 8, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              <span style={{ color: "#6b7280" }}>#{m.rank} </span>{m.name}
            </div>
            <div style={{ flex: 1, height: 20, position: "relative", background: "rgba(255,255,255,0.03)", borderRadius: 3 }}>
              <div style={{ position: "absolute", left: `${((b[0]-1)/N)*100}%`, width: `${((b[1]-b[0]+1)/N)*100}%`, height: "45%", top: 0, background: "#ef4444", opacity: 0.5, borderRadius: 2 }} />
              <div style={{ position: "absolute", left: `${((s[0]-1)/N)*100}%`, width: `${((s[1]-s[0]+1)/N)*100}%`, height: "45%", bottom: 0, background: "#3b82f6", opacity: 0.5, borderRadius: 2 }} />
              <div style={{ position: "absolute", left: `${((m.rank-1)/N)*100}%`, top: "50%", transform: "translate(-50%,-50%)", width: 5, height: 5, background: "#fff", borderRadius: "50%", zIndex: 2 }} />
            </div>
            <div style={{ width: 50, textAlign: "center" }}>{cpW ? <Badge color="#ef4444">wider</Badge> : <Badge color="#22c55e">ok</Badge>}</div>
          </div>
        );
      })}
      <div style={{ display: "flex", gap: 16, marginTop: 12, fontSize: 11, color: "#6b7280" }}>
        <span><span style={{ display: "inline-block", width: 12, height: 6, background: "#ef4444", opacity: 0.5, borderRadius: 1, marginRight: 4 }} />Bootstrap 95%</span>
        <span><span style={{ display: "inline-block", width: 12, height: 6, background: "#3b82f6", opacity: 0.5, borderRadius: 1, marginRight: 4 }} />Conformal {alpha}%</span>
      </div>
    </div>
  );
}

export default function App() {
  const [alpha, setAlpha] = useState(90);
  const [tab, setTab] = useState("leaderboard");
  const [search, setSearch] = useState("");
  const [cat, setCat] = useState("all");
  const [sort, setSort] = useState("rank");
  const [orgF, setOrgF] = useState("all");
  const orgs = useMemo(() => ["all", ..._.uniq(ALL_MODELS.map(m => m.org))], []);

  const models = useMemo(() => {
    let m = [...ALL_MODELS];
    if (search) m = m.filter(x => x.name.toLowerCase().includes(search.toLowerCase()));
    if (orgF !== "all") m = m.filter(x => x.org === orgF);
    if (cat === "code") return m.sort((a, b) => a.codeRank - b.codeRank);
    if (cat === "noncode") return m.sort((a, b) => a.noncodeRank - b.noncodeRank);
    if (sort === "elo") return m.sort((a, b) => b.elo - a.elo);
    if (sort === "width") return m.sort((a, b) => (a.sets[alpha][1]-a.sets[alpha][0]) - (b.sets[alpha][1]-b.sets[alpha][0]));
    if (sort === "votes") return m.sort((a, b) => b.votes - a.votes);
    return m.sort((a, b) => a.rank - b.rank);
  }, [search, cat, sort, orgF, alpha]);

  return (
    <div style={{ background: "#09090b", minHeight: "100vh", color: "#e5e7eb", fontFamily: "'Inter',-apple-system,sans-serif" }}>
      <div style={{ padding: "20px 20px 0", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 2 }}>
          <span style={{ fontSize: 20, fontWeight: 800, color: "#f9fafb", letterSpacing: "-0.04em" }}>Conformal Arena</span>
          <Badge color="#3b82f6">REAL DATA</Badge>
          <span style={{ fontSize: 11, color: "#3f3f46", marginLeft: "auto" }}>135,634 votes · 48 models · by Pingash Vohra</span>
        </div>
        <p style={{ fontSize: 12, color: "#52525b", margin: "4px 0 12px" }}>Distribution-free uncertainty quantification for LLM rankings with formal coverage guarantees</p>
        <div style={{ display: "flex", gap: 0 }}>
          {[["leaderboard","Leaderboard"],["compare","Compare"],["ci","Bootstrap vs CP"],["method","Method"]].map(([k,v]) => (
            <button key={k} onClick={() => setTab(k)} style={{ padding: "8px 14px", fontSize: 12, fontWeight: tab===k?600:400, cursor: "pointer", color: tab===k?"#f9fafb":"#52525b", background: "none", border: "none", borderBottom: tab===k?"2px solid #3b82f6":"2px solid transparent" }}>{v}</button>
          ))}
        </div>
      </div>

      <div style={{ padding: "12px 20px 20px" }}>
        {tab === "leaderboard" && <>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center", marginBottom: 10 }}>
            <span style={{ fontSize: 11, color: "#52525b" }}>Coverage</span>
            {[80,85,90,95].map(a => <Pill key={a} active={alpha===a} onClick={() => setAlpha(a)}>{a}%</Pill>)}
            <div style={{ width: 1, height: 20, background: "rgba(255,255,255,0.08)" }} />
            <span style={{ fontSize: 11, color: "#52525b" }}>Category</span>
            {[["all","All"],["code","Code"],["noncode","Non-Code"]].map(([k,v]) => <Pill key={k} active={cat===k} onClick={() => setCat(k)}>{v}</Pill>)}
            <div style={{ width: 1, height: 20, background: "rgba(255,255,255,0.08)" }} />
            <select value={orgF} onChange={e => setOrgF(e.target.value)} style={{ ...ss, fontSize: 12, padding: "4px 8px", minWidth: 90 }}>{orgs.map(o => <option key={o} value={o}>{o === "all" ? "All Labs" : o}</option>)}</select>
            <input placeholder="Search..." value={search} onChange={e => setSearch(e.target.value)} style={{ padding: "5px 10px", fontSize: 12, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 6, color: "#e5e7eb", outline: "none", width: 130 }} />
          </div>
          <div style={{ display: "flex", gap: 8, marginBottom: 6, fontSize: 11, color: "#52525b" }}>
            <span>Sort:</span>
            {[["rank","Rank"],["elo","Elo"],["width","Narrowest"],["votes","Votes"]].map(([k,v]) => <span key={k} onClick={() => setSort(k)} style={{ cursor: "pointer", color: sort===k?"#93c5fd":"#52525b", fontWeight: sort===k?600:400 }}>{v}</span>)}
          </div>
          <div style={{ display: "flex", padding: "6px 0", borderBottom: "1px solid rgba(255,255,255,0.1)", fontSize: 10, color: "#52525b", textTransform: "uppercase", letterSpacing: "0.06em" }}>
            <div style={{ width: 28, textAlign: "right", marginRight: 6 }}>#</div>
            <div style={{ width: 170 }}>Model</div>
            <div style={{ width: 45, textAlign: "right", marginRight: 8 }}>Elo</div>
            <div style={{ flex: 1 }}>Prediction Set ({alpha}%)</div>
            <div style={{ width: 52, textAlign: "center" }}>Range</div>
            <div style={{ width: 28, textAlign: "center" }}>W</div>
            <div style={{ width: 50, textAlign: "right" }}>Votes</div>
          </div>
          {models.map(m => {
            const s = m.sets[alpha], r = cat==="code"?m.codeRank:cat==="noncode"?m.noncodeRank:m.rank, w = s[1]-s[0]+1, c = bc(w);
            return (
              <div key={m.name} style={{ display: "flex", alignItems: "center", padding: "5px 0", borderBottom: "1px solid rgba(255,255,255,0.04)" }}
                onMouseEnter={e => e.currentTarget.style.background="rgba(255,255,255,0.02)"} onMouseLeave={e => e.currentTarget.style.background="transparent"}>
                <div style={{ width: 28, textAlign: "right", marginRight: 6, fontSize: 12, color: "#52525b", fontWeight: 600 }}>{r}</div>
                <div style={{ width: 170, overflow: "hidden" }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "#e5e7eb", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{m.name}</div>
                  <div style={{ fontSize: 10, color: OC[m.org] || "#6b7280" }}>{m.org}</div>
                </div>
                <div style={{ width: 45, textAlign: "right", marginRight: 8, fontSize: 12, color: "#9ca3af", fontFamily: "monospace" }}>{m.elo}</div>
                <div style={{ flex: 1, height: 20, background: "rgba(255,255,255,0.03)", borderRadius: 4, position: "relative" }}>
                  <div style={{ position: "absolute", left: `${((s[0]-1)/N)*100}%`, width: `${(w/N)*100}%`, height: "100%", background: c, opacity: 0.6, borderRadius: 3, transition: "all 0.3s" }} />
                  <div style={{ position: "absolute", left: `${((r-1)/N)*100}%`, top: "50%", transform: "translate(-50%,-50%)", width: 6, height: 6, background: "#fff", borderRadius: "50%", zIndex: 2 }} />
                </div>
                <div style={{ width: 52, textAlign: "center", fontSize: 10, color: "#6b7280", fontFamily: "monospace" }}>[{s[0]}-{s[1]}]</div>
                <div style={{ width: 28, textAlign: "center", fontSize: 12, color: c, fontWeight: 700 }}>{w}</div>
                <div style={{ width: 50, textAlign: "right", fontSize: 10, color: "#52525b" }}>{m.votes.toLocaleString()}</div>
              </div>
            );
          })}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 8, marginTop: 14 }}>
            {[["100%","Adjacent indistinguishable","at 90% coverage"],["94.6%","Empirical coverage","target: 90%"],["80%","Arena overconfident","vs bootstrap CIs"],["55%","Code more uncertain","q\u0302: 9.88 vs 6.38"]].map(([v,l,s]) => (
              <div key={l} style={{ background: "rgba(255,255,255,0.02)", borderRadius: 6, padding: "10px 12px", border: "1px solid rgba(255,255,255,0.05)" }}>
                <div style={{ fontSize: 18, fontWeight: 700, color: "#f9fafb" }}>{v}</div>
                <div style={{ fontSize: 11, color: "#6b7280" }}>{l}</div>
                <div style={{ fontSize: 10, color: "#3f3f46" }}>{s}</div>
              </div>
            ))}
          </div>
        </>}

        {tab === "compare" && <>
          <h3 style={{ fontSize: 15, fontWeight: 700, color: "#f9fafb", margin: "8px 0" }}>Compare Two Models</h3>
          <p style={{ fontSize: 12, color: "#52525b", marginBottom: 12 }}>If prediction sets overlap, the ranking difference is noise.</p>
          <div style={{ display: "flex", gap: 4, marginBottom: 12 }}>{[80,85,90,95].map(a => <Pill key={a} active={alpha===a} onClick={() => setAlpha(a)}>{a}%</Pill>)}</div>
          <CompareView alpha={alpha} />
        </>}

        {tab === "ci" && <>
          <h3 style={{ fontSize: 15, fontWeight: 700, color: "#f9fafb", margin: "8px 0" }}>Bootstrap CIs vs Conformal Prediction</h3>
          <div style={{ display: "flex", gap: 4, marginBottom: 12 }}>{[80,85,90,95].map(a => <Pill key={a} active={alpha===a} onClick={() => setAlpha(a)}>{a}%</Pill>)}</div>
          <CIView alpha={alpha} />
        </>}

        {tab === "method" && (
          <div style={{ maxWidth: 560, fontSize: 13, lineHeight: 1.8, color: "#a1a1aa" }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: "#f9fafb", marginBottom: 12 }}>How it works</h3>
            <p><strong style={{ color: "#e5e7eb" }}>1. Split</strong> — 98,348 real Arena battles into train (60%) and calibration (40%).</p>
            <p><strong style={{ color: "#e5e7eb" }}>2. Bootstrap</strong> — Resample 100x, compute Elo each time. Predicted rank = median.</p>
            <p><strong style={{ color: "#e5e7eb" }}>3. Calibrate</strong> — Score = |true rank - predicted rank| on held-out data.</p>
            <p><strong style={{ color: "#e5e7eb" }}>4. Threshold</strong> — q̂ at the ⌈(1-α)(1+1/n)⌉ quantile. Finite-sample exact.</p>
            <p><strong style={{ color: "#e5e7eb" }}>5. Predict</strong> — Set = [predicted ± q̂] for each model.</p>
            <div style={{ background: "rgba(59,130,246,0.06)", border: "1px solid rgba(59,130,246,0.15)", borderRadius: 8, padding: "14px 16px", margin: "20px 0" }}>
              <div style={{ fontSize: 15, fontWeight: 700, color: "#60a5fa" }}>P(true_rank ∈ set) ≥ 1 - α</div>
              <p style={{ fontSize: 12, color: "#6b7280", margin: "4px 0 0" }}>Distribution-free. Model-free. Verified at 94.6% (target 90%).</p>
            </div>
            <div style={{ display: "grid", gap: 8, marginTop: 20 }}>
              {[["#ef4444","100% indistinguishable","Every adjacent pair overlaps at 90% coverage."],["#eab308","Code 55% noisier","q̂: 9.88 (code) vs 6.38 (non-code). Single leaderboards mislead."],["#f97316","Rankings drift","Set width grows 47% over time. Some models drop 16 ranks."],["#3b82f6","Arena overconfident","80% of models have wider CP sets than Arena's bootstrap CIs."]].map(([c,t,d]) => (
                <div key={t} style={{ background: "rgba(255,255,255,0.02)", borderRadius: 6, padding: "10px 14px", borderLeft: `3px solid ${c}` }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: c }}>{t}</div>
                  <div style={{ fontSize: 12, color: "#6b7280", marginTop: 2 }}>{d}</div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 24, padding: 12, background: "rgba(255,255,255,0.02)", borderRadius: 6, fontSize: 11, color: "#3f3f46" }}>
              Pingash Vohra · University of Waterloo · LMArena 140K dataset · Angelopoulos & Bates (2021)
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
