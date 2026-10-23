import { Link } from "react-router";
import Hero from "../components/Hero.tsx";
import ProductCard from "../components/ProductCard.tsx";
import { ErrorMessage, LoadingGrid } from "../components/StatusMessage.tsx";
import { fetchFilters, fetchProducts } from "../api.ts";
import { useApi } from "../hooks/useApi.ts";
import type { ProductSummary } from "../types.ts";
import { danIcons } from "../brand/dan.ts";
import { hideBrokenImage } from "../components/DanMascot.tsx";
import { openChat } from "../chatEvents.ts";

/** Two in-stock styles from each category, so the homepage shows the range of the collection. */
function pickFeatured(products: ProductSummary[], perCategory = 2, max = 8): ProductSummary[] {
  const byCategory = new Map<string, ProductSummary[]>();
  for (const p of products) {
    if (!p.in_stock) continue;
    const list = byCategory.get(p.category.slug) ?? [];
    if (list.length < perCategory) list.push(p);
    byCategory.set(p.category.slug, list);
  }
  return [...byCategory.values()].flat().slice(0, max);
}

export default function HomePage() {
  const filters = useApi((s) => fetchFilters(s), []);
  const products = useApi((s) => fetchProducts({ sort: "price_desc" }, s), []);

  return (
    <>
      <Hero productCount={filters.data?.total_products ?? null} />

      <section className="section container" aria-labelledby="categories-heading">
        <div className="section__head">
          <div>
            <p className="eyebrow">Shop by category</p>
            <h2 id="categories-heading" className="section__title">Find your fit</h2>
          </div>
          <Link to="/shop" className="text-link">View all products →</Link>
        </div>
        {filters.error && <ErrorMessage error={filters.error} title="Categories couldn't load" />}
        <div className="category-grid">
          {filters.loading && !filters.data &&
            Array.from({ length: 6 }, (_, i) => <div key={i} className="skeleton category-tile--skeleton" />)}
          {filters.data?.categories.map((c) => (
            <Link key={c.slug} to={`/shop?category=${c.slug}`} className="category-tile">
              {c.image_url && <img src={c.image_url} alt="" loading="lazy" />}
              <span className="category-tile__label">
                {c.label}
                <span className="category-tile__count">{c.count} styles</span>
              </span>
            </Link>
          ))}
        </div>
      </section>

      <section className="section section--tinted" aria-labelledby="featured-heading">
        <div className="container">
          <div className="section__head">
            <div>
              <p className="eyebrow">Featured</p>
              <h2 id="featured-heading" className="section__title">Styles from across the collection</h2>
            </div>
            <Link to="/shop" className="text-link">Shop everything →</Link>
          </div>
          {products.error && <ErrorMessage error={products.error} title="Products couldn't load" />}
          {products.loading && !products.data && <LoadingGrid count={8} />}
          {products.data && (
            <div className="product-grid">
              {pickFeatured(products.data.products).map((p) => (
                <ProductCard key={p.product_id} product={p} />
              ))}
            </div>
          )}
        </div>
      </section>

      <section className="section container" aria-label="Why shop with us">
        <ul className="value-props">
          <li>
            <img className="value-props__icon" src={danIcons.yCrest} alt="" width={56} height={36} onError={hideBrokenImage} />
            <h3>Every size, every style</h3>
            <p>Most styles come in XS through XXL. Each product page shows exactly which sizes are in stock.</p>
          </li>
          <li>
            <img className="value-props__icon" src={danIcons.pawPrint} alt="" width={42} height={35} onError={hideBrokenImage} />
            <h3>Up-to-date stock</h3>
            <p>Availability comes straight from our inventory, so what you see is what's on the shelf.</p>
          </li>
          <li className="value-props__help">
            <img className="value-props__icon value-props__icon--cookie" src={danIcons.yCookie} alt="" width={40} height={40} onError={hideBrokenImage} />
            <h3>Help when you want it</h3>
            <p>Not sure what to pick? Handsome Dan, our shopping assistant, can sniff out the right style and size.</p>
            <button type="button" className="button button--outline button--small" onClick={() => openChat()}>
              Ask Handsome Dan
            </button>
          </li>
        </ul>
      </section>
    </>
  );
}
