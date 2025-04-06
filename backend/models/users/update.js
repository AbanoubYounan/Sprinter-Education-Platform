const quering = require('../../config/db');

async function VerifyUser(UserID) {
    const query = `
    UPDATE users SET verified = true, email_verification_token = NULL, email_verification_expires = NULL WHERE user_ID = ?
    `
    const values = [UserID]
    try{
        await quering(query, values);   
        return true;
    }catch(error){
        console.log('Error in VerifyUser', error)
        throw error
    }
    
}

async function UpdateEmailVerificationToken(EmailVerificationToken, EmailVerificationExpires, Email) {
    const query = `
    UPDATE users SET email_verification_token = ?, email_verification_expires = ? WHERE email = ?
    `
    const values = [EmailVerificationToken, EmailVerificationExpires, Email]
    try{
        await quering(query, values);   
        return true;
    }catch(error){
        console.log('Error in updateEmailVerificationToken', error)
        throw error
    }
    
}

async function updatePassword(Email, PasswordHash) {
    const query = 'UPDATE users SET password_hash = ? WHERE email = ?'
    try{
        await quering(query, [PasswordHash, Email]);
        return true;
    }catch{
        console.error("Error updating password:", error);
        throw error;
    }

}


module.exports = {
    VerifyUser,
    UpdateEmailVerificationToken,
    updatePassword
}