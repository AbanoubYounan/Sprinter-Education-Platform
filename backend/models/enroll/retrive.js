const quering = require('../../config/db');

async function checkEnrollment(UserID, CourseID) {
    const query =  `
                    SELECT 
                        CASE 
                            WHEN COUNT(*) > 0 THEN 'Enrolled'
                            ELSE 'Not Enrolled'
                        END AS enrollment_status
                    FROM 
                        enrollments
                    WHERE 
                        course_ID = ?
                        AND user_ID = ?;
                    `

    const values = [CourseID, UserID];
    try{
        const result = await quering(query, values);
        return (result[0]['enrollment_status'] == 'Enrolled');
    }catch(error){
        console.log('Error in Enroll')
        throw error
    }
};


module.exports = {
    checkEnrollment
}