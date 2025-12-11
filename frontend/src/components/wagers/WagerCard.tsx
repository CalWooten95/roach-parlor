import React, { useState } from 'react';
import {
  Box,
  Typography,
  IconButton,
  Menu,
  MenuItem,
  Chip,
  Divider,
  Stack,
  Alert,
} from '@mui/material';
import {
  MoreVert as MoreVertIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Schedule as ScheduleIcon,
  Archive as ArchiveIcon,
  Unarchive as UnarchiveIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
} from '@mui/icons-material';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusBadge } from '@/components/ui/Badge';
import { Wager, WagerStatus } from '@/types';
import { formatCurrency, formatDate, formatRelativeTime, calculatePayout } from '@/utils/helpers';

export interface WagerCardProps {
  wager: Wager;
  onStatusUpdate: (wagerId: number, status: WagerStatus) => void;
  onArchive: (wagerId: number, archived: boolean) => void;
  onDelete: (wagerId: number) => void;
  onEdit?: ((wager: Wager) => void) | undefined;
  showActions?: boolean;
  loading?: boolean;
}

export function WagerCard({
  wager,
  onStatusUpdate,
  onArchive,
  onDelete,
  onEdit,
  showActions = true,
  loading = false,
}: WagerCardProps) {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [statusMenuAnchor, setStatusMenuAnchor] = useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleStatusMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setStatusMenuAnchor(event.currentTarget);
  };

  const handleStatusMenuClose = () => {
    setStatusMenuAnchor(null);
  };

  const handleStatusUpdate = (status: WagerStatus) => {
    onStatusUpdate(wager.id, status);
    handleStatusMenuClose();
  };

  const handleArchive = () => {
    onArchive(wager.id, !wager.archived);
    handleMenuClose();
  };

  const handleDelete = () => {
    onDelete(wager.id);
    handleMenuClose();
  };

  const handleEdit = () => {
    if (onEdit) {
      onEdit(wager);
    }
    handleMenuClose();
  };

  const potentialPayout = calculatePayout(wager.amount, wager.line);
  const isActive = wager.status === 'pending' && !wager.archived;

  return (
    <Card
      sx={{
        opacity: wager.archived ? 0.7 : 1,
        border: isActive ? '2px solid' : '1px solid',
        borderColor: isActive ? 'primary.main' : 'divider',
      }}
    >
      <Box sx={{ p: 2 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box sx={{ flex: 1, mr: 2 }}>
            <Typography variant="h6" component="h3" sx={{ mb: 1, wordBreak: 'break-word' }}>
              {wager.description}
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
              <StatusBadge status={wager.status} />
              {wager.isFrePlay && <Chip label="Free Play" size="small" color="info" />}
              {wager.isLiveBet && <Chip label="Live Bet" size="small" color="warning" />}
              {wager.archived && <Chip label="Archived" size="small" color="default" />}
            </Stack>
          </Box>
          
          {showActions && (
            <IconButton
              onClick={handleMenuOpen}
              size="small"
              disabled={loading}
              aria-label="Wager actions"
            >
              <MoreVertIcon />
            </IconButton>
          )}
        </Box>

        {/* Wager Details */}
        <Box sx={{ mb: 2 }}>
          <Stack direction="row" spacing={3} sx={{ mb: 1 }}>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Amount
              </Typography>
              <Typography variant="h6" color="primary">
                {formatCurrency(wager.amount)}
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Line
              </Typography>
              <Typography variant="body1" fontWeight="medium">
                {wager.line}
              </Typography>
            </Box>
            {potentialPayout && (
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Potential Payout
                </Typography>
                <Typography variant="body1" color="success.main" fontWeight="medium">
                  {formatCurrency(potentialPayout)}
                </Typography>
              </Box>
            )}
          </Stack>
        </Box>

        {/* Matchup Information */}
        {wager.matchup && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Matchup
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2">
                {wager.matchup.awayTeam} @ {wager.matchup.homeTeam}
              </Typography>
              <Chip label={wager.matchup.league} size="small" variant="outlined" />
            </Box>
            <Typography variant="caption" color="text.secondary">
              {formatDate(wager.matchup.scheduledTime)}
            </Typography>
          </Box>
        )}

        {/* Legs */}
        {wager.legs && wager.legs.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Legs ({wager.legs.length})
            </Typography>
            <Stack spacing={1}>
              {wager.legs.map((leg) => (
                <Box
                  key={leg.id}
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    p: 1,
                    bgcolor: 'background.paper',
                    borderRadius: 1,
                    border: '1px solid',
                    borderColor: 'divider',
                  }}
                >
                  <Typography variant="body2" sx={{ flex: 1 }}>
                    {leg.description}
                  </Typography>
                  <StatusBadge status={leg.status} size="small" />
                </Box>
              ))}
            </Stack>
          </Box>
        )}

        {/* Live Data */}
        {wager.liveScore && (
          <Box sx={{ mb: 2 }}>
            <Alert severity="info" sx={{ py: 0.5 }}>
              <Typography variant="body2">
                Live Score: {wager.liveScore.awayScore} - {wager.liveScore.homeScore}
                {wager.liveScore.period && ` (${wager.liveScore.period})`}
              </Typography>
            </Alert>
          </Box>
        )}

        {/* Footer */}
        <Divider sx={{ my: 2 }} />
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="caption" color="text.secondary">
            Created {formatRelativeTime(wager.createdAt)}
          </Typography>
          
          {isActive && showActions && (
            <Button
              variant="outlined"
              size="small"
              onClick={handleStatusMenuOpen}
              disabled={loading}
              startIcon={
                wager.status === 'won' ? (
                  <TrendingUpIcon />
                ) : wager.status === 'lost' ? (
                  <TrendingDownIcon />
                ) : (
                  <ScheduleIcon />
                )
              }
            >
              Update Status
            </Button>
          )}
        </Box>
      </Box>

      {/* Actions Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        {onEdit && (
          <MenuItem onClick={handleEdit}>
            <EditIcon sx={{ mr: 1 }} />
            Edit
          </MenuItem>
        )}
        <MenuItem onClick={handleArchive}>
          {wager.archived ? <UnarchiveIcon sx={{ mr: 1 }} /> : <ArchiveIcon sx={{ mr: 1 }} />}
          {wager.archived ? 'Unarchive' : 'Archive'}
        </MenuItem>
        <MenuItem onClick={handleDelete} sx={{ color: 'error.main' }}>
          <DeleteIcon sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>

      {/* Status Update Menu */}
      <Menu
        anchorEl={statusMenuAnchor}
        open={Boolean(statusMenuAnchor)}
        onClose={handleStatusMenuClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <MenuItem onClick={() => handleStatusUpdate('won')}>
          <TrendingUpIcon sx={{ mr: 1, color: 'success.main' }} />
          Won
        </MenuItem>
        <MenuItem onClick={() => handleStatusUpdate('lost')}>
          <TrendingDownIcon sx={{ mr: 1, color: 'error.main' }} />
          Lost
        </MenuItem>
        <MenuItem onClick={() => handleStatusUpdate('push')}>
          <ScheduleIcon sx={{ mr: 1, color: 'info.main' }} />
          Push
        </MenuItem>
        <MenuItem onClick={() => handleStatusUpdate('cancelled')}>
          <ScheduleIcon sx={{ mr: 1, color: 'warning.main' }} />
          Cancelled
        </MenuItem>
        <MenuItem onClick={() => handleStatusUpdate('pending')}>
          <ScheduleIcon sx={{ mr: 1 }} />
          Pending
        </MenuItem>
      </Menu>
    </Card>
  );
}