import React from 'react';
import {
  Box,
  TextField,
  TextFieldProps,
  FormControl,
  FormLabel,
  FormHelperText,
  Select,
  SelectProps,
  MenuItem,
  Checkbox,
  FormControlLabel,
  Switch,
  RadioGroup,
  Radio,
  InputLabel,
} from '@mui/material';

// Enhanced TextField with better accessibility
export interface FormFieldProps extends Omit<TextFieldProps, 'error'> {
  error?: boolean;
  helperText?: string;
}

export function FormField({ error, helperText, ...props }: FormFieldProps) {
  const fieldId = props.id || `field-${Math.random().toString(36).substr(2, 9)}`;
  const helperTextId = helperText ? `${fieldId}-helper` : undefined;

  return (
    <TextField
      {...props}
      id={fieldId}
      error={error}
      helperText={helperText}
      aria-describedby={helperTextId}
      sx={{
        mb: 2,
        ...props.sx,
      }}
    />
  );
}

// Enhanced Select with better accessibility
export interface FormSelectProps extends Omit<SelectProps, 'error'> {
  label: string;
  error?: boolean;
  helperText?: string;
  options: Array<{ value: string | number; label: string; disabled?: boolean }>;
}

export function FormSelect({
  label,
  error,
  helperText,
  options,
  ...props
}: FormSelectProps) {
  const fieldId = props.id || `select-${Math.random().toString(36).substr(2, 9)}`;
  const helperTextId = helperText ? `${fieldId}-helper` : undefined;
  const labelId = `${fieldId}-label`;

  return (
    <FormControl fullWidth error={error} sx={{ mb: 2 }}>
      <InputLabel id={labelId}>{label}</InputLabel>
      <Select
        {...props}
        labelId={labelId}
        id={fieldId}
        label={label}
        aria-describedby={helperTextId}
      >
        {options.map((option) => (
          <MenuItem
            key={option.value}
            value={option.value}
            disabled={option.disabled}
          >
            {option.label}
          </MenuItem>
        ))}
      </Select>
      {helperText && (
        <FormHelperText id={helperTextId}>{helperText}</FormHelperText>
      )}
    </FormControl>
  );
}

// Checkbox with proper labeling
export interface FormCheckboxProps {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  error?: boolean;
  helperText?: string;
}

export function FormCheckbox({
  label,
  checked,
  onChange,
  disabled,
  error,
  helperText,
}: FormCheckboxProps) {
  const fieldId = `checkbox-${Math.random().toString(36).substr(2, 9)}`;
  const helperTextId = helperText ? `${fieldId}-helper` : undefined;

  return (
    <FormControl error={error} sx={{ mb: 2 }}>
      <FormControlLabel
        control={
          <Checkbox
            id={fieldId}
            checked={checked}
            onChange={(e) => onChange(e.target.checked)}
            disabled={disabled}
            aria-describedby={helperTextId}
          />
        }
        label={label}
      />
      {helperText && (
        <FormHelperText id={helperTextId}>{helperText}</FormHelperText>
      )}
    </FormControl>
  );
}

// Switch with proper labeling
export interface FormSwitchProps {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  error?: boolean;
  helperText?: string;
}

export function FormSwitch({
  label,
  checked,
  onChange,
  disabled,
  error,
  helperText,
}: FormSwitchProps) {
  const fieldId = `switch-${Math.random().toString(36).substr(2, 9)}`;
  const helperTextId = helperText ? `${fieldId}-helper` : undefined;

  return (
    <FormControl error={error} sx={{ mb: 2 }}>
      <FormControlLabel
        control={
          <Switch
            id={fieldId}
            checked={checked}
            onChange={(e) => onChange(e.target.checked)}
            disabled={disabled}
            aria-describedby={helperTextId}
          />
        }
        label={label}
      />
      {helperText && (
        <FormHelperText id={helperTextId}>{helperText}</FormHelperText>
      )}
    </FormControl>
  );
}

// Radio Group with proper labeling
export interface FormRadioGroupProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string; disabled?: boolean }>;
  disabled?: boolean;
  error?: boolean;
  helperText?: string;
  row?: boolean;
}

export function FormRadioGroup({
  label,
  value,
  onChange,
  options,
  disabled,
  error,
  helperText,
  row = false,
}: FormRadioGroupProps) {
  const fieldId = `radio-group-${Math.random().toString(36).substr(2, 9)}`;
  const helperTextId = helperText ? `${fieldId}-helper` : undefined;

  return (
    <FormControl error={error} sx={{ mb: 2 }}>
      <FormLabel id={fieldId} component="legend">
        {label}
      </FormLabel>
      <RadioGroup
        aria-labelledby={fieldId}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        row={row}
        aria-describedby={helperTextId}
      >
        {options.map((option) => (
          <FormControlLabel
            key={option.value}
            value={option.value}
            control={<Radio />}
            label={option.label}
            disabled={disabled || option.disabled}
          />
        ))}
      </RadioGroup>
      {helperText && (
        <FormHelperText id={helperTextId}>{helperText}</FormHelperText>
      )}
    </FormControl>
  );
}

// Form container with proper spacing
export interface FormContainerProps {
  children: React.ReactNode;
  onSubmit?: (e: React.FormEvent) => void;
  spacing?: number;
}

export function FormContainer({
  children,
  onSubmit,
  spacing = 2,
}: FormContainerProps) {
  return (
    <Box
      component="form"
      onSubmit={onSubmit}
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: spacing,
      }}
      noValidate
    >
      {children}
    </Box>
  );
}