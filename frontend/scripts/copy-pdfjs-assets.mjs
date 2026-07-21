import { cp, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const frontendRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const pdfjsRoot = path.join(frontendRoot, "node_modules", "pdfjs-dist");
const publicRoot = path.join(frontendRoot, "public", "pdfjs");

await mkdir(publicRoot, { recursive: true });
await Promise.all([
  cp(path.join(pdfjsRoot, "cmaps"), path.join(publicRoot, "cmaps"), {
    recursive: true,
    force: true,
  }),
  cp(path.join(pdfjsRoot, "standard_fonts"), path.join(publicRoot, "standard_fonts"), {
    recursive: true,
    force: true,
  }),
]);

console.log("PDF.js CMap and standard font assets are ready.");
