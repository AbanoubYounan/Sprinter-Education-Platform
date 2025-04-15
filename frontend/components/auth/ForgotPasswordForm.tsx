'use client';
/* eslint-disable  @typescript-eslint/no-explicit-any */

import { Box, Button, TextField, Typography } from '@mui/material';
import { useState } from 'react';
import axios from 'axios';

interface Props {
  onSwitch: (mode: 'login') => void;
}

export default function ForgotPasswordForm({ onSwitch }: Props) {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    try {
      setLoading(true)
      const response = await axios.post('https://sprinter-back.mes-design.com/api/auth/request-password-reset', {
        Email: email,
      });
      setMessage(response.data.message);
    } catch (error: any) {
      setMessage(error.response?.data?.message ?? 'Something went wrong.');
    } finally {
      setLoading(false)
    }
  };

  return (
    <Box>
      <Typography variant="body2" color="text.secondary" mb={2}>
        Enter your email address and we’ll send you a link to reset your password.
      </Typography>

      <TextField
        fullWidth
        label="Email"
        variant="outlined"
        margin="normal"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />

      <Button fullWidth variant="contained" sx={{ mt: 2, bgcolor: '#0066FF' }} onClick={handleSubmit}>
        {loading? 'Sending...' : 'Send Reset Link'}
      </Button>

      {message && (
        <Typography variant="body2" mt={2} color="primary">
          {message}
        </Typography>
      )}

      <Typography align="center" mt={3} fontSize="small">
        Back to{' '}
        <span
          style={{ color: '#0066FF', cursor: 'pointer' }}
          onClick={() => onSwitch('login')}
        >
          Login
        </span>
      </Typography>
    </Box>
  );
}
