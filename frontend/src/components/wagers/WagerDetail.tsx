import React, { useState } from 'react';
import {
  Box,
  Typography,
  Stack,
  Divider,
  Chip,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Edit as EditIcon,
  Archive as ArchiveIcon,
  Unarchive as UnarchiveIcon,
  Delete as DeleteIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Schedule as ScheduleIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusBadge } from '@/components/ui/Badge';
import { Wager, WagerStatus } from '@/types';
import { formatCurrency, formatDate, formatRelativeTime, calculatePayout } from '@/utils/helpers';

export interface WagerDetailProps {
  wager: Wager;
  onStatusUpdate: (wagerId: number, status: WagerStatus) => void;
  onArchive: (wagerId: number, archived: boolean) => void;
  onDelete: (wagerId: number) => void;
  onEdit?: (wager: Wager) => void;
  onClose?: () => void;
  loading?: boolean;
}

export function WagerDetail({
  wager,
  onStatusUpdate,
  onArchive,
  onDelete,
  onEdit,
  onClose,
  loading = false,
}: WagerDetailProps) {
  const [statusMenuOpen, setStatusMenuOpen] = useState(false);

  const potentialPayout = calculatePayout(wager.amount, wager.line);
  const isActive = wager.status === 'pending' && !wager.archived;

  const handleStatusUpdate = (status: WagerStatus) => {
    onStatusUpdate(wager.id, status);
    setStatusMenuOpen(false);
  };

  const handleArchive = () => {
    onArchive(wager.id, !wager.archived);
  };

  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this wager? This action cannot be undone.')) {
      onDelete(wager.id);
    }
  };

  const handleEdit = () => {
    if (onEdit) {
      onEdit(wager);
    }
  };

  return (
    <Box>
      {/* Header */}
      <Card>
        <Box sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h4" component="h1" gutterBottom>
                Wager Details
              </Typography>
              <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
                {wager.description}
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                <StatusBadge status={wager.status} />
                {wager.isFrePlay && <Chip label="Free Play" size="small" color="info" />}
                {wager.isLiveBet && <Chip label="Live Bet" size="small" color="warning" />}
                {wager.archived && <Chip label="Archived" size="small" color="default" />}
                {wager.autoCalculate && <Chip label="Auto Calculate" size="small" color="primary" />}
                {wager.liveTrackingEnabled && <Chip label="Live Tracking" size="small" color="secondary" />}
              </Stack>
            </Box>

            <Stack direction="row" spacing={1}>
              {onEdit && (
                <Tooltip title="Edit wager">
                  <IconButton onClick={handleEdit} disabled={loading}>
                    <EditIcon />
                  </IconButton>
                </Tooltip>
              )}
              <Tooltip title={wager.archived ? 'Unarchive' : 'Archive'}>
                <IconButton onClick={handleArchive} disabled={loading}>
                  {wager.archived ? <UnarchiveIcon /> : <ArchiveIcon />}
                </IconButton>
              </Tooltip>
              <Tooltip title="Delete wager">
                <IconButton onClick={handleDelete} disabled={loading} color="error">
                  <DeleteIcon />
                </IconButton>
              </Tooltip>
              {onClose && (
                <Button variant="outlined" onClick={onClose}>
                  Close
                </Button>
              )}
            </Stack>
          </Box>

          {/* Wager Information */}
          <Stack direction="row" spacing={4} sx={{ mb: 3 }}>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Amount
              </Typography>
              <Typography variant="h5" color="primary" fontWeight="bold">
                {formatCurrency(wager.amount)}
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Line
              </Typography>
              <Typography variant="h6" fontWeight="medium">
                {wager.line}
              </Typography>
            </Box>
            {potentialPayout && (
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Potential Payout
                </Typography>
                <Typography variant="h6" color="success.main" fontWeight="medium">
                  {formatCurrency(potentialPayout)}
                </Typography>
              </Box>
            )}
            {wager.payout && (
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Actual Payout
                </Typography>
                <Typography variant="h6" color="success.main" fontWeight="medium">
                  {formatCurrency(wager.payout)}
                </Typography>
              </Box>
            )}
          </Stack>

          {/* Status Update Actions */}
          {isActive && (
            <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
              <Button
                variant="contained"
                color="success"
                startIcon={<TrendingUpIcon />}
                onClick={() => handleStatusUpdate('won')}
                disabled={loading}
              >
                Mark as Won
              </Button>
              <Button
                variant="contained"
                color="error"
                startIcon={<TrendingDownIcon />}
                onClick={() => handleStatusUpdate('lost')}
                disabled={loading}
              >
                Mark as Lost
              </Button>
              <Button
                variant="outlined"
                startIcon={<ScheduleIcon />}
                onClick={() => handleStatusUpdate('push')}
                disabled={loading}
              >
                Mark as Push
              </Button>
              <Button
                variant="outlined"
                startIcon={<ScheduleIcon />}
                onClick={() => handleStatusUpdate('cancelled')}
                disabled={loading}
              >
                Cancel
              </Button>
            </Stack>
          )}

          {/* Timestamps */}
          <Box sx={{ display: 'flex', gap: 4, color: 'text.secondary' }}>
            <Typography variant="body2">
              Created: {formatDate(wager.createdAt)}
            </Typography>
            {wager.resultedAt && (
              <Typography variant="body2">
                Resulted: {formatDate(wager.resultedAt)}
              </Typography>
            )}
            {wager.lastCalculationAttempt && (
              <Typography variant="body2">
                Last Calculation: {formatDate(wager.lastCalculationAttempt)}
              </Typography>
            )}
          </Box>
        </Box>
      </Card>

      {/* Matchup Information */}
      {wager.matchup && (
        <Card sx={{ mt: 2 }}>
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Matchup Information
            </Typography>
            <Stack spacing={2}>
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Teams
                </Typography>
                <Typography variant="h6">
                  {wager.matchup.awayTeam} @ {wager.matchup.homeTeam}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 4 }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    League
                  </Typography>
                  <Chip label={wager.matchup.league} variant="outlined" />
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Scheduled Time
                  </Typography>
                  <Typography variant="body1">
                    {formatDate(wager.matchup.scheduledTime)}
                  </Typography>
                </Box>
              </Box>
              {(wager.matchup.externalGameId || wager.matchup.espnEventId) && (
                <Box sx={{ display: 'flex', gap: 4 }}>
                  {wager.matchup.externalGameId && (
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        External Game ID
                      </Typography>
                      <Typography variant="body2" fontFamily="monospace">
                        {wager.matchup.externalGameId}
                      </Typography>
                    </Box>
                  )}
                  {wager.matchup.espnEventId && (
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        ESPN Event ID
                      </Typography>
                      <Typography variant="body2" fontFamily="monospace">
                        {wager.matchup.espnEventId}
                      </Typography>
                    </Box>
                  )}
                </Box>
              )}
            </Stack>
          </Box>
        </Card>
      )}

      {/* Live Data */}
      {(wager.liveScore || wager.currentOdds) && (
        <Card sx={{ mt: 2 }}>
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Live Data
            </Typography>
            {wager.liveScore && (
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="body1" fontWeight="medium">
                  Live Score: {wager.liveScore.awayScore} - {wager.liveScore.homeScore}
                </Typography>
                {wager.liveScore.period && (
                  <Typography variant="body2">
                    Period: {wager.liveScore.period}
                  </Typography>
                )}
                {wager.liveScore.gameTime && (
                  <Typography variant="body2">
                    Game Time: {wager.liveScore.gameTime}
                  </Typography>
                )}
                <Typography variant="body2">
                  Status: {wager.liveScore.status}
                </Typography>
              </Alert>
            )}
            {wager.currentOdds && (
              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Current Odds ({wager.currentOdds.provider})
                </Typography>
                <Stack direction="row" spacing={2}>
                  {wager.currentOdds.moneylineHome && (
                    <Chip label={`ML Home: ${wager.currentOdds.moneylineHome}`} size="small" />
                  )}
                  {wager.currentOdds.moneylineAway && (
                    <Chip label={`ML Away: ${wager.currentOdds.moneylineAway}`} size="small" />
                  )}
                  {wager.currentOdds.spreadHome && (
                    <Chip label={`Spread: ${wager.currentOdds.spreadHome}`} size="small" />
                  )}
                  {wager.currentOdds.totalOver && (
                    <Chip label={`O/U: ${wager.currentOdds.totalOver}`} size="small" />
                  )}
                </Stack>
                <Typography variant="caption" color="text.secondary">
                  Updated: {formatRelativeTime(wager.currentOdds.timestamp)}
                </Typography>
              </Box>
            )}
          </Box>
        </Card>
      )}

      {/* Legs */}
      {wager.legs && wager.legs.length > 0 && (
        <Card sx={{ mt: 2 }}>
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Legs ({wager.legs.length})
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Description</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Created</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {wager.legs.map((leg) => (
                    <TableRow key={leg.id}>
                      <TableCell>{leg.description}</TableCell>
                      <TableCell>
                        <StatusBadge status={leg.status} size="small" />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {formatRelativeTime(leg.createdAt)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        </Card>
      )}

      {/* Calculation History */}
      {wager.calculations && wager.calculations.length > 0 && (
        <Card sx={{ mt: 2 }}>
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Calculation History
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Type</TableCell>
                    <TableCell>Result</TableCell>
                    <TableCell>Confidence</TableCell>
                    <TableCell>Date</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {wager.calculations.map((calc) => (
                    <TableRow key={calc.id}>
                      <TableCell>
                        <Chip
                          label={calc.calculationType}
                          size="small"
                          color={calc.calculationType === 'auto' ? 'primary' : 'default'}
                        />
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={calc.result as WagerStatus} size="small" />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {Math.round(calc.confidenceScore * 100)}%
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {formatRelativeTime(calc.calculatedAt)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Tooltip title="View calculation details">
                          <IconButton size="small">
                            <TimelineIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        </Card>
      )}
    </Box>
  );
}