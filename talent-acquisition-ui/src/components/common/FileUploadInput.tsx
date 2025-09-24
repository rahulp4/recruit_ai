// src/components/common/FileUploadInput.tsx
// (You might need to create a src/components/common folder)
import React, { useState } from 'react';
import { Box, Typography, Button, LinearProgress, Alert, AlertTitle } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';
import CircularProgress from '@mui/material/CircularProgress'; // For loading spinner on button

// Define props for this reusable component
interface FileUploadInputProps {
  buttonText: string; // Text for the choose file button
  uploadButtonText: string; // Text for the upload button
  allowedFileExtensions: string[]; // e.g., ['.docx', '.pdf']
  acceptedFileMimeTypes: string[]; // e.g., ['application/vnd.openxmlformats-officedocument.wordprocessingml.document']
  onFileSelect: (file: File | null) => void; // Callback when a file is selected (for parent to handle)
  onUploadClick: (file: File) => Promise<void>; // Callback when upload button is clicked
  isDisabled: boolean; // Disable the entire control
  uploading: boolean; // Is the upload in progress
  uploadMessage: { type: 'success' | 'error' | 'info', text: string } | null; // Message feedback
}

const FileUploadInput: React.FC<FileUploadInputProps> = ({
  buttonText,
  uploadButtonText,
  allowedFileExtensions,
  acceptedFileMimeTypes,
  onFileSelect,
  onUploadClick,
  isDisabled,
  uploading,
  uploadMessage,
}) => {
  const [internalSelectedFile, setInternalSelectedFile] = useState<File | null>(null);
  const [internalMessage, setInternalMessage] = useState<{ type: 'error' | 'info', text: string } | null>(null);

  const handleInternalFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setInternalMessage(null); // Clear internal messages
    const file = event.target.files && event.target.files[0];
    if (file) {
      if (acceptedFileMimeTypes.includes(file.type)) {
        setInternalSelectedFile(file);
        onFileSelect(file); // Notify parent
      } else {
        setInternalSelectedFile(null);
        setInternalMessage({ type: 'error', text: `Invalid file type. Please upload a ${allowedFileExtensions.join('/')} file.` });
        onFileSelect(null); // Notify parent of invalid file
      }
    } else {
      setInternalSelectedFile(null);
      onFileSelect(null); // Notify parent of no file selected
    }
  };

  const handleInternalUploadClick = async () => {
    if (internalSelectedFile) {
      await onUploadClick(internalSelectedFile); // Let parent handle upload logic and messages
      setInternalSelectedFile(null); // Clear internal file after upload attempt
    } else {
      setInternalMessage({ type: 'info', text: 'Please select a file to upload.' });
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
      {/* Buttons Row */}
      <Box 
        sx={{ 
          display: 'flex', 
          flexDirection: { xs: 'column', sm: 'row' }, 
          alignItems: 'center', 
          justifyContent: 'center', 
          gap: { xs: 1, sm: 1.5 }, // Gap between buttons
          mb: 1.5 // Margin below the button group
        }}
      >
        {/* Choose File Button */}
        <input
          accept={allowedFileExtensions.map(ext => `.${ext.substring(1)}`).join(',')} // e.g., ".docx,.pdf"
          style={{ display: 'none' }}
          id="file-upload-input"
          type="file"
          onChange={handleInternalFileChange}
          disabled={isDisabled || uploading}
        />
        <label htmlFor="file-upload-input">
          <Button
            variant="outlined"
            component="span"
            startIcon={<CloudUploadIcon />}
            disabled={isDisabled || uploading}
            size="small"
            sx={{ py: 0.5, px: 1.5 }}
          >
            {internalSelectedFile ? `Change ${allowedFileExtensions[0].substring(1).toUpperCase()} File` : buttonText}
          </Button>
        </label>

        {/* Upload Button */}
        <Button
          variant="contained"
          color="primary"
          onClick={handleInternalUploadClick}
          disabled={!internalSelectedFile || isDisabled || uploading}
          startIcon={uploading ? null : <CloudUploadIcon />}
          size="small"
          sx={{ py: 0.5, px: 1.5 }}
        >
          {uploading ? <CircularProgress size={16} color="inherit" /> : uploadButtonText}
        </Button>
      </Box>

      {/* Selected File Display */}
      {internalSelectedFile && (
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5, my: 1, width: '100%' }}>
          <InsertDriveFileIcon color="action" sx={{fontSize: '1rem', flexShrink: 0}} />
          <Typography 
            variant="caption" 
            color="text.primary" 
            noWrap 
            title={internalSelectedFile.name} 
            sx={{
              maxWidth: 'calc(100% - 40px)', 
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {internalSelectedFile.name} ({Math.round(internalSelectedFile.size / 1024)} KB)
          </Typography>
        </Box>
      )}

      {/* Progress and Messages */}
      {uploading && (
        <LinearProgress variant="indeterminate" sx={{ width: '100%', my: 1.5 }} />
      )}
      {/* Combine internal messages and parent-provided messages */}
      {(internalMessage || uploadMessage) && (
        <Alert 
          severity={uploadMessage?.type || internalMessage?.type || 'info'} 
          sx={{ 
            width: '100%', my: 1.5, py: 0.25, fontSize: '0.75rem',
            '& .MuiAlert-icon': { fontSize: '1.1rem', mr: 0.5, alignItems: 'center' },
            '& .MuiAlertTitle-root': { fontSize: '0.85rem', mb: 0.1, fontWeight: 'medium' }
          }}
        >
          <AlertTitle>{(uploadMessage?.type || internalMessage?.type) === 'success' ? 'Success' : (uploadMessage?.type || internalMessage?.type) === 'error' ? 'Error' : 'Info'}</AlertTitle>
          {uploadMessage?.text || internalMessage?.text}
        </Alert>
      )}
    </Box>
  );
};

export default FileUploadInput;