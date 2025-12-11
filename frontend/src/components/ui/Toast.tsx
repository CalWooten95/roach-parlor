import React from 'react';
import {
  Snackbar,
  Alert as MuiAlert,
  AlertProps,
  Slide,
  SlideProps,
} from '@mui/material';

export interface ToastProps {
  open: boolean;
  message: string;
  severity?: AlertProps['severity'];
  duration?: number;
  onClose: () => void;
  action?: React.ReactNode;
  position?: {
    vertical: 'top' | 'bottom';
    horizontal: 'left' | 'center' | 'right';
  };
}

function SlideTransition(props: SlideProps) {
  return <Slide {...props} direction="up" />;
}

export function Toast({
  open,
  message,
  severity = 'info',
  duration = 6000,
  onClose,
  action,
  position = { vertical: 'bottom', horizontal: 'left' },
}: ToastProps) {
  return (
    <Snackbar
      open={open}
      autoHideDuration={duration}
      onClose={onClose}
      anchorOrigin={position}
      TransitionComponent={SlideTransition}
    >
      <MuiAlert
        onClose={onClose}
        severity={severity}
        variant="filled"
        action={action}
        sx={{ width: '100%' }}
        role="alert"
      >
        {message}
      </MuiAlert>
    </Snackbar>
  );
}

// Toast context for global toast management
interface ToastContextType {
  showToast: (message: string, severity?: AlertProps['severity']) => void;
  showSuccess: (message: string) => void;
  showError: (message: string) => void;
  showWarning: (message: string) => void;
  showInfo: (message: string) => void;
}

const ToastContext = React.createContext<ToastContextType | undefined>(undefined);

interface ToastState {
  open: boolean;
  message: string;
  severity: AlertProps['severity'];
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toast, setToast] = React.useState<ToastState>({
    open: false,
    message: '',
    severity: 'info',
  });

  const showToast = React.useCallback((message: string, severity: AlertProps['severity'] = 'info') => {
    setToast({ open: true, message, severity });
  }, []);

  const showSuccess = React.useCallback((message: string) => {
    showToast(message, 'success');
  }, [showToast]);

  const showError = React.useCallback((message: string) => {
    showToast(message, 'error');
  }, [showToast]);

  const showWarning = React.useCallback((message: string) => {
    showToast(message, 'warning');
  }, [showToast]);

  const showInfo = React.useCallback((message: string) => {
    showToast(message, 'info');
  }, [showToast]);

  const handleClose = React.useCallback(() => {
    setToast(prev => ({ ...prev, open: false }));
  }, []);

  const contextValue = React.useMemo(
    () => ({
      showToast,
      showSuccess,
      showError,
      showWarning,
      showInfo,
    }),
    [showToast, showSuccess, showError, showWarning, showInfo]
  );

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      <Toast
        open={toast.open}
        message={toast.message}
        severity={toast.severity}
        onClose={handleClose}
      />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = React.useContext(ToastContext);
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}