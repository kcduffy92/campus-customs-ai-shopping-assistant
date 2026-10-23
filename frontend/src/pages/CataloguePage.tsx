import { useEffect, useState } from "react";
import { useSearchParams } from "react-router";
import ProductCard from "../components/ProductCard.tsx";
import { EmptyState, ErrorMessage, LoadingGrid } from "../components/StatusMessage.tsx";
import { DanPoseImage } from "../components/DanMascot.tsx";
import { fetchFilters, fetchProducts } from "../api.ts";
import { useApi } from "../hooks/useApi.ts";
import type { SortOption } from "../types.ts";

const SORT_LABELS: Record<SortOption, string> = {
  name: "Name (A–Z)",
  price_asc: "Price: low to high",
  price_desc: "Price: high to low",
};

export default function CataloguePage() {
  const [params, setParams] = useSearchParams();
  const category = params.get("category") ?? "";
  const color = params.get("color") ?? "";
  const q = params.get("q") ?? "";
  const inStock = params.get("in_stock") === "true";
  const sortParam = params.get("sort") as SortOption | null;
  const sort: SortOption = sortParam && sortParam in SORT_LABELS ? sortParam : "name";

  const filters = useApi((s) => fetchFilters(s), []);
  const products = useApi((s) => fetchProducts({ category, color, q, inStock, sort }, s), [category, color, q, inStock, sort]);

  // Filters start expanded on desktop and collapsed on phones, so products are visible first.
  const [filtersOpen, setFiltersOpen] = useState(() => window.matchMedia("(min-width: 901px)").matches);

  // Search box updates the URL after a short pause so each keystroke doesn't trigger a request.
  const [search, setSearch] = useState(q);
  useEffect(() => setSearch(q), [q]);
  useEffect(() => {
    if (search.trim() === q) return;
    const t = setTimeout(() => update({ q: search.trim() }), 300);
    return () => clearTimeout(t);
  }, [search]);

  function update(changes: Record<string, string | null>) {
    const next = new URLSearchParams(params);
    for (const [k, v] of Object.entries(changes)) {
      if (v) next.set(k, v);
      else next.delete(k);
    }
    setParams(next, { replace: true });
  }

  const categoryLabel = filters.data?.categories.find((c) => c.slug === category)?.label;
  const colorLabel = filters.data?.colors.find((c) => c.slug === color)?.label;
  const hasFilters = Boolean(category || color || q || inStock);

  return (
    <div className="container catalogue">
      <header className="page-head">
        <p className="eyebrow">Shop</p>
        <h1 className="page-title">{categoryLabel ?? "All products"}</h1>
        <p className="page-lead">
          {products.data
            ? `${products.data.total} ${products.data.total === 1 ? "style" : "styles"}`
            : "Loading styles…"}
          {colorLabel && ` in ${colorLabel.toLowerCase()}`}
          {q && ` matching “${q}”`}
        </p>
      </header>

      <div className="catalogue__layout">
        <aside className="filters" aria-label="Filter products">
          <details
            className="filters__panel"
            open={filtersOpen}
            onToggle={(e) => setFiltersOpen((e.currentTarget as HTMLDetailsElement).open)}
          >
            <summary className="filters__summary">Filters</summary>

            <div className="filters__group">
              <label htmlFor="search" className="filters__label">Search</label>
              <input
                id="search"
                type="search"
                className="input"
                placeholder="e.g. navy, bulldog, quarter-zip"
                maxLength={100}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            <fieldset className="filters__group">
              <legend className="filters__label">Category</legend>
              <div className="chip-list">
                <button type="button" className="chip" aria-pressed={!category} onClick={() => update({ category: null })}>
                  All
                </button>
                {filters.data?.categories.map((c) => (
                  <button
                    key={c.slug}
                    type="button"
                    className="chip"
                    aria-pressed={category === c.slug}
                    onClick={() => update({ category: category === c.slug ? null : c.slug })}
                  >
                    {c.label} <span className="chip__count">{c.count}</span>
                  </button>
                ))}
              </div>
            </fieldset>

            <fieldset className="filters__group">
              <legend className="filters__label">Color</legend>
              <div className="chip-list">
                {filters.data?.colors.map((c) => (
                  <button
                    key={c.slug}
                    type="button"
                    className="chip"
                    aria-pressed={color === c.slug}
                    onClick={() => update({ color: color === c.slug ? null : c.slug })}
                  >
                    <span className={`swatch swatch--${c.slug}`} aria-hidden="true" />
                    {c.label}
                  </button>
                ))}
              </div>
            </fieldset>

            <div className="filters__group">
              <label className="checkbox">
                <input type="checkbox" checked={inStock} onChange={(e) => update({ in_stock: e.target.checked ? "true" : null })} />
                Hide sold-out styles
              </label>
            </div>

            {hasFilters && (
              <button type="button" className="button button--outline button--small" onClick={() => setParams({}, { replace: true })}>
                Clear all filters
              </button>
            )}
          </details>
        </aside>

        <section className="catalogue__results" aria-label="Products">
          <div className="results-bar">
            <label htmlFor="sort" className="results-bar__label">Sort by</label>
            <select id="sort" className="select" value={sort} onChange={(e) => update({ sort: e.target.value === "name" ? null : e.target.value })}>
              {Object.entries(SORT_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>

          {products.error && <ErrorMessage error={products.error} title="Products couldn't load" />}
          {products.loading && !products.data && <LoadingGrid count={9} />}
          {products.data && products.data.total === 0 && (
            <EmptyState title="No styles match those filters">
              <DanPoseImage pose="sniffing" height={120} className="empty-dan" />
              <p>Dan sniffed around but couldn't find a match. Try a different search or clear a filter.</p>
              <button type="button" className="button button--outline button--small" onClick={() => setParams({}, { replace: true })}>
                Clear all filters
              </button>
            </EmptyState>
          )}
          {products.data && products.data.total > 0 && (
            <div className="product-grid" aria-busy={products.loading}>
              {products.data.products.map((p) => (
                <ProductCard key={p.product_id} product={p} />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
