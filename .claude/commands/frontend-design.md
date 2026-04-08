Before writing any JSX or CSS, apply the following design process and principles to the component or page being built.

## Step 1 — Understand context first

Identify:
- **Purpose**: what does this UI element do and what decision does the user make here?
- **Audience**: who is looking at this, under what conditions (e.g. glance-at-a-dashboard vs. careful form input)?
- **Tone**: calm / urgent / playful / utilitarian?
- **Constraints**: existing colour palette, spacing scale, component conventions already in use?

## Step 2 — Choose a deliberate aesthetic direction

Pick a clear direction and commit to it. Do not default to "clean and minimal" unless that is genuinely the right call for the context. Options include but are not limited to:

- Data-dense / utilitarian (appropriate for dashboards read at a glance)
- Calm / ambient (low contrast, muted palette, generous whitespace)
- High-contrast / urgent (bold type, saturated accent, clear hierarchy)
- Warm / domestic (rounded corners, earthy tones, friendly type)

## Step 3 — Typography

- Avoid Inter, Roboto, and Arial as primary display faces — they produce generic output.
- Pair a display/heading face with a legible body face where text hierarchy exists.
- For dashboards, lean toward tabular/monospaced numerals so times and numbers align.
- Establish and reuse a clear type scale (do not set arbitrary `font-size` values inline).

## Step 4 — Colour

- Define a small palette: 1–2 dominant neutrals, 1 primary accent, semantic colours (success/warning/error) that match the existing `delay_colour` system (green / amber / red) where applicable.
- Avoid purple gradients on white — the most clichéd AI-generated palette.
- Ensure sufficient contrast for readability (WCAG AA minimum).

## Step 5 — Layout and space

- Prefer a consistent spacing scale (multiples of 4 px or 8 px).
- Use alignment to create visual order; do not scatter elements randomly.
- For card-based UIs (like TravelCard), keep internal padding consistent across all cards.
- Maps or media thumbnails should have a fixed, predictable aspect ratio.

## Step 6 — Motion (only if appropriate)

- Prefer no animation over animation that adds no meaning.
- If animating: keep duration short (150–300 ms), use ease-out for elements entering, ease-in for elements leaving.
- Never animate layout-affecting properties (width, height, top, left) — use transform and opacity only.

## Step 7 — Implementation standards

- Write the minimum CSS needed; reuse existing classes/variables where they exist.
- Do not add decorative elements that are not present in the design rationale above.
- Match implementation complexity to the aesthetic vision: a restrained design needs precise spacing and typography, not elaborate code.

---

After completing this design process, proceed with implementation.
