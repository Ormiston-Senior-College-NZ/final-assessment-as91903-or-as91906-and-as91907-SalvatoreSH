---
name: SafeNet Professional Identity
colors:
  surface: '#f9f9ff'
  surface-dim: '#d8d9e3'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3fd'
  surface-container: '#ecedf7'
  surface-container-high: '#e6e7f2'
  surface-container-highest: '#e1e2ec'
  on-surface: '#191b23'
  on-surface-variant: '#424754'
  inverse-surface: '#2e3038'
  inverse-on-surface: '#eff0fa'
  outline: '#727785'
  outline-variant: '#c2c6d6'
  surface-tint: '#005ac2'
  primary: '#0058be'
  on-primary: '#ffffff'
  primary-container: '#2170e4'
  on-primary-container: '#fefcff'
  inverse-primary: '#adc6ff'
  secondary: '#006c49'
  on-secondary: '#ffffff'
  secondary-container: '#6cf8bb'
  on-secondary-container: '#00714d'
  tertiary: '#924700'
  on-tertiary: '#ffffff'
  tertiary-container: '#b75b00'
  on-tertiary-container: '#fffbff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#adc6ff'
  on-primary-fixed: '#001a42'
  on-primary-fixed-variant: '#004395'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#ffdcc6'
  tertiary-fixed-dim: '#ffb786'
  on-tertiary-fixed: '#311400'
  on-tertiary-fixed-variant: '#723600'
  background: '#f9f9ff'
  on-background: '#191b23'
  surface-variant: '#e1e2ec'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 30px
  title-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.05em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
---

## Brand & Style

The design system is anchored in a **Corporate / Modern** aesthetic, specifically tailored for the cybersecurity sector where clarity and trust are paramount. The visual language avoids alarmist tropes, opting instead for a "composed guardian" persona. It utilizes a refined palette and generous whitespace to reduce cognitive load during high-stakes monitoring tasks.

Key characteristics include:
- **Clarity over Complexity:** Information hierarchy is strictly enforced to ensure critical threats are noticed immediately without overwhelming the user.
- **Precision:** Mathematical spacing and consistent alignment reflect the rigorous nature of data security.
- **Approachability:** Softened corners and subtle transitions make the technical environment feel accessible to both IT professionals and executive stakeholders.

## Colors

The color strategy for this design system utilizes a high-clarity light mode palette to ensure maximum readability. 

- **Foundational Neutrals:** The use of Slate-tinted backgrounds (`#F8FAFC` and `#EEF2F7`) prevents screen glare and provides a sophisticated backdrop that makes white cards "pop" with clear elevation.
- **Semantic Accents:** Colors are used functionally rather than decoratively. Blue (`#3B82F6`) denotes primary actions and system-state information. Green (`#10B981`) signifies "Secure" or "Healthy" states, while Red (`#EF4444`) and Orange (`#F59E0B`) are strictly reserved for alerts and vulnerabilities.
- **Contrast Compliance:** All text-to-background combinations are calibrated to meet WCAG 2.1 AA standards, ensuring the dashboard remains accessible to all users.

## Typography

The design system employs **Inter** for its exceptional legibility in data-heavy interfaces. The typeface features a tall x-height which aids in readability at small sizes, crucial for technical logs and detailed reports.

- **Scale:** A modular scale ensures a clear distinction between data points (labels) and structural headers.
- **Weights:** Use `600` (Semi-Bold) for interactive elements and headers to create a strong visual anchor. Use `400` (Regular) for secondary information and long-form text.
- **Utility:** Micro-labels (`label-md`) use a slight letter-spacing increase and uppercase styling to provide organizational clarity without adding bulk to the UI.

## Layout & Spacing

This design system follows a **12-column fluid grid** for the main dashboard content, allowing cards to reflow based on the screen's real estate.

- **Responsive Strategy:** 
  - **Desktop (1024px+):** 12 columns, 24px gutters. Side navigation is persistent.
  - **Tablet (768px - 1023px):** 6 columns, 16px gutters. Side navigation collapses to an icon-only rail or drawer.
  - **Mobile (Up to 767px):** 1 column or 2 column (small cards), 16px margins.
- **Rhythm:** An 8px base grid governs all padding and margins to maintain vertical and horizontal harmony. Component heights should always be multiples of 8.

## Elevation & Depth

To maintain a clean and professional look, depth is communicated through **Tonal Layers** and **Ambient Shadows**.

1.  **Level 0 (Background):** `#F8FAFC`. The lowest layer.
2.  **Level 1 (Secondary Containers):** `#EEF2F7`. Used for grouping elements within a page, like a sidebar or a header section.
3.  **Level 2 (Cards/Surface):** `#FFFFFF`. The primary surface for content. These utilize a very soft, diffused shadow: `0 4px 6px -1px rgba(30, 41, 59, 0.05), 0 2px 4px -2px rgba(30, 41, 59, 0.05)`.
4.  **Level 3 (Popovers/Modals):** High elevation. Uses a more pronounced shadow to create distinct separation from the dashboard: `0 20px 25px -5px rgba(30, 41, 59, 0.1)`.

Low-contrast outlines (`1px solid #D1D5DB`) are used on all Level 2 elements to ensure structural integrity on high-brightness displays.

## Shapes

The design system uses a **Rounded** shape language to soften the industrial feel of cybersecurity data. 

- **Small Components:** Checkboxes and small tags use `rounded (0.5rem)`.
- **Standard Components:** Buttons and Input fields use `rounded (0.5rem)`.
- **Containers:** Main dashboard cards and modals use `rounded-lg (1rem)` to create a friendly, modern containerized look.
- **Interactive States:** Focus states should mirror the object's border radius with a 2px offset.

## Components

### Buttons
- **Primary:** Background `#3B82F6`, Text `#FFFFFF`. Solid fill.
- **Secondary:** Background `#FFFFFF`, Border `#D1D5DB`, Text `#1E293B`.
- **Danger:** Background `#EF4444`, Text `#FFFFFF`.

### Input Fields
- **Default:** White background, 1px border `#D1D5DB`, placeholder text `#64748B`.
- **Focus:** 1px border `#3B82F6` with a subtle blue outer glow (4px spread, 10% opacity).

### Cards
- White background, 1rem corner radius, 1px border `#D1D5DB`. Use for data visualizations, threat lists, and system health summaries. Internal padding should be `1.5rem` (spacing-lg).

### Status Chips
- Used for "Risk Levels". 
- **High:** Light red background, bold red text. 
- **Normal:** Light green background, bold green text.
- Chips should be pill-shaped with uppercase 12px semi-bold text.

### Data Tables
- Clean, no vertical borders. Horizontal dividers in `#EEF2F7`. Header row uses `#F8FAFC` background with `label-md` typography.

### Progress Indicators
- Smooth, rounded bars using the Secondary Accent (`#10B981`) for success/completion and Primary Accent (`#3B82F6`) for active scanning processes.