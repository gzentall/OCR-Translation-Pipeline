# Flask UI Reference Document

## Login Page

### Layout Measurements
- Container: `min-width: 400px`, `max-width: 500px`, `padding: 48px`, `border-radius: 16px`
- Shadow: `0 4px 12px rgba(0, 0, 0, 0.15)`
- Logo icon size: `48px`
- Title font: headline-medium (28px, weight 400)
- Subtitle font: body-medium (14px)
- Form groups: `margin-bottom: 24px`
- Login actions: `margin-top: 32px`, `gap: 16px`
- Demo note: `padding: 16px`, `border-radius: 8px`, `margin-top: 24px`

### Colors
- Background: `var(--md-sys-color-surface)`
- Container: `var(--md-sys-color-surface-container)`
- Logo: `var(--md-sys-color-primary)`
- Title: `var(--md-sys-color-on-surface)`
- Subtitle: `var(--md-sys-color-on-surface-variant)`
- Demo note bg: `var(--md-sys-color-primary-container)`
- Demo note text: `var(--md-sys-color-on-primary-container)`

### Components
- Text fields: MDC outlined variant, full width
- Button: MDC raised variant, full width
- Logo: Material Icons `local_post_office`

### Interactions
- Auto-focus on username field on load
- Form submission via fetch POST to `/login`
- Redirect on successful login
- Alert on error

## Main App (Browse Page)

### App Bar
**Measurements:**
- Height: `64px`
- Padding: `0 24px`
- Elevation: level 2

**Components:**
- Logo/title
- Search bar: `width: 360px`, `height: 40px`, `border-radius: 20px`
- User menu: Avatar with dropdown
- Material Icons

### Navigation Tabs
**Measurements:**
- Height: `48px`
- Min width per tab: `90px`
- Indicator height: `2px`
- Indicator color: primary

**Tabs:**
1. Documents
2. References  
3. Users (admin only)

### Filter Chips
**Measurements:**
- Height: `32px`
- Gap between chips: `8px`
- Border radius: `8px`

**Filters:**
- Date Range (with dropdown calendar)
- Status (with multi-select dropdown)
- Language (with dropdown)

### Documents Grid
**Measurements:**
- Grid: `display: grid`, `grid-template-columns: repeat(auto-fill, minmax(280px, 1fr))`, `gap: 24px`
- Card: `width: 100%`, `aspect-ratio: 1/1.2`, `border-radius: 12px`, `elevation: 1`
- Thumbnail: `height: 180px`, `object-fit: cover`
- Card content: `padding: 16px`, `gap: 8px`
- Title: `font-size: 16px`, `font-weight: 500`, `line-height: 24px`, max 2 lines
- Metadata: `font-size: 12px`, `color: on-surface-variant`
- Status badge: `padding: 4px 8px`, `border-radius: 4px`, `font-size: 11px`, uppercase

**Hover Effects:**
- Elevation increases to level 2
- Scale: `1.02`
- Transition: `200ms cubic-bezier(0.4, 0, 0.2, 1)`

## Document Editor (3-Column Layout)

### Overall Layout
- Full viewport: `width: 100vw`, `height: 100vh`, `overflow: hidden`
- Header: `height: 64px`, `position: fixed`, `top: 0`, `z-index: 1000`
- Content: `height: calc(100vh - 64px)`, `display: grid`, `grid-template-columns: 1fr 1fr 400px`
- Column gaps: `0px`
- Column dividers: `border-right: 1px solid outline-variant`

### Column 1: Image Viewer
- Background: `surface-variant`
- Padding: `24px`
- Image: `max-width: 100%`, `max-height: 100%`, `object-fit: contain`, `user-select: none`
- Zoom controls: `position: absolute`, `bottom: 16px`, `left: 50%`, `transform: translateX(-50%)`
- Zoom slider: `width: 120px`
- Page controls: `position: absolute`, `top: 50%`, `transform: translateY(-50%)`
- Left/Right buttons: IconButtons, disabled when at edges

### Column 2: Tabbed Editor
- Tabs height: `48px`, `border-bottom: 1px solid outline-variant`
- Tab panels: `padding: 24px`, `height: calc(100% - 48px)`, `overflow-y: auto`
- Form fields: `height: 56px`, `gap: 16px`
- Text areas: `min-height: 120px`, `resize: vertical`
- Toggle switch: `position: absolute`, `top: 16px`, `right: 16px`

### Column 3: Comments Panel
- Comments list: `padding: 16px`, `height: calc(100% - 120px)`, `overflow-y: auto`
- Comment item: `padding: 12px 0`, `border-bottom: 1px solid outline-variant`
- Author: `font-size: 12px`, `font-weight: 500`
- Text: `font-size: 14px`, `margin-top: 4px`
- Time: `font-size: 11px`, `color: on-surface-variant`
- Input area: `position: sticky`, `bottom: 0`, `padding: 16px`, `border-top: 1px solid outline-variant`
- Textarea: `min-height: 56px`, `max-height: 120px`, auto-grow
- Send button: FAB style, `size: small`

### Footer
- Height: `64px`, `position: fixed`, `bottom: 0`, `width: 100%`, `z-index: 1000`
- Background: `surface`, `border-top: 1px solid outline-variant`
- Layout: Flexbox, `justify-content: space-between`, `padding: 0 24px`
- Status buttons: ToggleButtonGroup, joined appearance
- Save button: `variant: contained`, `color: primary`, `height: 40px`

## References List

- List layout: M3 List component, full width
- List item: `height: 72px`, `padding: 8px 16px`, `border-bottom: 1px solid outline-variant`
- Primary text: `font-size: 16px`, `font-weight: 500`
- Secondary text: `font-size: 14px`, `color: on-surface-variant`
- Type badge: Chip, `size: small`, color-coded
- Variant chips: `margin-top: 8px`, `gap: 4px`, `size: small`
- Document count: `font-size: 12px`, right-aligned
- Actions: IconButtons (Edit, Delete), visible on hover

## Users Management

- Table/List layout
- Headers: `font-size: 12px`, `font-weight: 500`, `color: on-surface-variant`, uppercase
- Rows: `height: 56px`, `hover: surface-variant`
- Role badges: Chip, color-coded (SUPER_ADMIN: error, ADMIN: primary, USER: secondary)
- Status indicators: check_circle (active), cancel (inactive)
- Add user FAB: bottom-right corner
- Dialog: `max-width: 600px`

## Color System

### Primary
- main: `#6750A4`
- container: `#D0BCFF`
- on-primary: `#FFFFFF`
- on-container: `#1D1B20`

### Secondary
- main: `#625B71`
- container: `#CCC2DC`

### Tertiary
- main: `#7D5260`
- container: `#EFB8C8`

### Error
- main: `#B3261E`
- container: `#F2B8B5`

### Surface
- main: `#FFFBFE`
- variant: `#E7E0EC`
- on-surface: `#1D1B20`
- on-surface-variant: `#49454F`

### Outline
- main: `#79747E`
- variant: `#E7E0EC`

## Z-Index Hierarchy

1. Main content: `1`
2. Navigation tabs: `2`
3. App bar: `3`
4. Profile dropdown: `1000`
5. Side sheets: `1100`
6. Floating elements: `1300`
7. Modals/Dialogs: `2000`
8. Snackbars: `4000`


