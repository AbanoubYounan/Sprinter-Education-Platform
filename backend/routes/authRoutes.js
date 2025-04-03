const express = require('express');
const usersController = require('../controllers/usersControllers')

const router = express.Router();

router.post('/sign-up', usersController.StudentSignUp);
router.post('/verify-email', usersController.VerifyEmail)
router.post('/login', usersController.Login)
router.post('/request-password-reset', usersController.requestPasswordReset)
router.post('/reset-password', usersController.resetPassword)

module.exports = router;


