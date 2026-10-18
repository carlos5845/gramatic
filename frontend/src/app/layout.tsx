import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GrammarAI - Detección y Corrección Gramatical Inteligente",
  description: "Sistema integral de Detección de Errores con BERT, Corrección Generativa con T5 y Explicaciones Pedagógicas con ERRANT.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" className="h-full">
      <body className="min-h-full bg-slate-50 text-slate-900 antialiased font-sans">
        {children}
      </body>
    </html>
  );
}
