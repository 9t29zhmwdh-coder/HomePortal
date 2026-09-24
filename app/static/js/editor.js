// Edit mode: drag tiles on a fixed-size grid, pick sizes from a list, save the layout.
// Sizes change only through the select, never by dragging an edge, so tiles keep
// the predefined formats the server accepts.
(function () {
  const el = document.getElementById("grid");
  const status = document.getElementById("edit-status");
  const grid = GridStack.init({
    column: Number(el.dataset.columns),
    cellHeight: 110,
    margin: 8,
    float: true,
    disableResize: true,
    handle: ".drag-handle",
    animate: true,
  }, el);

  let dirty = false;
  const markDirty = () => {
    dirty = true;
    status.textContent = el.dataset.msgUnsaved;
  };
  grid.on("change", markDirty);

  el.querySelectorAll(".size-select").forEach((select) => {
    select.addEventListener("change", () => {
      const [w, h] = select.value.split("x").map(Number);
      grid.update(select.closest(".grid-stack-item"), { w, h });
      markDirty();
    });
  });

  async function saveLayout() {
    // save() leaves out values equal to the defaults (x or y 0, w or h 1), the server wants all four.
    const layout = grid.save(false).map(({ id, x = 0, y = 0, w = 1, h = 1 }) => ({ id, x, y, w, h }));
    const response = await fetch(el.dataset.saveUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": el.dataset.csrf },
      body: JSON.stringify(layout),
    });
    if (response.ok) {
      dirty = false;
      status.textContent = el.dataset.msgSaved;
    } else {
      const detail = await response.json().catch(() => ({}));
      status.textContent = el.dataset.msgFailed + (detail.error ? " (" + detail.error + ")" : "");
    }
  }

  document.getElementById("save-layout").addEventListener("click", saveLayout);
  window.addEventListener("beforeunload", (event) => {
    if (dirty) event.preventDefault();
  });
})();
