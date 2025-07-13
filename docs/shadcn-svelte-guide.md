# shadcn-svelte Implementation Guide

## Overview
This document outlines the implementation of shadcn-svelte components and patterns in the Let's Talk application, including theme management, component usage, and best practices.

## Theme System

### Theme Store (`/lib/stores/theme.ts`)
- **Purpose**: Manages light/dark theme state with localStorage persistence
- **Features**:
  - Automatic theme detection from localStorage
  - Theme toggle functionality
  - HTML class management for theme switching
  - SSR-safe implementation

### Theme Toggle Component (`/lib/components/ThemeToggle.svelte`)
- **Purpose**: Provides a button to toggle between light and dark themes
- **Features**:
  - Visual feedback with Sun/Moon icons
  - Accessible button with proper ARIA labels
  - Integrated with theme store

### Theme Integration
- **Layout**: Theme is initialized in `+layout.svelte` on mount
- **Styling**: CSS variables automatically switch based on `.dark` class
- **Persistence**: Theme preference saved to localStorage

## Component Architecture

### Core Components Used
1. **Button** (`/lib/components/ui/button.svelte`)
   - Variants: default, secondary, destructive, outline, ghost, link
   - Sizes: default, sm, lg, icon
   - Updated to use CSS variables for theming

2. **Input** (`/lib/components/ui/input.svelte`)
   - Auto-theming with CSS variables
   - Proper focus states and accessibility

3. **Card** (`/lib/components/ui/card.svelte`)
   - Semantic container with proper theming
   - Shadow and border management

4. **Alert** (`/lib/components/ui/alert.svelte`)
   - Contextual notifications
   - Variants: default, destructive
   - Icon support for better UX

5. **Badge** (`/lib/components/ui/badge.svelte`)
   - Status indicators
   - Variants: default, secondary, destructive, outline

6. **Switch** (`/lib/components/ui/switch.svelte`)
   - Toggle component for boolean values
   - Accessible and keyboard navigable

7. **Label** (`/lib/components/ui/label.svelte`)
   - Semantic form labeling
   - Proper association with form controls

8. **Separator** (`/lib/components/ui/separator.svelte`)
   - Visual content separation
   - Respects theme colors

9. **AlertDialog** (`/lib/components/ui/alert-dialog.svelte`)
   - Modal confirmation dialogs
   - Proper accessibility with focus management
   - Composable with header, content, and footer

10. **Dropdown Menu** (`/lib/components/ui/dropdown-menu`)
    - Context menus and action lists
    - Keyboard navigation support

11. **Form** (`/lib/components/ui/form`)
    - Form validation and structure
    - Integrated with form libraries

12. **Dialog** (`/lib/components/ui/dialog`)
    - Modal dialogs for complex interactions
    - Backdrop management and focus trapping

## CSS Variables and Theming

### Color System
The application uses CSS variables defined in `app.css`:

```css
:root {
  --background: hsl(0 0% 100%);
  --foreground: hsl(240 10% 3.9%);
  --muted: hsl(240 4.8% 95.9%);
  --muted-foreground: hsl(240 3.8% 46.1%);
  --card: hsl(0 0% 100%);
  --card-foreground: hsl(240 10% 3.9%);
  --border: hsl(240 5.9% 90%);
  --input: hsl(240 5.9% 90%);
  --primary: hsl(240 5.9% 10%);
  --primary-foreground: hsl(0 0% 98%);
  --secondary: hsl(240 4.8% 95.9%);
  --secondary-foreground: hsl(240 5.9% 10%);
  --accent: hsl(240 4.8% 95.9%);
  --accent-foreground: hsl(240 5.9% 10%);
  --destructive: hsl(0 72.2% 50.6%);
  --destructive-foreground: hsl(0 0% 98%);
  --ring: hsl(240 10% 3.9%);
  --sidebar: hsl(0 0% 98%);
  --sidebar-foreground: hsl(240 5.3% 26.1%);
  /* ... more variables */
}

.dark {
  --background: hsl(240 10% 3.9%);
  --foreground: hsl(0 0% 98%);
  /* ... dark theme overrides */
}
```

### Usage in Components
Always use semantic color classes:
- `bg-background` instead of `bg-white`
- `text-foreground` instead of `text-black`
- `text-muted-foreground` instead of `text-gray-500`
- `border-border` instead of `border-gray-200`

## Settings Page Implementation

### Architecture Pattern
The settings page demonstrates best practices:

1. **Semantic Layout**: Using `container`, `space-y-*`, and responsive patterns
2. **Proper Card Usage**: Each settings section in a themed card
3. **Status Indicators**: Using badges for setting states
4. **Form Controls**: Proper input/switch/label associations
5. **Loading States**: Semantic loading indicators
6. **Error Handling**: Contextual alerts with proper icons

### Key Features
- **Responsive Design**: Works on mobile and desktop
- **Accessibility**: Proper ARIA labels and keyboard navigation
- **Visual Feedback**: Clear indication of changes and states
- **Error Handling**: Contextual error messages
- **Loading States**: Professional loading indicators

## Best Practices

### Component Usage
1. **Always use semantic colors** from CSS variables
2. **Prefer composition** over custom styling
3. **Use proper variants** for different contexts
4. **Include accessibility** attributes
5. **Handle loading states** gracefully

### Styling Guidelines
1. **Use CSS variables** for theming
2. **Avoid hardcoded colors** in favor of semantic classes
3. **Maintain consistent spacing** with Tailwind utilities
4. **Use proper typography** scale
5. **Ensure proper contrast** in both themes

### Theme Integration
1. **Initialize theme** in layout
2. **Use theme store** for state management
3. **Apply theme classes** to html element
4. **Handle SSR** with proper checks
5. **Provide theme toggle** in UI

## Adding New Components

### Installation
```bash
cd frontend
pnpm exec shadcn-svelte add [component-name]
```

### Integration Steps
1. **Install component** using CLI
2. **Update imports** in consuming components
3. **Apply theme variables** if needed
4. **Test in both themes** to ensure proper rendering
5. **Document usage** in this guide

## Common Patterns

### Form Fields
```svelte
<div class="space-y-2">
  <Label for="field-id">Field Label</Label>
  <Input id="field-id" type="text" placeholder="Enter value..." />
  <p class="text-sm text-muted-foreground">Help text</p>
</div>
```

### Action Buttons
```svelte
<div class="flex gap-2">
  <Button variant="outline" onclick={cancel}>Cancel</Button>
  <Button onclick={save}>Save</Button>
</div>
```

### Status Indicators
```svelte
<Badge variant={status === 'active' ? 'default' : 'secondary'}>
  {status}
</Badge>
```

### Confirmation Dialogs
```svelte
<AlertDialog open={showDialog} onOpenChange={(open) => showDialog = open}>
  <AlertDialogContent>
    <AlertDialogHeader>
      <AlertDialogTitle>Confirm Action</AlertDialogTitle>
      <AlertDialogDescription>
        Are you sure you want to proceed?
      </AlertDialogDescription>
    </AlertDialogHeader>
    <AlertDialogFooter>
      <Button variant="outline" onclick={cancel}>Cancel</Button>
      <Button variant="destructive" onclick={confirm}>Confirm</Button>
    </AlertDialogFooter>
  </AlertDialogContent>
</AlertDialog>
```

## Future Enhancements

### Planned Components
- **Data Table**: For structured data display
- **Tabs**: For organizing related content
- **Popover**: For contextual information
- **Command**: For command palettes
- **Calendar**: For date selection

### Theme Enhancements
- **Theme variants**: Additional color schemes
- **System theme**: Auto-detection of OS preference
- **Custom themes**: User-defined color schemes
- **Theme persistence**: Server-side theme storage

## Troubleshooting

### Common Issues
1. **Theme not applying**: Check HTML class initialization
2. **Components not themed**: Verify CSS variable usage
3. **Build errors**: Ensure all imports are correct
4. **SSR issues**: Add proper browser checks

### Debug Tips
1. **Check localStorage**: Verify theme persistence
2. **Inspect CSS variables**: Confirm theme switching
3. **Test in both themes**: Ensure proper rendering
4. **Validate accessibility**: Use screen readers

This guide should be updated as new components are added and patterns are established.