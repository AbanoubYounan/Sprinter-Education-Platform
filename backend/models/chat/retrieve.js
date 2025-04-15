const quering = require('../../config/db');

async function GetAllSessions(UserID) {

    const query = `
        SELECT session_ID, title FROM Sessions WHERE user_ID = ?
    `;

    const values = [UserID];
    try{
        const rows = await quering(query, values);
        return rows.length? rows[0]: null;
    }catch(error){
        console.log('Error in GetAllSessions', error)
        throw error
    }
};

module.exports = {
    GetAllSessions
}