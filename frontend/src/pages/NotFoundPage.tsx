import { Link } from "react-router";
import { DanPoseImage } from "../components/DanMascot.tsx";

export default function NotFoundPage() {
  return (
    <div className="container page-narrow">
      <div className="notice notice--cream">
        <DanPoseImage pose="sniffing" height={140} className="empty-dan" />
        <p className="eyebrow">404</p>
        <h1 className="notice__title">This page wandered off campus</h1>
        <p>Handsome Dan sniffed everywhere, but the page you're looking for doesn't exist.</p>
        <div className="hero__actions">
          <Link to="/" className="button button--primary">Go to the homepage</Link>
          <Link to="/shop" className="button button--outline">Browse products</Link>
        </div>
      </div>
    </div>
  );
}
