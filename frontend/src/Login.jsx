import { useState } from "react";
import { supabase } from "./supabaseClient";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function signIn(event) {
    event.preventDefault();
    setBusy(true);
    setError("");

    const { error: signInError } = await supabase.auth.signInWithPassword({
      email: email.trim(),
      password,
    });

    if (signInError) {
      setError(
        signInError.message === "Invalid login credentials"
          ? "Wrong email or password."
          : signInError.message
      );
    }
    // On success, App.jsx notices the new session and shows the dashboard.
    setBusy(false);
  }

  return (
    <main className="dashboard login-page">
      <section className="login-card">
        <div className="brand">
          <div className="brand-mark">SC</div>
          <div>
            <h1>Supply Chain</h1>
            <p>Inventory &amp; Replenishment Dashboard</p>
          </div>
        </div>

        <h2>Sign in</h2>
        <p className="login-hint">
          Access is limited to approved team members. Ask the administrator
          for an account.
        </p>

        <form onSubmit={signIn} className="login-form">
          <label>
            Email
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>

          {error && (
            <p className="pm-message pm-error" role="alert">
              {error}
            </p>
          )}

          <button type="submit" className="refresh-button" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}

export default Login;
