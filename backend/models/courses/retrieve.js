const quering = require('../../config/db');

async function getAllCourses(UserID=null) {
    try{
        let rows = []
        if(UserID){
            const query = `
                            SELECT 
                                c.course_ID,
                                c.course_title,
                                c.description,
                                c.category,
                                c.level,
                                c.instructor_id,
                                u.full_name AS instructor_name,
                                c.price,
                                c.thumbnail_url,
                                c.total_hours,
                                c.created_at,
                                IFNULL(AVG(r.rating), 0) AS average_rating,
                                COUNT(r.review_ID) AS review_count,
                                COALESCE(e.status, 'Not Enrolled') AS enrollment_status
                            FROM 
                                courses c
                            JOIN 
                                users u ON c.instructor_id = u.user_ID
                            LEFT JOIN 
                                course_reviews r ON c.course_ID = r.course_ID
                            LEFT JOIN 
                                enrollments e ON c.course_ID = e.course_ID AND e.user_ID = ?
                            GROUP BY 
                                c.course_ID,
                                c.course_title,
                                c.description,
                                c.category,
                                c.level,
                                c.instructor_id,
                                u.full_name,
                                c.price,
                                c.thumbnail_url,
                                c.total_hours,
                                c.created_at,
                                e.status;
            `
            rows = await quering(query, [UserID]);
        }else{
            const query = `
                            SELECT 
                            c.course_ID,
                            c.course_title,
                            c.description,
                            c.category,
                            c.level,
                            c.instructor_id,
                            u.full_name AS instructor_name,
                            c.price,
                            c.thumbnail_url,
                            c.total_hours,
                            c.created_at,
                            IFNULL(AVG(r.rating), 0) AS average_rating,
                            COUNT(r.review_ID) AS review_count
                        FROM 
                            courses c
                        JOIN 
                            users u ON c.instructor_id = u.user_ID
                        LEFT JOIN 
                            course_reviews r ON c.course_ID = r.course_ID
                        GROUP BY 
                            c.course_ID,
                            c.course_title,
                            c.description,
                            c.category,
                            c.level,
                            c.instructor_id,
                            u.full_name,
                            c.price,
                            c.thumbnail_url,
                            c.total_hours,
                            c.created_at;
            `
            rows = await quering(query);
        }
        return rows;
    }catch(error){
        console.log('Error in getAllCourses', error)
        throw error
    }
    
}

async function getCourseChapters(CourseID) {
    try{
        const query = `
            SELECT 
                ch.chapter_ID,
                ch.title,
                ch.description,
                ch.created_at,
                cc.position
            FROM 
                course_chapters cc
            JOIN 
                chapters ch ON cc.chapter_ID = ch.chapter_ID
            WHERE 
                cc.course_ID = ?
            ORDER BY 
                cc.position ASC;
        `
        const rows = await quering(query, [CourseID])
        return rows
    }catch{
        console.log('Error in getCourseChapters', error)
        throw error
    }
}

async function getChapterContent(ChapterID) {
    try{
        const query = `
            SELECT 
                co.content_ID,
                co.content_type,
                co.content_url,
                co.description,
                co.duration,
                co.created_at,
                cc.position
            FROM 
                chapter_content cc
            JOIN 
                content co ON cc.content_ID = co.content_ID
            WHERE 
                cc.chapter_ID = ?
            ORDER BY 
                cc.position ASC;
        `
        const rows = await quering(query, [ChapterID])
        return rows
    }catch{
        console.log('Error in getChapterContent', error)
        throw error
    }
}

module.exports = {
    getAllCourses,
    getCourseChapters,
    getChapterContent
}