const express = require('express');
const coursesController = require('../controllers/coursesControllers')

const router = express.Router();

router.get('/', coursesController.getAllCourses);

module.exports = router;


