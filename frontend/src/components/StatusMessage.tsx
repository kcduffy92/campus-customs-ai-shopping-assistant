import type { ReactNode } from "react";

export function LoadingGrid({ count = 8, label = "Loading products" }: { count?: number; label?: string }) {
  return (
    <div className="product-grid" role="status" aria-live="polite">
      <span className="sr-only">{label}…</span>
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="skeleton-card" aria-hidden="true">
          <div className="skeleton skeleton--media" />
          <div className="skeleton skeleton--line" />
          <div className="skeleton skeleton--line skeleton--short" />
        </div>
      ))}
    </div>
  );
}

export function ErrorMessage({ title = "Something went wrong", error, action }: { title?: string; error: Error; action?: ReactNode }) {
  return (
    <div className="notice notice--error" role="alert">
      <h2 className="notice__title">{title}</h2>
      <p>{error.message}</p>
      {action}
    </div>
  );
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="notice">
      <h2 className="notice__title">{title}</h2>
      {children}
    </div>
  );
}
