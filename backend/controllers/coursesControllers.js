const coursesModel = require('../models/courses/index')

exports.getAllCourses = async (_, res) => {
    try {
      const courses = await coursesModel.getAllCourses()
      return res.json({ courses: courses });
    } catch (error) {
      return res.status(500).json({ message: 'Server error', error });
    }
};
