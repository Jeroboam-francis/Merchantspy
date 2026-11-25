import { configureStore, createSlice } from "@reduxjs/toolkit";

function loadSavedViews() {
  try {
    const saved = JSON.parse(localStorage.getItem("airtel_saved_views") || "[]");
    return Array.isArray(saved) && saved.every((item) => typeof item === "string") ? saved : [];
  }
  catch { return []; }
}

function loadWidgets() {
  const all = ["revenue", "collections", "disbursements", "activity"];
  try {
    const saved = JSON.parse(localStorage.getItem("airtel_dashboard_widgets") || "null");
    return Array.isArray(saved) ? saved.filter((item) => all.includes(item)) : all;
  } catch { return all; }
}

const viewSlice = createSlice({
  name: "view",
  initialState: { range: "30d", search: "", savedViews: loadSavedViews(), widgets: loadWidgets() },
  reducers: {
    setRange: (state, action) => { state.range = action.payload; },
    setSearch: (state, action) => { state.search = action.payload; },
    saveView: (state, action) => {
      if (!state.savedViews.includes(action.payload)) state.savedViews.push(action.payload);
    },
    removeView: (state, action) => {
      state.savedViews = state.savedViews.filter((view) => view !== action.payload);
    },
    setWidget: (state, action) => {
      const { name, enabled } = action.payload;
      state.widgets = enabled ? [...new Set([...state.widgets, name])] : state.widgets.filter((widget) => widget !== name);
    },
  },
});

export const { setRange, setSearch, saveView, removeView, setWidget } = viewSlice.actions;
const persistSavedViews = () => (next) => (action) => {
  const result = next(action);
  if (action.type === saveView.type || action.type === removeView.type) {
    localStorage.setItem("airtel_saved_views", JSON.stringify(store.getState().view.savedViews));
  }
  if (action.type === setWidget.type) {
    localStorage.setItem("airtel_dashboard_widgets", JSON.stringify(store.getState().view.widgets));
  }
  return result;
};
export const store = configureStore({ reducer: { view: viewSlice.reducer }, middleware: (getDefault) => getDefault().concat(persistSavedViews) });
