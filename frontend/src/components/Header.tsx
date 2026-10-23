import { useEffect, useState } from "react";
import { Link, NavLink, useLocation } from "react-router";
import Logo from "./Logo.tsx";
import { useAuth } from "../auth/AuthContext.tsx";

function AccountLink() {
  const { user, checking } = useAuth();
  const { pathname } = useLocation();
  const signedIn = Boolean(user);
  return (
    <Link
      to={signedIn ? "/account" : "/account/login"}
      state={signedIn || pathname.startsWith("/account") ? undefined : { from: pathname }}
      className={`header__account${pathname.startsWith("/account") ? " active" : ""}`}
      aria-label={signedIn ? `My account (${user!.first_name})` : "Sign in"}
      data-checking={checking || undefined}
    >
      <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
        <circle cx="12" cy="8" r="4" fill="none" stroke="currentColor" strokeWidth="1.8" />
        <path d="M4 20c1.5-4 4.5-6 8-6s6.5 2 8 6" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
      <span className="header__account-label">{signedIn ? `Hi, ${user!.first_name}` : "Sign in"}</span>
    </Link>
  );
}

const SHOP_LINKS = [
  { to: "/shop?category=hoodies", label: "Hoodies" },
  { to: "/shop?category=sweatshirts", label: "Crewnecks" },
  { to: "/shop?category=quarter-zips", label: "Quarter-Zips" },
  { to: "/shop?category=t-shirts", label: "Tees" },
  { to: "/shop?category=jackets", label: "Jackets" },
];

export default function Header() {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();

  useEffect(() => setMenuOpen(false), [location.pathname, location.search]);

  const activeCategory = new URLSearchParams(location.search).get("category");

  return (
    <header className="header">
      <div className="announcement">Yale-inspired apparel · Sizes XS–XXL · Up-to-date stock on every style</div>
      <div className="header__bar container">
        <Link to="/" className="header__brand" aria-label="Campus Customs home">
          <Logo />
        </Link>

        <nav id="primary-nav" className="nav" data-open={menuOpen} aria-label="Primary">
          <NavLink to="/" end className="nav__link">
            Home
          </NavLink>
          <NavLink
            to="/shop"
            className={({ isActive }) => `nav__link${isActive && !activeCategory ? " active" : ""}`}
          >
            Shop all
          </NavLink>
          {SHOP_LINKS.map((l) => {
            const slug = new URLSearchParams(l.to.split("?")[1]).get("category");
            const isActive = location.pathname === "/shop" && activeCategory === slug;
            return (
              <Link key={l.to} to={l.to} className={`nav__link${isActive ? " active" : ""}`} aria-current={isActive ? "page" : undefined}>
                {l.label}
              </Link>
            );
          })}
        </nav>

        <div className="header__actions">
          <AccountLink />
          <button
            type="button"
            className="header__menu-toggle"
            aria-expanded={menuOpen}
            aria-controls="primary-nav"
            onClick={() => setMenuOpen((o) => !o)}
          >
            <span className="sr-only">{menuOpen ? "Close menu" : "Open menu"}</span>
            <span className="hamburger" aria-hidden="true" data-open={menuOpen} />
          </button>
        </div>
      </div>
    </header>
  );
}
