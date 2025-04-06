const quering = require('../../config/db');

async function StoreResetToken(Email, Token, ExpiresAt) {
    const query = `
        INSERT INTO password_resets (email, token, expires_at) VALUES (?, ?, ?)
    `;
    const values = [Email, Token, ExpiresAt];
    try{
        await quering(query, values);
        return true;
    }catch(error){
        console.log('Error in storeResetToken', error)
        throw error
    }
}

module.exports = {
    StoreResetToken
}