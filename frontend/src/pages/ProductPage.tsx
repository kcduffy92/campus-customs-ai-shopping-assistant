import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import ProductCard from "../components/ProductCard.tsx";
import { ErrorMessage } from "../components/StatusMessage.tsx";
import { ApiError, fetchProduct, fetchProducts } from "../api.ts";
import { useApi } from "../hooks/useApi.ts";
import { capitalize, formatPrice, stockLabel } from "../format.ts";
import { danIcons } from "../brand/dan.ts";
import { hideBrokenImage } from "../components/DanMascot.tsx";
import { openChat } from "../chatEvents.ts";

export default function ProductPage() {
  const { productId = "" } = useParams();
  const { data: product, error, loading } = useApi((s) => fetchProduct(productId, s), [productId]);
  const related = useApi(
    (s) => (product ? fetchProducts({ category: product.category.slug, inStock: true }, s) : Promise.resolve(null)),
    [product?.category.slug],
  );
  const [selectedSize, setSelectedSize] = useState<string | null>(null);

  useEffect(() => setSelectedSize(null), [productId]);

  useEffect(() => {
    if (product) document.title = `${product.display_name} | Campus Customs`;
    return () => {
      document.title = "Campus Customs | Yale Apparel";
    };
  }, [product]);

  if (error) {
    const notFound = error instanceof ApiError && (error.status === 404 || error.status === 422);
    return (
      <div className="container page-narrow">
        <ErrorMessage
          title={notFound ? "We couldn't find that product" : "This product couldn't load"}
          error={notFound ? new Error("It may have been removed, or the link may be mistyped.") : error}
          action={<Link to="/shop" className="button button--primary">Browse all products</Link>}
        />
      </div>
    );
  }

  if (loading || !product) {
    return (
      <div className="container product-page" role="status" aria-live="polite">
        <span className="sr-only">Loading product…</span>
        <div className="skeleton product-page__media-skeleton" />
        <div>
          <div className="skeleton skeleton--line" />
          <div className="skeleton skeleton--line skeleton--short" />
        </div>
      </div>
    );
  }

  const selected = product.sizes.find((s) => s.size === selectedSize) ?? null;
  const relatedProducts = (related.data?.products ?? []).filter((p) => p.product_id !== product.product_id).slice(0, 4);

  return (
    <>
      <div className="container">
        <nav className="breadcrumbs" aria-label="Breadcrumb">
          <ol>
            <li><Link to="/">Home</Link></li>
            <li><Link to="/shop">Shop</Link></li>
            <li><Link to={`/shop?category=${product.category.slug}`}>{product.category.label}</Link></li>
            <li aria-current="page">{product.display_name}</li>
          </ol>
        </nav>
      </div>

      <article className="container product-page">
        <div className="product-page__media">
          <img src={product.image_url} alt={product.display_name} width={900} height={900} />
        </div>

        <div className="product-page__info">
          <p className="eyebrow">{product.category.label}</p>
          <h1 className="product-page__title">{product.display_name}</h1>
          <p className="product-page__price">{formatPrice(product.price)}</p>

          <p className="product-page__description">{product.description}</p>

          <fieldset className="size-picker">
            <legend className="size-picker__legend">
              Size
              {selected && (
                <span className={`size-picker__status size-picker__status--${selected.status}`}>
                  {selected.size}: {stockLabel(selected.status, selected.quantity)}
                  {selected.status === "in_stock" && ` (${selected.quantity} available)`}
                </span>
              )}
            </legend>
            <div className="size-picker__options">
              {product.sizes.map((s) => (
                <button
                  key={s.size}
                  type="button"
                  className={`size-option size-option--${s.status}`}
                  aria-pressed={selectedSize === s.size}
                  disabled={s.status === "sold_out"}
                  onClick={() => setSelectedSize(s.size)}
                  title={stockLabel(s.status, s.quantity)}
                >
                  <span className="size-option__size">{s.size}</span>
                  <span className="size-option__stock">{s.status === "sold_out" ? "Sold out" : `${s.quantity} left`}</span>
                </button>
              ))}
            </div>
            {!product.in_stock && <p className="size-picker__note">This style is currently sold out in every size.</p>}
          </fieldset>

          <div className="product-page__actions">
            {/* Opens the assistant on this page (it already knows which product "this" is); nothing is sent until the shopper presses Send. */}
            <button
              type="button"
              className="button button--primary button--block product-page__ask"
              onClick={() =>
                openChat(selected ? `Is this available in size ${selected.size}?` : "Can you tell me more about this one?")
              }
            >
              <img className="product-page__ask-avatar" src={danIcons.avatar} alt="" width={28} height={28} onError={hideBrokenImage} />
              Ask Handsome Dan about this item
            </button>
            <button type="button" className="button button--outline button--block" disabled>
              Add to bag
            </button>
            <p className="product-page__hint">Online checkout isn't available yet.</p>
          </div>

          <dl className="details-list">
            <div>
              <dt>Style</dt>
              <dd>{capitalize(product.garment_type)}</dd>
            </div>
            <div>
              <dt>Colors</dt>
              <dd className="color-list">
                {product.color_details.map((c) => (
                  <span key={c.name} className="color-pill">
                    <span className={`swatch swatch--${c.family}`} aria-hidden="true" />
                    {capitalize(c.name)}
                  </span>
                ))}
              </dd>
            </div>
            <div>
              <dt>Total in stock</dt>
              <dd>{product.total_stock} across {product.sizes.filter((s) => s.quantity > 0).length} sizes</dd>
            </div>
            <div>
              <dt>Tags</dt>
              <dd className="tag-list">
                {product.search_tags.map((t) => (
                  <Link key={t} to={`/shop?q=${encodeURIComponent(t)}`} className="tag">{t}</Link>
                ))}
              </dd>
            </div>
          </dl>
        </div>
      </article>

      {relatedProducts.length > 0 && (
        <section className="section section--tinted" aria-labelledby="related-heading">
          <div className="container">
            <div className="section__head">
              <h2 id="related-heading" className="section__title">More {product.category.label.toLowerCase()}</h2>
              <Link to={`/shop?category=${product.category.slug}`} className="text-link">View all →</Link>
            </div>
            <div className="product-grid">
              {relatedProducts.map((p) => (
                <ProductCard key={p.product_id} product={p} />
              ))}
            </div>
          </div>
        </section>
      )}
    </>
  );
}
