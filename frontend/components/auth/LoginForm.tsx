import { Box, Button, Divider, TextField, Typography } from '@mui/material';

export default function LoginForm({ onSwitch }: { onSwitch: (mode: 'signup' | 'forgot') => void }) {
  return (
    <Box>
      <TextField fullWidth label="Email" variant="outlined" margin="normal" />
      <TextField fullWidth label="Password" variant="outlined" type="password" margin="normal" />

      <Button fullWidth variant="contained" sx={{ mt: 2, bgcolor: '#0066FF' }}>
        Login
      </Button>

      <Typography align="center" mt={2} fontSize="small" className="cursor-pointer" onClick={() => onSwitch('forgot')}>
        Forgot your password?
      </Typography>

      <Typography align="center" mt={1} fontSize="small">
        Don’t have an account? <span className="text-blue-600 cursor-pointer" onClick={() => onSwitch('signup')}>Join Us</span>
      </Typography>
    </Box>
  );
}
