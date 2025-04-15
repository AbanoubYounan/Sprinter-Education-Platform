const quering = require('../../config/db');

async function CreateNewSeesion(UserID, SessionID, Title) {
    const query = `
        INSERT INTO Sessions (user_ID, session_ID, title) VALUES (?, ?, ?)
    `;
    const values = [UserID, SessionID, Title];
    try{
        await quering(query, values);
        return true;
    }catch(error){
        console.log('Error in createNewSeesion', error)
        throw error
    }
}

module.exports = {
    CreateNewSeesion
}