import React from 'react';
import { Alert, AlertTitle } from '@mui/material';

export interface StatusMessage {
  type: 'success' | 'error' | 'info' | 'warning';
  text: string;
}

interface StatusAlertProps {
  message: StatusMessage | null;
  onClose?: () => void;
  loading?: boolean;
}

const StatusAlert: React.FC<StatusAlertProps> = ({ message, onClose, loading = false }) => {
  if (!message || loading) {
    return null;
  }

  return (
    <Alert onClose={onClose} severity={message.type}>
      <AlertTitle>{message.type.charAt(0).toUpperCase() + message.type.slice(1)}</AlertTitle>
      {message.text}
    </Alert>
  );
};

export default StatusAlert;