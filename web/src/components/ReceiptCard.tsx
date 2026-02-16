"use client";

import type { Receipt } from "../types";
import { ExportButton } from "./ExportButton";
import { ComparisonTable } from "./ComparisonTable";

interface Props {
  receipt: Receipt;
}

function StarRating({ rating }: { rating: number }) {
  const full = Math.floor(rating);
  const hasHalf = rating - full >= 0.3;
  const stars = [];

  for (let i = 0; i < 5; i++) {
    if (i < full) {
      stars.push(
        <svg
          key={i}
          className="h-4 w-4"
          viewBox="0 0 20 20"
          fill="var(--accent)"
        >
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
      );
    } else if (i === full && hasHalf) {
      stars.push(
        <svg key={i} className="h-4 w-4" viewBox="0 0 20 20">
          <defs>
            <linearGradient id={`half-${i}`}>
              <stop offset="50%" stopColor="var(--accent)" />
              <stop offset="50%" stopColor="#e8e2da" />
            </linearGradient>
          </defs>
          <path
            fill={`url(#half-${i})`}
            d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"
          />
        </svg>
      );
    } else {
      stars.push(
        <svg
          key={i}
          className="h-4 w-4"
          viewBox="0 0 20 20"
          fill="#e8e2da"
        >
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
      );
    }
  }

  return <div className="flex items-center gap-0.5">{stars}</div>;
}

export function ReceiptCard({ receipt }: Props) {
  // If comparison data exists, render the comparison table instead
  if (receipt.comparison_products?.length) {
    return (
      <div>
        <ComparisonTable
          products={receipt.comparison_products}
          recommendedName={receipt.product_name}
          summary={receipt.comparison_summary}
        />
        <div className="mt-2 flex justify-end">
          <ExportButton receipt={receipt} />
        </div>
      </div>
    );
  }

  return (
    <div
      className="overflow-hidden rounded-xl"
      style={{
        border: "1px solid var(--border)",
        background: "var(--bg-chat)",
        boxShadow: "var(--shadow-md)",
      }}
    >
      {/* Animated gradient bar */}
      <div className="gradient-sweep h-[1.5px]" />

      <div className="p-5">
        {/* Label */}
        <span
          className="text-[10px] font-semibold uppercase tracking-[0.15em]"
          style={{ color: "var(--accent)" }}
        >
          Product Recommendation
        </span>

        {/* Product name */}
        <h3
          className="mt-1.5 text-xl font-semibold tracking-tight"
          style={{
            fontFamily: "'Playfair Display', Georgia, serif",
            color: "var(--text-primary)",
          }}
        >
          {receipt.product_name}
        </h3>

        {/* Rating */}
        {receipt.average_rating != null && (
          <div className="mt-2 flex items-center gap-2">
            <StarRating rating={receipt.average_rating} />
            <span
              className="text-sm font-medium"
              style={{ color: "var(--text-secondary)" }}
            >
              {receipt.average_rating.toFixed(1)} / 5.0
            </span>
          </div>
        )}

        {/* Editorial ornament divider */}
        <div className="relative my-4">
          <div
            className="h-px w-full"
            style={{ background: "var(--border-light)" }}
          />
          <div
            className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-1.5 w-1.5 rounded-full"
            style={{ background: "var(--accent)" }}
          />
        </div>

        {/* Price section */}
        <div className="flex items-end justify-between">
          <div>
            <span
              className="text-[10px] font-semibold uppercase tracking-[0.1em]"
              style={{ color: "var(--text-muted)" }}
            >
              Best Price
            </span>
            <div
              className="mt-0.5 text-3xl font-bold tabular-nums"
              style={{
                fontFamily: "'Playfair Display', Georgia, serif",
                color: "var(--accent)",
              }}
            >
              ${receipt.price.toFixed(2)}
              <span
                className="ml-1.5 text-sm font-normal"
                style={{ color: "var(--text-muted)" }}
              >
                {receipt.currency}
              </span>
            </div>
          </div>

          {/* Price range pill */}
          {receipt.price_range && (
            <span
              className="rounded-full px-3 py-1 text-xs font-medium"
              style={{
                background: "var(--accent-softer)",
                color: "var(--accent)",
              }}
            >
              {receipt.price_range}
            </span>
          )}
        </div>

        {/* Recommendation - editor's note style */}
        {receipt.recommendation_reason && (
          <div
            className="mt-4 rounded-lg p-4"
            style={{
              background: "var(--accent-softer)",
              borderLeft: "3px solid var(--accent)",
            }}
          >
            <span
              className="text-[10px] font-semibold uppercase tracking-[0.1em]"
              style={{ color: "var(--accent)" }}
            >
              Our Take
            </span>
            <p
              className="mt-1 text-sm italic leading-relaxed"
              style={{ color: "var(--text-secondary)" }}
            >
              {receipt.recommendation_reason}
            </p>
          </div>
        )}

        {/* Export */}
        <div className="mt-4 flex justify-end">
          <ExportButton receipt={receipt} />
        </div>
      </div>
    </div>
  );
}
