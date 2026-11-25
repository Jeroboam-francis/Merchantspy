import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import networkMark from "../assets/merchant-network.svg";

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@airtel.example");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  if (user) return <Navigate to="/" replace />;
  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try { await login(email, password); navigate("/", { replace: true }); }
    catch (failure) { setError(failure.message); }
    finally { setBusy(false); }
  }
  return (
    <main className="login-page">
      <form className="login-card" onSubmit={submit}>
        <span className="brand-title"><img src={networkMark} alt="" /><span className="brand-mark">airtel</span></span><p className="eyebrow">MERCHANT INTELLIGENCE</p>
        <h1>Welcome back</h1><p className="login-copy">Sign in to your business analytics workspace.</p>
        <label>Email address<input type="email" autoComplete="username" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
        <label>Password<input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
        {error && <p className="inline-error" role="alert">{error}</p>}
        <button className="primary-button login-submit" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
        <small>Use the administrator credentials configured for your API environment.</small>
      </form>
    </main>
  );
}
