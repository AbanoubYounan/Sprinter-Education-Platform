const quering = require('../../config/db');

async function checkEmailVerficationToken(Token) {

    const query = `
        SELECT user_ID, email_verification_expires FROM users WHERE email_verification_token = ?
    `;

    const values = [Token];
    try{
        const rows = await quering(query, values);   
        return rows.length? rows[0]: null;
    }catch(error){
        console.log('Error in checkEmailVerficationToken', error)
        throw error
    }
};

async function FindResetToken(Token) {
    const query = 'SELECT * FROM password_resets WHERE token = ? AND expires_at > NOW()'
    try{
        const rows = await quering(query, [Token]);
        return rows ? rows[0] : null;
    }catch(error){
        console.log('Error in FindResetToken', error)
        throw error
    }
}


module.exports = {
    checkEmailVerficationToken,
    FindResetToken
}