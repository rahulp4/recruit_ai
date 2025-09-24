// src/components/DocxUploadModal.tsx
import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  Button, Box, Typography
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

interface DocxUploadModalProps {
  open: boolean;
  onClose: () => void;
  onUpload: (file: File) => void;
}

const DocxUploadModal: React.FC<DocxUploadModalProps> = ({ open, onClose, onUpload }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) {
      setSelectedFile(e.target.files[0]);
    }
  };

const handleUploadClick = () => {
  if (!selectedFile) {
    console.error("No file selected.");
    return;
  }

  console.log('Uploading file:', selectedFile.name, selectedFile.type);
  onUpload(selectedFile);
  setSelectedFile(null);
  onClose();
};


  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle textAlign="center">Upload .docx File</DialogTitle>
      <DialogContent>
        <Box display="flex" justifyContent="center" gap={2} mt={2}>
          <input
            id="docx-upload"
            type="file"
            accept=".docx"
            hidden
            onChange={handleFileChange}
          />
          <label htmlFor="docx-upload">
            <Button
              variant="outlined"
              component="span"
              startIcon={<CloudUploadIcon />}
              sx={{
                borderColor: '#9DB2FB',
                color: '#4A6CF7',
                fontWeight: 600,
                textTransform: 'none'
              }}
            >
              Choose .docx File
            </Button>
          </label>
          <Button
            variant="contained"
            startIcon={<CloudUploadIcon />}
            disabled={!selectedFile}
            onClick={handleUploadClick}
            sx={{
              backgroundColor: '#E0E0E0',
              color: '#757575',
              fontWeight: 600,
              textTransform: 'none',
              '&:hover': { backgroundColor: '#d5d5d5' }
            }}
          >
            Upload & Analyse
          </Button>
        </Box>
        {selectedFile && (
          <Typography variant="body2" align="center" mt={2}>
            Selected: {selectedFile.name}
          </Typography>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default DocxUploadModal;
