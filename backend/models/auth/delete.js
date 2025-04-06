const quering = require('../../config/db');

async function deleteResetToken(email){
    const query = `DELETE FROM password_resets WHERE email = ?`
    await quering(query, [email])
}

module.exports = {
    deleteResetToken
}