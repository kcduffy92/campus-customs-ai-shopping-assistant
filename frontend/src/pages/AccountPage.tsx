import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router";
import { useAuth } from "../auth/AuthContext.tsx";
import { DanPoseImage } from "../components/DanMascot.tsx";
import { openChat } from "../chatEvents.ts";

function memberSince(createdAt: string): string {
  // Stored as UTC text "YYYY-MM-DD HH:MM:SS"; show it as a local date.
  const date = new Date(createdAt.replace(" ", "T") + "Z");
  return Number.isNaN(date.getTime())
    ? createdAt
    : date.toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
}

export default function AccountPage() {
  const { user, checking, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [signingOut, setSigningOut] = useState(false);
  const welcome = (location.state as { welcome?: boolean } | null)?.welcome;

  if (checking) {
    return (
      <div className="container page-narrow" role="status" aria-live="polite">
        <span className="sr-only">Loading your account…</span>
        <div className="skeleton skeleton--line" />
        <div className="skeleton skeleton--line skeleton--short" />
      </div>
    );
  }
  // While signing out, wait for the redirect to the homepage instead of bouncing to the sign-in page.
  if (!user) return signingOut ? null : <Navigate to="/account/login" replace state={{ from: "/account" }} />;

  async function onSignOut() {
    setSigningOut(true);
    try {
      await logout();
    } finally {
      navigate("/", { replace: true });
    }
  }

  return (
    <div className="container account">
      {welcome && (
        <div className="form-alert form-alert--success" role="status">
          Your account has been created. Welcome to Campus Customs, {user.first_name}!
        </div>
      )}
      <header className="page-head">
        <p className="eyebrow">My account</p>
        <h1 className="page-title">Hi, {user.first_name}</h1>
        <p className="page-lead">You're signed in as {user.email}.</p>
      </header>

      <div className="account__grid">
        <section className="account__panel" aria-labelledby="details-heading">
          <h2 id="details-heading" className="account__panel-title">Account details</h2>
          <dl className="details-list">
            <div>
              <dt>Name</dt>
              <dd>{`${user.first_name} ${user.last_name}`.trim()}</dd>
            </div>
            <div>
              <dt>Email</dt>
              <dd>{user.email}</dd>
            </div>
            <div>
              <dt>Member since</dt>
              <dd>{memberSince(user.created_at)}</dd>
            </div>
          </dl>
          <button type="button" className="button button--outline account__signout" onClick={onSignOut} disabled={signingOut}>
            {signingOut ? "Signing out…" : "Sign out"}
          </button>
        </section>

        <section className="account__panel account__panel--cream" aria-labelledby="next-heading">
          <DanPoseImage pose="fetching" height={120} className="account__dan" />
          <h2 id="next-heading" className="account__panel-title">Keep shopping</h2>
          <p>Find your next favorite crewneck, hoodie or quarter-zip, or ask Handsome Dan to fetch some ideas.</p>
          <div className="account__actions">
            <Link to="/shop" className="button button--primary">
              Browse the collection
            </Link>
            <button type="button" className="button button--outline" onClick={() => openChat()}>
              Ask Handsome Dan
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
