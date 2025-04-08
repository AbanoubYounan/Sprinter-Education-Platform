const quering = require('../../config/db');

async function Enroll(UserID, CourseID) {
    const query = `
        INSERT INTO enrollments (
            user_ID, course_ID
        ) VALUES (?, ?)
    `;

    const values = [UserID, CourseID];
    try{
        await quering(query, values);
        return true;
    }catch(error){
        console.log('Error in Enroll')
        throw error
    }
};


module.exports = {
    Enroll
}