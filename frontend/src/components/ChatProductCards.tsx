import { Link } from "react-router";
import type { ChatProductCard } from "../types.ts";
import { formatPrice } from "../format.ts";

/** One-line availability for a chat card, using the stock the backend read from the inventory table. */
function availability(card: ChatProductCard): { text: string; tone: "ok" | "low" | "out" } {
  if (card.size && card.size_status) {
    if (card.size_status === "sold_out") return { text: `${card.size} sold out`, tone: "out" };
    if (card.size_status === "low_stock") return { text: `${card.size}: only ${card.size_quantity} left`, tone: "low" };
    return { text: `${card.size} in stock`, tone: "ok" };
  }
  if (!card.in_stock) return { text: "Sold out", tone: "out" };
  if (card.available_sizes.length === 6) return { text: "All sizes in stock", tone: "ok" };
  return { text: `Sizes: ${card.available_sizes.join(", ")}`, tone: "ok" };
}

interface Props {
  cards: ChatProductCard[];
  /** Called when a card is opened (the widget closes itself on small screens so the product page is visible). */
  onOpen?: () => void;
}

/** Horizontal, swipeable row of product cards under an assistant message. */
export default function ChatProductCards({ cards, onOpen }: Props) {
  if (!cards.length) return null;
  return (
    <ul className="chat-cards" aria-label={`${cards.length} recommended ${cards.length === 1 ? "product" : "products"}`}>
      {cards.map((card) => {
        const stock = availability(card);
        return (
          <li key={card.product_id} className="chat-card">
            <Link to={card.url} className="chat-card__link" onClick={onOpen}>
              <div className="chat-card__media">
                <img src={card.image_url} alt="" loading="lazy" width={300} height={300} />
              </div>
              <div className="chat-card__body">
                <span className="chat-card__name">{card.name}</span>
                <span className="chat-card__price">{formatPrice(card.price)}</span>
                <span className={`chat-card__stock chat-card__stock--${stock.tone}`}>{stock.text}</span>
              </div>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
