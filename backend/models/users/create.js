const quering = require('../../config/db');

async function SignUp(FullName, Email, PasswordHash, Role, EmailVerificationToken, EmailVerificationExpires) {

    // Insert the user data into the database
    const query = `
        INSERT INTO users (
            full_name, email, password_hash, role, email_verification_token, email_verification_expires
        ) VALUES (?, ?, ?, ?, ?, ?)
    `;

    const values = [FullName, Email, PasswordHash, Role, EmailVerificationToken, EmailVerificationExpires];
    try{
        await quering(query, values);
        return true;
    }catch(error){
        console.log('Error in creating new user')
        throw error
    }
};


module.exports = {
    SignUp
}