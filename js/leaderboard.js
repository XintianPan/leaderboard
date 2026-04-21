// CD-Agent leaderboard renderer.
// Loads data/index.json -> data/runs/*.json, renders sortable table,
// per-category chart + per-lab table for the selected row.

const DATA_INDEX = "data/index.json";
const fmtPct = (x) => (x * 100).toFixed(2) + "%";
const fmtMoney = (x) => "$" + Number(x).toFixed(2);
const fmtInt = (x) => Number(x).toLocaleString();

async function loadAll() {
  const idx = await fetch(DATA_INDEX).then(r => r.json());
  const runs = await Promise.all(
    idx.runs.map(name =>
      fetch(`data/runs/${name}.json`).then(r => r.json())
        .then(doc => ({ name, ...doc }))
    )
  );
  runs.sort((a, b) =>
    b.summary.weighted_accuracy - a.summary.weighted_accuracy
  );
  return runs;
}

function renderTable(runs) {
  const tbody = document.querySelector("#leaderboard tbody");
  tbody.innerHTML = "";
  if (!runs.length) {
    tbody.innerHTML = `<tr><td colspan="9" class="empty-hint">No submissions yet.</td></tr>`;
    return;
  }
  runs.forEach((r, i) => {
    const s = r.summary;
    const acc = s.weighted_accuracy;
    const tr = document.createElement("tr");
    tr.dataset.runName = r.name;
    tr.innerHTML = `
      <td class="rank">${i + 1}</td>
      <td><strong>${escapeHtml(s.model)}</strong><br>
          <small style="color:var(--muted)">${escapeHtml(r.submission.run_name)}</small></td>
      <td><span class="pill ${agentPill(s.agent_style)}">${escapeHtml(s.agent_style)}</span></td>
      <td>
        <div class="accuracy-bar">
          <span style="width:${(acc * 100).toFixed(2)}%"></span>
          <label>${fmtPct(acc)}</label>
        </div>
      </td>
      <td class="num">${s.total_points.toFixed(1)} / ${s.total_max_points}</td>
      <td class="num">${fmtMoney(s.total_cost)}</td>
      <td class="num">${fmtInt(s.total_steps)}</td>
      <td>${escapeHtml(s.judge_model)}</td>
      <td>${escapeHtml(r.submission.submitter)}<br>
          <small style="color:var(--muted)">${escapeHtml(r.submission.submitted_at)}</small></td>
    `;
    tr.addEventListener("click", () => selectRun(r, tr));
    tbody.appendChild(tr);
  });
}

function agentPill(style) {
  if (style === "native-tools") return "";
  if (style === "claude-sdk")   return "alt";
  return "neutral";
}

let categoryChart = null;

function selectRun(run, tr) {
  document.querySelectorAll("#leaderboard tbody tr.selected")
    .forEach(x => x.classList.remove("selected"));
  tr.classList.add("selected");

  const s = run.summary;
  document.querySelector("#drilldown-title").textContent =
    `${s.model} — ${run.submission.run_name}`;

  const cats = Object.entries(s.per_category)
    .map(([k, v]) => ({
      name: k,
      acc: v.max_points ? v.points_awarded / v.max_points : 0,
      points: v.points_awarded,
      max: v.max_points,
      n: v.total,
    }))
    .sort((a, b) => b.acc - a.acc);

  const ctx = document.getElementById("category-chart").getContext("2d");
  if (categoryChart) categoryChart.destroy();
  categoryChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: cats.map(c => c.name),
      datasets: [{
        label: "Weighted accuracy",
        data: cats.map(c => c.acc * 100),
        backgroundColor: "#00356b",
        borderColor: "#001f4a",
        borderWidth: 1,
      }],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { beginAtZero: true, max: 100, ticks: { callback: v => v + "%" } },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const c = cats[ctx.dataIndex];
              return `${(c.acc * 100).toFixed(2)}%  —  ${c.points.toFixed(1)}/${c.max} pts (${c.n} q)`;
            },
          },
        },
      },
    },
  });

  const labs = [...s.labs].sort((a, b) =>
    b.weighted_accuracy - a.weighted_accuracy);
  const lbody = document.querySelector("#labs-table tbody");
  lbody.innerHTML = labs.map(l => `
    <tr>
      <td>${escapeHtml(l.scenario_id)}</td>
      <td>${escapeHtml(l.scenario_name)}</td>
      <td class="num">${fmtPct(l.weighted_accuracy)}</td>
      <td class="num">${l.points_awarded.toFixed(1)} / ${l.max_points}</td>
      <td class="num">${l.total_questions}</td>
      <td class="num">${l.total_steps}</td>
      <td class="num">${fmtMoney(l.total_cost)}</td>
    </tr>
  `).join("");

  document.querySelector("#drilldown").style.display = "";
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

loadAll().then(runs => {
  renderTable(runs);
  if (runs.length) {
    const firstRow = document.querySelector("#leaderboard tbody tr");
    selectRun(runs[0], firstRow);
  }
}).catch(err => {
  document.querySelector("#leaderboard tbody").innerHTML =
    `<tr><td colspan="9" class="empty-hint">Failed to load data: ${escapeHtml(err.message)}</td></tr>`;
  console.error(err);
});
