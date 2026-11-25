const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export async function api(path, options = {}) {
  const token = localStorage.getItem("airtel_access_token");
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return response;
}

export async function getJson(path) {
  return (await api(path)).json();
}

export async function downloadReport(format = "csv") {
  const response = await api(`/reports/merchants.${format}`);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `merchant-report.${format}`;
  anchor.click();
  URL.revokeObjectURL(url);
}
