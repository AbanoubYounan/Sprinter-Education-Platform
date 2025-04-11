const coursesModel = require('../models/courses/index')
const enrollModel = require('../models/enroll/index')
const jwt = require('jsonwebtoken');
const signURL = require('../utils/cdnSignURL')


exports.getAllCourses = async (req, res) => {
    try {
      const token = req.headers['authorization'];
      if (!token) {
        const courses = await coursesModel.getAllCourses()
        const coursesOBJ = {}
        for(const course of courses){
          coursesOBJ[course['course_ID']] = {
            'course_title': course['course_title'],
            'description': course['description'],
            'category': course['category'],
            'level': course['level'],
            'instructor_id': course['instructor_id'],
            'instructor_name': course['instructor_name'],
            'price': course['price'],
            'thumbnail_url': course['thumbnail_url'],
            'total_hours': course['total_hours'],
            'created_at': course['created_at'],
            'average_rating': course['average_rating'],
            'review_count': course['review_count']
          }
        }
        return res.status(200).json({ courses: coursesOBJ });
      }else{
        jwt.verify(token, process.env.JWT_SECRET, async (err, decoded) => {
            if (err) {
              const courses = await coursesModel.getAllCourses()
              return res.status(200).json({ courses: courses });
            }else{
              const UserID = decoded['UserID'];
              const courses = await coursesModel.getAllCourses(UserID)
              const coursesOBJ = {}
              for(const course of courses){
                coursesOBJ[course['course_ID']] = {
                  'course_title': course['course_title'],
                  'description': course['description'],
                  'category': course['category'],
                  'level': course['level'],
                  'instructor_id': course['instructor_id'],
                  'instructor_name': course['instructor_name'],
                  'price': course['price'],
                  'thumbnail_url': course['thumbnail_url'],
                  'total_hours': course['total_hours'],
                  'created_at': course['created_at'],
                  'average_rating': course['average_rating'],
                  'review_count': course['review_count'],
                  'enrollment_status': course['enrollment_status']
                }
              }
              return res.status(200).json({ courses: coursesOBJ });
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

    const chapters = await coursesModel.getCourseChapters(CourseID)
    const chaptersObj = {}
    for(const chapter of chapters){
      chaptersObj[`${chapter['position']}+${chapter['chapter_ID']}`] = {
        'title': chapter['title'],
        'description': chapter['description'],
        'created_at': chapter['created_at'],
        'position': chapter['position']
      }
    }
    return res.status(200).json({"Chapters": chaptersObj})
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

    const contents = await coursesModel.getChapterContent(ChapterID)
    const contentObj = {}
    for(const content of contents){
      let url = content['content_url'];
      if(content['content_type']=='pdf'){
        url = await signURL(`sprinter/${content['content_ID']}.pdf`)
      }
      contentObj[`${content['position']}+${content['content_ID']}`]={
        'content_title': content['content_title'],
        'content_type': content['content_type'],
        'content_url': url,
        'description': content['description'],
        'duration': content['duration'],
        'created_at': content['created_at'],
        'position': content['position']
      }
    }
    return res.status(200).json({"Content": contentObj})
  } catch (error) {
    console.log('error in getChapterContent controller', error)
    return res.status(500).json({ message: 'Server error', error });
  }
}
