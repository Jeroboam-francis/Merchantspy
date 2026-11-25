import { useEffect, useState } from "react";

export function useApi(loader, dependencies = [], refreshMs = 0) {
  const [state, setState] = useState({ data: null, loading: true, error: "" });
  useEffect(() => {
    let active = true;
    setState((current) => ({ ...current, loading: true, error: "" }));
    async function refresh() {
      try {
        const data = await loader();
        if (active) setState({ data, loading: false, error: "" });
      } catch (error) {
        if (active) setState({ data: null, loading: false, error: error.message });
      }
    }
    void refresh();
    const timer = refreshMs ? window.setInterval(refresh, refreshMs) : null;
    return () => { active = false; if (timer) window.clearInterval(timer); };
  // The dependencies are supplied by each page as stable primitive values.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...dependencies, refreshMs]);
  return state;
}
