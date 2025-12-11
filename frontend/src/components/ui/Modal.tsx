import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogProps,
  IconButton,
  Typography,
  Box,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';

export interface ModalProps extends Omit<DialogProps, 'title'> {
  title?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
  onClose?: () => void;
  size?: 'small' | 'medium' | 'large' | 'fullscreen';
  showCloseButton?: boolean;
}

export function Modal({
  title,
  children,
  actions,
  onClose,
  size = 'medium',
  showCloseButton = true,
  ...props
}: ModalProps) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const sizeMap = {
    small: 'sm',
    medium: 'md',
    large: 'lg',
    fullscreen: false,
  } as const;

  const maxWidth = size === 'fullscreen' ? false : sizeMap[size];
  const fullScreen = size === 'fullscreen' || isMobile;

  return (
    <Dialog
      {...props}
      onClose={onClose}
      maxWidth={maxWidth}
      fullWidth
      fullScreen={fullScreen}
      aria-labelledby={title ? 'modal-title' : undefined}
      sx={{
        '& .MuiDialog-paper': {
          margin: isMobile ? 0 : 2,
          maxHeight: isMobile ? '100vh' : 'calc(100vh - 64px)',
        },
        ...props.sx,
      }}
    >
      {title && (
        <DialogTitle
          id="modal-title"
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            pb: 1,
          }}
        >
          <Typography variant="h6" component="h2">
            {title}
          </Typography>
          {showCloseButton && onClose && (
            <IconButton
              aria-label="Close modal"
              onClick={onClose}
              size="small"
              sx={{ ml: 1 }}
            >
              <CloseIcon />
            </IconButton>
          )}
        </DialogTitle>
      )}

      <DialogContent
        sx={{
          padding: theme.spacing(2),
          '&.MuiDialogContent-root': {
            paddingTop: title ? theme.spacing(1) : theme.spacing(2),
          },
        }}
      >
        {children}
      </DialogContent>

      {actions && (
        <DialogActions
          sx={{
            padding: theme.spacing(1, 2, 2),
            gap: 1,
          }}
        >
          {actions}
        </DialogActions>
      )}
    </Dialog>
  );
}