const express = require('express');
const cors = require('cors');
// const usersRoutes = require('./routes/usersRoutes')
const authRoutes = require('./routes/authRoutes')
const coursesRoutes = require('./routes/coursesRoutes')
const chatsRoutes = require('./routes/chatsRoutes')


const app = express();

app.use(express.json());

const allowedOrigins = ["http://localhost:3010", "http://sprinter.mes-design.com/", "https://sprinter.mes-design.com"]; // Only allow our frontend

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


// app.use('/api/users', usersRoutes)
app.use('/api/auth', authRoutes)
app.use('/api/courses', coursesRoutes)
app.use('/api/chat', chatsRoutes)

module.exports = app;
