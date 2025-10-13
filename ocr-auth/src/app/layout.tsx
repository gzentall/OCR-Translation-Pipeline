import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import "../styles/tokens.css"
import { SessionProvider } from "@/components/SessionProvider"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "OCR Document System",
  description: "Upload and process PDF documents with OCR and translation",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
      return (
        <html lang="en">
          <head>
            <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet" />
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Flex:wght@100..900&display=swap" rel="stylesheet" />
          </head>
          <body className={inter.className}>
            <SessionProvider>
              {children}
            </SessionProvider>
          </body>
        </html>
      )
}