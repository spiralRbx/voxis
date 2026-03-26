const documents = [
  {
    id: "readme",
    title: "Package Overview",
    summary: "Start here for installation, architecture, quickstart examples, path resolution, presets, and the high-level package story.",
    path: "./README.md",
  },
  {
    id: "effects",
    title: "Effects Overview",
    summary: "Read the grouped catalog summary before going deeper into the full callable reference.",
    path: "./docs/EFFECTS.md",
  },
  {
    id: "reference",
    title: "Effect Reference",
    summary: "Full Python callable catalog with signatures, starter calls, clip operations, utilities, and preset helpers.",
    path: "./docs/EFFECT_REFERENCE.md",
  },
  {
    id: "realtime",
    title: "Realtime Guide",
    summary: "Architecture, browser-side API layout, realtime notes, local demo apps, and the relationship between Python and JS paths.",
    path: "./docs/REALTIME.md",
  },
];

const elements = {
  list: document.querySelector("#doc-list"),
  filter: document.querySelector("#doc-filter"),
  title: document.querySelector("#doc-title"),
  summary: document.querySelector("#doc-summary"),
  content: document.querySelector("#doc-content"),
  sourceLink: document.querySelector("#doc-source-link"),
};

const state = {
  activeId: documents[0].id,
  filter: "",
  cache: new Map(),
};

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function parseInline(text) {
  let html = escapeHtml(text);
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  return html;
}

function renderMarkdown(markdown) {
  const lines = markdown.replace(/\r/g, "").split("\n");
  const html = [];
  let paragraph = [];
  let listType = null;
  let inCode = false;
  let codeLines = [];

  const flushParagraph = () => {
    if (!paragraph.length) {
      return;
    }
    html.push(`<p>${parseInline(paragraph.join(" "))}</p>`);
    paragraph = [];
  };

  const closeList = () => {
    if (!listType) {
      return;
    }
    html.push(`</${listType}>`);
    listType = null;
  };

  const flushCode = () => {
    html.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
    codeLines = [];
  };

  for (const rawLine of lines) {
    const line = rawLine ?? "";
    const trimmed = line.trim();

    if (trimmed.startsWith("```")) {
      flushParagraph();
      closeList();
      if (inCode) {
        flushCode();
        inCode = false;
      } else {
        inCode = true;
      }
      continue;
    }

    if (inCode) {
      codeLines.push(line);
      continue;
    }

    if (!trimmed) {
      flushParagraph();
      closeList();
      continue;
    }

    const headingMatch = trimmed.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      flushParagraph();
      closeList();
      const level = headingMatch[1].length;
      html.push(`<h${level}>${parseInline(headingMatch[2])}</h${level}>`);
      continue;
    }

    if (/^-{3,}$/.test(trimmed)) {
      flushParagraph();
      closeList();
      html.push("<hr>");
      continue;
    }

    const unorderedMatch = trimmed.match(/^[-*]\s+(.+)$/);
    if (unorderedMatch) {
      flushParagraph();
      if (listType !== "ul") {
        closeList();
        html.push("<ul>");
        listType = "ul";
      }
      html.push(`<li>${parseInline(unorderedMatch[1])}</li>`);
      continue;
    }

    const orderedMatch = trimmed.match(/^\d+\.\s+(.+)$/);
    if (orderedMatch) {
      flushParagraph();
      if (listType !== "ol") {
        closeList();
        html.push("<ol>");
        listType = "ol";
      }
      html.push(`<li>${parseInline(orderedMatch[1])}</li>`);
      continue;
    }

    paragraph.push(trimmed);
  }

  flushParagraph();
  closeList();

  if (inCode) {
    flushCode();
  }

  return html.join("\n");
}

async function loadDocument(doc) {
  if (state.cache.has(doc.id)) {
    return state.cache.get(doc.id);
  }
  const response = await fetch(doc.path);
  if (!response.ok) {
    throw new Error(`Failed to load ${doc.path}: ${response.status}`);
  }
  const text = await response.text();
  state.cache.set(doc.id, text);
  return text;
}

async function renderDocument(docId) {
  const doc = documents.find((item) => item.id === docId) ?? documents[0];
  state.activeId = doc.id;
  renderDocList();
  elements.title.textContent = doc.title;
  elements.summary.textContent = doc.summary;
  elements.sourceLink.href = doc.path;
  elements.content.innerHTML = '<div class="viewer-empty">Loading document...</div>';

  try {
    const markdown = await loadDocument(doc);
    elements.content.innerHTML = renderMarkdown(markdown);
  } catch (error) {
    console.error(error);
    elements.content.innerHTML = `<div class="viewer-empty">${escapeHtml(String(error.message || error))}</div>`;
  }
}

function renderDocList() {
  const query = state.filter.trim().toLowerCase();
  const filteredDocs = documents.filter((doc) => {
    if (!query) {
      return true;
    }
    return `${doc.title} ${doc.summary}`.toLowerCase().includes(query);
  });

  elements.list.innerHTML = "";
  filteredDocs.forEach((doc) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `doc-button${doc.id === state.activeId ? " active" : ""}`;
    button.innerHTML = `<strong>${doc.title}</strong><span>${doc.summary}</span>`;
    button.addEventListener("click", () => {
      renderDocument(doc.id);
    });
    elements.list.appendChild(button);
  });
}

elements.filter.addEventListener("input", (event) => {
  state.filter = event.target.value;
  renderDocList();
});

renderDocList();
renderDocument(state.activeId);
