'use client';
/* eslint-disable  @typescript-eslint/no-explicit-any */
import {
  Box,
  Button,
  Card,
  CardContent,
  TextField,
  Typography,
  CircularProgress,
} from '@mui/material';
import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import axios from 'axios';

export default function ResetPasswordClient() {
  const [newPassword, setNewPassword] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('t');

  useEffect(() => {
    if (!token) {
      setMessage('Invalid or missing token.');
    }
  }, [token]);

  const handleReset = async () => {
    if (!token || !newPassword) {
      setMessage("Password can't be empty.");
      return;
    }

    try {
      setLoading(true);
      const response = await axios.post('https://sprinter-back.mes-design.com/api/auth/reset-password', {
        token,
        newPassword,
      });
      setMessage(response.data.message);
      setTimeout(() => {
        router.push('/');
      }, 2000);
    } catch (error: any) {
      setMessage(error.response?.data?.message ?? 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      display="flex"
      alignItems="center"
      justifyContent="center"
      minHeight="100vh"
      bgcolor="#f4f6f8"
    >
      <Card sx={{ maxWidth: 400, width: '100%', boxShadow: 3, p: 2 }}>
        <CardContent>
          <Typography variant="h5" gutterBottom align="center">
            Reset Password
          </Typography>

          <Typography variant="body2" color="text.secondary" mb={3} align="center">
            Enter your new password to complete the reset process.
          </Typography>

          <TextField
            fullWidth
            type="password"
            label="New Password"
            variant="outlined"
            margin="normal"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />

          <Button
            fullWidth
            variant="contained"
            sx={{ mt: 2, bgcolor: '#0066FF' }}
            onClick={handleReset}
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} color="inherit" /> : 'Reset Password'}
          </Button>

          {message && (
            <Typography variant="body2" mt={2} color="primary" align="center">
              {message}
            </Typography>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}