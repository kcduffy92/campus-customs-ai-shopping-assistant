import { Link } from "react-router";
import Logo from "./Logo.tsx";
import { brand } from "../brand/brand.ts";
import { danIcons } from "../brand/dan.ts";
import { hideBrokenImage } from "./DanMascot.tsx";

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer__grid">
        <div>
          <Logo inverted />
          <p className="footer__tagline">{brand.tagline}</p>
        </div>
        <nav aria-label="Footer">
          <h2 className="footer__heading">Shop</h2>
          <ul className="footer__links">
            <li><Link to="/shop">All products</Link></li>
            <li><Link to="/shop?category=hoodies">Hoodies</Link></li>
            <li><Link to="/shop?category=sweatshirts">Crewnecks &amp; Sweatshirts</Link></li>
            <li><Link to="/shop?category=t-shirts">T-Shirts</Link></li>
          </ul>
        </nav>
        <div>
          <h2 className="footer__heading">Need help?</h2>
          <p className="footer__text">
            Handsome Dan, our shopping assistant, can help with styles, sizes and stock. Open the chat in the corner.
          </p>
        </div>
      </div>
      <div className="container footer__legal">
        <img className="paw-icon paw-icon--light" src={danIcons.pawPrint} alt="" width={16} height={13} onError={hideBrokenImage} />
        © {new Date().getFullYear()} Campus Customs · Built as a course project for AI Foundations.
      </div>
    </footer>
  );
}
