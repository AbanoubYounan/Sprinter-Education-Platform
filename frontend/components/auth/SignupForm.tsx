import { Box, Button, Checkbox, Divider, FormControlLabel, TextField, Typography } from '@mui/material';

export default function SignupForm({ onSwitch }: { onSwitch: (mode: 'login') => void }) {
  return (
    <Box>
      <TextField fullWidth label="Email" variant="outlined" margin="normal" />

      <FormControlLabel
        control={<Checkbox defaultChecked />}
        label={
          <Typography fontSize="small">
            I agree to the <span className="text-gray-700 font-medium underline">terms and conditions</span>
          </Typography>
        }
      />

      <Button fullWidth variant="contained" sx={{ mt: 2, bgcolor: '#0066FF' }}>
        Join Us
      </Button>

      <Typography align="center" mt={2} fontSize="small">
        Already have an account?{' '}
        <span className="text-blue-600 cursor-pointer" onClick={() => onSwitch('login')}>
          Login
        </span>
      </Typography>
    </Box>
  );
}
