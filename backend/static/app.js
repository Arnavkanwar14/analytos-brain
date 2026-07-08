const state = {
  activeTab: "products",
  entities: [],
};

async function j(url, opts = {}) {
  const response = await fetch(url, {
    headers: { "content-type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${url}: ${response.status} ${body || ""}`.trim());
  }
  return response.json();
}

function show(id, value) {
  document.getElementById(id).textContent =
    typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

function setStatus(id, message, kind = "muted") {
  const el = document.getElementById(id);
  const baseClass = id === "globalStatus" ? "status-badge" : "status";
  el.className = `${baseClass} ${kind}`;
  el.textContent = message;
}

function setStatusHtml(id, html, kind = "muted") {
  const el = document.getElementById(id);
  const baseClass = id === "globalStatus" ? "status-badge" : "status";
  el.className = `${baseClass} ${kind}`;
  el.innerHTML = html;
}

function formatHostedApproveError(error) {
  const msg = String(error?.message || "");
  const isHosted = window.location.hostname.includes("hf.space");
  const isApprove = msg.includes("/api/runs/") && msg.includes("/approve");
  const isContention =
    msg.toLowerCase().includes("concurrent modification") ||
    msg.toLowerCase().includes("table version");
  if (!(isHosted && isApprove && isContention)) return null;
  return (
    "Hosted Space hit transient merge contention. Please retry once in 2-3 seconds. " +
    'If it still fails, use local fallback: <a href="http://127.0.0.1:8001" target="_blank" rel="noopener noreferrer">open localhost:8001</a> ' +
    "(local governance flow remains source-of-truth)."
  );
}

async function withAction(statusId, label, fn) {
  setStatus(statusId, `${label}...`, "loading");
  setStatus("globalStatus", `${label}...`, "loading");
  try {
    const result = await fn();
    setStatus(statusId, `${label} complete`, "ok");
    setStatus("globalStatus", "Ready", "muted");
    return result;
  } catch (error) {
    const hostedError = formatHostedApproveError(error);
    if (hostedError && statusId === "runsStatus") {
      setStatusHtml(statusId, hostedError, "error");
    } else {
      setStatus(statusId, error.message, "error");
    }
    setStatus("globalStatus", "Action failed", "error");
    throw error;
  }
}

async function loadHealthAndStats() {
  await withAction("healthMsg", "Loading health", async () => {
    const health = await j("/api/health");
    const stats = await j("/api/stats");
    show("health", `status: ${health.status || "ok"}`);
    show("stats", stats);
  });
}

async function loadEntities(kind = state.activeTab) {
  const map = {
    products: "/api/products",
    proof_points: "/api/proof_points",
    features: "/api/features",
    icp: "/api/icp",
    personas: "/api/personas",
  };
  state.activeTab = kind;
  state.entities = await j(map[kind]);
  applyEntityFilter();
}

function applyEntityFilter() {
  const term = document.getElementById("entityFilter").value.trim().toLowerCase();
  if (!term) {
    show("entities", state.entities);
    return;
  }
  const filtered = (state.entities || []).filter((x) =>
    JSON.stringify(x).toLowerCase().includes(term)
  );
  show("entities", filtered);
}

async function loadRecent() {
  const data = await withAction("globalStatus", "Loading recent changes", async () =>
    j("/api/recent?limit=25")
  );
  const branches = document.getElementById("recentBranches");
  const commits = document.getElementById("recentCommits");
  branches.innerHTML = "";
  commits.innerHTML = "";
  for (const e of data.branches || []) {
    const li = document.createElement("li");
    li.textContent = `${e.created_at || "n/a"} | ${e.branch || "n/a"} | status=${e.status || "n/a"} | actor=${e.actor || "n/a"}`;
    branches.appendChild(li);
  }
  for (const e of data.commits || []) {
    const li = document.createElement("li");
    li.textContent = `${e.created_at || "n/a"} | ${e.graph} | actor=${e.actor || "n/a"} | commit=${e.commit || "n/a"}`;
    commits.appendChild(li);
  }
}

async function runSearch() {
  const query = document.getElementById("searchInput").value.trim();
  if (!query) {
    setStatus("searchMeta", "Enter a search query first.", "muted");
    return;
  }
  const data = await withAction("searchMeta", "Running hybrid search", async () =>
    j(`/api/search?q=${encodeURIComponent(query)}&limit=8`)
  );
  setStatus("searchMeta", `engine: ${data.engine || "n/a"} | query: ${data.query}`, "ok");
  const ul = document.getElementById("searchResults");
  ul.innerHTML = "";
  for (const r of data.results || []) {
    const li = document.createElement("li");
    li.textContent = `[${r.graph}/${r.type}] ${r.title} (${r.slug}) :: ${r.snippet || ""}`;
    ul.appendChild(li);
  }
}

function actorRole() {
  return document.getElementById("actorRole").value;
}

async function loadRuns() {
  const data = await withAction("runsStatus", "Loading runs", async () => j("/api/runs"));
  const ul = document.getElementById("runs");
  ul.innerHTML = "";
  for (const run of data.runs || []) {
    const li = document.createElement("li");
    li.className = "run-item";
    li.textContent = `${run.run_id} [${run.status}] branch=${run.branch || "n/a"} docs=${(run.docs || []).join(", ")}`;

    const viewBtn = document.createElement("button");
    viewBtn.className = "btn btn-secondary btn-sm";
    viewBtn.textContent = "Show Diff";
    viewBtn.onclick = () => viewRunDiff(run.run_id, run.branch);

    const approveBtn = document.createElement("button");
    approveBtn.className = "btn btn-primary btn-sm";
    approveBtn.textContent = "Approve & Merge";
    approveBtn.onclick = async () => {
      const result = await withAction("runsStatus", `Approving ${run.run_id}`, async () =>
        j(`/api/runs/${run.run_id}/approve`, {
          method: "POST",
          body: JSON.stringify({ actor_role: actorRole() }),
        })
      );
      if (result?.merge_retried) {
        setStatus(
          "runsStatus",
          `Approved ${run.run_id} after retrying transient merge conflict.`,
          "ok"
        );
      }
      await loadRuns();
      await loadRecent();
    };

    const rejectBtn = document.createElement("button");
    rejectBtn.className = "btn btn-secondary btn-sm";
    rejectBtn.textContent = "Reject / Discard";
    rejectBtn.onclick = async () => {
      await withAction("runsStatus", `Discarding ${run.run_id}`, async () =>
        j(`/api/runs/${run.run_id}/discard`, {
          method: "POST",
          body: JSON.stringify({ actor_role: actorRole() }),
        })
      );
      await loadRuns();
      await loadRecent();
    };

    li.append(" ");
    li.appendChild(viewBtn);
    li.append(" ");
    li.appendChild(approveBtn);
    li.append(" ");
    li.appendChild(rejectBtn);
    ul.appendChild(li);
  }
}

async function viewRunDiff(runId, branch) {
  const url = branch
    ? `/api/runs/${runId}/diff?branch=${encodeURIComponent(branch)}`
    : `/api/runs/${runId}/diff`;
  const data = await withAction("runsStatus", `Loading diff ${runId}`, async () => j(url));
  show("runDetail", data);
}

async function ingestRun() {
  const runId = document.getElementById("ingestRunId").value.trim();
  const docsRaw = document.getElementById("ingestDocs").value.trim();
  const docs = docsRaw ? docsRaw.split(",").map((d) => d.trim()).filter(Boolean) : undefined;
  const useLlm = document.getElementById("ingestUseLlm").checked;
  const payload = { use_llm: useLlm };
  if (runId) payload.run_id = runId;
  if (docs && docs.length) payload.docs = docs;
  const data = await withAction("ingestStatus", "Ingesting to branch", async () =>
    j("/api/ingest", { method: "POST", body: JSON.stringify(payload) })
  );
  const branch = data?.manifest?.branch || `ingest/${data.run_id}`;
  setStatus("ingestStatus", `Created branch ${branch}. Ready for human review.`, "ok");
  show("ingestLog", data.log || data.manifest || data);
  await loadRuns();
  await loadRecent();
}

async function checkRoleScope() {
  const data = await withAction("scopeStatus", "Checking role scope", async () => j("/api/role-scope"));
  const lines = [];
  const matrix = data.matrix || {};
  for (const [role, graphs] of Object.entries(matrix)) {
    lines.push(`${role}:`);
    for (const [graph, info] of Object.entries(graphs)) {
      lines.push(`  - ${graph}: ${info.visible ? "ALLOW" : "DENY"} (rows=${info.row_count || 0})`);
    }
  }
  show("scopeResults", lines.join("\n"));
}

async function runContentAgent() {
  const topic = document.getElementById("contentTopic").value.trim();
  const payload = {};
  if (topic) payload.topic = topic;
  const data = await withAction("agentStatus", "Generating blog draft", async () =>
    j("/api/agents/content-draft", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  );
  show("agentOutput", data.result || data);
}

async function runGtmAgent() {
  const product = document.getElementById("gtmProduct").value.trim();
  const payload = {};
  if (product) payload.product = product;
  const data = await withAction("agentStatus", "Generating prospect brief", async () =>
    j("/api/agents/prospect-brief", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  );
  try {
    show("agentOutput", JSON.parse(data.result || "{}"));
  } catch (_error) {
    show("agentOutput", data.result || data);
  }
}

async function loadGtmProductOptions() {
  const products = await j("/api/products");
  const select = document.getElementById("gtmProduct");
  const current = select.value;
  select.innerHTML = "";
  const defaultOption = document.createElement("option");
  defaultOption.value = "";
  defaultOption.textContent = "Auto-select from approved products (default)";
  select.appendChild(defaultOption);
  for (const product of products || []) {
    const option = document.createElement("option");
    option.value = product.slug || "";
    option.textContent = product.name || product.slug || "Unnamed product";
    select.appendChild(option);
  }
  if (current) select.value = current;
}

async function boot() {
  await loadHealthAndStats();
  await loadEntities("products");
  await loadGtmProductOptions();
  await loadRecent();
  await loadRuns();
  await checkRoleScope();

  document.getElementById("searchBtn").onclick = runSearch;
  document.getElementById("searchInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter") runSearch();
  });
  document.getElementById("entityFilter").addEventListener("input", applyEntityFilter);
  document.getElementById("refreshRuns").onclick = loadRuns;
  document.getElementById("ingestBtn").onclick = ingestRun;
  document.getElementById("scopeBtn").onclick = checkRoleScope;
  document.getElementById("contentAgentBtn").onclick = runContentAgent;
  document.getElementById("gtmAgentBtn").onclick = runGtmAgent;

  for (const tab of document.querySelectorAll(".tab")) {
    tab.onclick = async () => {
      for (const x of document.querySelectorAll(".tab")) x.classList.remove("active");
      tab.classList.add("active");
      await loadEntities(tab.dataset.tab);
    };
  }
}

boot().catch((e) => {
  setStatus("globalStatus", `Failed to load dashboard: ${e.message}`, "error");
});
