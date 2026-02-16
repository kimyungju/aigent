"use client";

import type { ProductSummary } from "../types";

interface Props {
  products: ProductSummary[];
  recommendedName: string;
  summary?: string | null;
}

function MiniStars({ rating }: { rating: number }) {
  const full = Math.floor(rating);
  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: 5 }, (_, i) => (
        <svg
          key={i}
          className="h-3 w-3"
          viewBox="0 0 20 20"
          fill={i < full ? "var(--accent)" : "var(--border)"}
        >
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
      ))}
      <span className="ml-1 text-[11px] font-medium" style={{ color: "var(--text-secondary)" }}>
        {rating}
      </span>
    </div>
  );
}

export function ComparisonTable({ products, recommendedName, summary }: Props) {
  return (
    <div
      className="overflow-hidden rounded-xl"
      style={{ border: "1px solid var(--border)", background: "var(--bg-chat)", boxShadow: "var(--shadow-md)" }}
    >
      {/* Header bar */}
      <div className="h-1 gradient-sweep" />

      <div className="p-4">
        <h3
          className="mb-3 text-sm font-semibold uppercase tracking-wider"
          style={{ color: "var(--text-muted)" }}
        >
          Product Comparison
        </h3>

        <div
          className="grid gap-3"
          style={{
            gridTemplateColumns: `repeat(${Math.min(products.length, 3)}, 1fr)`,
          }}
        >
          {products.map((product) => {
            const isRecommended =
              product.product_name.toLowerCase() === recommendedName.toLowerCase();

            return (
              <div
                key={product.product_name}
                className="rounded-lg p-3 transition-all"
                style={{
                  background: isRecommended ? "var(--accent-soft)" : "var(--bg-secondary)",
                  border: isRecommended
                    ? "1.5px solid var(--accent)"
                    : "1px solid var(--border-light)",
                }}
              >
                {isRecommended && (
                  <span
                    className="mb-2 inline-block rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider"
                    style={{ background: "var(--accent)", color: "var(--user-text)" }}
                  >
                    Recommended
                  </span>
                )}

                <h4
                  className="text-sm font-semibold leading-tight"
                  style={{
                    fontFamily: "'Playfair Display', Georgia, serif",
                    color: "var(--text-primary)",
                  }}
                >
                  {product.product_name}
                </h4>

                <div
                  className="mt-2 text-lg font-bold tabular-nums"
                  style={{ color: "var(--accent)" }}
                >
                  ${product.price.toFixed(2)}
                  <span className="ml-1 text-[10px] font-normal" style={{ color: "var(--text-muted)" }}>
                    {product.currency}
                  </span>
                </div>

                {product.average_rating != null && (
                  <div className="mt-1.5">
                    <MiniStars rating={product.average_rating} />
                  </div>
                )}

                {product.price_range && (
                  <div className="mt-1.5 text-[11px]" style={{ color: "var(--text-muted)" }}>
                    Range: {product.price_range}
                  </div>
                )}

                {product.pros && product.pros.length > 0 && (
                  <div className="mt-2">
                    <div className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: "var(--success)" }}>
                      Pros
                    </div>
                    <ul className="mt-0.5 space-y-0.5">
                      {product.pros.map((pro, i) => (
                        <li key={i} className="text-[11px] leading-tight" style={{ color: "var(--text-secondary)" }}>
                          + {pro}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {product.cons && product.cons.length > 0 && (
                  <div className="mt-1.5">
                    <div className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: "var(--warning)" }}>
                      Cons
                    </div>
                    <ul className="mt-0.5 space-y-0.5">
                      {product.cons.map((con, i) => (
                        <li key={i} className="text-[11px] leading-tight" style={{ color: "var(--text-secondary)" }}>
                          - {con}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {summary && (
          <div
            className="mt-3 rounded-lg p-3 text-xs leading-relaxed"
            style={{
              background: "var(--accent-softer)",
              borderLeft: "3px solid var(--accent)",
              color: "var(--text-secondary)",
              fontStyle: "italic",
            }}
          >
            {summary}
          </div>
        )}
      </div>
    </div>
  );
}
