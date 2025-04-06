'use client';
import { useEffect, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import axios from 'axios';
import { Box, Typography, Alert, Button, CircularProgress } from '@mui/material';
import { TURBOPACK_CLIENT_MIDDLEWARE_MANIFEST } from 'next/dist/shared/lib/constants';

export default function VerifyEmailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  const hasVerifiedRef = useRef(false); // Prevent double request

  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (!token || hasVerifiedRef.current) return;

    hasVerifiedRef.current = true; // Mark as verified

    const verifyEmail = async () => {
      try {
        const res = await axios.post('http://127.0.0.1:5000/api/auth/verify-email', {
          Token: token,
        });

        setStatus('success');
        setMessage(res.data.message || 'Email verified successfully!');
      } catch (err: any) {
        const errMsg =
          err?.response?.data?.Message ||
          err?.response?.data?.message ||
          'Something went wrong during verification.';
        setStatus('error');
        setMessage(errMsg);
      }
    };

    verifyEmail();
  }, [token]);

  return (
    <Box maxWidth="sm" mx="auto" mt={10} p={3} textAlign="center">
      <Typography variant="h5" mb={3}>
        Email Verification
      </Typography>

      {status === 'loading' && <CircularProgress />}

      {status !== 'loading' && (
        <>
          <Alert severity={status} sx={{ mb: 2 }}>
            {message}
          </Alert>

          {status != 'success' &&
            <Button variant="outlined" onClick={() => router.push(`/verify-email?token=${token}`)}>
              Try Again
            </Button>
          }
        </>
      )}
    </Box>
  );
}