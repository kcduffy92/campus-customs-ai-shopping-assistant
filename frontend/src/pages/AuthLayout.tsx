import type { ReactNode } from "react";
import { DanMedallion } from "../components/DanMascot.tsx";

/** Shared two-column shell for the sign-in and registration pages (single column on phones). */
export default function AuthLayout({ title, intro, children }: { title: string; intro: ReactNode; children: ReactNode }) {
  return (
    <div className="container auth">
      <div className="auth__card">
        <div className="auth__form-col">
          <p className="eyebrow">Your account</p>
          <h1 className="auth__title">{title}</h1>
          <p className="auth__intro">{intro}</p>
          {children}
        </div>
        <aside className="auth__aside" aria-hidden="true">
          <DanMedallion pose="sitting" size={168} className="auth__art" />
          <p className="auth__aside-title">Campus Customs</p>
          <ul className="auth__perks">
            <li>Keep your details in one place</li>
            <li>Stay signed in on this device for up to 7 days</li>
            <li>Browse 100+ Yale-inspired styles in sizes XS–XXL</li>
          </ul>
        </aside>
      </div>
    </div>
  );
}
