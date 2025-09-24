// src/components/user_management/CreateUserForm.tsx
import React, { useState } from 'react';
import {
  Box,
  Grid,
  TextField,
  Button,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
} from '@mui/material';
import { Organization } from '../../types/jobDescriptionTypes';
import { CreateUserPayload } from '../../types/userTypes';
import { createUserApi } from '../../services/apiService';
import StatusAlert, { StatusMessage } from '../common/StatusAlert';
import TitledCard from '../common/TitledCard';
import axios from 'axios';

interface CreateUserFormProps {
  organizations: Organization[];
  roles: string[];
}

const CreateUserForm: React.FC<CreateUserFormProps> = ({ organizations, roles }) => {
  const [formData, setFormData] = useState<CreateUserPayload>({
    fullName: '',
    email: '',
    organizationId: '',
    role: '',
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<StatusMessage | null>(null);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | SelectChangeEvent<string>) => {
    setFormData({
      ...formData,
      [event.target.name]: event.target.value,
    });
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setMessage(null);

    if (!formData.organizationId) {
      setMessage({ type: 'error', text: 'Please select an organization.' });
      setLoading(false);
      return;
    }

    if (!formData.role) {
      setMessage({ type: 'error', text: 'Please select a role.' });
      setLoading(false);
      return;
    }

    try {
      const response = await createUserApi(formData);
      if (response.status === 201) {
        setMessage({ type: 'success', text: `User "${response.data.fullName}" created successfully!` });
        // Reset form
        setFormData({
          fullName: '',
          email: '',
          organizationId: formData.organizationId, // Keep org selected
          role: '',
        });
      }
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        const errorData = error.response.data;
        setMessage({
          type: 'error',
          text: errorData.message || errorData.error || 'Failed to create user. Please try again.',
        });
      } else {
        setMessage({ type: 'error', text: 'An unexpected error occurred. Please try again.' });
      }
      console.error('Create user error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <TitledCard title="Create New User">
      <StatusAlert message={message} onClose={() => setMessage(null)} />
      <Box component="form" onSubmit={handleSubmit} noValidate sx={{ mt: 1, p: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              required
              fullWidth
              id="fullName"
              label="Full Name"
              name="fullName"
              autoComplete="name"
              value={formData.fullName}
              onChange={handleChange}
              disabled={loading}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              required
              fullWidth
              id="email"
              label="Email Address"
              name="email"
              autoComplete="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              disabled={loading}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth required disabled={loading}>
              <InputLabel id="organization-select-label">Organization</InputLabel>
              <Select
                labelId="organization-select-label"
                id="organizationId"
                name="organizationId"
                value={formData.organizationId}
                label="Organization"
                onChange={handleChange}
              >
                {organizations.map((org) => (
                  <MenuItem key={org.id} value={org.id}>
                    {org.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth required disabled={loading}>
              <InputLabel id="role-select-label">Role</InputLabel>
              <Select
                labelId="role-select-label"
                id="role"
                name="role"
                value={formData.role}
                label="Role"
                onChange={handleChange}
              >
                {roles.map((role) => (
                  <MenuItem key={role} value={role}>
                    {role.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase())}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>
        <Button
          type="submit"
          fullWidth
          variant="contained"
          sx={{ mt: 3, mb: 2 }}
          disabled={loading || !formData.fullName || !formData.email || !formData.organizationId || !formData.role}
        >
          {loading ? <CircularProgress size={24} color="inherit" /> : 'Create User'}
        </Button>
      </Box>
    </TitledCard>
  );
};

export default CreateUserForm;