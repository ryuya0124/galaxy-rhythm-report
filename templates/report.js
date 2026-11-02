(() => {
  "use strict";
  const data = JSON.parse(document.getElementById("report-data").textContent);
  const markdown = JSON.parse(
    document.getElementById("markdown-data").textContent,
  );
  const byGame = new Map();
  data.apps.forEach((app) => {
    if (!byGame.has(app.game))
      byGame.set(app.game, { title: app.title, apps: [], windows: [] });
    byGame.get(app.game).apps.push(app);
  });
  data.windows.forEach((row, index) =>
    byGame.get(row.game).windows.push({ ...row, index }),
  );
  const $ = (id) => document.getElementById(id);
  const escape = (value) =>
    String(value).replace(
      /[&<>"']/g,
      (char) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[char],
    );
  const number = (value) =>
    Number(value.toFixed(2)).toLocaleString("en-US", {
      maximumFractionDigits: 2,
    });
  const normalize = (value) =>
    value.normalize("NFKC").toLocaleLowerCase("ja").trim();
  const palette = [
    "#3347ce",
    "#82a341",
    "#c18e4d",
    "#9582bc",
    "#718e91",
    "#b87979",
  ];
  const gameSelect = $("game-select");
  const conditionSelect = $("condition-select");
  function renderTiming() {
    const game = byGame.get(gameSelect.value);
    const row = data.windows[Number(conditionSelect.value)];
    if (!game.windows.length || !row || row.game !== gameSelect.value) {
      $("timing-result").innerHTML =
        `<div class="timing-empty"><h3>共通の固定ms表は掲載していません</h3><p>${escape(game.apps[0].summary)}</p></div>`;
      return;
    }
    const peak = Math.max(...row.early_ms, ...row.late_ms, 1);
    const scale = Math.ceil(peak / 25) * 25;
    const rows = row.grades
      .map((grade, i) => {
        const early = row.early_ms[i];
        const late = row.late_ms[i];
        const start = 50 - (early / scale) * 50;
        const width = ((early + late) / scale) * 50;
        return `<div class="timing-row"><span class="grade-name">${escape(grade)}</span><div class="timing-track" aria-hidden="true"><div class="timing-bar" style="--start:${start}%;--width:${width}%;--bar-color:${palette[i % palette.length]}"></div></div><span class="timing-value"><span class="sr-only">早側</span>−${number(early)}<span class="separator">/</span><span class="sr-only">遅側</span>+${number(late)}</span></div>`;
      })
      .join("");
    $("timing-result").innerHTML =
      `<div class="timing-content"><div class="timing-heading"><div><h3>${escape(row.note)}</h3><p>${escape(row.mode)}</p></div><span class="scale-tag">目盛り ±${number(scale)} ms</span></div><div class="timing-axis" aria-hidden="true"><span>判定</span><div class="axis-labels"><span>−${number(scale)}</span><span>0</span><span>+${number(scale)}</span></div><span>早 / 遅 · ms</span></div>${rows}${row.comment ? `<p class="timing-caution">${escape(row.comment)}</p>` : ""}</div>`;
  }
  function chooseGame(index) {
    const game = byGame.get(gameSelect.value);
    conditionSelect.innerHTML = game.windows.length
      ? game.windows
          .map(
            (row) =>
              `<option value="${row.index}">${escape(row.note)} — ${escape(row.mode)}</option>`,
          )
          .join("")
      : '<option value="">共通の固定表なし</option>';
    conditionSelect.disabled = !game.windows.length;
    if (
      Number.isInteger(index) &&
      game.windows.some((row) => row.index === index)
    )
      conditionSelect.value = String(index);
    renderTiming();
  }
  gameSelect.addEventListener("change", () => chooseGame());
  conditionSelect.addEventListener("change", renderTiming);
  document.querySelectorAll("[data-inspect]").forEach((button) =>
    button.addEventListener("click", () => {
      const index = Number(button.dataset.inspect);
      gameSelect.value = data.windows[index].game;
      chooseGame(index);
      $("inspector").scrollIntoView({
        behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
          ? "instant"
          : "smooth",
        block: "start",
      });
      gameSelect.focus({ preventScroll: true });
    }),
  );
  const cards = [...document.querySelectorAll(".game-card")];
  function filter() {
    const query = normalize($("search").value);
    const category = $("window-filter").value;
    let games = 0;
    let apps = 0;
    cards.forEach((card) => {
      const visible =
        (!query || normalize(card.dataset.search).includes(query)) &&
        (category === "all" || card.dataset.category === category);
      card.hidden = !visible;
      if (visible) {
        games += 1;
        apps += byGame.get(card.dataset.game).apps.length;
      }
    });
    $("result-count").textContent = `${games}ゲーム / ${apps}アプリを表示`;
    $("empty-state").hidden = games !== 0;
  }
  $("search").addEventListener("input", filter);
  $("window-filter").addEventListener("change", filter);
  $("reset-search").addEventListener("click", () => {
    $("search").value = "";
    $("window-filter").value = "all";
    filter();
    $("search").focus();
  });
  document.addEventListener("keydown", (event) => {
    if (
      event.key === "/" &&
      !event.ctrlKey &&
      !event.metaKey &&
      !event.altKey &&
      !["INPUT", "TEXTAREA", "SELECT"].includes(
        document.activeElement.tagName,
      ) &&
      !document.activeElement.isContentEditable
    ) {
      event.preventDefault();
      $("search").focus();
    }
  });
  function saveBlob(content, type, name) {
    const link = document.createElement("a");
    const url = URL.createObjectURL(new Blob([content], { type }));
    link.href = url;
    link.download = name;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
  }
  document.querySelectorAll("[data-download]").forEach((link) =>
    link.addEventListener("click", (event) => {
      if (location.protocol !== "file:") return;
      event.preventDefault();
      const kind = link.dataset.download;
      if (kind === "md")
        saveBlob(markdown, "text/markdown;charset=utf-8", link.download);
      if (kind === "json")
        saveBlob(
          JSON.stringify(data, null, 2) + "\n",
          "application/json;charset=utf-8",
          link.download,
        );
      if (kind === "html")
        saveBlob(
          "<!doctype html>\n" + document.documentElement.outerHTML,
          "text/html;charset=utf-8",
          link.download,
        );
    }),
  );
  gameSelect.value = "holodori";
  chooseGame();
})();
