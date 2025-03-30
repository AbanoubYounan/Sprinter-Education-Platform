const express = require('express');
const cors = require('cors');
const usersRoutes = require('./routes/usersRoutes')


const app = express();

app.use(express.json());

const allowedOrigins = ["http://localhost:3000"]; // Only allow our frontend

app.use(
  cors({
    origin: allowedOrigins, // Specific origins
    credentials: true, // Allow cookies & auth headers
    methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization"],
  })
);

// Enable preflight requests for all routes
app.options("*", cors());


app.use('/api/users', usersRoutes)

module.exports = app;
