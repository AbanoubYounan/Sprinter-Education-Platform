const express = require('express');
const usersController = require('../controllers/usersControllers')
const verifyToken = require('../utils/verifyToken')


const router = express.Router();

router.post('/login', usersController.login);

module.exports = router;


