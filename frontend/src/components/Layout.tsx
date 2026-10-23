import { useEffect } from "react";
import { Outlet, useLocation } from "react-router";
import Header from "./Header.tsx";
import Footer from "./Footer.tsx";
import ChatWidget from "./ChatWidget.tsx";

export default function Layout() {
  const { pathname } = useLocation();

  // Start each new page at the top (filter changes on /shop keep their scroll position).
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  return (
    <div className="app">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <Header />
      <main id="main" className="main" tabIndex={-1}>
        <Outlet />
      </main>
      <Footer />
      {/* Rendered once in the layout so the conversation survives page navigation. */}
      <ChatWidget />
    </div>
  );
}
