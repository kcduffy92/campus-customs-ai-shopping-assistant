import { brand } from "../brand/brand.ts";

export default function Logo({ inverted = false }: { inverted?: boolean }) {
  return (
    <span className={`logo${inverted ? " logo--inverted" : ""}`}>
      {brand.mascot.logoMark ? (
        <img className="logo__mark" src={brand.mascot.logoMark} alt="" />
      ) : (
        <span className="logo__mark logo__mark--placeholder" aria-hidden="true">
          CC
        </span>
      )}
      <span className="logo__text">
        <span className="logo__name">Campus Customs</span>
        <span className="logo__sub">Yale-inspired apparel</span>
      </span>
    </span>
  );
}
