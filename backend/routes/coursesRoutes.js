const express = require('express');
const coursesController = require('../controllers/coursesControllers')
const verifyToken = require('../utils/verifyToken')
const router = express.Router();

router.get('/', coursesController.getAllCourses);
router.get('/names', coursesController.getAllCoursesNames);
router.get('/lessons', coursesController.getAllCoursesAndLessons);
router.get('/:CourseID', verifyToken.verifyToken, coursesController.getCourseChapters)
router.get('/Chapter/:ChapterID', verifyToken.verifyToken, coursesController.getChapterContent)
router.put('/enroll', verifyToken.verifyToken, coursesController.Enroll)

module.exports = router;


