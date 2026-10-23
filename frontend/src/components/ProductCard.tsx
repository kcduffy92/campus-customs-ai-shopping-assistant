import { Link } from "react-router";
import type { ProductSummary } from "../types.ts";
import { formatPrice, sizeAvailability } from "../format.ts";

export default function ProductCard({ product }: { product: ProductSummary }) {
  return (
    <article className="product-card">
      <Link to={`/products/${product.product_id}`} className="product-card__link">
        <div className="product-card__media">
          <img src={product.image_url} alt={product.display_name} loading="lazy" width={600} height={600} />
          {!product.in_stock && <span className="badge badge--sold-out product-card__badge">Sold out</span>}
        </div>
        <div className="product-card__body">
          <p className="product-card__category">{product.category.label}</p>
          <h3 className="product-card__name">{product.display_name}</h3>
          <div className="product-card__meta">
            <span className="product-card__price">{formatPrice(product.price)}</span>
            <span className="product-card__sizes">{sizeAvailability(product.sizes)}</span>
          </div>
        </div>
      </Link>
    </article>
  );
}
