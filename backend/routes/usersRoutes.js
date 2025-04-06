const express = require('express');
const usersController = require('../controllers/usersControllers')

const router = express.Router();

router.post('/sign-up', usersController.StudentSignUp);

module.exports = router;


