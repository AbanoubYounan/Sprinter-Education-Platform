const coursesModel = require('../models/courses/index')
const enrollModel = require('../models/enroll/index')
const jwt = require('jsonwebtoken');


exports.getAllCourses = async (req, res) => {
    try {
      const token = req.headers['authorization'];
      if (!token) {
        const courses = await coursesModel.getAllCourses()
        return res.status(200).json({ courses: courses });
      }else{
        jwt.verify(token, process.env.JWT_SECRET, async (err, decoded) => {
            if (err) {
              const courses = await coursesModel.getAllCourses()
              return res.status(200).json({ courses: courses });
            }else{
              const UserID = decoded['UserID'];
              const courses = await coursesModel.getAllCourses(UserID)
              return res.status(200).json({ courses: courses });
            }
        });
      }
    } catch (error) {
      console.log('error in getAllCourses controller', error)
      return res.status(500).json({ message: 'Server error', error });
    }
};

exports.Enroll = async (req, res) => {
  try {
    const { CourseID } = req.body;
    const { UserID } = req.user;

    if(!CourseID || !UserID){
      return res.status(400).json({"Message": "Fields can't be empty."})
    }

    const isEnrolled = await enrollModel.checkEnrollment(UserID, CourseID)
    if(isEnrolled){
      return res.status(400).json({"Message": "You're already enrolled."})
    }
    await enrollModel.Enroll(UserID, CourseID)

    return res.status(201).json({ "Message": "Enrolled Successfuly" });

  } catch (error) {
    console.log('error in Enroll controller', error)
    return res.status(500).json({ message: 'Server error', error });
  }
}

exports.getCourseChapters = async (req, res) => {
  try {
    const { CourseID } = req.params;

    if(!CourseID){
      return res.status(400).json({"Message": "CourseID is Required"})
    }

    const result = await coursesModel.getCourseChapters(CourseID)
    return res.status(200).json({"Chapters": result})
  } catch (error) {
    console.log('error in getCourseChapters controller', error)
    return res.status(500).json({ message: 'Server error', error });
  }
}

exports.getChapterContent = async (req, res) => {
  try {
    const { ChapterID } = req.params;

    if(!ChapterID){
      return res.status(400).json({"Message": "ChapterID is Required"})
    }

    const result = await coursesModel.getChapterContent(ChapterID)
    return res.status(200).json({"Content": result})
  } catch (error) {
    console.log('error in getChapterContent controller', error)
    return res.status(500).json({ message: 'Server error', error });
  }
}
