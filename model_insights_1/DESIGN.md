# Design System Specification: Pothole Intelligence Studio

## 1. Overview & Creative North Star: "The Tactical Overseer"

This design system is built to transform engineering telemetry into an authoritative, mission-critical environment. Our Creative North Star is **The Tactical Overseer**. We are moving away from the "web app" aesthetic toward a "high-fidelity instrumentation" feel. 

The system rejects the standard box-model grid in favor of **Tonal Layering** and **Luminous Depth**. By utilizing high-contrast typography and a "NASA Mission Control" layout philosophy, we prioritize data density without sacrificing elegance. The interface should feel like a piece of high-end hardware—machined, precise, and undeniably professional.

---

## 2. Colors & Surface Philosophy

Our palette is rooted in the deep obsidian of smart-city infrastructure, punctuated by high-visibility functional accents.

### Color Tokens
*   **Core Background:** `#10131a` (The void; the base of the city at night).
*   **Primary Accent:** `#ffc174` / `#f59e0b` (Industrial Amber; used for critical focus).
*   **Secondary Accent:** `#4cd7f6` / `#03b5d3` (Cyan; used for data-flow and scanners).
*   **Severity Spectrum:**
    *   `None`: `#22c55e` (Emerald)
    *   `Shallow`: `#eab308` (Gold)
    *   `Moderate`: `#f97316` (Emergency Orange)
    *   `Deep`: `#ef4444` (High-Alert Red with 20px pulsing glow).

### The "No-Line" Rule
Standard 1px borders are strictly prohibited for layout sectioning. Visual separation must be achieved through **Surface Hierarchy**:
*   **Surface (Base):** `#10131a`
*   **Surface-Container-Low:** `#191b23` (Main dashboard regions).
*   **Surface-Container-Highest:** `#32353d` (Active or interactive cards).

### The "Glass & Gradient" Rule
To achieve the "Studio" aesthetic, all floating panels (modals, pop-overs, dropdowns) must use **Glassmorphism**:
*   **Background:** `surface_container_low` at 70% opacity.
*   **Effect:** `backdrop-filter: blur(12px)`.
*   **Accent:** A subtle linear gradient (Top-Left to Bottom-Right) from `primary` to `primary_container` at 5% opacity across the card face to add "visual soul."

---

## 3. Typography: The Engineering Font Stack

The typography is a deliberate contrast between the technical and the functional.

| Level | Token | Font | Size | Weight | Character Spacing |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Display** | `display-lg` | Space Grotesk | 3.5rem | 700 | -0.02em |
| **Headline** | `headline-md` | Space Grotesk | 1.75rem | 500 | -0.01em |
| **Title** | `title-md` | Inter | 1.125rem | 600 | 0 |
| **Body** | `body-md` | Inter | 0.875rem | 400 | 0 |
| **Metrics** | `label-md` | JetBrains Mono | 0.75rem | 500 | 0.05em |

**Editorial Direction:** Use `display-lg` for single, high-impact numbers (e.g., Total Potholes Repaired). Use `JetBrains Mono` for all coordinate data, timestamps, and sensor IDs to reinforce the "code/engineering" vibe.

---

## 4. Elevation & Depth: Tonal Layering

We avoid traditional drop shadows in favor of **Ambient Light**.

*   **The Layering Principle:** Nested containers should get progressively lighter. A `surface_container_lowest` sidebar sitting on a `surface` background creates a natural recession.
*   **Ambient Shadows:** For floating elements, use an extra-diffused shadow: `box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4)`. The shadow should feel like a soft occlusion, not a dark outline.
*   **The "Ghost Border":** Where containment is required (e.g., table cells), use a "Ghost Border": `outline_variant` at **15% opacity**. Never use 100% opaque lines.
*   **Signature Texture:** All base surfaces should feature a `subtle grid-dot background` (rgba(255,255,255,0.03)) with a 24px spacing to ground the UI in a mapping/CAD context.

---

## 5. Components

### Buttons
*   **Primary:** Solid `primary_container` with `on_primary_container` text. 0.25rem (sm) radius.
*   **Secondary:** Ghost style. Transparent background, `primary` Ghost Border (20% opacity), `primary` text.
*   **States:** Hovering a primary button should trigger a subtle `surface_tint` outer glow.

### Cards & Telemetry Blocks
*   **Constraint:** No divider lines. Separate content using **Vertical White Space** (1.5rem minimum) or a change to `surface_container_high`.
*   **Header:** Title in `label-sm` (uppercase) using `on_surface_variant` (muted) to keep the focus on the data.

### Inputs & Fields
*   **Style:** Underline-only or subtle "Surface-Low" fills. Use `JetBrains Mono` for the input text to maintain the engineering aesthetic.
*   **Error State:** Border becomes `error` with a 4px soft outer glow.

### Custom Component: The "Severity Pulse"
For "Deep" severity pothole markers, use a circular dot with a CSS animation:
`box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);` transitioning to `box-shadow: 0 0 0 15px rgba(239, 68, 68, 0);`.

---

## 6. Do’s and Don’ts

### Do
*   **Do** embrace asymmetry. Allow the map view to take 70% of the screen while telemetry sits in a slim, dense 30% column.
*   **Do** use `secondary` (Cyan) specifically for "Active Scanning" or "AI Processing" states.
*   **Do** use high-contrast typography scales. A small `label-sm` next to a massive `display-lg` creates an expensive, editorial look.

### Don't
*   **Don't** use solid white (#FFFFFF). Always use `on_surface` (#e1e2ec) to prevent eye strain in dark environments.
*   **Don't** use standard 4-way borders. If you must separate, use a single top or left border with a gradient stroke.
*   **Don't** use rounded corners above `0.75rem`. This is an engineering tool; it should feel sharp and precise, not "bubbly" or consumer-grade.