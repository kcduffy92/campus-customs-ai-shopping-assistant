// Mirrors backend/models.py. Keep the two in sync when the API changes.

export type StockStatus = "in_stock" | "low_stock" | "sold_out";

export interface SizeStock {
  size: string;
  quantity: number;
  status: StockStatus;
}

export interface Category {
  slug: string;
  label: string;
}

export interface ProductSummary {
  product_id: string;
  name: string;
  display_name: string;
  garment_type: string;
  category: Category;
  colors: string[];
  color_families: string[];
  price: number;
  image_url: string;
  sizes: SizeStock[];
  total_stock: number;
  in_stock: boolean;
}

export interface ColorInfo {
  name: string;
  family: string;
}

export interface ProductDetail extends ProductSummary {
  color_details: ColorInfo[];
  description: string;
  search_tags: string[];
}

export interface ProductList {
  total: number;
  products: ProductSummary[];
}

export interface FilterOption {
  slug: string;
  label: string;
  count: number;
  image_url: string | null;
}

export interface CatalogueFilters {
  categories: FilterOption[];
  colors: FilterOption[];
  price_min: number;
  price_max: number;
  total_products: number;
}

export type SortOption = "name" | "price_asc" | "price_desc";

// ---------- Shopping assistant (mirrors ChatRequest / ChatResponse in backend/models.py) ----------

export type ChatRole = "user" | "assistant";

export interface ChatTurn {
  role: ChatRole;
  content: string;
  /** Ids of product cards shown with an earlier assistant reply (lets follow-up questions refer to them). */
  product_ids?: string[];
}

/** The page the customer is on when they send a message. The backend re-verifies the product id. */
export interface PageContext {
  path: string;
  product_id: string | null;
}

export interface ChatRequest {
  message: string;
  /** Only used for signed-out visitors; signed-in customers' context comes from their saved conversation. */
  history: ChatTurn[];
  page: PageContext;
  /** Signed-in customers: the saved conversation to continue, or null to start a new one. */
  conversation_id: number | null;
}

export interface ConversationSummary {
  id: number;
  title: string;
  topics: string[];
  preview: string;
  started_at: string;
  updated_at: string;
  message_count: number;
}

export interface SavedChatMessage {
  id: number;
  role: ChatRole;
  content: string;
  products: ChatProductCard[];
  created_at: string;
}

export interface ChatHistory {
  conversation_id: number | null;
  messages: SavedChatMessage[];
  has_more: boolean;
}

/** Product card shown in the chat. Built by the backend from database rows, never invented by the model. */
export interface ChatProductCard {
  product_id: string;
  name: string;
  category: string;
  price: number;
  image_url: string;
  url: string;
  colors: string[];
  in_stock: boolean;
  available_sizes: string[];
  size: string | null;
  size_quantity: number | null;
  size_status: StockStatus | null;
}

export interface ChatResponse {
  reply: string;
  products: ChatProductCard[];
  saved: boolean;
  conversation_id: number | null;
  user_message_id: number | null;
  message_id: number | null;
}

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  name: string;
  created_at: string;
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface RegisterInput {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  confirm_password: string;
}
