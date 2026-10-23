import { Link } from "react-router";
import { DanPoseImage, hideBrokenImage } from "./DanMascot.tsx";
import { danIcons } from "../brand/dan.ts";

/**
 * Homepage hero. Handsome Dan (sitting pose) sits in a cream medallion with a gold ring, so the pose's cream
 * background reads as part of the badge rather than a rectangle on Yale blue. Shown at or below the artwork's own size.
 */
export default function Hero({ productCount }: { productCount: number | null }) {
  return (
    <section className="hero">
      <div className="container hero__inner">
        <div className="hero__copy">
          <p className="eyebrow eyebrow--light">Campus Customs</p>
          <h1 className="hero__title">Bulldog pride, made to wear.</h1>
          <p className="hero__lead">
            Hoodies, crewnecks, quarter-zips, tees and jackets for Yale students, alumni and fans.
            {productCount ? ` Browse ${productCount} styles` : " Browse every style"} with up-to-date sizes and stock.
          </p>
          <div className="hero__actions">
            <Link to="/shop" className="button button--light">
              Shop the collection
            </Link>
            <Link to="/shop?category=hoodies" className="button button--ghost-light">
              Shop hoodies
            </Link>
          </div>
        </div>
        <div className="hero__art">
          <div className="hero__medallion">
            <DanPoseImage pose="sitting" height={300} eager alt="Handsome Dan, the Campus Customs bulldog, sitting" />
          </div>
          <p className="hero__art-caption">
            <img className="paw-icon paw-icon--light" src={danIcons.pawPrint} alt="" width={18} height={15} onError={hideBrokenImage} />
            Handsome Dan can help you find your fit. Just open the chat.
          </p>
        </div>
      </div>
    </section>
  );
}
