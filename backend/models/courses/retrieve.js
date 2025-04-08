const quering = require('../../config/db');

async function getAllCourses() {

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
    try{
        const rows = await quering(query);   
        return rows;
    }catch(error){
        console.log('Error in getAllCourses')
        throw error
    }
    
}

module.exports = {
    getAllCourses
}