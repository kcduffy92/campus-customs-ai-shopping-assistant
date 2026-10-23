# Brand assets

Put the Handsome Dan illustrations, logo marks and animation files here, then wire them up in
`src/brand/brand.ts` (the `mascot` slots). Colors, fonts, radii and shadows are CSS variables in
`src/styles/theme.css`, so they can be re-skinned in one place.

Slots that already exist:

| Slot | Where it appears |
|---|---|
| `mascot.hero` | Homepage hero, right-hand side (`components/Hero.tsx`) |
| `mascot.chatAvatar` | Chat launcher button, chat header, assistant message bubbles (`components/ChatWidget.tsx`) |
| `mascot.logoMark` | Header and footer logo (`components/Logo.tsx`) |
