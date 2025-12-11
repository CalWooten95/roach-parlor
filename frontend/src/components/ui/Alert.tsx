import React from 'react';
import {
  Alert as MuiAlert,
  AlertTitle,
  AlertProps as MuiAlertProps,
  Collapse,
  IconButton,
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';

export interface AlertProps extends MuiAlertProps {
  title?: string;
  children: React.ReactNode;
  dismissible?: boolean;
  onDismiss?: () => void;
  show?: boolean;
}

export function Alert({
  title,
  children,
  dismissible = false,
  onDismiss,
  show = true,
  ...props
}: AlertProps) {
  const [visible, setVisible] = React.useState(show);

  React.useEffect(() => {
    setVisible(show);
  }, [show]);

  const handleDismiss = () => {
    setVisible(false);
    if (onDismiss) {
      onDismiss();
    }
  };

  return (
    <Collapse in={visible}>
      <MuiAlert
        {...props}
        action={
          dismissible ? (
            <IconButton
              aria-label="Close alert"
              color="inherit"
              size="small"
              onClick={handleDismiss}
            >
              <CloseIcon fontSize="inherit" />
            </IconButton>
          ) : (
            props.action
          )
        }
        role="alert"
        sx={{
          mb: visible ? 2 : 0,
          ...props.sx,
        }}
      >
        {title && <AlertTitle>{title}</AlertTitle>}
        {children}
      </MuiAlert>
    </Collapse>
  );
}