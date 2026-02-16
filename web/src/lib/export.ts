import type { Receipt } from "../types";

export function receiptToText(receipt: Receipt): string {
  const lines = [
    `Product: ${receipt.product_name}`,
    `Price: $${receipt.price.toFixed(2)} ${receipt.currency}`,
  ];

  if (receipt.average_rating != null) {
    lines.push(`Rating: ${receipt.average_rating}/5`);
  }
  if (receipt.price_range) {
    lines.push(`Price Range: ${receipt.price_range}`);
  }
  if (receipt.recommendation_reason) {
    lines.push(`Recommendation: ${receipt.recommendation_reason}`);
  }

  if (receipt.comparison_products?.length) {
    lines.push("", "--- Comparison ---");
    for (const p of receipt.comparison_products) {
      lines.push(`  ${p.product_name} — $${p.price.toFixed(2)} ${p.currency}`);
      if (p.average_rating != null) {
        lines.push(`    Rating: ${p.average_rating}/5`);
      }
      if (p.pros?.length) {
        lines.push(`    Pros: ${p.pros.join(", ")}`);
      }
      if (p.cons?.length) {
        lines.push(`    Cons: ${p.cons.join(", ")}`);
      }
    }
    if (receipt.comparison_summary) {
      lines.push("", receipt.comparison_summary);
    }
  }

  return lines.join("\n");
}

export function receiptToJSON(receipt: Receipt): string {
  return JSON.stringify(receipt, null, 2);
}

export function receiptToCSV(receipt: Receipt): string {
  const headers = ["Product Name", "Price", "Currency", "Rating", "Price Range"];
  const rows = [headers.join(",")];

  const escape = (s: string) =>
    s.includes(",") || s.includes('"') ? `"${s.replace(/"/g, '""')}"` : s;

  rows.push(
    [
      escape(receipt.product_name),
      receipt.price.toFixed(2),
      receipt.currency,
      receipt.average_rating != null ? String(receipt.average_rating) : "",
      receipt.price_range ? escape(receipt.price_range) : "",
    ].join(",")
  );

  if (receipt.comparison_products?.length) {
    for (const p of receipt.comparison_products) {
      rows.push(
        [
          escape(p.product_name),
          p.price.toFixed(2),
          p.currency,
          p.average_rating != null ? String(p.average_rating) : "",
          p.price_range ? escape(p.price_range) : "",
        ].join(",")
      );
    }
  }

  return rows.join("\n");
}

export function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
