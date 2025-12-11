import React from 'react';
import {
  TextField,
  InputAdornment,
  IconButton,
  Box,
  Chip,
  Paper,
  Typography,
  useTheme,
} from '@mui/material';
import {
  Search as SearchIcon,
  Clear as ClearIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';

export interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  onClear?: () => void;
  placeholder?: string;
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  size?: 'small' | 'medium';
  variant?: 'outlined' | 'filled' | 'standard';
  debounceMs?: number;
  sx?: any;
}

export function SearchInput({
  value,
  onChange,
  onClear,
  placeholder = 'Search...',
  disabled = false,
  loading = false,
  fullWidth = true,
  size = 'medium',
  variant = 'outlined',
  debounceMs = 300,
  sx,
}: SearchInputProps) {
  const [localValue, setLocalValue] = React.useState(value);
  const debounceRef = React.useRef<ReturnType<typeof setTimeout>>();

  React.useEffect(() => {
    setLocalValue(value);
  }, [value]);

  const handleChange = (newValue: string) => {
    setLocalValue(newValue);

    // Clear existing timeout
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    // Set new timeout
    debounceRef.current = setTimeout(() => {
      onChange(newValue);
    }, debounceMs);
  };

  const handleClear = () => {
    setLocalValue('');
    onChange('');
    if (onClear) {
      onClear();
    }
  };

  React.useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  return (
    <TextField
      value={localValue}
      onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleChange(e.target.value)}
      placeholder={placeholder}
      disabled={disabled || loading}
      fullWidth={fullWidth}
      size={size}
      variant={variant}
      InputProps={{
        startAdornment: (
          <InputAdornment position="start">
            <SearchIcon color={disabled ? 'disabled' : 'action'} />
          </InputAdornment>
        ),
        endAdornment: localValue && (
          <InputAdornment position="end">
            <IconButton
              size="small"
              onClick={handleClear}
              disabled={disabled || loading}
              aria-label="Clear search"
            >
              <ClearIcon />
            </IconButton>
          </InputAdornment>
        ),
      }}
      sx={{
        '& .MuiOutlinedInput-root': {
          backgroundColor: 'background.paper',
        },
        ...sx,
      }}
    />
  );
}

// Advanced search with filters
export interface FilterOption {
  id: string;
  label: string;
  value: any;
  color?: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning';
}

export interface AdvancedSearchProps {
  searchValue: string;
  onSearchChange: (value: string) => void;
  filters: FilterOption[];
  onFiltersChange: (filters: FilterOption[]) => void;
  availableFilters?: FilterOption[];
  placeholder?: string;
  disabled?: boolean;
  showFilterButton?: boolean;
}

export function AdvancedSearch({
  searchValue,
  onSearchChange,
  filters,
  onFiltersChange,
  availableFilters = [],
  placeholder = 'Search...',
  disabled = false,
  showFilterButton = true,
}: AdvancedSearchProps) {
  const theme = useTheme();
  const [showFilters, setShowFilters] = React.useState(false);

  const handleFilterAdd = (filter: FilterOption) => {
    if (!filters.find(f => f.id === filter.id)) {
      onFiltersChange([...filters, filter]);
    }
  };

  const handleFilterRemove = (filterId: string) => {
    onFiltersChange(filters.filter(f => f.id !== filterId));
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
        <SearchInput
          value={searchValue}
          onChange={onSearchChange}
          placeholder={placeholder}
          disabled={disabled}
          fullWidth
        />
        
        {showFilterButton && availableFilters.length > 0 && (
          <IconButton
            onClick={() => setShowFilters(!showFilters)}
            color={filters.length > 0 ? 'primary' : 'default'}
            aria-label="Toggle filters"
            sx={{ mt: 0.5 }}
          >
            <FilterIcon />
          </IconButton>
        )}
      </Box>

      {/* Active filters */}
      {filters.length > 0 && (
        <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {filters.map((filter) => (
            <Chip
              key={filter.id}
              label={filter.label}
              color={filter.color || 'primary'}
              size="small"
              onDelete={() => handleFilterRemove(filter.id)}
              variant="outlined"
            />
          ))}
        </Box>
      )}

      {/* Filter options */}
      {showFilters && availableFilters.length > 0 && (
        <Paper
          sx={{
            mt: 1,
            p: 2,
            border: `1px solid ${theme.palette.divider}`,
          }}
        >
          <Typography variant="subtitle2" gutterBottom>
            Available Filters
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {availableFilters
              .filter(filter => !filters.find(f => f.id === filter.id))
              .map((filter) => (
                <Chip
                  key={filter.id}
                  label={filter.label}
                  color={filter.color || 'default'}
                  size="small"
                  onClick={() => handleFilterAdd(filter)}
                  variant="outlined"
                  sx={{ cursor: 'pointer' }}
                />
              ))}
          </Box>
        </Paper>
      )}
    </Box>
  );
}