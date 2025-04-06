const quering = require('../../config/db');

async function getUserByEmail(Email) {

    const query = `
        SELECT * FROM users WHERE email = ? LIMIT 1
    `;

    const values = [Email];
    try{
        const rows = await quering(query, values);   
        return rows.length? rows[0]: null;
    }catch(error){
        console.log('Error in getUserByEmail')
        throw error
    }
};

module.exports = {
    getUserByEmail
}