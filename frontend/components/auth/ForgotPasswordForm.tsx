import { Box, Button, TextField, Typography } from '@mui/material';

export default function ForgotPasswordForm({ onSwitch }: { onSwitch: (mode: 'login') => void }) {
  return (
    <Box>
      <Typography variant="body2" color="textSecondary" mb={2}>
        Enter your email address and we’ll send you a link to reset your password.
      </Typography>

      <TextField fullWidth label="Email" variant="outlined" margin="normal" />

      <Button fullWidth variant="contained" sx={{ mt: 2, bgcolor: '#0066FF' }}>
        Send Reset Link
      </Button>

      <Typography align="center" mt={3} fontSize="small">
        Back to{' '}
        <span className="text-blue-600 cursor-pointer" onClick={() => onSwitch('login')}>
          Login
        </span>
      </Typography>
    </Box>
  );
}
