import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Paper,
  Box,
  Typography,
  Checkbox,
  IconButton,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  KeyboardArrowDown as ArrowDownIcon,
  KeyboardArrowUp as ArrowUpIcon,
} from '@mui/icons-material';
import { LoadingSpinner } from './LoadingSpinner';

export interface Column<T = any> {
  id: keyof T;
  label: string;
  minWidth?: number;
  align?: 'left' | 'right' | 'center';
  sortable?: boolean;
  format?: (value: any, row: T) => React.ReactNode;
  hideOnMobile?: boolean;
}

export interface DataTableProps<T = any> {
  columns: Column<T>[];
  data: T[];
  loading?: boolean;
  selectable?: boolean;
  selectedRows?: Set<string | number>;
  onSelectionChange?: (selected: Set<string | number>) => void;
  sortBy?: keyof T;
  sortDirection?: 'asc' | 'desc';
  onSort?: (column: keyof T) => void;
  onRowClick?: (row: T, index: number) => void;
  getRowId?: (row: T, index: number) => string | number;
  emptyMessage?: string;
  stickyHeader?: boolean;
  maxHeight?: number | string;
  expandable?: boolean;
  renderExpandedRow?: (row: T) => React.ReactNode;
  actions?: (row: T) => React.ReactNode;
}

export function DataTable<T = any>({
  columns,
  data,
  loading = false,
  selectable = false,
  selectedRows = new Set(),
  onSelectionChange,
  sortBy,
  sortDirection = 'asc',
  onSort,
  onRowClick,
  getRowId = (_, index) => index,
  emptyMessage = 'No data available',
  stickyHeader = false,
  maxHeight,
  expandable = false,
  renderExpandedRow,
  actions,
}: DataTableProps<T>) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [expandedRows, setExpandedRows] = React.useState<Set<string | number>>(new Set());

  const handleSelectAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!onSelectionChange) return;

    if (event.target.checked) {
      const allIds = new Set(data.map((row, index) => getRowId(row, index)));
      onSelectionChange(allIds);
    } else {
      onSelectionChange(new Set());
    }
  };

  const handleSelectRow = (rowId: string | number) => {
    if (!onSelectionChange) return;

    const newSelected = new Set(selectedRows);
    if (newSelected.has(rowId)) {
      newSelected.delete(rowId);
    } else {
      newSelected.add(rowId);
    }
    onSelectionChange(newSelected);
  };

  const handleExpandRow = (rowId: string | number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(rowId)) {
      newExpanded.delete(rowId);
    } else {
      newExpanded.add(rowId);
    }
    setExpandedRows(newExpanded);
  };

  const handleSort = (column: keyof T) => {
    if (onSort && columns.find(col => col.id === column)?.sortable !== false) {
      onSort(column);
    }
  };

  const visibleColumns = isMobile 
    ? columns.filter(col => !col.hideOnMobile)
    : columns;

  const isAllSelected = data.length > 0 && selectedRows.size === data.length;
  const isIndeterminate = selectedRows.size > 0 && selectedRows.size < data.length;

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <LoadingSpinner message="Loading data..." />
      </Box>
    );
  }

  return (
    <TableContainer 
      component={Paper} 
      sx={{ 
        maxHeight,
        '& .MuiTableCell-root': {
          borderBottom: `1px solid ${theme.palette.divider}`,
        }
      }}
    >
      <Table stickyHeader={stickyHeader} aria-label="data table">
        <TableHead>
          <TableRow>
            {selectable && (
              <TableCell padding="checkbox">
                <Checkbox
                  indeterminate={isIndeterminate}
                  checked={isAllSelected}
                  onChange={handleSelectAll}
                  inputProps={{ 'aria-label': 'select all rows' }}
                />
              </TableCell>
            )}
            
            {expandable && <TableCell />}
            
            {visibleColumns.map((column) => (
              <TableCell
                key={String(column.id)}
                align={column.align}
                style={{ minWidth: column.minWidth }}
                sortDirection={sortBy === column.id ? sortDirection : false}
              >
                {column.sortable !== false && onSort ? (
                  <TableSortLabel
                    active={sortBy === column.id}
                    direction={sortBy === column.id ? sortDirection : 'asc'}
                    onClick={() => handleSort(column.id)}
                    aria-label={`Sort by ${column.label}`}
                  >
                    {column.label}
                  </TableSortLabel>
                ) : (
                  column.label
                )}
              </TableCell>
            ))}
            
            {actions && <TableCell align="right">Actions</TableCell>}
          </TableRow>
        </TableHead>
        
        <TableBody>
          {data.length === 0 ? (
            <TableRow>
              <TableCell 
                colSpan={
                  visibleColumns.length + 
                  (selectable ? 1 : 0) + 
                  (expandable ? 1 : 0) + 
                  (actions ? 1 : 0)
                }
                align="center"
                sx={{ py: 4 }}
              >
                <Typography variant="body2" color="text.secondary">
                  {emptyMessage}
                </Typography>
              </TableCell>
            </TableRow>
          ) : (
            data.map((row, index) => {
              const rowId = getRowId(row, index);
              const isSelected = selectedRows.has(rowId);
              const isExpanded = expandedRows.has(rowId);

              return (
                <React.Fragment key={String(rowId)}>
                  <TableRow
                    hover={!!onRowClick}
                    selected={isSelected}
                    onClick={onRowClick ? () => onRowClick(row, index) : undefined}
                    sx={{
                      cursor: onRowClick ? 'pointer' : 'default',
                      '&:hover': {
                        backgroundColor: onRowClick ? theme.palette.action.hover : 'transparent',
                      },
                    }}
                    role={onRowClick ? 'button' : undefined}
                    tabIndex={onRowClick ? 0 : -1}
                  >
                    {selectable && (
                      <TableCell padding="checkbox">
                        <Checkbox
                          checked={isSelected}
                          onChange={() => handleSelectRow(rowId)}
                          inputProps={{ 'aria-label': `select row ${index + 1}` }}
                          onClick={(e: React.MouseEvent) => e.stopPropagation()}
                        />
                      </TableCell>
                    )}
                    
                    {expandable && (
                      <TableCell>
                        <IconButton
                          size="small"
                          onClick={(e: React.MouseEvent) => {
                            e.stopPropagation();
                            handleExpandRow(rowId);
                          }}
                          aria-label={isExpanded ? 'collapse row' : 'expand row'}
                        >
                          {isExpanded ? <ArrowUpIcon /> : <ArrowDownIcon />}
                        </IconButton>
                      </TableCell>
                    )}
                    
                    {visibleColumns.map((column) => (
                      <TableCell key={String(column.id)} align={column.align}>
                        {column.format 
                          ? column.format(row[column.id], row)
                          : String(row[column.id] ?? '')
                        }
                      </TableCell>
                    ))}
                    
                    {actions && (
                      <TableCell align="right" onClick={(e: React.MouseEvent) => e.stopPropagation()}>
                        {actions(row)}
                      </TableCell>
                    )}
                  </TableRow>
                  
                  {expandable && isExpanded && renderExpandedRow && (
                    <TableRow>
                      <TableCell 
                        colSpan={
                          visibleColumns.length + 
                          (selectable ? 1 : 0) + 
                          (expandable ? 1 : 0) + 
                          (actions ? 1 : 0)
                        }
                        sx={{ py: 0 }}
                      >
                        <Box sx={{ py: 2 }}>
                          {renderExpandedRow(row)}
                        </Box>
                      </TableCell>
                    </TableRow>
                  )}
                </React.Fragment>
              );
            })
          )}
        </TableBody>
      </Table>
    </TableContainer>
  );
}