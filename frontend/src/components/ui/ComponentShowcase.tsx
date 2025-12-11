import React from 'react';
import { Typography, Box, Divider } from '@mui/material';
import {
  Button,
  Card,
  Modal,
  LoadingSpinner,
  Alert,
  FormField,
  FormSelect,
  FormCheckbox,
  FormSwitch,
  FormRadioGroup,
  FormContainer,
  Grid,
  GridItem,
  ResponsiveContainer,
  FlexBox,
  useToast,
  StatusBadge,
  NotificationBadge,
  DataTable,
  Pagination,
  SearchInput,
  AdvancedSearch,
  PageLayout,
} from './index';

/**
 * Component showcase for testing and demonstrating the UI library
 * This component is used for development and testing purposes
 */
export function ComponentShowcase() {
  const [modalOpen, setModalOpen] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [formData, setFormData] = React.useState({
    text: '',
    select: '',
    checkbox: false,
    switch: false,
    radio: '',
  });
  const toast = useToast();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    setTimeout(() => {
      setLoading(false);
      toast.showSuccess('Form submitted successfully!');
    }, 2000);
  };

  const selectOptions = [
    { value: 'option1', label: 'Option 1' },
    { value: 'option2', label: 'Option 2' },
    { value: 'option3', label: 'Option 3' },
  ];

  const radioOptions = [
    { value: 'radio1', label: 'Radio Option 1' },
    { value: 'radio2', label: 'Radio Option 2' },
    { value: 'radio3', label: 'Radio Option 3' },
  ];

  return (
    <PageLayout
      title="Component Library Showcase"
      subtitle="This page demonstrates all the components in our UI library with proper accessibility features and responsive design."
      actions={
        <Button variant="outlined" onClick={() => toast.showInfo('Showcase actions!')}>
          Demo Action
        </Button>
      }
    >
      <Box>

        {/* Buttons Section */}
        <Card title="Buttons" sx={{ mb: 4 }}>
          <FlexBox gap={2} wrap="wrap">
            <Button variant="contained" onClick={() => toast.showInfo('Primary button clicked')}>
              Primary Button
            </Button>
            <Button variant="outlined" onClick={() => toast.showWarning('Secondary button clicked')}>
              Secondary Button
            </Button>
            <Button variant="text" onClick={() => toast.showError('Text button clicked')}>
              Text Button
            </Button>
            <Button variant="contained" loading={loading} onClick={() => setLoading(!loading)}>
              {loading ? 'Loading...' : 'Toggle Loading'}
            </Button>
            <Button variant="contained" disabled>
              Disabled Button
            </Button>
          </FlexBox>
        </Card>

        {/* Alerts Section */}
        <Card title="Alerts" sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Alert severity="success" dismissible>
              This is a success alert with dismiss functionality.
            </Alert>
            <Alert severity="info" title="Information">
              This is an info alert with a title.
            </Alert>
            <Alert severity="warning">
              This is a warning alert.
            </Alert>
            <Alert severity="error">
              This is an error alert.
            </Alert>
          </Box>
        </Card>

        {/* Modal Section */}
        <Card title="Modal" sx={{ mb: 4 }}>
          <Button variant="contained" onClick={() => setModalOpen(true)}>
            Open Modal
          </Button>
          
          <Modal
            open={modalOpen}
            onClose={() => setModalOpen(false)}
            title="Example Modal"
            size="medium"
            actions={
              <FlexBox gap={1}>
                <Button variant="outlined" onClick={() => setModalOpen(false)}>
                  Cancel
                </Button>
                <Button variant="contained" onClick={() => setModalOpen(false)}>
                  Confirm
                </Button>
              </FlexBox>
            }
          >
            <Typography>
              This is an example modal with proper accessibility features including
              focus trapping, keyboard navigation, and ARIA labels.
            </Typography>
          </Modal>
        </Card>

        {/* Loading Section */}
        <Card title="Loading States" sx={{ mb: 4 }}>
          <FlexBox gap={4} align="center">
            <LoadingSpinner size="small" message="Small spinner" />
            <LoadingSpinner size="medium" message="Medium spinner" />
            <LoadingSpinner size="large" message="Large spinner" />
          </FlexBox>
        </Card>

        {/* Form Section */}
        <Card title="Form Components" sx={{ mb: 4 }}>
          <FormContainer onSubmit={handleSubmit}>
            <FormField
              label="Text Input"
              value={formData.text}
              onChange={(e) => setFormData({ ...formData, text: e.target.value })}
              helperText="Enter some text here"
              required
            />

            <FormSelect
              label="Select Option"
              value={formData.select}
              onChange={(e) => setFormData({ ...formData, select: e.target.value as string })}
              options={selectOptions}
              helperText="Choose an option from the dropdown"
            />

            <FormCheckbox
              label="Checkbox Option"
              checked={formData.checkbox}
              onChange={(checked) => setFormData({ ...formData, checkbox: checked })}
              helperText="This is a checkbox with helper text"
            />

            <FormSwitch
              label="Switch Option"
              checked={formData.switch}
              onChange={(checked) => setFormData({ ...formData, switch: checked })}
              helperText="This is a switch with helper text"
            />

            <FormRadioGroup
              label="Radio Group"
              value={formData.radio}
              onChange={(value) => setFormData({ ...formData, radio: value })}
              options={radioOptions}
              helperText="Select one option from the radio group"
            />

            <FlexBox gap={2} justify="flex-end">
              <Button type="button" variant="outlined">
                Reset
              </Button>
              <Button type="submit" variant="contained" loading={loading}>
                Submit Form
              </Button>
            </FlexBox>
          </FormContainer>
        </Card>

        {/* Grid Section */}
        <Card title="Responsive Grid" sx={{ mb: 4 }}>
          <Grid spacing={2}>
            <GridItem xs={12} md={4}>
              <Card padding="small">
                <Typography variant="h6">Column 1</Typography>
                <Typography variant="body2">
                  This is the first column in a responsive grid.
                </Typography>
              </Card>
            </GridItem>
            <GridItem xs={12} md={4}>
              <Card padding="small">
                <Typography variant="h6">Column 2</Typography>
                <Typography variant="body2">
                  This is the second column in a responsive grid.
                </Typography>
              </Card>
            </GridItem>
            <GridItem xs={12} md={4}>
              <Card padding="small">
                <Typography variant="h6">Column 3</Typography>
                <Typography variant="body2">
                  This is the third column in a responsive grid.
                </Typography>
              </Card>
            </GridItem>
          </Grid>
        </Card>

        {/* Badge Section */}
        <Card title="Badges and Status Indicators" sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <Box>
              <Typography variant="h6" gutterBottom>Status Badges</Typography>
              <FlexBox gap={1} wrap="wrap">
                <StatusBadge status="won" />
                <StatusBadge status="lost" />
                <StatusBadge status="pending" />
                <StatusBadge status="archived" />
                <StatusBadge status="live" />
              </FlexBox>
            </Box>
            
            <Box>
              <Typography variant="h6" gutterBottom>Notification Badges</Typography>
              <FlexBox gap={2} align="center">
                <NotificationBadge count={5}>
                  <Button variant="outlined">Messages</Button>
                </NotificationBadge>
                <NotificationBadge count={0} showZero>
                  <Button variant="outlined">Alerts</Button>
                </NotificationBadge>
                <NotificationBadge count={99}>
                  <Button variant="outlined">Notifications</Button>
                </NotificationBadge>
              </FlexBox>
            </Box>
          </Box>
        </Card>

        {/* Search Section */}
        <Card title="Search Components" sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <Box>
              <Typography variant="h6" gutterBottom>Basic Search</Typography>
              <SearchInput
                value=""
                onChange={() => {}}
                placeholder="Search wagers..."
              />
            </Box>
            
            <Box>
              <Typography variant="h6" gutterBottom>Advanced Search with Filters</Typography>
              <AdvancedSearch
                searchValue=""
                onSearchChange={() => {}}
                filters={[
                  { id: 'won', label: 'Won', value: 'won', color: 'success' },
                  { id: 'pending', label: 'Pending', value: 'pending', color: 'warning' },
                ]}
                onFiltersChange={() => {}}
                availableFilters={[
                  { id: 'lost', label: 'Lost', value: 'lost', color: 'error' },
                  { id: 'archived', label: 'Archived', value: 'archived' },
                ]}
              />
            </Box>
          </Box>
        </Card>

        {/* Data Table Section */}
        <Card title="Data Table" sx={{ mb: 4 }}>
          <DataTable
            columns={[
              { id: 'id', label: 'ID', minWidth: 50 },
              { id: 'description', label: 'Description', minWidth: 200 },
              { id: 'amount', label: 'Amount', align: 'right', format: (value) => `$${value}` },
              { id: 'status', label: 'Status', format: (value) => <StatusBadge status={value} /> },
            ]}
            data={[
              { id: 1, description: 'Lakers vs Warriors', amount: 100, status: 'won' },
              { id: 2, description: 'Cowboys vs Giants', amount: 50, status: 'pending' },
              { id: 3, description: 'Dodgers vs Padres', amount: 75, status: 'lost' },
            ]}
            selectable
            onRowClick={(row) => toast.showInfo(`Clicked row: ${row.description}`)}
          />
        </Card>

        {/* Pagination Section */}
        <Card title="Pagination" sx={{ mb: 4 }}>
          <Pagination
            currentPage={1}
            totalPages={10}
            pageSize={25}
            totalItems={250}
            onPageChange={() => {}}
            onPageSizeChange={() => {}}
          />
        </Card>

        {/* Toast Section */}
        <Card title="Toast Notifications">
          <FlexBox gap={2} wrap="wrap">
            <Button variant="outlined" onClick={() => toast.showSuccess('Success message!')}>
              Show Success
            </Button>
            <Button variant="outlined" onClick={() => toast.showError('Error message!')}>
              Show Error
            </Button>
            <Button variant="outlined" onClick={() => toast.showWarning('Warning message!')}>
              Show Warning
            </Button>
            <Button variant="outlined" onClick={() => toast.showInfo('Info message!')}>
              Show Info
            </Button>
          </FlexBox>
        </Card>
      </Box>
    </PageLayout>
  );
}