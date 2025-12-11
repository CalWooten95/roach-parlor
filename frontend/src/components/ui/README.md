# UI Component Library

This directory contains a comprehensive, accessible, and responsive UI component library built with Material-UI and React. All components follow accessibility best practices and support mobile-responsive design.

## Components Overview

### Core Components

#### Button
Enhanced button component with loading states and accessibility features.
```tsx
<Button variant="contained" loading={isLoading} onClick={handleClick}>
  Submit
</Button>
```

#### Card
Flexible card component with optional title, subtitle, and actions.
```tsx
<Card title="Wager Details" actions={<Button>Edit</Button>}>
  <Typography>Card content goes here</Typography>
</Card>
```

#### Modal
Accessible modal with focus trapping and keyboard navigation.
```tsx
<Modal
  open={isOpen}
  onClose={handleClose}
  title="Confirm Action"
  size="medium"
  actions={<Button onClick={handleConfirm}>Confirm</Button>}
>
  <Typography>Are you sure?</Typography>
</Modal>
```

### Status & Feedback Components

#### StatusBadge
Displays wager status with appropriate colors.
```tsx
<StatusBadge status="won" />
<StatusBadge status="pending" />
<StatusBadge status="lost" />
```

#### Alert
Dismissible alerts with different severity levels.
```tsx
<Alert severity="success" dismissible onDismiss={handleDismiss}>
  Wager updated successfully!
</Alert>
```

#### Toast
Global toast notifications via context.
```tsx
const toast = useToast();
toast.showSuccess('Operation completed!');
```

#### LoadingSpinner
Loading indicators with optional messages.
```tsx
<LoadingSpinner size="large" message="Loading wagers..." />
```

### Data Display Components

#### DataTable
Feature-rich data table with sorting, selection, and expansion.
```tsx
<DataTable
  columns={[
    { id: 'description', label: 'Description' },
    { id: 'amount', label: 'Amount', format: (value) => `$${value}` },
    { id: 'status', label: 'Status', format: (value) => <StatusBadge status={value} /> }
  ]}
  data={wagers}
  selectable
  onRowClick={handleRowClick}
  sortBy="amount"
  sortDirection="desc"
  onSort={handleSort}
/>
```

#### Pagination
Comprehensive pagination with page size selection.
```tsx
<Pagination
  currentPage={currentPage}
  totalPages={totalPages}
  pageSize={pageSize}
  totalItems={totalItems}
  onPageChange={setCurrentPage}
  onPageSizeChange={setPageSize}
  showPageSizeSelector
  showItemCount
/>
```

### Form Components

#### FormField
Enhanced text input with accessibility features.
```tsx
<FormField
  label="Wager Description"
  value={description}
  onChange={(e) => setDescription(e.target.value)}
  helperText="Enter a description for your wager"
  required
  error={!!errors.description}
/>
```

#### FormSelect
Accessible select dropdown.
```tsx
<FormSelect
  label="Wager Status"
  value={status}
  onChange={(e) => setStatus(e.target.value)}
  options={[
    { value: 'pending', label: 'Pending' },
    { value: 'won', label: 'Won' },
    { value: 'lost', label: 'Lost' }
  ]}
/>
```

#### SearchInput
Debounced search input with clear functionality.
```tsx
<SearchInput
  value={searchTerm}
  onChange={setSearchTerm}
  placeholder="Search wagers..."
  debounceMs={300}
/>
```

#### AdvancedSearch
Search with filter chips.
```tsx
<AdvancedSearch
  searchValue={searchTerm}
  onSearchChange={setSearchTerm}
  filters={activeFilters}
  onFiltersChange={setActiveFilters}
  availableFilters={[
    { id: 'won', label: 'Won', value: 'won', color: 'success' },
    { id: 'pending', label: 'Pending', value: 'pending', color: 'warning' }
  ]}
/>
```

### Layout Components

#### Grid & FlexBox
Responsive layout components.
```tsx
<Grid spacing={2}>
  <GridItem xs={12} md={6}>
    <Card>Content 1</Card>
  </GridItem>
  <GridItem xs={12} md={6}>
    <Card>Content 2</Card>
  </GridItem>
</Grid>

<FlexBox direction="row" justify="space-between" align="center" gap={2}>
  <Typography>Title</Typography>
  <Button>Action</Button>
</FlexBox>
```

#### PageLayout
Consistent page structure with header and actions.
```tsx
<PageLayout
  title="Wager Management"
  subtitle="Manage your betting activity"
  actions={<Button variant="contained">Add Wager</Button>}
  breadcrumbs={<Breadcrumbs />}
>
  <WagerList />
</PageLayout>
```

#### SidebarLayout
Navigation sidebar with collapsible sections.
```tsx
<SidebarLayout
  sidebarItems={[
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: <DashboardIcon />,
      href: '/dashboard'
    },
    {
      id: 'wagers',
      label: 'Wagers',
      icon: <WagerIcon />,
      children: [
        { id: 'active', label: 'Active', href: '/wagers/active' },
        { id: 'archived', label: 'Archived', href: '/wagers/archived' }
      ]
    }
  ]}
  activeItemId="dashboard"
  onItemClick={handleNavigation}
>
  <PageContent />
</SidebarLayout>
```

## Accessibility Features

All components include:

- **ARIA Labels**: Proper labeling for screen readers
- **Keyboard Navigation**: Full keyboard support
- **Focus Management**: Logical focus order and visible focus indicators
- **Color Contrast**: WCAG AA compliant color combinations
- **Screen Reader Support**: Semantic HTML and ARIA attributes
- **Reduced Motion**: Respects user's motion preferences

## Responsive Design

Components automatically adapt to different screen sizes:

- **Mobile First**: Optimized for mobile devices
- **Breakpoint Aware**: Uses Material-UI breakpoints (xs, sm, md, lg, xl)
- **Touch Friendly**: Minimum 44px touch targets on mobile
- **Flexible Layouts**: Grid and flexbox layouts that reflow

## Theme Integration

All components use the centralized theme system:

```tsx
import { theme } from '../../theme';

// Components automatically inherit:
// - Color palette
// - Typography scale
// - Spacing system
// - Border radius
// - Shadows and elevation
```

## Testing

Components include comprehensive test coverage:

- **Unit Tests**: Individual component functionality
- **Accessibility Tests**: Screen reader and keyboard navigation
- **Responsive Tests**: Different viewport sizes
- **Integration Tests**: Component interactions

Run tests with:
```bash
npm test -- --testPathPattern=components/ui
```

## Usage Guidelines

### Import Components
```tsx
import { Button, Card, DataTable, useToast } from '../components/ui';
```

### Theme Provider
Wrap your app with the theme provider:
```tsx
import { ThemeProvider } from '@mui/material/styles';
import { theme } from './theme';

<ThemeProvider theme={theme}>
  <App />
</ThemeProvider>
```

### Toast Provider
Add toast functionality:
```tsx
import { ToastProvider } from './components/ui';

<ToastProvider>
  <App />
</ToastProvider>
```

## Performance Considerations

- **Code Splitting**: Components can be imported individually
- **Memoization**: Complex components use React.memo where appropriate
- **Virtualization**: Large data tables support virtual scrolling
- **Debouncing**: Search inputs include built-in debouncing
- **Lazy Loading**: Modal and drawer content loads on demand

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

When adding new components:

1. Follow existing patterns and naming conventions
2. Include comprehensive TypeScript types
3. Add accessibility features (ARIA labels, keyboard navigation)
4. Ensure responsive design
5. Write unit tests
6. Update this README
7. Add to ComponentShowcase for visual testing

## Component Showcase

View all components in action:
```tsx
import { ComponentShowcase } from './components/ui/ComponentShowcase';
```

The showcase demonstrates all components with various props and states, making it easy to test visual changes and accessibility features during development.