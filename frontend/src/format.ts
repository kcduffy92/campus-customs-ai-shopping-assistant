import type { SizeStock, StockStatus } from "./types";

const usd = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

export const formatPrice = (price: number) => usd.format(price);

export const capitalize = (text: string) => text.replace(/\b\w/g, (c) => c.toUpperCase());

export function stockLabel(status: StockStatus, quantity?: number): string {
  if (status === "sold_out") return "Sold out";
  if (status === "low_stock") return quantity ? `Only ${quantity} left` : "Low stock";
  return "In stock";
}

/** Short availability line for product cards, e.g. "4 of 6 sizes available". */
export function sizeAvailability(sizes: SizeStock[]): string {
  const available = sizes.filter((s) => s.quantity > 0).length;
  if (available === 0) return "Sold out";
  if (available === sizes.length) return "All sizes available";
  return `${available} of ${sizes.length} sizes available`;
}
